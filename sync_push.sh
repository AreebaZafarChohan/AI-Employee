#!/bin/bash
# Sync Push - Secure Vault Sync
# Usage: ./sync_push.sh <commit-message>

cd AI-Employee-Vault || exit

echo "[Vault Sync] Preparing push..."

# Add changes (respecting .gitignore)
git add .

# Check if there are changes
if git diff --cached --quiet; then
    echo "[Vault Sync] No changes to push."
    exit 0
fi

MESSAGE=${1:-"vault-sync-$(date +'%Y-%m-%d %H:%M:%S')"}

git commit -m "$MESSAGE"

# Attempt to push
if git push origin main; then
    echo "[Vault Sync] Successfully pushed changes."
else
    echo "[Vault Sync] Push failed. Attempting pull/rebase first..."
    git pull --rebase origin main
    git push origin main
fi
