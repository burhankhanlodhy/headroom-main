<#
.SYNOPSIS
  Connect to the Horizon proxy on the VPS/Pi and launch OpenCode through it.

.DESCRIPTION
  The OpenCode analog of connect-horizon-vps.ps1:

  1. Opens (or reuses) the SSH tunnel: localhost:<LocalPort> -> remote loopback <RemotePort>.
     Delegates to connect-horizon-vps.ps1 -NoLaunch, so all tunnel state handling
     (reuse, /readyz wait, port checks) is identical to the Claude flow.
  2. Runs `horizon wrap opencode --no-proxy --port <LocalPort>` from the repo venv.
     Wrap injects the Horizon provider block + horizon MCP server + Serena into
     OpenCode's config (~/.config/opencode/opencode.json, snapshotted first),
     then launches opencode as a child. --no-proxy is mandatory: the proxy is
     remote; without it wrap would spawn a second, local proxy on the port.
  3. On exit, runs `horizon unwrap opencode` to restore the pre-wrap config.

.EXAMPLE
  .\connect-horizon-vps-opencode.ps1 -VpsHost raspberrypi5@192.168.0.71
  .\connect-horizon-vps-opencode.ps1 -VpsHost raspberrypi5@192.168.0.71 -- --resume
  .\connect-horizon-vps-opencode.ps1 -VpsHost user@pi -KillTunnelOnExit
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$VpsHost,

    [int]$RemotePort = 8787,
    [int]$LocalPort = 18787,
    [switch]$KillTunnelOnExit,

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$OpencodeArgs
)

$ErrorActionPreference = "Stop"

$repoPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $repoPython)) {
    Write-Error "Repo venv not found at $repoPython. Run scripts\bootstrap-windows-dev.ps1 first (wrap opencode needs the horizon CLI)."
}
if (-not (Get-Command opencode -ErrorAction SilentlyContinue)) {
    Write-Error "'opencode' not found in PATH. Install OpenCode first: https://opencode.ai"
}

# 1. Tunnel only - never launch Claude here.
& $PSScriptRoot\connect-horizon-vps.ps1 -VpsHost $VpsHost -RemotePort $RemotePort -LocalPort $LocalPort -NoLaunch
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# 2. Wrap OpenCode through the tunnel. Extra args after `--` pass through to opencode.
$horizonArgs = @("-m", "horizon.cli", "wrap", "opencode", "--no-proxy", "--port", "$LocalPort", "--")
if ($OpencodeArgs) { $horizonArgs += $OpencodeArgs }

$exitCode = 0
try {
    Write-Host ""
    Write-Host "Launching OpenCode through Horizon (tunnel port $LocalPort)..."
    & $repoPython @horizonArgs
    if finally {
    # 3. Restore the pre-wrap OpenCode config. --no-stop-proxy is mandatory:
    # the proxy is remote; without it unwrap may kill whatever answers on the
    # local port - which here is the SSH tunnel itself.
    Write-Host ""
    Write-Host "Restoring OpenCode config..."
    & $repoPython -m horizon.cli unwrap opencode --port $LocalPort --no-stop-proxy
}e config..."
    & $repoPython -m horizon.cli unwrap opencode
}

if ($KillTunnelOnExit) {
    & $PSScriptRoot\disconnect-horizon-vps.ps1
}
else {
    Write-Host ""
    Write-Host "Tunnel left running. To close it:"
    Write-Host "  .\disconnect-horizon-vps.ps1"
}

exit $exitCode
