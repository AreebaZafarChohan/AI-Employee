#!/usr/bin/env bash
# Silver Reasoning Engine — shell wrapper
# Usage: ./run.sh [--dry-run] [--debug]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../../../../" && pwd)"

cd "$PROJECT_ROOT"

# Load .env if present
if [[ -f ".env" ]]; then
    set -a
    source .env
    set +a
fi

SRE_DRY_RUN="${SRE_DRY_RUN:-false}"
SRE_LOG_LEVEL="${SRE_LOG_LEVEL:-INFO}"

for arg in "$@"; do
  case "$arg" in
    --dry-run) SRE_DRY_RUN="true" ;;
    --debug)   SRE_LOG_LEVEL="DEBUG" ;;
  esac
done

export SRE_DRY_RUN
export SRE_LOG_LEVEL

exec python3 "${SCRIPT_DIR}/silver_reasoning_engine.py"
