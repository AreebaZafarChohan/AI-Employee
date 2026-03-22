#!/bin/bash
# Run Gold Tier API server
# Usage: ./run_api.sh [dev|prod]

set -e

MODE="${1:-dev}"

echo "Starting Gold Tier API in $MODE mode..."

if [ "$MODE" = "dev" ]; then
    # Development: auto-reload, single worker
    export LOG_LEVEL=DEBUG
    uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
else
    # Production: multiple workers
    export LOG_LEVEL=INFO
    uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4
fi
