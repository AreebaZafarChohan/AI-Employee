#!/bin/bash
# Start Python Watchers
echo "Starting Watcher System..."
cd "$(dirname "$0")/.."

# Activate virtual environment
if [ -d "backend/venv" ]; then
    source backend/venv/bin/activate
fi

export PYTHONPATH=$(pwd):$PYTHONPATH

# Run watcher orchestrator
exec python3 run_all_watchers.py
