# AI Employee - Windows Task Scheduler Setup
# Run this script as Administrator to create the daily briefing task
#
# Usage:
#   .\setup_scheduled_task.ps1

$ErrorActionPreference = "Stop"

Write-Host "========================================"
Write-Host "AI Employee - Task Scheduler Setup"
Write-Host "========================================"
Write-Host

# Get script directory
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PROJECT_ROOT = Split-Path -Parent $SCRIPT_DIR

Write-Host "Project root: $PROJECT_ROOT"
Write-Host

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] `
    [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole( `
    [Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "WARNING: Not running as Administrator!" -ForegroundColor Yellow
    Write-Host "Task creation may fail without elevated privileges."
    Write-Host
    $response = Read-Host "Continue anyway? (y/n)"
    if ($response -ne 'y') {
        Write-Host "Aborted."
        exit 0
    }
    Write-Host
}

# Task name
$TASK_NAME = "AI-Employee\DailyBriefing"
$TASK_XML = "$SCRIPT_DIR\daily_briefing_task.xml"

# Update XML with actual project root
$xmlContent = Get-Content $TASK_XML -Raw
$xmlContent = $xmlContent.Replace('$(PROJECT_ROOT)', $PROJECT_ROOT)

# Save updated XML
$TEMP_XML = "$env:TEMP\daily_briefing_task_temp.xml"
$xmlContent | Out-File -FilePath $TEMP_XML -Encoding UTF8

Write-Host "1. Checking if task already exists..."
$existingTask = schtasks /Query /TN $TASK_NAME 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ⚠ Task already exists" -ForegroundColor Yellow
    $response = Read-Host "   Delete and recreate? (y/n)"
    if ($response -eq 'y') {
        schtasks /Delete /TN $TASK_NAME /F
        Write-Host "   ✓ Task deleted"
    } else {
        Write-Host "   Skipping creation"
        Write-Host
        Write-Host "To run existing task manually:"
        Write-Host "  schtasks /Run /TN `"$TASK_NAME`""
        exit 0
    }
} else {
    Write-Host "   ✓ Task does not exist"
}

Write-Host
Write-Host "2. Creating scheduled task..."
Write-Host "   Task name: $TASK_NAME"
Write-Host "   Schedule: Daily at 8:00 AM"
Write-Host "   Script: $SCRIPT_DIR\daily_briefing.ps1"
Write-Host

# Create task
schtasks /Create /XML $TEMP_XML /TN $TASK_NAME

if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✓ Task created successfully" -ForegroundColor Green
} else {
    Write-Host "   ✗ Task creation failed" -ForegroundColor Red
    Write-Host
    Write-Host "Troubleshooting:"
    Write-Host "  1. Run this script as Administrator"
    Write-Host "  2. Check Task Scheduler for errors"
    Write-Host "  3. Manually create task using GUI"
    exit 1
}

Write-Host
Write-Host "3. Verifying task..."
schtasks /Query /TN $TASK_NAME /V /FO LIST | Select-String "TaskName|Status|Next Run"

Write-Host
Write-Host "========================================"
Write-Host "Setup Complete!"
Write-Host "========================================"
Write-Host
Write-Host "Next steps:"
Write-Host "  1. Test the task manually:"
Write-Host "     schtasks /Run /TN `"$TASK_NAME`""
Write-Host
Write-Host "  2. Check task history:"
Write-Host "     Get-ScheduledTask -TaskName DailyBriefing -TaskPath AI-Employee\ | Get-ScheduledTaskInfo"
Write-Host
Write-Host "  3. View logs:"
Write-Host "     Get-Content "$PROJECT_ROOT\AI-Employee-Vault\Logs\daily-briefing-*.log" -Tail 20"
Write-Host
Write-Host "  4. Open Task Scheduler:"
Write-Host "     taskschd.msc"
Write-Host

# Cleanup
Remove-Item $TEMP_XML -Force
