# Test Daily Briefing Script - Windows PowerShell
# Simulates scheduled run for testing
#
# Usage:
#   .\test_daily_briefing.ps1

$ErrorActionPreference = "Stop"

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "========================================"
Write-Host "Testing Daily Briefing Script"
Write-Host "========================================"
Write-Host

# Check if script exists
if (-not (Test-Path "$SCRIPT_DIR\daily_briefing.ps1")) {
    Write-Host "ERROR: daily_briefing.ps1 not found in $SCRIPT_DIR" -ForegroundColor Red
    exit 1
}

Write-Host "1. Running daily briefing script..."
Write-Host "----------------------------------------"

# Run the script
& "$SCRIPT_DIR\daily_briefing.ps1"

$EXIT_CODE = $LASTEXITCODE

Write-Host "----------------------------------------"
Write-Host
Write-Host "2. Test Results:"
Write-Host "   Exit code: $EXIT_CODE"

if ($EXIT_CODE -eq 0) {
    Write-Host "   ✓ Test PASSED" -ForegroundColor Green
} else {
    Write-Host "   ✗ Test FAILED" -ForegroundColor Red
}

Write-Host
Write-Host "3. Checking log file..."
$LOG_DIR = Join-Path $SCRIPT_DIR "..\AI-Employee-Vault\Logs"
$LOG_FILE = Get-ChildItem "$LOG_DIR\daily-briefing-*.log" | Sort-Object LastWriteTime -Descending | Select-Object -First 1

if ($LOG_FILE) {
    Write-Host "   ✓ Log file found: $($LOG_FILE.FullName)" -ForegroundColor Green
    Write-Host
    Write-Host "   Last 10 lines:"
    Write-Host "   ---"
    Get-Content $LOG_FILE.FullName -Tail 10 | ForEach-Object { Write-Host "   $_" }
    Write-Host "   ---"
} else {
    Write-Host "   ⚠ No log file found" -ForegroundColor Yellow
}

Write-Host
Write-Host "========================================"
Write-Host "Test Complete"
Write-Host "========================================"

exit $EXIT_CODE
