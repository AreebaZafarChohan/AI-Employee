# sync_push.ps1 - Secure Vault Sync for Windows

Set-Location -Path "AI-Employee-Vault"

Write-Host "[Vault Sync] Preparing push..." -ForegroundColor Cyan

# Add changes (respecting .gitignore)
git add .

# Check if there are changes
$diff = git diff --cached --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "[Vault Sync] No changes to push." -ForegroundColor Green
    exit 0
}

$message = "vault-sync-$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
git commit -m "$message"

# Attempt to push
git push origin main
if ($LASTEXITCODE -eq 0) {
    Write-Host "[Vault Sync] Successfully pushed changes." -ForegroundColor Green
} else {
    Write-Host "[Vault Sync] Push failed. Attempting pull/rebase first..." -ForegroundColor Yellow
    git pull --rebase origin main
    git push origin main
}
