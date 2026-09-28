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

function Invoke-Horizon {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$HorizonArgs)
    if (Get-Command horizon -ErrorAction SilentlyContinue) {
        & horizon @HorizonArgs
        return $LASTEXITCODE
    }
    elseif (Get-Command py -ErrorAction SilentlyContinue) {
        & py -m horizon @HorizonArgs
        return $LASTEXITCODE
    }
    elseif (Get-Command python -ErrorAction SilentlyContinue) {
        & python -m horizon @HorizonArgs
        return $LASTEXITCODE
    }
    return $null
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
    Write-Host "Or launch via wrap:  horizon wrap claude --no-proxy --port $LocalPort"
}
else {
    Write-Host ""
    Write-Host "Launching Claude Code through Horizon (--no-proxy, port $LocalPort)..."
    $code = Invoke-Horizon wrap claude --no-proxy --port $LocalPort @ClaudeArgs
    if ($null -eq $code) {
        Write-Warning "horizon CLI not found. Set manually for this shell instead:"
        Write-Host "  `$env:ANTHROPIC_BASE_URL = 'http://127.0.0.1:$LocalPort'"
        Write-Host "  claude $($ClaudeArgs -join ' ')"
    }
    else {
        $exitCode = $code
    }
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
