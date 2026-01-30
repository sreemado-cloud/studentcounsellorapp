# Troubleshoot "localhost refused to connect"
# Run from project root: .\troubleshoot-localhost.ps1

$ErrorActionPreference = "Continue"
Write-Host "`n=== Student Counsellor App - Localhost Troubleshooter ===`n" -ForegroundColor Cyan

# 1. Check Docker
Write-Host "1. Checking Docker..." -ForegroundColor Yellow
$dockerOk = $false
try {
    docker info 2>$null | Out-Null
    $dockerOk = $true
    Write-Host "   Docker is running.`n" -ForegroundColor Green
} catch {
    Write-Host "   Docker is NOT running or not accessible.`n" -ForegroundColor Red
}

if (-not $dockerOk) {
    Write-Host "   -> Start Docker Desktop, wait until it's ready, then run this script again.`n" -ForegroundColor White
    exit 1
}

# 2. Project root
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$composePath = Join-Path $root "docker-compose.yml"
if (-not (Test-Path $composePath)) {
    Write-Host "   Run this script from the project root (where docker-compose.yml is).`n" -ForegroundColor Red
    exit 1
}
Set-Location $root

# 3. Stop and bring up with rebuild
Write-Host "2. Stopping existing containers..." -ForegroundColor Yellow
docker compose down 2>$null | Out-Null

Write-Host "`n3. Starting MongoDB, backend, frontend (build if needed)..." -ForegroundColor Yellow
docker compose up -d --build

Write-Host "`n4. Waiting 35 seconds for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 35

# 4. Status
Write-Host "`n5. Container status:" -ForegroundColor Yellow
docker compose ps -a

Write-Host "`n---" -ForegroundColor DarkGray
Write-Host "Open in browser: " -NoNewline
Write-Host "http://localhost:3000" -ForegroundColor Cyan
Write-Host "   (API: http://localhost:8000)`n" -ForegroundColor DarkGray

Write-Host "If you still see 'localhost refused to connect':" -ForegroundColor Yellow
Write-Host "  - Check all three containers are 'Up' above." -ForegroundColor White
Write-Host "  - If mongodb is 'unhealthy': docker compose logs mongodb" -ForegroundColor White
Write-Host "  - If backend/frontend are 'Exit': docker compose logs backend" -ForegroundColor White
Write-Host ""
