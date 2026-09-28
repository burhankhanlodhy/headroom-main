<#
.SYNOPSIS
  Connect to a Horizon proxy running on a VPS and launch Claude Code through it.

.DESCRIPTION
  1. Opens a background SSH tunnel: localhost:<LocalPort> -> VPS loopback <RemotePort>.
  2. Waits for the remote proxy to answer /readyz through the tunnel.
  3. Runs `horizon wrap claude --no-proxy --port <LocalPort>` (extra args pass through
     to Claude Code), so wrap configures base URL + MCP without spawning a local proxy.

  Assumes the VPS proxy is published on the VPS loopback only (e.g. Docker
  -p 127.0.0.1:8787:8787). The tunnel is the security boundary; no proxy token needed.

.EXAMPLE
  .\connect-horizon-vps.ps1 -VpsHost user@203.0.113.10
  .\connect-horizon-vps.ps1 -VpsHost user@203.0.113.10 -LocalPort 18787 -- --resume
  .\connect-horizon-vps.ps1 -VpsHost user@203.0.113.10 -NoLaunch
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$VpsHost,

    [int]$RemotePort = 8787,
    [int]$LocalPort = 8787,
    [string]$SshKey,

    [switch]$NoLaunch,
    [switch]$KillTunnelOnExit,

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ClaudeArgs
)

$ErrorActionPreference = "Stop"
$StateFile = Join-Path $env:USERPROFILE ".horizon\vps-tunnel-state.json"

function Test-PortListening([int]$Port) {
    [bool](Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}

# Reuse a live tunnel from a previous run instead of starting a second one.
$reuseTunnel = $false
if (Test-Path $StateFile) {
    $state = Get-Content $StateFile -Raw | ConvertFrom-Json
    $proc = Get-Process -Id $state.SshPid -ErrorAction SilentlyContinue
    if ($proc -and -not $proc.HasExited) {
        Write-Host "Reusing existing tunnel to $($state.VpsHost) on local port $($state.LocalPort)."
        $LocalPort = $state.LocalPort
        $reuseTunnel = $true
    }
    else {
        Remove-Item $StateFile -Force
    }
}

if (-not $reuseTunnel) {
    if (Test-PortListening $LocalPort) {
        Write-Error "Local port $LocalPort is already in use. Pick another with -LocalPort (e.g. 18787)."
    }

    $sshArgs = @(
        "-N",
        "-L", "${LocalPort}:127.0.0.1:${RemotePort}",
        "-o", "ServerAliveInterval=15",
        "-o", "ServerAliveCountMax=3",
        "-o", "ExitOnForwardFailure=yes",
        "-o", "StrictHostKeyChecking=accept-new",
        $VpsHost
    )
    if ($SshKey) { $sshArgs = @("-i", $SshKey) + $sshArgs }

    Write-Host "Opening tunnel ${LocalPort} -> ${VpsHost}:${RemotePort}..."
    $ssh = Start-Process ssh -ArgumentList $sshArgs -WindowStyle Hidden -PassThru

    $ready = $false
    for ($i = 0; $i -lt 15; $i++) {
        if ($ssh.HasExited) { break }
        try {
            $resp = Invoke-WebRequest -Uri "http://127.0.0.1:${LocalPort}/readyz" -UseBasicParsing -TimeoutSec 2
            if ($resp.StatusCode -eq 200) { $ready = $true; break }
        }
        catch {
            Start-Sleep -Seconds 1
        }
    }

    if (-not $ready) {
        $sshExitCode = $ssh.ExitCode
        Stop-Process -Id $ssh.Id -Force -ErrorAction SilentlyContinue
        Remove-Item $StateFile -Force -ErrorAction SilentlyContinue
        if ($ssh.HasExited) {
            Write-Error ("SSH exited before the tunnel was ready (exit code {0}). " +
                "If the VPS asks for a password, a hidden window cannot prompt for it - " +
                "set up key auth or run 'ssh $VpsHost exit' once interactively." -f $sshExitCode)
        }
        Write-Error "Tunnel is up but the proxy did not answer /readyz on the VPS. Is the container running?"
    }

    New-Item -Path (Split-Path $StateFile) -ItemType Directory -Force | Out-Null
    [pscustomobject]@{
        VpsHost    = $VpsHost
        RemotePort = $RemotePort
        LocalPort  = $LocalPort
        SshPid     = $ssh.Id
        StartedAt  = (Get-Date).ToString("o")
    } | ConvertTo-Json | Set-Content $StateFile -Encoding utf8
    Write-Host "Tunnel ready (ssh pid $($ssh.Id))."
}

$exitCode = 0
if ($NoLaunch) {
    Write-Host ""
    Write-Host "Tunnel only. Point your client at:  http://127.0.0.1:$LocalPort"
    Write-Host "Or relaunch with Claude:  .\connect-horizon-vps.ps1 -VpsHost $VpsHost -LocalPort $LocalPort"
}
else {
    Write-Host ""
    Write-Host "Launching Claude Code through Horizon (tunnel port $LocalPort)..."
    if (-not (Get-Command claude -ErrorAction SilentlyContinue)) {
        Write-Warning "claude not found in PATH. Set manually for this shell instead:"
        Write-Host "  `$env:ANTHROPIC_BASE_URL = 'http://127.0.0.1:$LocalPort'"
        Write-Host "  claude $($ClaudeArgs -join ' ')"
        exit 1
    }
    # Lean direct launch: claude must inherit THIS console's stdin or it
    # silently falls back to --print mode ("Input must be provided..."),
    # so claude stays a direct child of this console. Tunnel mode needs no
    # local proxy or MCP setup.
    $env:ANTHROPIC_BASE_URL = "http://127.0.0.1:$LocalPort"
    $env:ENABLE_TOOL_SEARCH = "true"

    # Also route durably through Claude's user settings: the API client did
    # not pick the base URL up from process env alone (the proxy stayed at
    # zero requests), while the settings env block is applied on every
    # claude start. Original values are restored when the session ends.
    $settingsPath = Join-Path $env:USERPROFILE ".claude\settings.json"
    $savedBase = $null
    $savedTool = $null
    $createdSettings = $false
    $settingsPatched = $false
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    if (Test-Path $settingsPath) {
        try {
            $settings = Get-Content $settingsPath -Raw | ConvertFrom-Json
            if ($settings.PSObject.Properties["env"]) {
                if ($settings.env.PSObject.Properties["ANTHROPIC_BASE_URL"]) { $savedBase = $settings.env.ANTHROPIC_BASE_URL }
                if ($settings.env.PSObject.Properties["ENABLE_TOOL_SEARCH"]) { $savedTool = $settings.env.ENABLE_TOOL_SEARCH }
            }
            else {
                $settings | Add-Member -NotePropertyName env -NotePropertyValue ([pscustomobject]@{})
            }
            if ($settings.env.PSObject.Properties["ANTHROPIC_BASE_URL"]) { $settings.env.ANTHROPIC_BASE_URL = $env:ANTHROPIC_BASE_URL }
            else { $settings.env | Add-Member -NotePropertyName ANTHROPIC_BASE_URL -NotePropertyValue $env:ANTHROPIC_BASE_URL }
            if ($settings.env.PSObject.Properties["ENABLE_TOOL_SEARCH"]) { $settings.env.ENABLE_TOOL_SEARCH = "true" }
            else { $settings.env | Add-Member -NotePropertyName ENABLE_TOOL_SEARCH -NotePropertyValue "true" }
            [IO.File]::WriteAllText($settingsPath, ($settings | ConvertTo-Json -Depth 20), $utf8NoBom)
            $settingsPatched = $true
        }
        catch {
            Write-Warning "Could not patch $settingsPath ($($_.Exception.Message)); relying on environment variables only."
        }
    }
    else {
        [IO.File]::WriteAllText($settingsPath, (@{ env = [pscustomobject]@{ ANTHROPIC_BASE_URL = $env:ANTHROPIC_BASE_URL; ENABLE_TOOL_SEARCH = "true" } } | ConvertTo-Json -Depth 20), $utf8NoBom)
        $createdSettings = $true
        $settingsPatched = $true
    }

    try {
        if ($ClaudeArgs) { & claude @ClaudeArgs } else { & claude }
        $exitCode = $LASTEXITCODE
        if ($null -eq $exitCode) { $exitCode = 1 }
    }
    finally {
        if ($settingsPatched) {
            try {
                if ($createdSettings) {
                    [IO.File]::WriteAllText($settingsPath, "{}", $utf8NoBom)
                }
                else {
                    $settings = Get-Content $settingsPath -Raw | ConvertFrom-Json
                    if (-not $settings.PSObject.Properties["env"]) {
                        $settings | Add-Member -NotePropertyName env -NotePropertyValue ([pscustomobject]@{})
                    }
                    foreach ($pair in @(@("ANTHROPIC_BASE_URL", $savedBase), @("ENABLE_TOOL_SEARCH", $savedTool))) {
                        $name = $pair[0]
                        $old = $pair[1]
                        if ($null -ne $old) {
                            if ($settings.env.PSObject.Properties[$name]) { $settings.env.$name = $old }
                            else { $settings.env | Add-Member -NotePropertyName $name -NotePropertyValue $old }
                        }
                        elseif ($settings.env.PSObject.Properties[$name]) {
                            $settings.env.PSObject.Properties.Remove($name)
                        }
                    }
                    [IO.File]::WriteAllText($settingsPath, ($settings | ConvertTo-Json -Depth 20), $utf8NoBom)
                }
            }
            catch {
                Write-Warning "Could not restore ${settingsPath}: $($_.Exception.Message)"
            }
        }
    }
    Remove-Item Env:ANTHROPIC_BASE_URL -ErrorAction SilentlyContinue
    Remove-Item Env:ENABLE_TOOL_SEARCH -ErrorAction SilentlyContinue
}

if ($KillTunnelOnExit) {
    & $PSScriptRoot\disconnect-horizon-vps.ps1
}
else {
    Write-Host ""
    Write-Host "Tunnel left running. To disconnect and undo the wrap:"
    Write-Host "  .\disconnect-horizon-vps.ps1"
}

exit $exitCode
