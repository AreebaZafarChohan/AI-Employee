#!/usr/bin/env bash
# Orchestrator — shell wrapper
# Usage: ./run.sh [--watch] [--interval SECONDS] [--dry-run]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../../../.." && pwd)"

cd "$PROJECT_ROOT"

# Load .env if exists
if [[ -f ".env" ]]; then
    export $(grep -v '^#' .env | xargs)
fi

# Default values
WATCH=""
INTERVAL=""
DRY_RUN_FLAG=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --watch)
            WATCH="--watch"
            shift
            ;;
        --interval)
            INTERVAL="--interval $2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN_FLAG="--dry-run"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: ./run.sh [--watch] [--interval SECONDS] [--dry-run]"
            exit 1
            ;;
    esac
done

# Run orchestrator
exec python3 orchestrator.py $WATCH $INTERVAL $DRY_RUN_FLAG
