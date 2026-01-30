# ============================================================================
# Diagnose GitHub 403 - Check token auth and repo access
# ============================================================================
# Run: .\diagnose-github.ps1
# Paste token when prompted (use a Classic token with repo scope).
# Your token is never logged or saved.
# ============================================================================

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$repo = "sreemado-cloud/StudentCounsellorApp"
$apiRoot = "https://api.github.com"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "GitHub 403 Diagnostic (Step 1)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Creates token: https://github.com/settings/tokens" -ForegroundColor Gray
Write-Host "  -> Generate new token (classic) -> scope: repo" -ForegroundColor Gray
Write-Host ""

$token = Read-Host "Paste your Classic PAT (repo scope)"
$token = $token.Trim()
if ([string]::IsNullOrWhiteSpace($token)) { Write-Host "No token." -ForegroundColor Red; exit 1 }

$headers = @{
    "Authorization" = "token $token"
    "Accept"        = "application/vnd.github.v3+json"
}

# 1. Who am I?
Write-Host "[1/4] Token owner (who am I?)..." -ForegroundColor Yellow
try {
    $me = Invoke-RestMethod -Uri "$apiRoot/user" -Headers $headers -Method Get
    Write-Host "  Login: $($me.login)" -ForegroundColor Green
    Write-Host "  Name:  $($me.name)" -ForegroundColor Gray
} catch {
    Write-Host "  FAIL: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response.StatusCode -eq 401) { Write-Host "  Token invalid or expired." -ForegroundColor Red }
    exit 1
}
Write-Host ""

# 2. Can I see the repo?
Write-Host "[2/4] Repository access..." -ForegroundColor Yellow
try {
    $r = Invoke-RestMethod -Uri "$apiRoot/repos/$repo" -Headers $headers -Method Get
    Write-Host "  Repo: $($r.full_name)" -ForegroundColor Green
    Write-Host "  Owner: $($r.owner.login)" -ForegroundColor Gray
    Write-Host "  Private: $($r.private)" -ForegroundColor Gray
} catch {
    $sc = $_.Exception.Response.StatusCode
    Write-Host "  FAIL: $sc - $($_.Exception.Message)" -ForegroundColor Red
    if ($sc -eq 404) { Write-Host "  Repo not found or no access." -ForegroundColor Red }
    if ($sc -eq 403) { Write-Host "  No permission to access this repo." -ForegroundColor Red }
    exit 1
}
Write-Host ""

# 3. Do I have push access? (permissions)
Write-Host "[3/4] Your permissions on repo..." -ForegroundColor Yellow
try {
    $perm = Invoke-RestMethod -Uri "$apiRoot/repos/$repo" -Headers $headers -Method Get
    $p = $perm.permissions
    Write-Host "  admin: $($p.admin)  push: $($p.push)  pull: $($p.pull)" -ForegroundColor $(if ($p.push) { "Green" } else { "Red" })
    if (-not $p.push) {
        Write-Host "  You do NOT have push access. Fix repo permissions or use an admin token." -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "  Could not read permissions: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# 4. Git ls-remote (same as push auth path)
Write-Host "[4/4] Git ls-remote (HTTPS + token)..." -ForegroundColor Yellow
$pushUrl = "https://$($me.login):${token}@github.com/$repo.git"
$env:GIT_TERMINAL_PROMPT = "0"
$out = git ls-remote $pushUrl 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  FAIL" -ForegroundColor Red
    Write-Host "  $out" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Git over HTTPS still fails even though API works." -ForegroundColor Yellow
    Write-Host "  -> Try SSH or GitHub CLI (gh auth login) instead." -ForegroundColor Yellow
    exit 1
}
Write-Host "  OK (refs listed)" -ForegroundColor Green
Write-Host ""

Write-Host "========================================" -ForegroundColor Green
Write-Host "Token and repo access look OK." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "If push still fails, use SSH or 'gh auth login' instead of PAT." -ForegroundColor Gray
Write-Host ""
