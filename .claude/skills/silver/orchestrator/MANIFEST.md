# Orchestrator — Manifest

**Created:** 2026-02-25
**Domain:** silver
**Status:** Production Ready
**Version:** 1.0.0

## Overview

The `orchestrator` skill is the execution engine for the Silver Tier AI Employee. It monitors `/Approved`, validates approval files, executes actions via MCP tools, and archives completed items to `/Done`.

## Integration Points

### Upstream
- **silver_process_engine** — Creates plans and approval requests
- **gmail_watcher** — Provides incoming email items
- **linkedin_post_generator** — Creates social media drafts

### Downstream
- **MCP Email Server** — Executes email send/draft operations
- **File System MCP** (future) — Executes file operations
- **WhatsApp MCP** (future) — Executes WhatsApp messaging

### Data Flow
```
Needs_Action → silver_process_engine → Plans + Pending_Approval
                                           ↓
                                    Human approves
                                           ↓
                                    /Approved
                                           ↓
                                    orchestrator
                                           ↓
                                    MCP tools → Done
```

## Configuration

Add to `.env`:
```bash
# Orchestrator settings
APPROVAL_EXPIRY_HOURS=24
ORCHESTRATOR_INTERVAL=30
ORCHESTRATOR_DRY_RUN=false
```

## Files

| File | Purpose |
|------|---------|
| `orchestrator.py` | Main execution engine |
| `SKILL.md` | Full specification |
| `README.md` | Quick start guide |
| `assets/run.sh` | Shell wrapper |

## Testing

```bash
# Dry run test
DRY_RUN=true python orchestrator.py

# Watch mode test
python orchestrator.py --watch --interval 5

# Single cycle
python orchestrator.py
```

## Monitoring

Check logs:
```bash
tail -f AI-Employee-Vault/Logs/orchestrator-*.log
```

Key metrics:
- `success_count` — Executions succeeded
- `fail_count` — Executions failed
- `reject_count` — Approvals rejected (validation)

## Alerts

Configure alerts for:
- `fail_count > 5` in 10 minutes — Investigate execution errors
- `reject_count > 10` in 1 hour — Check approval workflow
- No executions in 24 hours — Verify orchestrator is running
