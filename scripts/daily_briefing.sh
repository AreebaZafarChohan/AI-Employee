#!/usr/bin/env bash
# Daily Briefing Runner - macOS/Linux
# Runs AI Employee daily briefing generation at 8:00 AM
#
# Usage:
#   ./daily_briefing.sh
#
# Schedule with cron:
#   0 8 * * * /path/to/AI-Employee/scripts/daily_briefing.sh

set -euo pipefail

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Change to project directory
cd "$PROJECT_ROOT"

# Log file
LOG_DIR="$PROJECT_ROOT/AI-Employee-Vault/Logs"
LOG_FILE="$LOG_DIR/daily-briefing-$(date +%Y-%m-%d).log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Log function
log() {
    echo "[$(date -Iseconds)] $*" | tee -a "$LOG_FILE"
}

# Start
log "Starting daily briefing..."

# Option 1: Generate daily briefing (primary task)
if [[ -f "$PROJECT_ROOT/daily_briefing_generator.py" ]]; then
    log "Generating daily briefing..."
    python3 "$PROJECT_ROOT/daily_briefing_generator.py" >> "$LOG_FILE" 2>&1
    log "Daily briefing generated"
# Option 2: Use orchestrator if available
elif [[ -f "$PROJECT_ROOT/orchestrator.py" ]]; then
    log "Using orchestrator.py..."
    python3 "$PROJECT_ROOT/orchestrator.py" >> "$LOG_FILE" 2>&1
    log "Daily briefing complete"
# Option 3: Use Python script with Claude API
elif [[ -f "$PROJECT_ROOT/ai_employee.py" ]]; then
    log "Using ai_employee.py..."
    python3 "$PROJECT_ROOT/ai_employee.py" --prompt "Generate daily briefing and update Dashboard" >> "$LOG_FILE" 2>&1
    log "Daily briefing complete"
# Option 4: Use Claude Code CLI (if installed with echo pipe)
elif command -v claude &> /dev/null; then
    log "Using Claude CLI (pipe method)..."
    echo "Generate daily briefing and update Dashboard" | claude >> "$LOG_FILE" 2>&1
    log "Daily briefing complete"
else
    log "ERROR: No daily briefing generator, orchestrator, ai_employee.py, or Claude CLI found"
    exit 1
fi

# Show log location
log "Log saved to: $LOG_FILE"
