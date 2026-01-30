# ============================================================================
# Fix SSH config permissions (Windows)
# ============================================================================
# SSH requires ~/.ssh and ~/.ssh/config to be readable only by you.
# Run: .\fix-ssh-config-permissions.ps1
# ============================================================================

$ErrorActionPreference = "Stop"
$sshDir = "$env:USERPROFILE\.ssh"
$configPath = "$sshDir\config"

Write-Host "Fixing permissions on $sshDir and config..." -ForegroundColor Yellow

if (-not (Test-Path $sshDir)) {
    Write-Host "  .ssh folder not found. Run push-via-ssh.ps1 first." -ForegroundColor Red
    exit 1
}

$winUser = if ($env:USERDOMAIN) { "$env:USERDOMAIN\$env:USERNAME" } else { $env:USERNAME }

# Ensure .ssh folder: only current user has access
icacls $sshDir /reset 2>$null
icacls $sshDir /inheritance:r 2>$null
icacls $sshDir /grant:r "${winUser}:(OI)(CI)F" 2>$null
Write-Host "  .ssh folder: OK" -ForegroundColor Green

if (Test-Path $configPath) {
    icacls $configPath /reset 2>$null
    icacls $configPath /inheritance:r 2>$null
    icacls $configPath /grant:r "${winUser}:F" 2>$null
    Write-Host "  config: OK" -ForegroundColor Green
}

# Also fix key files if present
foreach ($key in @("id_ed25519", "id_rsa")) {
    $p = "$sshDir\$key"
    if (Test-Path $p) {
        icacls $p /reset 2>$null
        icacls $p /inheritance:r 2>$null
        icacls $p /grant:r "${winUser}:F" 2>$null
        Write-Host "  ${key}: OK" -ForegroundColor Green
    }
}

Write-Host "Done. Run .\push-via-ssh.ps1 again." -ForegroundColor Green
