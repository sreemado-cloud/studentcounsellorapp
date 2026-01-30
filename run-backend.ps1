# Start MongoDB + Backend, then verify http://localhost:8000/health
# Run from project root: .\run-backend.ps1

$ErrorActionPreference = "Continue"
Write-Host "`n=== Start Backend & Check /health ===" -ForegroundColor Cyan
Write-Host ""

Set-Location $PSScriptRoot

# 1. Docker
Write-Host "1. Checking Docker..." -ForegroundColor Yellow
$null = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "   Docker is not running. Start Docker Desktop, then run this script again.`n" -ForegroundColor Red
    exit 1
}
Write-Host "   OK`n" -ForegroundColor Green

# 2. Bring up mongo + backend
Write-Host "2. Stopping any existing containers..." -ForegroundColor Yellow
docker compose down 2>$null | Out-Null

Write-Host "   Starting MongoDB + Backend (build if needed)..." -ForegroundColor Yellow
docker compose up -d --build mongodb backend

Write-Host "`n3. Waiting 35 seconds for backend to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 35

# 3. Container status
Write-Host "`n4. Container status:" -ForegroundColor Yellow
docker compose ps -a

# 4. Hit /health
Write-Host "`n5. Checking http://localhost:8000/health ..." -ForegroundColor Yellow
$healthOk = $false
try {
    $r = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 10
    if ($r.StatusCode -eq 200) {
        $healthOk = $true
        Write-Host "   Backend is UP. Response: $($r.Content)" -ForegroundColor Green
    }
} catch {
    Write-Host "   Request failed: $($_.Exception.Message)" -ForegroundColor Red
}

if (-not $healthOk) {
    Write-Host "`n--- Backend not reachable ---" -ForegroundColor Red
    Write-Host "`nBackend logs (last 80 lines):" -ForegroundColor Yellow
    docker compose logs backend --tail 80
    Write-Host "`nMongoDB logs (last 20 lines):" -ForegroundColor Yellow
    docker compose logs mongodb --tail 20
    Write-Host "`n--- Next steps ---" -ForegroundColor Yellow
    Write-Host "  - If you see MongoDB auth errors: fix root .env MONGO_INITDB_ROOT_PASSWORD." -ForegroundColor White
    Write-Host "  - Reset DB and retry: docker compose down -v" -ForegroundColor White
    Write-Host "    then run this script again.`n" -ForegroundColor White
    exit 1
}

Write-Host "`n---" -ForegroundColor DarkGray
Write-Host "Backend OK. Open http://localhost:8000/health or http://localhost:8000/docs" -ForegroundColor Green
Write-Host "Start frontend (dev): cd frontend; npm run dev" -ForegroundColor Cyan
Write-Host "Or full Docker: docker compose up -d`n" -ForegroundColor Cyan
