$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root 'backend'
$Frontend = Join-Path $Root 'frontend'
$Venv = Join-Path $Backend '.venv'

function Require-Command([string]$Name, [string]$Hint) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "$Name was not found. $Hint"
    }
}

Write-Host "ResumeIQ 2.2 setup" -ForegroundColor Cyan
Write-Host "Project: $Root"

Require-Command 'node' 'Install Node.js 24.19.0 or another supported Node 24 release.'
Require-Command 'npm' 'Install npm with Node.js.'
Require-Command 'docker' 'Install Docker Desktop and start the Docker Engine.'

$PythonExe = Join-Path $Venv 'Scripts\python.exe'
if (Test-Path $PythonExe) {
    $PythonVersion = & $PythonExe -c "import sys; print('.'.join(map(str, sys.version_info[:3])))"
    if ($LASTEXITCODE -ne 0) {
        throw "The existing backend environment at '$Venv' could not start Python."
    }
    if (-not $PythonVersion.StartsWith('3.14.')) {
        throw "backend\.venv already exists but uses Python $PythonVersion, not Python 3.14. Remove only '$Venv' after confirming it is safe, then rerun setup."
    }
} else {
    if (Test-Path $Venv) {
        throw "backend\.venv exists but its Python executable is missing. Remove only '$Venv' after confirming it is safe, then rerun setup."
    }
    Require-Command 'py' 'Install the Python launcher and Python 3.14.8.'
    $PythonVersion = & py -3.14 -c "import sys; print('.'.join(map(str, sys.version_info[:3])))"
    if ($LASTEXITCODE -ne 0) {
        throw 'Python 3.14 was not found. This project uses Python 3.14.8 because the selected PyMuPDF build is officially supported through Python 3.14.'
    }
    if (-not $PythonVersion.StartsWith('3.14.')) {
        throw "Expected Python 3.14.x, found $PythonVersion."
    }
}
Write-Host "Using Python $PythonVersion" -ForegroundColor Green

$NodeVersion = (& node --version).Trim().TrimStart('v')
$NodeParts = $NodeVersion.Split('.')
$NodeMajor = [int]$NodeParts[0]
$NodeMinor = [int]$NodeParts[1]
if (-not (($NodeMajor -eq 20 -and $NodeMinor -ge 19) -or ($NodeMajor -eq 22 -and $NodeMinor -ge 12) -or ($NodeMajor -gt 22))) {
    throw "Node.js $NodeVersion is not supported by this Vite setup. Use Node 24.19.0 from this PC inventory."
}
Write-Host "Using Node.js $NodeVersion" -ForegroundColor Green

$EnvFile = Join-Path $Root '.env'
if (-not (Test-Path $EnvFile)) {
    Copy-Item (Join-Path $Root '.env.example') $EnvFile
    Write-Host 'Created root .env from .env.example.' -ForegroundColor Green
} else {
    Write-Host 'Existing .env preserved.' -ForegroundColor Yellow
}

if (-not (Test-Path $PythonExe)) {
    & py -3.14 -m venv $Venv
    if ($LASTEXITCODE -ne 0) { throw 'Could not create backend virtual environment.' }
}

Write-Host 'Installing backend dependencies...' -ForegroundColor Cyan
& $PythonExe -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw 'pip upgrade failed.' }
& $PythonExe -m pip install -r (Join-Path $Backend 'requirements-dev.txt')
if ($LASTEXITCODE -ne 0) { throw 'Backend dependency installation failed. Do not start Uvicorn yet.' }
& $PythonExe -m pip check
if ($LASTEXITCODE -ne 0) { throw 'pip check found dependency conflicts.' }

Write-Host 'Running backend tests...' -ForegroundColor Cyan
Push-Location $Backend
try {
    & $PythonExe -m pytest -q
    if ($LASTEXITCODE -ne 0) { throw 'Backend tests failed.' }
} finally {
    Pop-Location
}

Write-Host 'Installing frontend dependencies...' -ForegroundColor Cyan
Push-Location $Frontend
try {
    & npm ci --no-audit --no-fund
    if ($LASTEXITCODE -ne 0) { throw 'Frontend npm install failed.' }
    & npm run build
    if ($LASTEXITCODE -ne 0) { throw 'Frontend production build failed.' }
} finally {
    Pop-Location
}

Write-Host 'Validating Docker Compose configuration...' -ForegroundColor Cyan
Push-Location $Root
try {
    & docker compose --env-file .env config --quiet
    if ($LASTEXITCODE -ne 0) { throw 'Docker Compose configuration is invalid.' }
} finally {
    Pop-Location
}

Write-Host ''
Write-Host 'Setup completed successfully.' -ForegroundColor Green
Write-Host 'Next: .\scripts\start-windows.ps1'
