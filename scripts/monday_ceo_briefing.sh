#!/usr/bin/env bash
# Monday CEO Briefing — Cron wrapper
# Schedule: Sunday 11:00 PM → ready for Monday morning
#
# crontab entry:
#   0 23 * * 0 /path/to/AI-Employee/scripts/monday_ceo_briefing.sh

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

LOG_FILE="$PROJECT_ROOT/AI-Employee-Vault/Logs/monday-ceo-briefing-$(date +%Y-%m-%d).log"
mkdir -p "$(dirname "$LOG_FILE")"

echo "[$(date -Iseconds)] Starting Monday CEO briefing..." >> "$LOG_FILE"

# Load .env if exists
if [[ -f ".env" ]]; then
    export $(grep -v '^#' .env | xargs)
fi

# Run the generator
if command -v python3 &> /dev/null; then
    python3 "$PROJECT_ROOT/monday_ceo_briefing.py" >> "$LOG_FILE" 2>&1
elif command -v python &> /dev/null; then
    python "$PROJECT_ROOT/monday_ceo_briefing.py" >> "$LOG_FILE" 2>&1
else
    echo "[$(date -Iseconds)] ERROR: Python not found" >> "$LOG_FILE"
    exit 1
fi

echo "[$(date -Iseconds)] Monday CEO briefing complete" >> "$LOG_FILE"
