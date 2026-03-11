[CmdletBinding()]
param(
    [string]$RepoUrl = "https://github.com/alg0s/crepe.git",
    [string]$InstallDir = "$env:LOCALAPPDATA\crepe",
    [string]$BinDir = "$HOME\.local\bin"
)

$ErrorActionPreference = "Stop"

function Require-Command([string]$Name) {
    if (!(Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Missing required command: $Name"
    }
}

Require-Command "git"
Require-Command "python"
Require-Command "npm"

if (Test-Path (Join-Path $InstallDir ".git")) {
    Write-Host "Updating existing install at $InstallDir"
    git -C $InstallDir fetch --all --tags
    git -C $InstallDir pull --ff-only
}
else {
    if (Test-Path $InstallDir) {
        Remove-Item -Recurse -Force $InstallDir
    }
    Write-Host "Cloning $RepoUrl into $InstallDir"
    git clone $RepoUrl $InstallDir
}

$venvPython = Join-Path $InstallDir ".venv\Scripts\python.exe"
if (!(Test-Path $venvPython)) {
    python -m venv (Join-Path $InstallDir ".venv")
}

& $venvPython -m pip install --upgrade pip
& (Join-Path $InstallDir ".venv\Scripts\pip.exe") install -r (Join-Path $InstallDir "requirements.txt")

Push-Location (Join-Path $InstallDir "frontend")
try {
    npm install
}
finally {
    Pop-Location
}

$configDir = Join-Path $env:APPDATA "crepe"
if (!(Test-Path $configDir)) {
    New-Item -ItemType Directory -Path $configDir | Out-Null
}
$dataDir = Join-Path $configDir "data"
if (!(Test-Path $dataDir)) {
    New-Item -ItemType Directory -Path $dataDir | Out-Null
}
$envFile = Join-Path $configDir ".env"
if (!(Test-Path $envFile)) {
    New-Item -ItemType File -Path $envFile | Out-Null
}
try {
    icacls $envFile /inheritance:r /grant:r "$($env:USERNAME):(R,W)" | Out-Null
}
catch {
    Write-Host "Could not apply strict ACL to $envFile; continuing."
}

$env:CREPE_CONFIG_DIR = $configDir
$env:CREPE_BASE_DIR = $dataDir
$env:CREPE_DB_PATH = Join-Path $dataDir "crepe.sqlite3"
Push-Location (Join-Path $InstallDir "backend")
try {
    $env:PYTHONPATH = "."
    & $venvPython -c "from crepe.config import load_config; from crepe.storage.db import RunDatabase; cfg=load_config(); RunDatabase(cfg.db_path); print(cfg.db_path)"
}
finally {
    Pop-Location
}

if (!(Test-Path $BinDir)) {
    New-Item -ItemType Directory -Path $BinDir -Force | Out-Null
}

$launcherPs1Path = Join-Path $BinDir "crepe.ps1"
$launcherPs1 = @"
`$script = "$InstallDir\\run-crepe.ps1"
& powershell -NoProfile -ExecutionPolicy Bypass -File `$script @args
"@
Set-Content -Path $launcherPs1Path -Value $launcherPs1 -Encoding UTF8

$launcherCmdPath = Join-Path $BinDir "crepe.cmd"
$launcherCmd = @"
@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "$InstallDir\run-crepe.ps1" %*
"@
Set-Content -Path $launcherCmdPath -Value $launcherCmd -Encoding ASCII

Write-Host "Installed crepe launchers at:"
Write-Host "  $launcherPs1Path"
Write-Host "  $launcherCmdPath"
Write-Host "Config directory: $configDir"
Write-Host "SQLite job DB: $($env:CREPE_DB_PATH)"
if ($env:PATH -notlike "*$BinDir*") {
    Write-Host "Add this directory to PATH: $BinDir"
}
Write-Host ""
Write-Host "Next steps:"
Write-Host "  crepe web"
