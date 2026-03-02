# AI Employee - Scheduling Guide

Automate daily briefing generation at 8:00 AM using OS-native schedulers.

---

## Task Description

**Command:** Generate daily briefing and update Dashboard

**Schedule:** Every day at 8:00 AM

**Output:** Updated `AI-Employee-Vault/Dashboard.md` with latest metrics and summary

---

## macOS / Linux (cron)

### Step 1: Create the Runner Script

Create `scripts/daily_briefing.sh`:

```bash
#!/usr/bin/env bash
# Daily Briefing Runner
# Runs AI Employee daily briefing generation

set -euo pipefail

# Project root directory
PROJECT_ROOT="/path/to/AI-Employee"  # UPDATE THIS PATH

# Change to project directory
cd "$PROJECT_ROOT"

# Log file
LOG_FILE="$PROJECT_ROOT/AI-Employee-Vault/Logs/daily-briefing-$(date +%Y-%m-%d).log"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

echo "[$(date -Iseconds)] Starting daily briefing..." >> "$LOG_FILE"

# Run Claude with daily briefing prompt
# Option A: Using Claude Code CLI (if installed)
if command -v claude &> /dev/null; then
    claude --prompt "Generate daily briefing and update Dashboard" >> "$LOG_FILE" 2>&1
else
    echo "[$(date -Iseconds)] ERROR: Claude CLI not found" >> "$LOG_FILE"
    exit 1
fi

echo "[$(date -Iseconds)] Daily briefing complete" >> "$LOG_FILE"
```

### Step 2: Make Script Executable

```bash
chmod +x /path/to/AI-Employee/scripts/daily_briefing.sh
```

### Step 3: Edit crontab

```bash
crontab -e
```

### Step 4: Add Cron Entry

Add this line to run at 8:00 AM daily:

```cron
# AI Employee Daily Briefing - 8:00 AM every day
0 8 * * * /path/to/AI-Employee/scripts/daily_briefing.sh
```

### Step 5: Verify Cron Job

```bash
# List all cron jobs
crontab -l

# Check cron service status
sudo systemctl status cron    # Linux
sudo launchctl list | grep cron # macOS
```

### Example: Complete Setup

```bash
# Create scripts directory
mkdir -p /path/to/AI-Employee/scripts

# Create the script
cat > /path/to/AI-Employee/scripts/daily_briefing.sh << 'EOF'
#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="/Users/yourname/projects/AI-Employee"
cd "$PROJECT_ROOT"
LOG_FILE="$PROJECT_ROOT/AI-Employee-Vault/Logs/daily-briefing-$(date +%Y-%m-%d).log"
mkdir -p "$(dirname "$LOG_FILE")"
echo "[$(date -Iseconds)] Starting daily briefing..." >> "$LOG_FILE"
if command -v claude &> /dev/null; then
    claude --prompt "Generate daily briefing and update Dashboard" >> "$LOG_FILE" 2>&1
else
    echo "[$(date -Iseconds)] ERROR: Claude CLI not found" >> "$LOG_FILE"
    exit 1
fi
echo "[$(date -Iseconds)] Daily briefing complete" >> "$LOG_FILE"
EOF

# Make executable
chmod +x /path/to/AI-Employee/scripts/daily_briefing.sh

# Add to crontab
(crontab -l 2>/dev/null; echo "0 8 * * * /path/to/AI-Employee/scripts/daily_briefing.sh") | crontab -
```

---

## Windows (Task Scheduler)

### Option A: Using PowerShell Script

#### Step 1: Create the Runner Script

Create `scripts/daily_briefing.ps1`:

```powershell
# Daily Briefing Runner
# Runs AI Employee daily briefing generation

$ErrorActionPreference = "Stop"

# Project root directory
$PROJECT_ROOT = "D:\Gemini_Cli\hackathon\hackathon_0\AI-Employee"

# Change to project directory
Set-Location $PROJECT_ROOT

# Log file
$LOG_FILE = "$PROJECT_ROOT\AI-Employee-Vault\Logs\daily-briefing-$(Get-Date -Format 'yyyy-MM-dd').log"

# Ensure log directory exists
$null = New-Item -ItemType Directory -Force -Path (Split-Path $LOG_FILE)

# Log start
"[$(Get-Date -Format 'o')] Starting daily briefing..." | Add-Content $LOG_FILE

try {
    # Run Claude with daily briefing prompt
    # Option A: Using Claude Code CLI (if installed)
    if (Get-Command claude -ErrorAction SilentlyContinue) {
        claude --prompt "Generate daily briefing and update Dashboard" | Add-Content $LOG_FILE
    }
    # Option B: Using Python orchestrator (alternative)
    elseif (Test-Path "orchestrator.py") {
        python orchestrator.py | Add-Content $LOG_FILE
    }
    else {
        throw "No Claude CLI or orchestrator found"
    }
    
    # Log success
    "[$(Get-Date -Format 'o')] Daily briefing complete" | Add-Content $LOG_FILE
}
catch {
    "[$(Get-Date -Format 'o')] ERROR: $($_.Exception.Message)" | Add-Content $LOG_FILE
    exit 1
}
```

#### Step 2: Create Task Scheduler XML

Create `scripts/daily_briefing_task.xml`:

```xml
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>AI Employee Daily Briefing - Runs at 8:00 AM daily</Description>
    <URI>\AI-Employee\DailyBriefing</URI>
  </RegistrationInfo>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2026-02-26T08:00:00</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByDay>
        <DaysInterval>1</DaysInterval>
      </ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>S-1-5-18</UserId>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>true</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>true</WakeToRun>
    <ExecutionTimeLimit>PT1H</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>powershell.exe</Command>
      <Arguments>-ExecutionPolicy Bypass -File "D:\Gemini_Cli\hackathon\hackathon_0\AI-Employee\scripts\daily_briefing.ps1"</Arguments>
      <WorkingDirectory>D:\Gemini_Cli\hackathon\hackathon_0\AI-Employee</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
```

#### Step 3: Import Task

Run PowerShell as Administrator:

```powershell
# Import the task
schtasks /Create /XML "D:\Gemini_Cli\hackathon\hackathon_0\AI-Employee\scripts\daily_briefing_task.xml" /TN "AI-Employee\DailyBriefing"

# Verify task
schtasks /Query /TN "AI-Employee\DailyBriefing"

# Run task manually (test)
schtasks /Run /TN "AI-Employee\DailyBriefing"
```

### Option B: Using GUI (Manual)

1. **Open Task Scheduler**
   - Press `Win + R`
   - Type `taskschd.msc`
   - Press Enter

2. **Create Basic Task**
   - Right-click "Task Scheduler Library"
   - Select "Create Basic Task..."
   - Name: `AI Employee Daily Briefing`
   - Description: `Generate daily briefing at 8:00 AM`

3. **Set Trigger**
   - Select "Daily"
   - Start: `8:00 AM`
   - Recur every: `1` days

4. **Set Action**
   - Select "Start a program"
   - Program/script: `powershell.exe`
   - Add arguments: `-ExecutionPolicy Bypass -File "D:\Gemini_Cli\hackathon\hackathon_0\AI-Employee\scripts\daily_briefing.ps1"`
   - Start in: `D:\Gemini_Cli\hackathon\hackathon_0\AI-Employee`

5. **Finish**
   - Check "Open Properties"
   - Check "Run with highest privileges"
   - Configure for: `Windows 10` (or your version)

---

## Manual Test Commands

### macOS / Linux

```bash
# Simulate scheduled run
/path/to/AI-Employee/scripts/daily_briefing.sh

# Check exit code
echo $?

# View log
tail -f /path/to/AI-Employee/AI-Employee-Vault/Logs/daily-briefing-*.log
```

### Windows

```powershell
# Run PowerShell script directly
powershell.exe -ExecutionPolicy Bypass -File "D:\Gemini_Cli\hackathon\hackathon_0\AI-Employee\scripts\daily_briefing.ps1"

# Run scheduled task manually
schtasks /Run /TN "AI-Employee\DailyBriefing"

# Check task status
schtasks /Query /TN "AI-Employee\DailyBriefing" /V /FO LIST

# View log
Get-Content "D:\Gemini_Cli\hackathon\hackathon_0\AI-Employee\AI-Employee-Vault\Logs\daily-briefing-*.log" -Tail 20
```

### Quick Test (Any OS)

```bash
# Test Claude CLI directly
claude --prompt "Generate daily briefing and update Dashboard"

# Check if Dashboard was updated
cat AI-Employee-Vault/Dashboard.md | head -30
```

---

## Troubleshooting

### Cron Job Not Running

```bash
# Check cron logs
grep CRON /var/log/syslog        # Ubuntu/Debian
grep cron /var/log/cron          # RHEL/CentOS
journalctl -u cron --no-pager    # systemd

# Verify cron syntax
crontab -l

# Test script manually
/path/to/AI-Employee/scripts/daily_briefing.sh
```

### Windows Task Not Running

```powershell
# Check task history
Get-ScheduledTask -TaskName "DailyBriefing" -TaskPath "AI-Employee\" | Get-ScheduledTaskInfo

# Check Event Viewer
Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-TaskScheduler/Operational'; Id=100} | Select-Object -First 10

# Verify task exists
schtasks /Query /TN "AI-Employee\DailyBriefing"
```

### Claude CLI Not Found

```bash
# Check if installed
which claude        # macOS/Linux
where claude        # Windows

# Install Claude Code CLI
npm install -g @anthropic-ai/claude-code

# Or use Python alternative
python orchestrator.py
```

---

## Environment Variables

Add to your script or system environment:

```bash
# Common variables
export VAULT_PATH="/path/to/AI-Employee-Vault"
export LOG_LEVEL="INFO"
export DRY_RUN="false"

# Claude-specific
export ANTHROPIC_API_KEY="your-api-key"  # If using API directly
```

---

## Monitoring

### Daily Check

```bash
# Check if log exists and has recent entries
ls -lh AI-Employee-Vault/Logs/daily-briefing-*.log

# Check for errors
grep -i error AI-Employee-Vault/Logs/daily-briefing-*.log | tail -5
```

### Weekly Summary

```bash
# Count successful runs
grep -c "complete" AI-Employee-Vault/Logs/daily-briefing-*.log

# Count failures
grep -c "ERROR" AI-Employee-Vault/Logs/daily-briefing-*.log
```

---

## Best Practices

1. **Test manually first** - Run script before scheduling
2. **Check permissions** - Ensure script can write to Logs/
3. **Set up alerts** - Monitor for failures
4. **Rotate logs** - Keep last 30 days of logs
5. **Handle timezone** - Cron uses system timezone
6. **Wake on AC** - Configure laptop to wake for tasks

---

---

## Monday CEO Briefing (Weekly)

**Command:** Generate weekly CEO briefing with revenue, bottlenecks, subscriptions, suggestions, and pending approvals

**Schedule:** Every Sunday at 11:00 PM (ready for Monday morning)

**Output:** Updated `AI-Employee-Vault/Briefings/YYYY-MM-DD_Monday.md` and `Dashboard.md`

### macOS / Linux (cron)

```cron
# Sunday 11:00 PM — Monday CEO Briefing
0 23 * * 0 /path/to/AI-Employee/scripts/monday_ceo_briefing.sh
```

### Windows (Task Scheduler)

```powershell
# Create weekly task — Sunday 11:00 PM
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 11:00PM
$action = New-ScheduledTaskAction -Execute "python" -Argument "monday_ceo_briefing.py" -WorkingDirectory "D:\Gemini_Cli\hackathon\hackathon_0\AI-Employee"
Register-ScheduledTask -TaskName "AI-Employee\MondayCEOBriefing" -Trigger $trigger -Action $action -Description "Weekly CEO Briefing"
```

### Manual Test

```bash
# Dry run
DRY_RUN=true python monday_ceo_briefing.py

# Full run
python monday_ceo_briefing.py

# Verify output
cat AI-Employee-Vault/Briefings/*_Monday.md
```

---

## Quick Reference

| OS | Command | Schedule |
|----|---------|----------|
| macOS/Linux | `crontab -e` | `0 8 * * *` (daily), `0 23 * * 0` (weekly) |
| Windows | `schtasks /Create` | Daily 8:00 AM, Sunday 11:00 PM |
| Test | Run script manually | On-demand |

---

**Next Steps:**
1. Update paths in scripts for your system
2. Test manually with test commands
3. Schedule using your OS instructions
4. Monitor first run to verify success
