# Monday CEO Briefing Generator

Generates a comprehensive weekly CEO briefing from vault data. Covers revenue, bottlenecks, subscriptions, suggestions, and pending approvals over a 7-day window.

## Quick Start

```bash
# Generate Monday CEO briefing
python monday_ceo_briefing.py

# Preview mode (no file writes)
DRY_RUN=true python monday_ceo_briefing.py
```

## What It Does

1. **Reads** business goals from Company_Handbook.md
2. **Scans** /Done folder for completed tasks (last 7 days)
3. **Extracts** accounting/financial data and subscriptions
4. **Reads** pending approvals from /Pending_Approval
5. **Generates** 6-section briefing:
   - Executive Summary
   - Revenue Summary
   - Bottlenecks & Blockers
   - Subscription Audit
   - Suggestions & Next Steps
   - Pending Approvals Overview
6. **Saves** to `/Briefings/YYYY-MM-DD_Monday.md`
7. **Updates** Dashboard.md with briefing link
8. **Logs** generation to `/Logs/`

## Configuration

| Env Var | Default | Description |
|---------|---------|-------------|
| `DRY_RUN` | `false` | Preview without writing files |
| `LOG_LEVEL` | `INFO` | DEBUG/INFO/WARNING/ERROR |
| `BRIEFING_LOOKBACK_DAYS` | `7` | Days of data to include |

## Schedule

Runs Sunday 11:00 PM so the briefing is ready Monday morning:

```cron
0 23 * * 0 /path/to/scripts/monday_ceo_briefing.sh
```

## Files Generated

| File | Purpose |
|------|---------|
| `Briefings/YYYY-MM-DD_Monday.md` | Weekly CEO briefing |
| `Logs/monday-ceo-briefing-YYYY-MM-DD.log` | Generation log |
| `Dashboard.md` | Updated with briefing link |
