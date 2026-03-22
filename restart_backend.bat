@echo off
REM Kill all uvicorn processes
taskkill /F /FI "WINDOWTITLE eq *uvicorn*" 2>nul
taskkill /F /IM python.exe /FI "MODULE eq uvicorn" 2>nul

REM Wait a moment
timeout /t 2 /nobreak >nul

REM Start backend
cd /d "%~dp0backend-python"
call venv\Scripts\activate.bat
set PYTHONPATH=.
start "UVICORN BACKEND" uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

echo Backend started!
