# Start the Student Counsellor App (MongoDB + Backend + Frontend)
# Run from project root: .\start-docker.ps1

$ErrorActionPreference = "Continue"
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Student Counsellor App - Docker Start" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Docker check
Write-Host "Checking Docker..." -ForegroundColor Yellow
$dr = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker is not running. Start Docker Desktop, then run this script again.`n" -ForegroundColor Red
    exit 1
}
Write-Host "Docker OK`n" -ForegroundColor Green

Set-Location $PSScriptRoot

# Stop any existing, then bring up with build
Write-Host "Stopping existing containers..." -ForegroundColor Yellow
docker compose down 2>$null | Out-Null

Write-Host "Starting MongoDB, Backend, Frontend (build if needed)..." -ForegroundColor Yellow
docker compose up -d --build

Write-Host "`nWaiting 50 seconds for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 50

# Status
Write-Host "`nContainer status:" -ForegroundColor Yellow
docker compose ps -a

Write-Host "`n----------------------------------------" -ForegroundColor DarkGray
Write-Host "Open in your browser: " -NoNewline
Write-Host "http://localhost:3000" -ForegroundColor Cyan
Write-Host "----------------------------------------`n" -ForegroundColor DarkGray

# Quick check
$front = docker compose ps frontend --format "{{.Status}}" 2>$null
$back = docker compose ps backend --format "{{.Status}}" 2>$null
if ($front -notmatch "Up|running" -or $back -notmatch "Up|running") {
    Write-Host "Some services may not be running. Check logs:" -ForegroundColor Yellow
    Write-Host "  docker compose logs backend" -ForegroundColor White
    Write-Host "  docker compose logs frontend" -ForegroundColor White
    Write-Host "  docker compose logs mongodb`n" -ForegroundColor White
}
