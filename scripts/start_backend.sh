#!/bin/bash
# Start FastAPI Backend
echo "Starting AI Employee Backend..."
cd "$(dirname "$0")/.."

# Activate virtual environment
if [ -d "backend/venv" ]; then
    source backend/venv/bin/activate
fi

# Ensure PYTHONPATH is set to root
export PYTHONPATH=$(pwd):$PYTHONPATH

# Run uvicorn directly for better control
exec python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
