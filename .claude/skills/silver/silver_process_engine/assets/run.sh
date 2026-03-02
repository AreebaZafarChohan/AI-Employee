#!/usr/bin/env bash
# Silver Process Engine — shell wrapper
# Usage: ./run.sh [--dry-run] [--debug]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"

DRY_RUN="${SILVER_PE_DRY_RUN:-false}"
LOG_LEVEL="${SILVER_PE_LOG_LEVEL:-INFO}"

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN="true" ;;
    --debug)   LOG_LEVEL="DEBUG" ;;
  esac
done

export SILVER_PE_DRY_RUN="$DRY_RUN"
export SILVER_PE_LOG_LEVEL="$LOG_LEVEL"

PYTHONPATH="${PYTHONPATH:-/tmp/gapi}" python3 "${SCRIPT_DIR}/silver_process_engine.py"
