# Run app in DEV mode: Docker (MongoDB + Backend) + Local frontend (Vite)
# Use this if "localhost refused to connect" with full Docker.

$ErrorActionPreference = "Continue"
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Student Counsellor App - DEV Mode" -ForegroundColor Cyan
Write-Host "  (Docker: Mongo+Backend | Local: Frontend)" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Set-Location $PSScriptRoot

# 1. Docker check
$null = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker is not running. Start Docker Desktop and run this script again.`n" -ForegroundColor Red
    exit 1
}

# 2. Start only MongoDB + Backend
Write-Host "Starting MongoDB and Backend..." -ForegroundColor Yellow
docker compose up -d mongodb backend
Write-Host "Waiting 45s for backend to connect to MongoDB..." -ForegroundColor Yellow
Start-Sleep -Seconds 45

# 3. Quick backend check
try {
    $r = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "Backend OK (port 8000)`n" -ForegroundColor Green
} catch {
    Write-Host "Backend not responding on :8000. Check: docker compose logs backend`n" -ForegroundColor Red
}

# 4. Frontend deps and dev server
$frontDir = Join-Path $PSScriptRoot "frontend"
if (-not (Test-Path (Join-Path $frontDir "node_modules"))) {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
    Set-Location $frontDir
    npm install
    Set-Location $PSScriptRoot
}

Write-Host "Starting frontend dev server (Vite) on http://localhost:3000 ..." -ForegroundColor Yellow
Write-Host "  Stop with Ctrl+C when done.`n" -ForegroundColor DarkGray
Set-Location $frontDir
npm run dev
