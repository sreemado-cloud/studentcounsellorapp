# ============================================================================
# Fix GitHub 403 "Permission denied" when pushing
# ============================================================================
# Git uses CACHED credentials from a different account. Clear them and
# re-authenticate as sreemado-cloud.
# Run: .\fix-github-push.ps1
# ============================================================================

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Fix GitHub Push (403 Permission Denied)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Clear Git credential cache (Windows Credential Manager)
Write-Host "[1/4] Clearing cached GitHub credentials..." -ForegroundColor Yellow
$deleted = $false
foreach ($key in @("git:https://github.com", "github.com", "Git Credential Manager:https://github.com")) {
    $result = cmdkey /delete:$key 2>&1
    if ($LASTEXITCODE -eq 0) { Write-Host "  Removed: $key" -ForegroundColor Gray; $deleted = $true }
}
if (-not $deleted) {
    Write-Host "  No cached GitHub entries found (or clear manually - see below)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  MANUAL: Open 'Credential Manager' -> Windows Credentials ->" -ForegroundColor Yellow
    Write-Host "    Look for 'git:https://github.com' or 'github.com' -> Remove" -ForegroundColor Yellow
}
Write-Host "  Done" -ForegroundColor Green
Write-Host ""

# Step 2: Verify remote
Write-Host "[2/4] Verifying remote URL..." -ForegroundColor Yellow
$remote = git remote get-url origin
Write-Host "  origin: $remote" -ForegroundColor Green
if ($remote -notmatch "sreemado-cloud/StudentCounsellorApp") {
    Write-Host "  Updating remote..." -ForegroundColor Gray
    git remote set-url origin https://github.com/sreemado-cloud/StudentCounsellorApp.git
    Write-Host "  Set to: https://github.com/sreemado-cloud/StudentCounsellorApp.git" -ForegroundColor Green
}
Write-Host ""

# Step 3: Use credential helper that will prompt (Windows)
Write-Host "[3/4] Configuring credential helper..." -ForegroundColor Yellow
git config --global credential.helper manager
Write-Host "  Using Git Credential Manager (will prompt on next push)" -ForegroundColor Green
Write-Host ""

# Step 4: Push (will prompt for login)
Write-Host "[4/4] Pushing to GitHub..." -ForegroundColor Yellow
Write-Host ""
Write-Host "  You will be prompted to sign in to GitHub." -ForegroundColor Cyan
Write-Host "  IMPORTANT: Sign in as sreemado-cloud (the repo owner)." -ForegroundColor Cyan
Write-Host "  - Browser: Choose 'Sign in with your browser' and use sreemado-cloud" -ForegroundColor Gray
Write-Host "  - Or Username: sreemado-cloud" -ForegroundColor Gray
Write-Host "  - Password: Your Personal Access Token (NOT your GitHub password)" -ForegroundColor Gray
Write-Host ""
Write-Host "  No token? Create one: https://github.com/settings/tokens" -ForegroundColor Gray
Write-Host "  New token -> Classic -> scope: repo -> Generate" -ForegroundColor Gray
Write-Host ""

git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Success! Code pushed to https://github.com/sreemado-cloud/StudentCounsellorApp" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "Push failed. Try manual steps below." -ForegroundColor Red
}
