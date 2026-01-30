# Backend / health check not up – quick diagnose
# Run from project root: .\troubleshoot-backend.ps1

$ErrorActionPreference = "Continue"
Write-Host "`n=== Backend /health not up – diagnostic ===`n" -ForegroundColor Cyan

Set-Location $PSScriptRoot

Write-Host "1. Container status:" -ForegroundColor Yellow
docker compose ps -a

Write-Host "`n2. Backend logs (last 60 lines):" -ForegroundColor Yellow
docker compose logs backend --tail 60

Write-Host "`n3. MongoDB logs (last 20 lines):" -ForegroundColor Yellow
docker compose logs mongodb --tail 20

Write-Host "`n---" -ForegroundColor DarkGray
Write-Host "Common fixes:" -ForegroundColor Yellow
Write-Host "  - MongoDB password mismatch: Ensure root .env has MONGO_INITDB_ROOT_PASSWORD" -ForegroundColor White
Write-Host "    matching how MongoDB was created. If unsure, reset: docker compose down -v" -ForegroundColor White
Write-Host "    then docker compose up -d --build" -ForegroundColor White
Write-Host "  - Backend not running: docker compose up -d mongodb backend" -ForegroundColor White
Write-Host "  - Rebuild backend: docker compose up -d --build backend`n" -ForegroundColor White
