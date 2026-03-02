# Daily Briefing Runner - Windows PowerShell
# Runs AI Employee daily briefing generation at 8:00 AM
#
# Usage:
#   .\daily_briefing.ps1
#
# Schedule with Task Scheduler:
#   schtasks /Create /XML "scripts\daily_briefing_task.xml" /TN "AI-Employee\DailyBriefing"

$ErrorActionPreference = "Stop"

# Get script directory
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PROJECT_ROOT = Split-Path -Parent $SCRIPT_DIR

# Change to project directory
Set-Location $PROJECT_ROOT

# Log file
$LOG_DIR = Join-Path $PROJECT_ROOT "AI-Employee-Vault\Logs"
$LOG_FILE = Join-Path $LOG_DIR "daily-briefing-$(Get-Date -Format 'yyyy-MM-dd').log"

# Ensure log directory exists
$null = New-Item -ItemType Directory -Force -Path $LOG_DIR

# Log function
function Log {
    param([string]$Message)
    $timestamp = Get-Date -Format 'o'
    "$timestamp $Message" | Add-Content $LOG_FILE
    Write-Host "$timestamp $Message"
}

# Start
Log "Starting daily briefing..."

try {
    # Option 1: Generate daily briefing (primary task)
    if (Test-Path "$PROJECT_ROOT\daily_briefing_generator.py") {
        Log "Generating daily briefing..."
        $output = cmd.exe /c "python `"$PROJECT_ROOT\daily_briefing_generator.py`" 2>&1"
        $exitCode = $LASTEXITCODE
        $output | Add-Content $LOG_FILE
        if ($exitCode -ne 0) {
            throw "Daily briefing generator failed with exit code $exitCode"
        }
        Log "Daily briefing generated"
    }
    # Option 2: Use orchestrator if available
    elseif (Test-Path "$PROJECT_ROOT\orchestrator.py") {
        Log "Using orchestrator.py..."
        $output = cmd.exe /c "python `"$PROJECT_ROOT\orchestrator.py`" 2>&1"
        $exitCode = $LASTEXITCODE
        $output | Add-Content $LOG_FILE
        if ($exitCode -ne 0) {
            throw "Orchestrator failed with exit code $exitCode"
        }
        Log "Daily briefing complete"
    }
    # Option 3: Use Python script with Claude API
    elseif (Test-Path "$PROJECT_ROOT\ai_employee.py") {
        Log "Using ai_employee.py..."
        $output = cmd.exe /c "python `"$PROJECT_ROOT\ai_employee.py`" --prompt `"Generate daily briefing and update Dashboard`" 2>&1"
        $exitCode = $LASTEXITCODE
        $output | Add-Content $LOG_FILE
        if ($exitCode -ne 0) {
            throw "ai_employee.py failed with exit code $exitCode"
        }
        Log "Daily briefing complete"
    }
    # Option 4: Use Claude Code CLI (if installed with echo pipe)
    elseif (Get-Command claude -ErrorAction SilentlyContinue) {
        Log "Using Claude CLI (pipe method)..."
        $output = echo "Generate daily briefing and update Dashboard" | claude 2>&1
        $exitCode = $LASTEXITCODE
        $output | Add-Content $LOG_FILE
        if ($exitCode -ne 0) {
            throw "Claude CLI failed with exit code $exitCode"
        }
        Log "Daily briefing complete"
    }
    else {
        throw "No daily_briefing_generator, orchestrator, ai_employee.py, or Claude CLI found"
    }
    
    # Show log location
    Log "Log saved to: $LOG_FILE"
}
catch {
    Log "ERROR: $($_.Exception.Message)"
    exit 1
}
