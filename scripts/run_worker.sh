#!/bin/bash
# Run Gold Tier Celery Worker
# Usage: ./run_worker.sh [dev|prod]

set -e

MODE="${1:-dev}"

echo "Starting Gold Tier Celery Worker in $MODE mode..."

if [ "$MODE" = "dev" ]; then
    # Development: single worker, verbose logging
    export LOG_LEVEL=DEBUG
    celery -A src.workers.celery_app worker --loglevel=debug --pool=solo
else
    # Production: concurrent workers
    export LOG_LEVEL=INFO
    celery -A src.workers.celery_app worker --loglevel=info --concurrency=4
fi
