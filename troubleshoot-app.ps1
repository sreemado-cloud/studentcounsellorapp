# Quick check: ensure frontend/backend are running so http://localhost:3000/login works.
# Run from project root: .\troubleshoot-app.ps1

Set-Location $PSScriptRoot

Write-Host "`n--- App reachability check ---`n" -ForegroundColor Cyan

$frontend = docker compose ps frontend --format "{{.Status}}" 2>$null
$backend  = docker compose ps backend  --format "{{.Status}}" 2>$null

if (-not $frontend -or $frontend -notmatch "Up") {
    Write-Host "Frontend is not running. Start the full stack:" -ForegroundColor Yellow
    Write-Host "  .\restart-app.ps1" -ForegroundColor Cyan
    Write-Host "  or: docker compose up -d`n" -ForegroundColor Cyan
    exit 1
}
if (-not $backend -or $backend -notmatch "Up") {
    Write-Host "Backend is not running. Start the full stack:" -ForegroundColor Yellow
    Write-Host "  .\restart-app.ps1" -ForegroundColor Cyan
    Write-Host "  or: docker compose up -d`n" -ForegroundColor Cyan
    exit 1
}

Write-Host "Frontend: $frontend" -ForegroundColor Green
Write-Host "Backend:  $backend" -ForegroundColor Green
Write-Host "`nApp URL:  http://localhost:3000" -ForegroundColor White
Write-Host "Login:    http://localhost:3000/login`n" -ForegroundColor White
