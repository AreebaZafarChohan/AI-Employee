#!/bin/bash
# Vault State Manager - Initialization Script
# Creates the canonical vault folder structure

set -euo pipefail

# Configuration
VAULT_PATH="${VAULT_PATH:-./vault}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "======================================"
echo "Vault State Manager - Initialization"
echo "======================================"
echo ""

# Check if VAULT_PATH is set
if [ -z "${VAULT_PATH}" ]; then
  echo -e "${RED}Error: VAULT_PATH not set${NC}"
  echo "Usage: VAULT_PATH=/path/to/vault ./vault-init.sh"
  exit 1
fi

echo -e "${YELLOW}Vault path: ${VAULT_PATH}${NC}"

# Create vault root if doesn't exist
if [ ! -d "${VAULT_PATH}" ]; then
  echo "Creating vault root directory..."
  mkdir -p "${VAULT_PATH}"
fi

# Create lifecycle folders
echo "Creating lifecycle folders..."
mkdir -p "${VAULT_PATH}/Needs_Action"
mkdir -p "${VAULT_PATH}/Needs_Action/emails"
mkdir -p "${VAULT_PATH}/Needs_Action/messages"
mkdir -p "${VAULT_PATH}/Needs_Action/files"
mkdir -p "${VAULT_PATH}/Needs_Action/finance-alerts"

mkdir -p "${VAULT_PATH}/Plans"
mkdir -p "${VAULT_PATH}/In_Progress"
mkdir -p "${VAULT_PATH}/Pending_Approval"
mkdir -p "${VAULT_PATH}/Approved"
mkdir -p "${VAULT_PATH}/Rejected"
mkdir -p "${VAULT_PATH}/Done"
mkdir -p "${VAULT_PATH}/Archive"

# Create update folders
echo "Creating update folders..."
mkdir -p "${VAULT_PATH}/Updates"
mkdir -p "${VAULT_PATH}/Updates/finance"
mkdir -p "${VAULT_PATH}/Updates/signals-from-lex.json"

# Create log folders
echo "Creating log folders..."
mkdir -p "${VAULT_PATH}/Logs"

# Initialize log files (empty)
touch "${VAULT_PATH}/Logs/watcher-gmail.json"
touch "${VAULT_PATH}/Logs/watcher-whats.json"
touch "${VAULT_PATH}/Logs/watcher-finance.json"
touch "${VAULT_PATH}/Logs/watcher-fs.json"
touch "${VAULT_PATH}/Logs/orchestrator-actions.json"
touch "${VAULT_PATH}/Logs/lex-decisions.json"

# Create Dashboard.md (human-maintained)
if [ ! -f "${VAULT_PATH}/Dashboard.md" ]; then
  echo "Creating Dashboard.md..."
  cat > "${VAULT_PATH}/Dashboard.md" <<EOF
# Digital FTE Dashboard

**Last Updated:** $(date -u +"%Y-%m-%dT%H:%M:%SZ")

---

## Status Overview

| Folder | Count | Action Required |
|--------|-------|-----------------|
| Needs_Action | 0 | None |
| Plans | 0 | None |
| In_Progress | 0 | Monitor |
| Pending_Approval | 0 | **Review & Approve** |
| Approved | 0 | Orchestrator Processing |
| Done | 0 | None |
| Rejected | 0 | None |

---

## Recent Activity

*(Manually updated by human)*

---

## Autonomy Tier

**Current Tier:** Bronze

- Bronze: All actions require approval
- Silver: Safe actions auto-approved
- Gold: Most actions auto-approved
- Platinum: Near-full autonomy

**Change Tier:** Edit \`.env\` file, set \`AUTONOMY_TIER=<tier>\`

---

## Alerts

None

---

## Notes

*(Add notes here)*

EOF
fi

# Create .gitignore
if [ ! -f "${VAULT_PATH}/.gitignore" ]; then
  echo "Creating .gitignore..."
  cat > "${VAULT_PATH}/.gitignore" <<EOF
# Ignore temporary files
*.tmp
*.swp
*.swo
*~

# Ignore logs (too large for git)
Logs/*.json

# Ignore local environment
.env

# Ignore credentials
credentials/
*.pem
*.key

# Ignore In_Progress (ephemeral state)
In_Progress/*

# Ignore Archive (keep only in backups)
Archive/*

# Keep folder structure
!.gitkeep
EOF
fi

# Add .gitkeep files to preserve empty folders
echo "Adding .gitkeep files..."
find "${VAULT_PATH}" -type d -empty -exec touch {}/.gitkeep \;

# Set permissions (allow current user read/write)
echo "Setting permissions..."
chmod -R u+rw "${VAULT_PATH}"

# Verification
echo ""
echo -e "${GREEN}✓ Vault initialized successfully${NC}"
echo ""
echo "Folder structure:"
tree -L 2 "${VAULT_PATH}" 2>/dev/null || find "${VAULT_PATH}" -type d -maxdepth 2

echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Copy .env.example to .env and set VAULT_PATH"
echo "2. Configure agent credentials (Gmail, WhatsApp, etc.)"
echo "3. Start agents: docker-compose up -d"
echo "4. Monitor Dashboard.md for status updates"
echo ""
echo "For more info, see SKILL.md"
