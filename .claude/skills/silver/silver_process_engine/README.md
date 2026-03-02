# Silver Process Engine

Scans `/Needs_Action`, classifies items, generates Plans, routes approvals, and archives to `/Done`.

## Quick Start

```bash
# Run once
PYTHONPATH=/tmp/gapi python3 .claude/skills/silver/silver_process_engine/assets/silver_process_engine.py

# Dry run (no file writes)
SILVER_PE_DRY_RUN=true python3 .claude/skills/silver/silver_process_engine/assets/silver_process_engine.py

# Debug logging
SILVER_PE_LOG_LEVEL=DEBUG python3 .claude/skills/silver/silver_process_engine/assets/silver_process_engine.py
```

## What It Does

1. Scans `/Needs_Action` for `.md` files
2. Classifies each item: `email` | `file_drop` | `whatsapp`
3. Assesses risk: `low` | `medium` | `high`
4. Writes plan to `/Plans/<slug>-plan.md`
5. If risk is medium/high → writes approval request to `/Pending_Approval/`
6. Logs action to `/Logs/`
7. Moves source item to `/Done/`

## Constraints

- Never executes real-world actions
- Never sends emails, makes API calls, or writes outside the vault
- Always requires human approval for medium/high risk items
