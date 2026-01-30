# ============================================================================
# Push to GitHub via SSH (bypasses HTTPS / PAT 403 issues)
# ============================================================================
# Use this if push-with-token.ps1 keeps giving 403.
# Run: .\push-via-ssh.ps1
# ============================================================================

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$repo = "sreemado-cloud/StudentCounsellorApp"
$repoOwner = "sreemado-cloud"
$sshUrl = "git@github.com:$repo.git"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Push via SSH" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Check for SSH key
Write-Host "[1/4] Checking for SSH key..." -ForegroundColor Yellow
$sshDir = "$env:USERPROFILE\.ssh"
$keyPaths = @("$sshDir\id_ed25519", "$sshDir\id_rsa")
$keyPath = $null
foreach ($p in $keyPaths) {
    if (Test-Path $p) { $keyPath = $p; break }
}
# Also scan .ssh for any key pair (e.g. custom names)
if (-not $keyPath -and (Test-Path $sshDir)) {
    foreach ($f in Get-ChildItem -Path $sshDir -File -Filter "id_*") {
        if ($f.Name -notmatch "\.pub$" -and $f.Name -notmatch "\.pub\.") {
            $keyPath = $f.FullName
            break
        }
    }
}
if (-not $keyPath) {
    Write-Host "  No SSH key found in $sshDir" -ForegroundColor Red
    Write-Host ""
    if (-not (Test-Path $sshDir)) {
        Write-Host "  Create key (PowerShell, default path):" -ForegroundColor Yellow
        Write-Host "    ssh-keygen -t ed25519 -C `"your@email.com`"" -ForegroundColor Gray
        Write-Host "    (Enter = default $sshDir\id_ed25519, passphrase optional)" -ForegroundColor Gray
    } else {
        Write-Host "  Create key:" -ForegroundColor Yellow
        Write-Host "    ssh-keygen -t ed25519 -C `"your@email.com`"" -ForegroundColor Gray
        Write-Host "    Use default path: $sshDir\id_ed25519" -ForegroundColor Gray
    }
    Write-Host ""
    Write-Host "  Add PUBLIC key to GitHub (sreemado-cloud):" -ForegroundColor Yellow
    Write-Host "    https://github.com/settings/keys -> New SSH key -> paste .pub contents" -ForegroundColor Gray
    Write-Host ""
    exit 1
}
Write-Host "  Found: $keyPath" -ForegroundColor Green
$keyPathUnix = $keyPath -replace '\\', '/'
Write-Host "  Key must be in https://github.com/settings/keys under account: $repoOwner" -ForegroundColor Gray
Write-Host ""

# 2. Test SSH with this key only (no config)
Write-Host "[2/4] Testing SSH (key only)..." -ForegroundColor Yellow
$prevErr = $ErrorActionPreference
$ErrorActionPreference = "Continue"
$sshOut = ssh -i $keyPath -o IdentitiesOnly=yes -T git@github.com 2>&1 | Out-String
$ErrorActionPreference = $prevErr
if ($sshOut -match "successfully authenticated") {
    Write-Host "  OK (GitHub accepts this key)" -ForegroundColor Green
    if ($sshOut -match "Hi\s+([^!]+)!") {
        $ghUser = $Matches[1].Trim()
        if ($ghUser -ne $repoOwner) {
            Write-Host "  WARNING: Key is on account '$ghUser', but repo owner is '$repoOwner'." -ForegroundColor Yellow
            Write-Host "  Add this key to ${repoOwner}: https://github.com/settings/keys (switch account if needed)" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "  SSH failed:" -ForegroundColor Red
    Write-Host "  $sshOut" -ForegroundColor Red
    Write-Host ""
    Write-Host "  1. Add PUBLIC key to ${repoOwner}: https://github.com/settings/keys" -ForegroundColor Yellow
    Write-Host "     (Log in as $repoOwner; paste $keyPath.pub)" -ForegroundColor Gray
    Write-Host "  2. Email sreejeshkm@gmail.com is for your GitHub login; key must be on $repoOwner." -ForegroundColor Gray
    exit 1
}
Write-Host ""

# 3. Remote + push via SSH wrapper (Git often ignores GIT_SSH_COMMAND on Windows)
Write-Host "[3/4] Remote -> $sshUrl" -ForegroundColor Yellow
git remote set-url origin $sshUrl
Write-Host ""

Write-Host "[4/4] Pushing via SSH wrapper..." -ForegroundColor Yellow
git branch -M main 2>$null

$wrapperBat = "$PSScriptRoot\ssh-push-wrapper.bat"
@"
@echo off
ssh -i "$keyPath" -o IdentitiesOnly=yes %*
"@ | Set-Content -Path $wrapperBat -Encoding ASCII

$env:GIT_SSH_COMMAND = $wrapperBat
$prevErr = $ErrorActionPreference
$ErrorActionPreference = "Continue"
git push -u origin main 2>&1 | ForEach-Object { Write-Host $_ }
$pushExit = $LASTEXITCODE
$ErrorActionPreference = $prevErr
Remove-Item Env:GIT_SSH_COMMAND -ErrorAction SilentlyContinue

if ($pushExit -ne 0) {
    Write-Host ""
    Write-Host "  Push failed." -ForegroundColor Yellow
    Write-Host "  1. Ensure this key is on ${repoOwner}: https://github.com/settings/keys" -ForegroundColor Gray
    Write-Host "  2. Try HTTPS instead:" -ForegroundColor Gray
    Write-Host "     git remote set-url origin https://github.com/$repo.git" -ForegroundColor Gray
    Write-Host "     git push -u origin main" -ForegroundColor Gray
    Write-Host "     (Use ${repoOwner} as user, Personal Access Token as password)" -ForegroundColor Gray
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Success! Pushed via SSH." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "  https://github.com/$repo" -ForegroundColor Cyan
Write-Host ""
