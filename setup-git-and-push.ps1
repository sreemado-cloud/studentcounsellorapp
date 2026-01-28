# ============================================================================
# Git Setup and Push Script for Student Counsellor App
# ============================================================================
# This script initializes Git, commits all code, and pushes to GitHub
# Run: .\setup-git-and-push.ps1
# ============================================================================

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Git Setup and Push to GitHub" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Git is installed
if (!(Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Git is not installed or not in PATH." -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Git from: https://git-scm.com/download/win" -ForegroundColor Yellow
    Write-Host "After installation, restart your terminal and run this script again." -ForegroundColor Yellow
    exit 1
}

Write-Host "[1/6] Checking Git installation..." -ForegroundColor Yellow
$gitVersion = git --version
Write-Host "  $gitVersion" -ForegroundColor Green
Write-Host ""

# Check if already a git repository
if (Test-Path ".git") {
    Write-Host "[2/6] Git repository already initialized" -ForegroundColor Yellow
    $existingRemote = git remote get-url origin 2>$null
    if ($existingRemote) {
        Write-Host "  Existing remote: $existingRemote" -ForegroundColor Gray
        $changeRemote = Read-Host "Change remote to https://github.com/sreemado-cloud/StudentCounsellorApp.git? (yes/no)"
        if ($changeRemote -eq "yes") {
            git remote set-url origin https://github.com/sreemado-cloud/StudentCounsellorApp.git
            Write-Host "  Remote updated" -ForegroundColor Green
        }
    }
} else {
    Write-Host "[2/6] Initializing Git repository..." -ForegroundColor Yellow
    git init
    Write-Host "  Repository initialized" -ForegroundColor Green
}

Write-Host ""

# Configure Git user (if not already configured)
Write-Host "[3/6] Configuring Git user..." -ForegroundColor Yellow
$gitUser = git config --global user.name
$gitEmail = git config --global user.email

if (!$gitUser) {
    $gitUser = Read-Host "Enter your Git username (or press Enter to skip)"
    if ($gitUser) {
        git config --global user.name $gitUser
    }
}

if (!$gitEmail) {
    $gitEmail = Read-Host "Enter your Git email (or press Enter to skip)"
    if ($gitEmail) {
        git config --global user.email $gitEmail
    }
}

if ($gitUser -or $gitEmail) {
    Write-Host "  Git user configured" -ForegroundColor Green
} else {
    Write-Host "  Using existing Git configuration" -ForegroundColor Gray
}
Write-Host ""

# Add remote repository
Write-Host "[4/6] Configuring remote repository..." -ForegroundColor Yellow
$remoteUrl = "https://github.com/sreemado-cloud/StudentCounsellorApp.git"
$existingRemote = git remote get-url origin 2>$null

if ($existingRemote) {
    if ($existingRemote -ne $remoteUrl) {
        Write-Host "  Updating remote URL..." -ForegroundColor Gray
        git remote set-url origin $remoteUrl
    }
    Write-Host "  Remote: $remoteUrl" -ForegroundColor Green
} else {
    Write-Host "  Adding remote: $remoteUrl" -ForegroundColor Gray
    git remote add origin $remoteUrl
    Write-Host "  Remote added" -ForegroundColor Green
}
Write-Host ""

# Stage all files
Write-Host "[5/6] Staging files..." -ForegroundColor Yellow
git add .
$stagedFiles = git diff --cached --name-only | Measure-Object -Line
Write-Host "  Staged $($stagedFiles.Lines) files" -ForegroundColor Green
Write-Host ""

# Check if there are changes to commit
$status = git status --porcelain
if (!$status) {
    Write-Host "  No changes to commit. Checking if we need to push..." -ForegroundColor Yellow
    $localCommits = git rev-list --count HEAD 2>$null
    $remoteCommits = git rev-list --count origin/main 2>$null
    
    if ($localCommits -gt 0) {
        Write-Host "[6/6] Pushing to GitHub..." -ForegroundColor Yellow
        git push -u origin main
        Write-Host "  Pushed successfully!" -ForegroundColor Green
    } else {
        Write-Host "  Nothing to commit or push." -ForegroundColor Yellow
    }
} else {
    # Create initial commit
    Write-Host "[6/6] Creating initial commit..." -ForegroundColor Yellow
    git commit -m "Initial commit: Student Counsellor App

- Multi-tenant student counselling platform
- FastAPI backend with MongoDB
- React frontend with TypeScript
- Docker Compose for local development
- Terraform for AWS EKS deployment
- Kubernetes manifests included"
    
    Write-Host "  Commit created" -ForegroundColor Green
    Write-Host ""
    
    # Push to GitHub
    Write-Host "[7/7] Pushing to GitHub..." -ForegroundColor Yellow
    Write-Host "  Note: You may be prompted for GitHub credentials" -ForegroundColor Gray
    Write-Host ""
    
    # Try to push (user may need to authenticate)
    try {
        git push -u origin main
        Write-Host "  Pushed successfully!" -ForegroundColor Green
    } catch {
        Write-Host "  Push failed. Trying 'master' branch..." -ForegroundColor Yellow
        try {
            git branch -M master
            git push -u origin master
            Write-Host "  Pushed successfully to master branch!" -ForegroundColor Green
        } catch {
            Write-Host "  ERROR: Could not push automatically." -ForegroundColor Red
            Write-Host ""
            Write-Host "You may need to:" -ForegroundColor Yellow
            Write-Host "  1. Create the repository on GitHub first:" -ForegroundColor Gray
            Write-Host "     https://github.com/new" -ForegroundColor Cyan
            Write-Host "     Name: StudentCounsellorApp" -ForegroundColor Gray
            Write-Host "     Visibility: Private (recommended) or Public" -ForegroundColor Gray
            Write-Host ""
            Write-Host "  2. Or authenticate with GitHub:" -ForegroundColor Gray
            Write-Host "     git push -u origin main" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "  3. Or use GitHub CLI:" -ForegroundColor Gray
            Write-Host "     gh repo create StudentCounsellorApp --private --source=. --remote=origin --push" -ForegroundColor Cyan
        }
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Git Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Repository URL: https://github.com/sreemado-cloud/StudentCounsellorApp" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Verify files are pushed: https://github.com/sreemado-cloud/StudentCounsellorApp" -ForegroundColor Gray
Write-Host "  2. Check that .env files are NOT committed (they should be in .gitignore)" -ForegroundColor Gray
Write-Host "  3. Consider adding a README.md if you haven't already" -ForegroundColor Gray
Write-Host ""
