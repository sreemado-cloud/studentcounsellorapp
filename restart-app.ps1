# Restart Student Counsellor App (MongoDB, Backend, Frontend) and seed the database.
# Single script to get the app working. Run from project root: .\restart-app.ps1

$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Restart App Dependencies" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 1. Docker
Write-Host "[1/6] Checking Docker..." -ForegroundColor Yellow
$null = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Docker is not running. Start Docker Desktop, then run this script again.`n" -ForegroundColor Red
    exit 1
}
Write-Host "  OK`n" -ForegroundColor Green

# 2. Root .env (for MONGO_INITDB_ROOT_PASSWORD)
Write-Host "[2/6] Checking .env..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    if (Test-Path "env.example") {
        Copy-Item "env.example" ".env"
        Write-Host "  Created .env from env.example (dev-friendly defaults)." -ForegroundColor Yellow
    } else {
        Write-Host "  No .env found. Create one with MONGO_INITDB_ROOT_PASSWORD.`n" -ForegroundColor Red
        exit 1
    }
}
# Parse only uncommented MONGO_INITDB_ROOT_PASSWORD (ignore # lines)
$mongoPassword = $null
foreach ($line in (Get-Content ".env")) {
    $t = $line.Trim()
    if ($t -eq "" -or $t.StartsWith("#")) { continue }
    if ($t -match "^\s*MONGO_INITDB_ROOT_PASSWORD\s*=\s*(.+)$") {
        $mongoPassword = $Matches[1].Trim()
        break
    }
}
if (-not $mongoPassword) {
    Write-Host "  MONGO_INITDB_ROOT_PASSWORD is missing or empty in .env. Set it, then retry.`n" -ForegroundColor Red
    exit 1
}
if ($mongoPassword -eq "change-me-use-strong-password") {
    Write-Host "  MONGO_INITDB_ROOT_PASSWORD is still the placeholder. Set a real value in .env, then retry.`n" -ForegroundColor Red
    exit 1
}
Write-Host "  OK`n" -ForegroundColor Green

# 2b. Backend .env (SECRET_KEY, etc.)
Write-Host "[3/6] Checking backend\.env..." -ForegroundColor Yellow
if (-not (Test-Path "backend\.env")) {
    Write-Host "  backend\.env missing. Copy backend\.env.example to backend\.env and set SECRET_KEY (32+ chars), etc.`n" -ForegroundColor Red
    exit 1
}
$be = Get-Content "backend\.env" -Raw
if ($be -match "SECRET_KEY\s*=\s*(\S+)") {
    $sk = $Matches[1].Trim()
    if ($sk.Length -lt 32) {
        Write-Host "  SECRET_KEY in backend\.env must be at least 32 characters. Current length: $($sk.Length).`n" -ForegroundColor Red
        exit 1
    }
}
Write-Host "  OK`n" -ForegroundColor Green

# 3. Validate compose config (catches env interpolation errors)
Write-Host "[4/6] Validating docker compose config..." -ForegroundColor Yellow
$configOut = docker compose config 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Config validation failed:`n" -ForegroundColor Red
    Write-Host $configOut -ForegroundColor Red
    Write-Host "`nFix .env / backend\.env and retry.`n" -ForegroundColor Yellow
    exit 1
}
Write-Host "  OK`n" -ForegroundColor Green

# 4. Stop existing stack
Write-Host "[5/6] Stopping existing containers..." -ForegroundColor Yellow
docker compose down 2>$null | Out-Null
Write-Host "  Done`n" -ForegroundColor Green

# 5. Start stack (build if needed)
Write-Host "[6/6] Starting MongoDB, Backend, Frontend..." -ForegroundColor Yellow
$upOut = docker compose up -d --build 2>&1
$upExit = $LASTEXITCODE
if ($upExit -ne 0) {
    Write-Host "`n  docker compose up failed (exit $upExit):`n" -ForegroundColor Red
    Write-Host $upOut -ForegroundColor Red
    Write-Host "`nCommon fixes:" -ForegroundColor Yellow
    Write-Host "  - Root .env: MONGO_INITDB_ROOT_PASSWORD set and not placeholder." -ForegroundColor White
    Write-Host "  - backend\.env: SECRET_KEY at least 32 chars; SUPER_ADMIN_EMAILS if needed." -ForegroundColor White
    Write-Host "  - Ports 27017, 8000, 3000 free. Stop other containers using them." -ForegroundColor White
    Write-Host "  - docker compose logs backend" -ForegroundColor White
    Write-Host "  - docker compose logs mongodb`n" -ForegroundColor White
    exit 1
}
Write-Host "  Done`n" -ForegroundColor Green

# Wait for backend /health
Write-Host "Waiting for backend (up to 90s)..." -ForegroundColor Yellow
$max = 18
$ok = $false
for ($i = 0; $i -lt $max; $i++) {
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

# Status
Write-Host "----------------------------------------" -ForegroundColor DarkGray
Write-Host "Container status:" -ForegroundColor White
docker compose ps -a
Write-Host "`n----------------------------------------" -ForegroundColor DarkGray

# Seed database (ensures sample users / institutions exist)
& "$PSScriptRoot\seed-database.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "`nRestart completed but seeding failed. App may be up; run .\seed-database.ps1 manually to retry.`n" -ForegroundColor Yellow
    exit 1
}

Write-Host "`n----------------------------------------" -ForegroundColor DarkGray
Write-Host "App URL:  " -NoNewline
Write-Host "http://localhost:3000" -ForegroundColor Cyan
Write-Host "Login:    " -NoNewline
Write-Host "http://localhost:3000/login" -ForegroundColor Cyan
Write-Host "API docs: " -NoNewline
Write-Host "http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "----------------------------------------`n" -ForegroundColor DarkGray
