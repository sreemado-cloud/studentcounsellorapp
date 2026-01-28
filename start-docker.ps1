# PowerShell script to start the Student Counsellor App with Docker

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Student Counsellor App - Docker Start" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
Write-Host "Checking Docker status..." -ForegroundColor Yellow
try {
    $dockerStatus = docker ps 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "❌ Docker Desktop is not running!" -ForegroundColor Red
        Write-Host ""
        Write-Host "Please:" -ForegroundColor Yellow
        Write-Host "1. Start Docker Desktop from the Start menu" -ForegroundColor White
        Write-Host "2. Wait until Docker Desktop is fully running (tray icon stops animating)" -ForegroundColor White
        Write-Host "3. Run this script again" -ForegroundColor White
        Write-Host ""
        Write-Host "Press any key to exit..."
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        exit 1
    }
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running or not installed" -ForegroundColor Red
    Write-Host "Please start Docker Desktop first" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Starting Docker Compose services..." -ForegroundColor Yellow
Write-Host ""

# Change to project directory
Set-Location $PSScriptRoot

# Start Docker Compose (keep this window open!)
$null = docker compose version 2>&1
if ($LASTEXITCODE -eq 0) {
    docker compose up
} else {
    docker-compose up
}
