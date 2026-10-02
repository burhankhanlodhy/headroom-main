<#
.SYNOPSIS
  Publish the built desktop installer to the dashboard's Downloads page.

.DESCRIPTION
  Uploads the NSIS installer and a latest.json (version, file, size, SHA-256,
  date) to the Pi 4, and stages an install script there. Installing into
  /var/www/contextshrink/releases needs sudo, so the script prints the one
  command to run. Earlier installers are kept; latest.json points at the new one.

  Run after desktop\build-installer.ps1, from PowerShell.
#>
param(
    [string]$Pi4 = "raspberrypi4@192.168.0.64"
)
$ErrorActionPreference = "Stop"

$app = Join-Path $PSScriptRoot "app"
$version = (Get-Content (Join-Path $app "src-tauri\tauri.conf.json") -Raw | ConvertFrom-Json).version
$installer = Get-ChildItem (Join-Path $app "src-tauri\target\release\bundle\nsis\*_${version}_x64-setup.exe") |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $installer) { throw "No installer for version $version. Run desktop\build-installer.ps1 first." }

$release = [ordered]@{
    version    = $version
    file       = $installer.Name
    size_bytes = $installer.Length
    sha256     = (Get-FileHash $installer.FullName -Algorithm SHA256).Hash.ToLower()
    released   = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
}
$staging = Join-Path ([IO.Path]::GetTempPath()) "cs-release-$version"
New-Item -ItemType Directory -Force $staging | Out-Null
$latest = Join-Path $staging "latest.json"
[IO.File]::WriteAllText($latest, ($release | ConvertTo-Json))

# Windows PowerShell 5.1 turns any stderr line from a native command (e.g.
# OpenSSH's harmless "IO is still pending on closed socket") into a terminating
# error under "Stop"; judge ssh/scp by their exit codes instead.
$ErrorActionPreference = "Continue"
function Assert-Ok([string]$what) {
    if ($LASTEXITCODE -ne 0) { throw "$what failed (exit $LASTEXITCODE)" }
}

$remote = ssh -o BatchMode=yes $Pi4 "mktemp -d /tmp/cs-release.XXXXXX" 2>$null
Assert-Ok "Creating the staging folder on the Pi 4"
$remote = "$remote".Trim()
scp -o BatchMode=yes -q $installer.FullName "${Pi4}:$remote/" 2>$null
Assert-Ok "Uploading the installer"
scp -o BatchMode=yes -q $latest "${Pi4}:$remote/" 2>$null
Assert-Ok "Uploading latest.json"

$script = @'
#!/bin/bash
# Install a staged ContextShrink release into the Downloads folder.
set -euo pipefail
SRC=__SRC__
DEST=/var/www/contextshrink/releases
sudo mkdir -p "$DEST"
sudo cp "$SRC"/*.exe "$DEST/"
sudo cp "$SRC/latest.json" "$DEST/latest.json"
sudo chown -R root:root "$DEST"
sudo chmod -R u=rwX,go=rX "$DEST"
rm -rf "$SRC"
echo "Published $(grep -o '"file": *"[^"]*"' "$DEST/latest.json")"
rm -f -- "$0"
'@ -replace "__SRC__", $remote
# Windows PowerShell 5.1 prefixes piped text with a UTF-8 BOM, which breaks the
# shebang: send BOM-less UTF-8, and strip CRs and any BOM on arrival as well.
$OutputEncoding = New-Object System.Text.UTF8Encoding $false
$script | ssh -o BatchMode=yes $Pi4 "tr -d '\r' | sed '1s/^\xEF\xBB\xBF//' > /tmp/cs-publish-release.sh && chmod 755 /tmp/cs-publish-release.sh && bash -n /tmp/cs-publish-release.sh" 2>$null
Assert-Ok "Staging the publish script"

"Staged $($installer.Name) ($([math]::Round($installer.Length / 1MB)) MB, sha256 $($release.sha256))"
"Run this to publish (asks for the Pi 4 sudo password):"
"  ssh -t $Pi4 /tmp/cs-publish-release.sh"
