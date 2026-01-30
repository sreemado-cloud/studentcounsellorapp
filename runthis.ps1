$repo = "$repo = https://github.com/sreemado-cloud/studentcounsellorapp"
try {
    gh api --method GET "repos/$repo" | Out-Null
    Write-Host "✅ Access confirmed for repository: $repo"
} catch {
    Write-Error "❌ Access denied or repository not found for: $repo"
}