$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root 'backend'
$Frontend = Join-Path $Root 'frontend'
$Venv = Join-Path $Backend '.venv'

if (-not (Test-Path (Join-Path $Venv 'Scripts\python.exe'))) {
    throw 'Backend environment is missing. Run .\scripts\setup-windows.ps1 first.'
}
if (-not (Test-Path (Join-Path $Frontend 'node_modules'))) {
    throw 'Frontend packages are missing. Run .\scripts\setup-windows.ps1 first.'
}
if (-not (Test-Path (Join-Path $Root '.env'))) {
    throw 'Root .env is missing. Run .\scripts\setup-windows.ps1 first.'
}

Push-Location $Root
try {
    docker compose up -d db
    if ($LASTEXITCODE -ne 0) { throw 'Could not start PostgreSQL. Check Docker Desktop and port 55432.' }

    $Ready = $false
    for ($Attempt = 0; $Attempt -lt 30; $Attempt++) {
        & docker compose exec -T db pg_isready -U resumeiq -d resumeiq *> $null
        if ($LASTEXITCODE -eq 0) { $Ready = $true; break }
        Start-Sleep -Seconds 1
    }
    if (-not $Ready) { throw 'PostgreSQL did not become ready within 30 seconds. Check: docker compose logs db' }
} finally {
    Pop-Location
}

function Quote-PS([string]$Value) { return "'" + $Value.Replace("'", "''") + "'" }
$BackendCommand = "Set-Location -LiteralPath $(Quote-PS $Backend); & $(Quote-PS (Join-Path $Venv 'Scripts\Activate.ps1')); python -m uvicorn app.main:app --reload"
$FrontendCommand = "Set-Location -LiteralPath $(Quote-PS $Frontend); npm run dev"

Start-Process -FilePath 'powershell.exe' -WorkingDirectory $Backend -ArgumentList @('-NoExit','-ExecutionPolicy','Bypass','-Command',$BackendCommand)
Start-Process -FilePath 'powershell.exe' -WorkingDirectory $Frontend -ArgumentList @('-NoExit','-ExecutionPolicy','Bypass','-Command',$FrontendCommand)
Start-Sleep -Seconds 4
Start-Process 'http://localhost:5173'

Write-Host 'ResumeIQ services launched.' -ForegroundColor Green
Write-Host 'Frontend: http://localhost:5173'
Write-Host 'API docs: http://localhost:8000/docs'
Write-Host 'Database: localhost:55432'
Write-Host 'Keep both service PowerShell windows open while using ResumeIQ.'
