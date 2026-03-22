#!/bin/bash
# =============================================================================
# AI Employee - Start All Services
# =============================================================================
# This script starts all components of the AI Employee system:
#   1. Backend API (FastAPI on port 8000)
#   2. Frontend (Next.js on port 3000)
#   3. Watchers (Gmail, LinkedIn, WhatsApp monitors)
#   4. AI Agent (Ralph reasoning loop)
#   5. Orchestrator (Task lifecycle manager)
# =============================================================================

echo ""
echo "============================================================================="
echo "                   AI EMPLOYEE - STARTING ALL SERVICES"
echo "============================================================================="
echo ""

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "[ERROR] Python is not installed or not in PATH"
    echo "Please install Python 3.8+ and add it to PATH"
    exit 1
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "[ERROR] Node.js is not installed or not in PATH"
    echo "Please install Node.js 20+ and add it to PATH"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "[WARNING] .env file not found"
    echo "Please create .env file from .env.example"
    read -p "Press enter to continue anyway..."
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Function to start a service in background
start_service() {
    local name=$1
    local command=$2
    echo "[INFO] Starting $name..."
    nohup $command > "logs/${name}.log" 2>&1 &
    echo $! > "logs/${name}.pid"
    sleep 2
}

# Start Backend API
start_service "backend" "cd backend && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

# Start Frontend
start_service "frontend" "cd frontend && npm run dev"

# Start Watchers
start_service "watcher-gmail" "python run.py watcher gmail --watch"
start_service "watcher-linkedin" "python run.py watcher linkedin --watch"
start_service "watcher-whatsapp" "python run.py watcher whatsapp --watch"

# Start Orchestrator
start_service "orchestrator" "python run.py orchestrator"

# Start AI Agent
start_service "ai-agent" "python run.py agent"

echo ""
echo "============================================================================="
echo "                     ALL SERVICES STARTED SUCCESSFULLY"
echo "============================================================================="
echo ""
echo "Services running:"
echo "  [1] Backend API    : http://localhost:8000"
echo "  [2] Frontend       : http://localhost:3000"
echo "  [3] Watchers       : Monitoring Gmail, LinkedIn, WhatsApp"
echo "  [4] Orchestrator   : Managing task lifecycle"
echo "  [5] AI Agent       : Ralph reasoning loop active"
echo ""
echo "Log files: ./logs/*.log"
echo "PID files: ./logs/*.pid"
echo ""
echo "To stop all services, run: ./start_all.sh stop"
echo "To view logs, run: tail -f logs/<service>.log"
echo "============================================================================="
echo ""
