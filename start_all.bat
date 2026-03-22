@echo off
REM =============================================================================
# AI Employee - Start All Services
# =============================================================================
REM This script starts all components of the AI Employee system:
REM   1. Backend API (FastAPI on port 8000)
REM   2. Frontend (Next.js on port 3000)
REM   3. Watchers (Gmail, LinkedIn, WhatsApp monitors)
REM   4. AI Agent (Ralph reasoning loop)
REM   5. Orchestrator (Task lifecycle manager)
REM =============================================================================

echo.
echo =============================================================================
echo                    AI EMPLOYEE - STARTING ALL SERVICES
echo =============================================================================
echo.

REM Check if Python is available
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ and add it to PATH
    pause
    exit /b 1
)

REM Check if Node.js is available
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Node.js is not installed or not in PATH
    echo Please install Node.js 20+ and add it to PATH
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist ".env" (
    echo [WARNING] .env file not found
    echo Please create .env file from .env.example
    pause
)

REM Create logs directory if it doesn't exist
if not exist "logs" mkdir logs

echo [INFO] Starting Backend API (FastAPI)...
start "AI Employee - Backend" cmd /k "cd backend && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 3 /nobreak >nul

echo [INFO] Starting Frontend (Next.js)...
start "AI Employee - Frontend" cmd /k "cd frontend && npm run dev"
timeout /t 5 /nobreak >nul

echo [INFO] Starting Watchers...
start "AI Employee - Watchers" cmd /k "python run.py watcher gmail --watch"
timeout /t 2 /nobreak >nul

start "AI Employee - Watchers" cmd /k "python run.py watcher linkedin --watch"
timeout /t 2 /nobreak >nul

start "AI Employee - Watchers" cmd /k "python run.py watcher whatsapp --watch"
timeout /t 2 /nobreak >nul

echo [INFO] Starting Orchestrator...
start "AI Employee - Orchestrator" cmd /k "python run.py orchestrator"
timeout /t 2 /nobreak >nul

echo [INFO] Starting AI Agent (Ralph Loop)...
start "AI Employee - AI Agent" cmd /k "python run.py agent"
timeout /t 2 /nobreak >nul

echo.
echo =============================================================================
echo                      ALL SERVICES STARTED SUCCESSFULLY
echo =============================================================================
echo.
echo Services running:
echo   [1] Backend API    : http://localhost:8000
echo   [2] Frontend       : http://localhost:3000
echo   [3] Watchers       : Monitoring Gmail, LinkedIn, WhatsApp
echo   [4] Orchestrator   : Managing task lifecycle
echo   [5] AI Agent       : Ralph reasoning loop active
echo.
echo To stop all services, close the terminal windows or press Ctrl+C in each
echo.
echo Logs directory: .\logs\
echo =============================================================================
echo.

pause
