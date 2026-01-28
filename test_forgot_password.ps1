# PowerShell script to test the forgot password endpoint
# Usage: .\test_forgot_password.ps1 -Email "user@example.com"

param(
    [Parameter(Mandatory=$true)]
    [string]$Email
)

Write-Host "Testing Forgot Password Endpoint..." -ForegroundColor Cyan
Write-Host "Email: $Email" -ForegroundColor Yellow
Write-Host ""

try {
    $body = @{
        email = $Email
    } | ConvertTo-Json

    Write-Host "Sending request to: http://localhost:8000/api/auth/forgot-password" -ForegroundColor Gray
    
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/forgot-password" `
        -Method POST `
        -Body $body `
        -ContentType "application/json" `
        -ErrorAction Stop

    Write-Host "✅ SUCCESS!" -ForegroundColor Green
    Write-Host "Response:" -ForegroundColor Cyan
    $response | ConvertTo-Json -Depth 10
}
catch {
    Write-Host "❌ ERROR!" -ForegroundColor Red
    Write-Host "Status Code: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Yellow
    Write-Host "Error Message: $($_.Exception.Message)" -ForegroundColor Red
    
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "Response Body:" -ForegroundColor Yellow
        Write-Host $responseBody
    }
}

Write-Host ""
Write-Host "Check backend terminal for detailed logs." -ForegroundColor Gray
