#!/bin/bash
# Sync Pull - Secure Vault Sync
# Handles conflicts by prioritizing local changes (Strategy: ours)

cd AI-Employee-Vault || exit

echo "[Vault Sync] Preparing pull..."

# Fetch remote changes
git fetch origin main

# Attempt merge with strategy: ours (avoids clobbering local task state)
# In high-concurrency scenarios, we favor our current state.
if git merge -X ours origin/main -m "Merge remote changes (Local-First Conflict Resolution)"; then
    echo "[Vault Sync] Successfully pulled and merged remote updates."
else
    echo "[Vault Sync] Conflict detected. Attempting to resolve via local priority..."
    git checkout --ours .
    git add .
    git commit -m "Auto-resolved conflicts using LOCAL PRIORITY"
fi
