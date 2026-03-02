#!/usr/bin/env bash
# Monday CEO Briefing Generator — shell wrapper
# Usage: ./run.sh [--dry-run] [--debug]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../../../.." && pwd)"

cd "$PROJECT_ROOT"

# Load .env if exists
if [[ -f ".env" ]]; then
    export $(grep -v '^#' .env | xargs)
fi

# Parse arguments
LOG_LEVEL="INFO"

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            export DRY_RUN="true"
            shift
            ;;
        --debug)
            LOG_LEVEL="DEBUG"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: ./run.sh [--dry-run] [--debug]"
            exit 1
            ;;
    esac
done

# Run generator
export LOG_LEVEL
exec python3 monday_ceo_briefing.py
