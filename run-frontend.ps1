# Start frontend so http://localhost:3000 works (backend must already be up)
# Run from project root: .\run-frontend.ps1

$ErrorActionPreference = "Continue"
Write-Host "`n=== Start Frontend (localhost:3000) ===" -ForegroundColor Cyan
Write-Host ""

Set-Location $PSScriptRoot

# Ensure backend is up
try {
    $r = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 3
} catch {
    Write-Host "Backend (localhost:8000) is not responding. Run .\run-backend.ps1 first.`n" -ForegroundColor Red
    exit 1
}
Write-Host "Backend OK`n" -ForegroundColor Green

Write-Host "Starting frontend..." -ForegroundColor Yellow
docker compose up -d --build frontend

Write-Host "`nWaiting 15 seconds for frontend to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

docker compose ps frontend
Write-Host ""
Write-Host "Open http://localhost:3000/login" -ForegroundColor Cyan
Write-Host "Login: admin@stateuniversity.edu / Admin123!" -ForegroundColor DarkGray
Write-Host ""
