# Commit and push changes to Git.
# Run from project root: .\git-commit-push.ps1 "your commit message"
# Or: .\git-commit-push.ps1  (prompts for message)

param(
    [Parameter(Position = 0)]
    [string]$Message
)

Set-Location $PSScriptRoot

Write-Host "`n--- Git commit & push ---`n" -ForegroundColor Cyan

# Status
$status = git status --porcelain 2>&1
if (-not $status) {
    Write-Host "Nothing to commit. Working tree clean.`n" -ForegroundColor Yellow
    exit 0
}

Write-Host "Changes:" -ForegroundColor White
git status -s
Write-Host ""

# Commit message
if (-not $Message) {
    $Message = Read-Host "Commit message"
}
if (-not $Message.Trim()) {
    Write-Host "Commit message is required.`n" -ForegroundColor Red
    exit 1
}

# Add all, commit, push
git add -A
git commit -m "$Message"
if ($LASTEXITCODE -ne 0) {
    Write-Host "`nCommit failed.`n" -ForegroundColor Red
    exit 1
}

git push
if ($LASTEXITCODE -ne 0) {
    Write-Host "`nPush failed. Fix remote/auth (e.g. SSH, PAT) and run: git push`n" -ForegroundColor Red
    exit 1
}

Write-Host "`nDone. Committed and pushed.`n" -ForegroundColor Green
