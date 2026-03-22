# CEO Briefings

This folder contains Monday morning CEO briefings generated automatically by the Gold Tier system.

## File Naming Convention

```
YYYY-MM-DD_DayName.md

Examples:
- 2026-03-10_Monday.md
- 2026-03-17_Monday.md
```

## Briefing Structure

Each CEO briefing contains:

```markdown
# CEO Briefing - {date}

## Executive Summary
{2-paragraph overview of last week and priorities for this week}

## Last Week's Achievements
- {achievement 1}
- {achievement 2}
- {achievement 3}

## This Week's Priorities
1. **Priority 1**: {description}
2. **Priority 2**: {description}
3. **Priority 3**: {description}

## Financial Snapshot
| Metric | Value |
|--------|-------|
| Revenue (MTD) | $X |
| Expenses (MTD) | $Y |
| Cash Flow | $Z |

## Pending Decisions Requiring CEO Attention
- {decision 1}
- {decision 2}

## System Status
✅ All systems operational

## Calendar Highlights
- {meeting 1}
- {meeting 2}
```

## Generation Schedule

**When:** Every Monday at 06:00 UTC  
**Script:** `monday_ceo_briefing.py`

## Data Sources

The briefing generator pulls data from:

1. **Done/** - Completed tasks from last week
2. **Accounting/** - Financial data from Odoo
3. **Social/Published/** - Social media performance
4. **Logs/** - System activity logs
5. **Plans/** - Upcoming deadlines

## Related Skills

- `briefing_generator` - Main briefing generation
- `priority_extractor` - Extracts weekly priorities
- `decision_tracker` - Tracks pending decisions

## Configuration

```bash
# In .env file
BRIEFING_DAY=Monday
BRIEFING_TIME=06:00
BRIEFING_TIMEZONE=UTC
```
