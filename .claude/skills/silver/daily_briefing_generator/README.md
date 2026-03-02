# Daily Briefing Generator

Automatically generates daily briefings from your vault data. Creates executive summaries, revenue snapshots, task summaries, identifies bottlenecks, and provides actionable suggestions.

## Quick Start

```bash
# Generate daily briefing
python daily_briefing_generator.py

# Preview mode (no file writes)
DRY_RUN=true python daily_briefing_generator.py
```

## What It Does

1. **Reads** business goals from Company_Handbook.md
2. **Scans** /Done folder for completed tasks (last 24h)
3. **Extracts** accounting/financial data
4. **Generates** 5-section briefing:
   - Executive Summary
   - Revenue Snapshot
   - Task Summary
   - Bottlenecks & Blockers
   - Suggestions & Next Steps
5. **Saves** to `/Briefings/YYYY-MM-DD_Daily.md`
6. **Updates** Dashboard.md with briefing link
7. **Logs** generation to `/Logs/`

## Output Example

```markdown
# Daily Briefing — 2026-02-25

## Executive Summary
Active goals, today's activity stats, task breakdown

## Revenue Snapshot
Recent transactions, revenue signals

## Task Summary
Completed tasks with previews

## Bottlenecks & Blockers
High priority items, pending approvals, goal alignment

## Suggestions & Next Steps
Actionable recommendations
```

## Configuration

| Env Var | Default | Description |
|---------|---------|-------------|
| `DRY_RUN` | `false` | Preview without writing files |
| `LOG_LEVEL` | `INFO` | DEBUG/INFO/WARNING/ERROR |
| `BRIEFING_LOOKBACK_HOURS` | `24` | Hours of tasks to include |

## Schedule

Add to your daily 8:00 AM scheduler:

**macOS/Linux:**
```cron
0 8 * * * python /path/to/daily_briefing_generator.py
```

**Windows:**
```powershell
# Add to daily_briefing.ps1
python daily_briefing_generator.py
```

## Files Generated

| File | Purpose |
|------|---------|
| `Briefings/YYYY-MM-DD_Daily.md` | Daily briefing |
| `Logs/daily-briefing-YYYY-MM-DD.log` | Generation log |
| `Dashboard.md` | Updated with briefing link |

## Troubleshooting

### No briefing generated
```bash
# Check Python
python --version

# Install dependency
pip install pyyaml

# Run with debug logging
LOG_LEVEL=DEBUG python daily_briefing_generator.py
```

### Missing data
- Ensure Company_Handbook.md exists
- Check /Done folder has recent files
- Verify file timestamps are within 24h

## Test

```bash
# Dry run
DRY_RUN=true python daily_briefing_generator.py

# Check output
cat AI-Employee-Vault/Briefings/*_Daily.md | head -50
```
