# ============================================================================
# Push to GitHub using Personal Access Token (bypasses Credential Manager)
# ============================================================================
# Use this when you get "403 Permission denied" even after clearing credentials.
# Run: .\push-with-token.ps1
# ============================================================================

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
Set-Location $ProjectRoot

$repoUrl = "https://github.com/sreemado-cloud/StudentCounsellorApp"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Push to GitHub (Token-Based)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check if repo exists
Write-Host "[1/4] Checking if repository exists..." -ForegroundColor Yellow
try {
    $resp = Invoke-WebRequest -Uri "$repoUrl" -Method Head -UseBasicParsing -TimeoutSec 5
    Write-Host "  Repository exists." -ForegroundColor Green
} catch {
    if ($_.Exception.Response.StatusCode -eq 404) {
        Write-Host "  ERROR: Repository does NOT exist!" -ForegroundColor Red
        Write-Host ""
        Write-Host "  Create it first:" -ForegroundColor Yellow
        Write-Host "    1. Open: https://github.com/new" -ForegroundColor Gray
        Write-Host "    2. Repository name: StudentCounsellorApp" -ForegroundColor Gray
        Write-Host "    3. Private or Public (your choice)" -ForegroundColor Gray
        Write-Host "    4. Do NOT add README, .gitignore, or license" -ForegroundColor Gray
        Write-Host "    5. Click 'Create repository'" -ForegroundColor Gray
        Write-Host ""
        Write-Host "  Then run this script again." -ForegroundColor Yellow
        exit 1
    }
    Write-Host "  (Could not verify - continuing anyway)" -ForegroundColor Gray
}
Write-Host ""

# Step 2: Get token
Write-Host "[2/4] Personal Access Token" -ForegroundColor Yellow
Write-Host "  Create a token: https://github.com/settings/tokens" -ForegroundColor Gray
Write-Host "  -> Generate new token (CLASSIC) -> scope: repo -> Generate" -ForegroundColor Gray
Write-Host "  (Fine-grained tokens often cause 403; use Classic with 'repo' scope.)" -ForegroundColor Gray
Write-Host ""
Write-Host "  NEVER paste your token in chat, email, or screenshots." -ForegroundColor Yellow
$token = Read-Host "  Paste your token (Classic, repo scope)"
$token = $token.Trim()
if ([string]::IsNullOrWhiteSpace($token)) {
    Write-Host "  No token provided. Exiting." -ForegroundColor Red
    exit 1
}
Write-Host "  Token received." -ForegroundColor Green
Write-Host ""

# Step 3: Push using token in URL (not stored anywhere)
Write-Host "[3/4] Pushing to GitHub..." -ForegroundColor Yellow
$pushUrl = "https://sreemado-cloud:$token@github.com/sreemado-cloud/StudentCounsellorApp.git"

# Ensure we're on main
git branch -M main 2>$null

$env:GIT_TERMINAL_PROMPT = "0"
git push $pushUrl main 2>&1 | ForEach-Object { Write-Host $_ }

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "  Push failed." -ForegroundColor Red
    Write-Host ""
    Write-Host "  Common causes:" -ForegroundColor Yellow
    Write-Host "    - Token expired or wrong scope (must have 'repo')" -ForegroundColor Gray
    Write-Host "    - Token created for a different GitHub account" -ForegroundColor Gray
    Write-Host "    - Repo under an org with SSO: authorize token for SSO" -ForegroundColor Gray
    Write-Host "    - Repo name typo: must be exactly StudentCounsellorApp" -ForegroundColor Gray
    exit 1
}

# Step 4: Set upstream (no extra push – avoids Credential Manager)
Write-Host "[4/4] Setting upstream..." -ForegroundColor Yellow
git branch --set-upstream-to=origin/main main 2>$null
Write-Host "  Upstream set to origin/main." -ForegroundColor Green
Write-Host "  For future pushes, use this script again or fix Credential Manager." -ForegroundColor Gray

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Success! Code pushed to GitHub." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  $repoUrl" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Your token was used only for this push (not saved)." -ForegroundColor Gray
Write-Host ""
