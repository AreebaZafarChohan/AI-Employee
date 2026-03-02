@echo off
REM Setup Email MCP Server for Claude Desktop on Windows
REM Run this script to configure Claude Desktop

echo Setting up Email MCP Server for Claude Desktop...
echo.

REM Get the project root directory
set PROJECT_ROOT=%~dp0..
set PROJECT_ROOT=%PROJECT_ROOT:~0,-1%

echo Project root: %PROJECT_ROOT%
echo.

REM Run the PowerShell setup script
powershell.exe -ExecutionPolicy Bypass -File "%~dp0setup-claude-desktop.ps1"

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Restart Claude Desktop if it's running
echo 2. Claude will now have access to:
echo    - send_email
echo    - draft_email
echo    - search_inbox
echo.
echo The .env file has DRY_RUN=false, so emails will be sent for real!
echo.
pause
