$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
Write-Host 'Close the FastAPI and Vite PowerShell windows before stopping the database.' -ForegroundColor Yellow
Push-Location $Root
try {
    docker compose down
    if ($LASTEXITCODE -ne 0) { throw 'Docker Compose could not stop the project.' }
} finally {
    Pop-Location
}
Write-Host 'ResumeIQ database container stopped. Persistent volumes were preserved.' -ForegroundColor Green
