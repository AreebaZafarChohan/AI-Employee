#!/bin/bash
# Start AI Agent Loop
echo "Starting AI Agent Reasoning Loop (Ralph)..."
cd "$(dirname "$0")/.."

# Activate virtual environment
if [ -d "backend/venv" ]; then
    source backend/venv/bin/activate
fi

export PYTHONPATH=$(pwd):$PYTHONPATH

# Detect which agent CLI is available
AGENT_CMD="gemini"
if ! command -v gemini &> /dev/null; then
    AGENT_CMD="claude"
fi

exec python3 ralph_loop.py --agent "$AGENT_CMD"
