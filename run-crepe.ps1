[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)

$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $RootDir "backend"
$FrontendDir = Join-Path $RootDir "frontend"
$VenvPython = Join-Path $RootDir ".venv\Scripts\python.exe"
$VenvUvicorn = Join-Path $RootDir ".venv\Scripts\uvicorn.exe"

function Show-Usage {
    Write-Host "Usage:"
    Write-Host "  .\run-crepe.ps1 run [pipeline] [extra args]"
    Write-Host "  .\run-crepe.ps1 web"
    Write-Host "  .\run-crepe.ps1 stop"
    Write-Host "  .\run-crepe.ps1 status [--limit N]"
    Write-Host "  .\run-crepe.ps1 pause [run_id]"
    Write-Host "  .\run-crepe.ps1 cancel [run_id]"
    Write-Host "  .\run-crepe.ps1 resume [run_id]"
    Write-Host ""
    Write-Host "Pipelines for run: all (default), extract, normalize, analyze, suggest, demo"
}

function Require-Runtime {
    if (!(Test-Path $VenvPython)) {
        throw "Python runtime not found at $VenvPython. Run install.ps1 first."
    }
}

function Ensure-DefaultRuntimePaths {
    if ([string]::IsNullOrWhiteSpace($env:CREPE_CONFIG_DIR)) {
        $env:CREPE_CONFIG_DIR = Join-Path $env:APPDATA "crepe"
    }
    if ([string]::IsNullOrWhiteSpace($env:CREPE_BASE_DIR)) {
        $env:CREPE_BASE_DIR = Join-Path $env:CREPE_CONFIG_DIR "data"
    }
    if ([string]::IsNullOrWhiteSpace($env:CREPE_DB_PATH)) {
        $env:CREPE_DB_PATH = Join-Path $env:CREPE_BASE_DIR "crepe.sqlite3"
    }
    if (!(Test-Path $env:CREPE_BASE_DIR)) {
        New-Item -ItemType Directory -Path $env:CREPE_BASE_DIR -Force | Out-Null
    }
}

function Get-PidFilePath {
    return (Join-Path $env:CREPE_CONFIG_DIR "web.pids.json")
}

function Require-GraphCredentials {
    Push-Location $BackendDir
    try {
        $env:PYTHONPATH = "."
        & $VenvPython -c "from crepe.config import load_config, validate_credentials; validate_credentials(load_config())" *> $null
        if ($LASTEXITCODE -ne 0) {
            throw "Missing required Graph credentials. Open Setup in the web UI and save credentials."
        }
    }
    finally {
        Pop-Location
    }
}

function Require-NoActiveJob {
    Push-Location $BackendDir
    try {
        $env:PYTHONPATH = "."
        & $VenvPython -c "from crepe.config import load_config; from crepe.storage.db import RunDatabase; cfg=load_config(); db=RunDatabase(cfg.db_path); raise SystemExit(1 if db.latest_run_by_status(('running','paused')) else 0)"
        if ($LASTEXITCODE -ne 0) {
            throw "Another job is active (running or paused). Use 'crepe status' and pause/cancel/resume as needed."
        }
    }
    finally {
        Pop-Location
    }
}

function Write-PidFile([int]$BackendPid, [int]$FrontendPid) {
    $payload = @{
        backend_pid = $BackendPid
        frontend_pid = $FrontendPid
        started_at = [DateTimeOffset]::UtcNow.ToString("o")
    }
    $pidFile = Get-PidFilePath
    $payload | ConvertTo-Json | Set-Content -Path $pidFile -Encoding UTF8
}

function Read-PidPayload {
    $pidFile = Get-PidFilePath
    if (!(Test-Path $pidFile)) {
        return $null
    }
    try {
        return Get-Content -Raw -Path $pidFile | ConvertFrom-Json
    }
    catch {
        return $null
    }
}

function Test-PidRunning([int]$Pid) {
    try {
        $proc = Get-Process -Id $Pid -ErrorAction Stop
        return $null -ne $proc
    }
    catch {
        return $false
    }
}

function Stop-TrackedServices {
    $payload = Read-PidPayload
    if ($null -ne $payload) {
        foreach ($pid in @($payload.backend_pid, $payload.frontend_pid)) {
            if ($pid -and (Test-PidRunning -Pid $pid)) {
                Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
            }
        }
    }
    $pidFile = Get-PidFilePath
    if (Test-Path $pidFile) {
        Remove-Item -Force $pidFile
    }
}

function Show-ServiceStatus {
    Write-Host "Service status:"
    $payload = Read-PidPayload
    if ($null -eq $payload) {
        Write-Host "- web: not tracked"
        return
    }

    if ($payload.backend_pid) {
        if (Test-PidRunning -Pid $payload.backend_pid) {
            Write-Host "- backend: running (pid=$($payload.backend_pid))"
        }
        else {
            Write-Host "- backend: stopped (stale pid=$($payload.backend_pid))"
        }
    }

    if ($payload.frontend_pid) {
        if (Test-PidRunning -Pid $payload.frontend_pid) {
            Write-Host "- frontend: running (pid=$($payload.frontend_pid))"
        }
        else {
            Write-Host "- frontend: stopped (stale pid=$($payload.frontend_pid))"
        }
    }
}

if ($Args.Count -eq 0) {
    Show-Usage
    exit 1
}

Require-Runtime
Ensure-DefaultRuntimePaths

$mode = $Args[0]
$rest = @()
if ($Args.Count -gt 1) {
    $rest = $Args[1..($Args.Count - 1)]
}

switch ($mode) {
    "run" {
        $pipeline = "all"
        if ($rest.Count -gt 0 -and -not $rest[0].StartsWith("-")) {
            $pipeline = $rest[0]
            if ($rest.Count -gt 1) {
                $rest = $rest[1..($rest.Count - 1)]
            }
            else {
                $rest = @()
            }
        }

        if ($pipeline -notin @("all", "extract", "normalize", "analyze", "suggest", "demo")) {
            throw "Unknown pipeline: $pipeline"
        }

        if ($pipeline -in @("all", "extract")) {
            Require-GraphCredentials
        }
        Require-NoActiveJob

        Push-Location $BackendDir
        try {
            $env:PYTHONPATH = "."
            & $VenvPython -m crepe.cli $pipeline @rest
            exit $LASTEXITCODE
        }
        finally {
            Pop-Location
        }
    }
    "cli" {
        & $PSCommandPath run @rest
        exit $LASTEXITCODE
    }
    "web" {
        if (!(Test-Path $VenvUvicorn)) {
            throw "uvicorn not found at $VenvUvicorn. Install backend dependencies first."
        }

        $nodeModulesPath = Join-Path $FrontendDir "node_modules"
        if (!(Test-Path $nodeModulesPath)) {
            throw "Missing frontend dependencies at $nodeModulesPath. Run npm install in frontend/."
        }

        if (Test-Path (Get-PidFilePath)) {
            Write-Host "Found existing web pid file. Stopping tracked services first."
            Stop-TrackedServices
        }

        Write-Host "Backend API:   http://127.0.0.1:8000"
        Write-Host "Frontend UI:   http://127.0.0.1:5173"
        Write-Host "PID file:      $(Get-PidFilePath)"
        Write-Host "Press Ctrl+C to stop both services."

        $backendProc = $null
        $frontendProc = $null
        try {
            $backendProc = Start-Process -FilePath $VenvUvicorn -WorkingDirectory $BackendDir -ArgumentList "crepe.api.app:create_app", "--factory", "--host", "127.0.0.1", "--port", "8000" -PassThru
            $frontendProc = Start-Process -FilePath "npm" -WorkingDirectory $FrontendDir -ArgumentList "run", "dev", "--", "--host", "127.0.0.1", "--port", "5173" -PassThru
            Write-PidFile -BackendPid $backendProc.Id -FrontendPid $frontendProc.Id
            Wait-Process -Id $backendProc.Id, $frontendProc.Id
        }
        finally {
            Stop-TrackedServices
        }
    }
    "stop" {
        Stop-TrackedServices
        Write-Host "Stopped tracked crepe web services."
    }
    "kill" {
        Stop-TrackedServices
        Write-Host "Stopped tracked crepe web services."
    }
    "status" {
        $limit = "10"
        if ($rest.Count -ge 2 -and $rest[0] -eq "--limit") {
            $limit = $rest[1]
        }

        Show-ServiceStatus
        Write-Host ""
        Push-Location $BackendDir
        try {
            $env:PYTHONPATH = "."
            & $VenvPython -m crepe.control_cli status --limit $limit
        }
        finally {
            Pop-Location
        }
    }
    "pause" {
        Push-Location $BackendDir
        try {
            $env:PYTHONPATH = "."
            if ($rest.Count -ge 1) {
                & $VenvPython -m crepe.control_cli pause --run-id $rest[0]
            }
            else {
                & $VenvPython -m crepe.control_cli pause
            }
        }
        finally {
            Pop-Location
        }
    }
    "cancel" {
        Push-Location $BackendDir
        try {
            $env:PYTHONPATH = "."
            if ($rest.Count -ge 1) {
                & $VenvPython -m crepe.control_cli cancel --run-id $rest[0]
            }
            else {
                & $VenvPython -m crepe.control_cli cancel
            }
        }
        finally {
            Pop-Location
        }
    }
    "resume" {
        Push-Location $BackendDir
        try {
            $env:PYTHONPATH = "."
            if ($rest.Count -ge 1) {
                & $VenvPython -m crepe.control_cli resume --run-id $rest[0]
            }
            else {
                & $VenvPython -m crepe.control_cli resume
            }
        }
        finally {
            Pop-Location
        }
    }
    default {
        throw "Unknown mode: $mode"
    }
}
