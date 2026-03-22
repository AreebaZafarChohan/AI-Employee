@echo off
echo Starting AI Employee Backend...
echo.

REM Check if WSL is available
wsl echo "WSL is available" >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: WSL is not available. Please install WSL.
    pause
    exit /b 1
)

REM Kill any existing backend
wsl bash -c "pkill -9 uvicorn 2>/dev/null" >nul 2>&1

REM Start backend in WSL
echo Starting backend on http://localhost:8000...
echo Press Ctrl+C to stop the backend.
echo.

wsl bash -c "cd /mnt/d/Gemini_Cli/hackathon/hackathon_0/AI-Employee/backend-python && source venv/bin/activate && PYTHONPATH=. uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

pause
