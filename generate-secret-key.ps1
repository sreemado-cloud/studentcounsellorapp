# Generate SECRET_KEY for deployment
# Usage: .\generate-secret-key.ps1

Write-Host "Generating SECRET_KEY for deployment..." -ForegroundColor Cyan
Write-Host ""

# Generate 32-byte random hex string
$bytes = New-Object byte[] 32
$rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
$rng.GetBytes($bytes)
$secretKey = [System.BitConverter]::ToString($bytes).Replace("-", "").ToLower()

Write-Host "SECRET_KEY generated:" -ForegroundColor Green
Write-Host $secretKey -ForegroundColor Yellow
Write-Host ""
Write-Host "Add this to your deployment environment variables:" -ForegroundColor Cyan
Write-Host "SECRET_KEY=$secretKey" -ForegroundColor White
Write-Host ""
Write-Host "Or add to backend/.env:" -ForegroundColor Cyan
Write-Host "SECRET_KEY=$secretKey" -ForegroundColor White
Write-Host ""

# Copy to clipboard (optional)
$secretKey | Set-Clipboard
Write-Host "✓ Copied to clipboard!" -ForegroundColor Green
