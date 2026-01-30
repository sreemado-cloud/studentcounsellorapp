# Run this in PowerShell from the project folder to seed the database.
# Starts MongoDB if needed, then seeds via a one-off backend container.

Set-Location $PSScriptRoot

Write-Host "Seeding database..." -ForegroundColor Cyan

# Ensure MongoDB is up (backend depends on it being healthy)
$mongoStatus = docker compose ps mongodb --format "{{.Status}}" 2>$null
if (-not $mongoStatus -or $mongoStatus -notmatch "healthy|Up") {
    Write-Host "Starting MongoDB..." -ForegroundColor Yellow
    docker compose up -d mongodb
    Write-Host "Waiting 40s for MongoDB to become healthy..." -ForegroundColor Yellow
    Start-Sleep -Seconds 40
}

# Use exec if backend is running, otherwise run a one-off container
$backendWasUp = $false
$backendStatus = docker compose ps backend --format "{{.Status}}" 2>$null
if ($backendStatus -and $backendStatus -match "Up") {
    $backendWasUp = $true
    docker compose exec backend python -m app.seed_data
} else {
    Write-Host "Backend not running; seeding via one-off container..." -ForegroundColor Yellow
    docker compose run --rm backend python -m app.seed_data
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nDone! You can now login at http://localhost:3000/login" -ForegroundColor Green
    Write-Host "Use: admin@stateuniversity.edu / Admin123!" -ForegroundColor Yellow
    if (-not $backendWasUp) {
        Write-Host "`nStarting backend and frontend so the app is reachable..." -ForegroundColor Yellow
        docker compose up -d
        Write-Host "Give it a minute, then open http://localhost:3000/login" -ForegroundColor Cyan
    }
} else {
    Write-Host "`nSeeding failed." -ForegroundColor Red
    Write-Host "  - Ensure Docker Desktop is running." -ForegroundColor White
    Write-Host "  - Check MongoDB: docker compose logs mongodb" -ForegroundColor White
    Write-Host "  - Root .env must have MONGO_INITDB_ROOT_PASSWORD matching your MongoDB." -ForegroundColor White
    Write-Host "`n  If you see 'Authentication failed': MongoDB was likely initialized with a different" -ForegroundColor Yellow
    Write-Host "  password. Reset the DB volume so it re-initializes with current .env:" -ForegroundColor Yellow
    Write-Host "    docker compose down -v" -ForegroundColor Cyan
    Write-Host "    .\restart-app.ps1" -ForegroundColor Cyan
    Write-Host "    .\seed-database.ps1" -ForegroundColor Cyan
    Write-Host "  (This wipes all DB data; you will re-seed.)" -ForegroundColor DarkGray
}
