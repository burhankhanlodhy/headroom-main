<#
.SYNOPSIS
  Undo connect-headroom-vps.ps1: close the SSH tunnel and restore Claude Code settings.

.DESCRIPTION
  1. Stops the background SSH tunnel recorded in the state file.
  2. Runs `headroom unwrap claude --port <LocalPort> --no-stop-proxy`, which removes
     the Headroom MCP servers, managed hooks, self-heal hook, and restores the
     previous ANTHROPIC_BASE_URL in .claude/settings.local.json.
     --no-stop-proxy is mandatory here: the proxy is remote, and without the flag
     unwrap would try to identify and kill whatever answers on the local port.

.EXAMPLE
  .\disconnect-headroom-vps.ps1
  .\disconnect-headroom-vps.ps1 -LocalPort 18787     # when no state file exists
  .\disconnect-headroom-vps.ps1 -KeepMcp             # keep the headroom_retrieve MCP
#>
[CmdletBinding()]
param(
    [int]$LocalPort = 0,
    [switch]$KeepMcp
)

$ErrorActionPreference = "Continue"
$StateFile = Join-Path $env:USERPROFILE ".headroom\vps-tunnel-state.json"

function Test-PortListening([int]$Port) {
    [bool](Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}

function Invoke-Headroom {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$HeadroomArgs)
    if (Get-Command headroom -ErrorAction SilentlyContinue) {
        & headroom @HeadroomArgs
        return $LASTEXITCODE
    }
    elseif (Get-Command py -ErrorAction SilentlyContinue) {
        & py -m headroom @HeadroomArgs
        return $LASTEXITCODE
    }
    elseif (Get-Command python -ErrorAction SilentlyContinue) {
        & python -m headroom @HeadroomArgs
        return $LASTEXITCODE
    }
    return $null
}

$state = $null
if (Test-Path $StateFile) {
    $state = Get-Content $StateFile -Raw | ConvertFrom-Json
}
if (-not $LocalPort) {
    if ($state) { $LocalPort = $state.LocalPort } else { $LocalPort = 8787 }
}

Write-Host ""
Write-Host "Disconnecting Headroom VPS tunnel (local port $LocalPort)..."

if ($state) {
    $proc = Get-Process -Id $state.SshPid -ErrorAction SilentlyContinue
    if ($proc -and -not $proc.HasExited) {
        Stop-Process -Id $state.SshPid -Force
        for ($i = 0; $i -lt 10 -and (Test-PortListening $LocalPort); $i++) {
            Start-Sleep -Milliseconds 500
        }
        Write-Host "Tunnel to $($state.VpsHost) closed."
    }
    else {
        Write-Host "Tunnel process was already gone."
    }
    Remove-Item $StateFile -Force -ErrorAction SilentlyContinue
}
elseif (Test-PortListening $LocalPort) {
    Write-Warning "Something is still listening on local port $LocalPort but no state file was found - not killing it. Close it manually if it is a leftover tunnel."
}
else {
    Write-Host "No state file and nothing listening on port $LocalPort; nothing to tear down."
}

Write-Host ""
$unwrapArgs = @("unwrap", "claude", "--port", $LocalPort, "--no-stop-proxy")
if ($KeepMcp) { $unwrapArgs += "--keep-mcp" }
$code = Invoke-Headroom @unwrapArgs
if ($null -eq $code) {
    Write-Warning "headroom CLI not found; skipping unwrap. Leftover wrap config may remain in:"
    Write-Host "  .claude\settings.local.json  (remove the headroom base-url entry, or rerun"
    Write-Host "  this script after installing headroom - its self-heal hook also self-cleans"
    Write-Host "  on the next Claude session start)."
}

if ($env:ANTHROPIC_BASE_URL) {
    Write-Warning "ANTHROPIC_BASE_URL is still set in this shell ('$env:ANTHROPIC_BASE_URL')."
    Write-Host "  Clear it with:  Remove-Item Env:ANTHROPIC_BASE_URL"
}

Write-Host ""
Write-Host "Done. Claude Code is back on its normal endpoint."
