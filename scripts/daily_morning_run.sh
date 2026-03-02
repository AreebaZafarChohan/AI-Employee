#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# AI Employee — Daily Morning Run
# Runs every day at 8:00 AM
#
# Steps:
#   1. silver_process_engine  — triage Needs_Action vault
#   2. linkedin_post_generator — draft LinkedIn post to /Social/
#   3. daily_briefing_generator — write briefing to /Briefings/
#
# Usage:
#   ./scripts/daily_morning_run.sh           # normal run
#   ./scripts/daily_morning_run.sh --dry-run # preview only
#   ./scripts/daily_morning_run.sh --debug   # verbose logging
# ─────────────────────────────────────────────────────────────

set -euo pipefail

# ── Resolve project root ──────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "$PROJECT_ROOT"

# ── Load .env ─────────────────────────────────────────────────
if [[ -f ".env" ]]; then
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
fi

# ── Parse flags ───────────────────────────────────────────────
DRY_RUN="false"
LOG_LEVEL="INFO"

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN="true" ;;
    --debug)   LOG_LEVEL="DEBUG" ;;
  esac
done

export DRY_RUN
export LOG_LEVEL
export SILVER_PE_DRY_RUN="$DRY_RUN"
export SILVER_PE_LOG_LEVEL="$LOG_LEVEL"
export LINKEDIN_DRY_RUN="$DRY_RUN"

# ── Logging helper ────────────────────────────────────────────
LOG_FILE="${PROJECT_ROOT}/logs/daily_morning_run_$(date +%Y%m%d).log"
mkdir -p "${PROJECT_ROOT}/logs"

log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $*"
    echo "$msg"
    echo "$msg" >> "$LOG_FILE"
}

log "========================================"
log " AI Employee — Daily Morning Run"
log " DRY_RUN=${DRY_RUN}  LOG_LEVEL=${LOG_LEVEL}"
log "========================================"

FAILED=0

# ── Step 1: Silver Process Engine ────────────────────────────
log ""
log "▶ Step 1/3 — Silver Process Engine"
if python3 .claude/skills/silver/silver_process_engine/assets/silver_process_engine.py >> "$LOG_FILE" 2>&1; then
    log "  ✓ Silver Process Engine completed"
else
    log "  ✗ Silver Process Engine FAILED (exit $?)"
    FAILED=$((FAILED + 1))
fi

# ── Step 2: LinkedIn Post Generator ──────────────────────────
log ""
log "▶ Step 2/3 — LinkedIn Post Generator (draft)"
if python3 .claude/skills/silver/linkedin_post_generator/assets/linkedin_post_generator.py >> "$LOG_FILE" 2>&1; then
    log "  ✓ LinkedIn draft saved to AI-Employee-Vault/Social/"
else
    log "  ✗ LinkedIn Post Generator FAILED (exit $?)"
    FAILED=$((FAILED + 1))
fi

# ── Step 3: Daily Briefing Generator ─────────────────────────
log ""
log "▶ Step 3/3 — Daily Briefing Generator"
if python3 daily_briefing_generator.py >> "$LOG_FILE" 2>&1; then
    log "  ✓ Briefing saved to AI-Employee-Vault/Briefings/"
else
    log "  ✗ Daily Briefing Generator FAILED (exit $?)"
    FAILED=$((FAILED + 1))
fi

# ── Summary ───────────────────────────────────────────────────
log ""
log "========================================"
if [[ $FAILED -eq 0 ]]; then
    log " ✅ All 3 steps completed successfully"
else
    log " ⚠  $FAILED step(s) failed — check log: $LOG_FILE"
fi
log " Log: $LOG_FILE"
log "========================================"

exit $FAILED
