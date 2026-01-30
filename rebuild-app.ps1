# Rebuild and restart the app after code changes (backend, frontend, or config).
# Run from project root: .\rebuild-app.ps1
# Optional: .\rebuild-app.ps1 -NoCache   (clean rebuild, no cache)
#           .\rebuild-app.ps1 -Prune    (clear Docker build cache then clean rebuild; use if you see "parent snapshot does not exist")

param(
    [switch]$NoCache,  # Use --no-cache for full clean rebuild
    [switch]$Prune     # Run docker builder prune -af first (fixes corrupted cache / "parent snapshot" errors)
)

$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Rebuild App (after code changes)" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Docker
Write-Host "[1/4] Checking Docker..." -ForegroundColor Yellow
$null = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Docker is not running. Start Docker Desktop, then retry.`n" -ForegroundColor Red
    exit 1
}
Write-Host "  OK`n" -ForegroundColor Green

# Stop
Write-Host "[2/4] Stopping containers..." -ForegroundColor Yellow
docker compose down 2>$null | Out-Null
Write-Host "  Done`n" -ForegroundColor Green

# Optional: prune build cache + remove app images (fixes "parent snapshot does not exist" and similar)
if ($Prune) {
    Write-Host "Removing app images and pruning Docker build cache..." -ForegroundColor Yellow
    docker rmi studentcounsellorapp-backend:latest studentcounsellorapp-frontend:latest 2>$null
    docker builder prune -af
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  Prune failed. Ensure Docker Desktop is running, then retry.`n" -ForegroundColor Red
        exit 1
    }
    $NoCache = $true
    Write-Host "  Done. Rebuilding with --no-cache.`n" -ForegroundColor Green
}

# Rebuild and start
Write-Host "[3/4] Rebuilding and starting..." -ForegroundColor Yellow
$buildArgs = @("-d", "--build")
if ($NoCache) { $buildArgs = @("-d", "--build", "--no-cache") }
$upOut = docker compose up $buildArgs 2>&1
$upExit = $LASTEXITCODE
if ($upExit -ne 0) {
    Write-Host "`n  docker compose up failed (exit $upExit):`n" -ForegroundColor Red
    Write-Host $upOut -ForegroundColor Red
    Write-Host "`nIf you see 'parent snapshot does not exist' or similar:" -ForegroundColor Yellow
    Write-Host "  1. .\rebuild-app.ps1 -Prune" -ForegroundColor Cyan
    Write-Host "  2. If it still fails: restart Docker Desktop, then run step 1 again.`n" -ForegroundColor White
    Write-Host "Otherwise: .\restart-app.ps1 for full checks and seed.`n" -ForegroundColor Yellow
    exit 1
}
Write-Host "  Done`n" -ForegroundColor Green

# Wait for backend
Write-Host "[4/4] Waiting for backend (up to 60s)..." -ForegroundColor Yellow
$ok = $false
for ($i = 0; $i -lt 12; $i++) {
    Start-Sleep -Seconds 5
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        if ($r.StatusCode -eq 200) { $ok = $true; break }
    } catch { }
}
if (-not $ok) {
    Write-Host "  Backend not ready yet. Check: docker compose logs backend`n" -ForegroundColor Yellow
} else {
    Write-Host "  Backend healthy`n" -ForegroundColor Green
}

Write-Host "----------------------------------------" -ForegroundColor DarkGray
docker compose ps -a
Write-Host "`n----------------------------------------" -ForegroundColor DarkGray
Write-Host "App:   " -NoNewline; Write-Host "http://localhost:3000" -ForegroundColor Cyan
Write-Host "Login: " -NoNewline; Write-Host "http://localhost:3000/login" -ForegroundColor Cyan
Write-Host "API:   " -NoNewline; Write-Host "http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "----------------------------------------`n" -ForegroundColor DarkGray
