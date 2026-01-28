# Run this in PowerShell from the project folder to seed the database.
# Make sure docker-compose up is running in another terminal first!

Set-Location $PSScriptRoot

Write-Host "Seeding database..." -ForegroundColor Cyan
docker compose exec backend python -m app.seed_data

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nDone! You can now login at http://localhost:3000/login" -ForegroundColor Green
    Write-Host "Use: admin@stateuniversity.edu / Admin123!" -ForegroundColor Yellow
} else {
    Write-Host "`nFailed. Make sure:" -ForegroundColor Red
    Write-Host "  1. Docker Desktop is running" -ForegroundColor White
    Write-Host "  2. docker-compose up is running in another terminal" -ForegroundColor White
    Write-Host "  3. You're in the project folder" -ForegroundColor White
}
