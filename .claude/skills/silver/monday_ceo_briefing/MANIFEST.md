# Monday CEO Briefing Generator — Manifest

**Created:** 2026-03-01
**Domain:** silver
**Status:** Production Ready
**Version:** 1.0.0

## Overview

The `monday_ceo_briefing` skill generates comprehensive weekly CEO briefings from vault data. It reads business goals, completed tasks (7-day window), accounting data, and pending approvals, then produces a 6-section executive report.

## Integration Points

### Upstream
- **Company_Handbook.md** — Business goals and objectives
- **/Done/*.md** — Completed tasks (last 7 days)
- **/Accounting/*.md** — Financial transactions, subscriptions
- **/Pending_Approval/*.md** — Items awaiting CEO approval
- **Dashboard.md** — Updated with briefing links

### Downstream
- **/Briefings/** — Generated briefing files
- **/Logs/** — Generation audit trail
- **CEO / Human stakeholders** — Weekly status awareness

### Data Flow
```
Company_Handbook ──────┐
/Done (7 days) ────────┤
/Accounting ───────────┼──→ monday_ceo_briefing ──→ /Briefings/
/Pending_Approval ─────┘                                ↓
                                                   Dashboard.md
```

## Configuration

Add to `.env`:
```bash
BRIEFING_LOOKBACK_DAYS=7
DRY_RUN=false
```

## Files

| File | Purpose |
|------|---------|
| `monday_ceo_briefing.py` | Main generation script |
| `SKILL.md` | Full specification |
| `MANIFEST.md` | This file |
| `README.md` | Quick start guide |
| `assets/run.sh` | Shell wrapper |

## Scheduling

### Sunday 11:00 PM (ready for Monday morning)

**cron (macOS/Linux):**
```cron
0 23 * * 0 /path/to/AI-Employee/scripts/monday_ceo_briefing.sh
```

**Task Scheduler (Windows):**
```xml
<Exec>
  <Command>python</Command>
  <Arguments>monday_ceo_briefing.py</Arguments>
</Exec>
```
Trigger: Weekly, Sunday 11:00 PM.

## Dependencies

- Python 3.8+
- PyYAML (`pip install pyyaml`)

## Environment Variables

| Variable | Default | Required |
|----------|---------|----------|
| `VAULT_PATH` | `./AI-Employee-Vault` | No |
| `DRY_RUN` | `false` | No |
| `LOG_LEVEL` | `INFO` | No |
| `BRIEFING_LOOKBACK_DAYS` | `7` | No |

## Output Files

### Briefing
- **Path:** `AI-Employee-Vault/Briefings/YYYY-MM-DD_Monday.md`
- **Format:** Markdown with YAML frontmatter
- **Frequency:** Weekly (Sunday night)

### Dashboard Update
- **Path:** `AI-Employee-Vault/Dashboard.md`
- **Change:** Adds link under `## Weekly Briefings`

### Log
- **Path:** `AI-Employee-Vault/Logs/monday-ceo-briefing-YYYY-MM-DD.log`
- **Format:** JSON lines

## Testing

```bash
DRY_RUN=true python monday_ceo_briefing.py
python monday_ceo_briefing.py
cat AI-Employee-Vault/Briefings/*_Monday.md
```
