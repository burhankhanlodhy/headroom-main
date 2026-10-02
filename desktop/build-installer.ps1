<#
.SYNOPSIS
  Build the ContextShrink Windows installer (NSIS .exe).

.DESCRIPTION
  1. Freezes the Horizon client (client\build-client.ps1) so users need no Python.
  2. Builds the Tauri app, bundling the client as a resource.
  Output: app\src-tauri\target\release\bundle\nsis\ContextShrink_<version>_x64-setup.exe
#>
$ErrorActionPreference = "Stop"

& (Join-Path $PSScriptRoot "client\build-client.ps1")

Push-Location (Join-Path $PSScriptRoot "app")
try {
    $ErrorActionPreference = "Continue"
    npm ci
    if ($LASTEXITCODE -ne 0) { throw "npm ci failed" }
    npx tauri build
    if ($LASTEXITCODE -ne 0) { throw "tauri build failed" }
}
finally {
    Pop-Location
}

Get-ChildItem (Join-Path $PSScriptRoot "app\src-tauri\target\release\bundle\nsis\*.exe") |
    ForEach-Object { "Installer: {0} ({1:N0} MB)" -f $_.FullName, ($_.Length / 1MB) }
