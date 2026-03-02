# Orchestrator

Monitors `/Approved`, executes approved plans, logs results, and archives to `/Done`.

## Quick Start

```bash
# Run one cycle
python orchestrator.py

# Watch mode (continuous monitoring)
python orchestrator.py --watch --interval 30

# Dry run (test without executing)
DRY_RUN=true python orchestrator.py
```

## What It Does

1. **Scans** `/Approved` for approval files
2. **Validates** approval metadata (fields, expiry, risk level)
3. **Loads** linked plan file
4. **Executes** action based on item_type:
   - `email` → Calls MCP email tools
   - `file_drop` → Processes file operations
   - `whatsapp` → Sends WhatsApp messages
5. **Logs** result to `/Logs/orchestrator-*.log`
6. **Archives** approval file to `/Done`

## Safety Features

| Feature | Description |
|---------|-------------|
| **Expiry Check** | Rejects approvals older than 24 hours |
| **Field Validation** | Ensures all required fields present |
| **Type Validation** | Validates risk_level, item_type enums |
| **Failure Logging** | Logs all errors with details |
| **Dry Run Mode** | Test without real execution |

## Example Approval File

```markdown
---
approval_id: 5f700bcd
plan_file: Plans/no-subject-69ee8d56-plan.md
source_file: email-no-subject-576f57dd.md
risk_level: high
requested_at: "2026-02-24T19:32:25Z"
status: approved
---

# Approval Request

Human has reviewed and approved this action.
```

## Configuration

| Env Var | Default | Description |
|---------|---------|-------------|
| `APPROVAL_EXPIRY_HOURS` | `24` | Hours before approval expires |
| `ORCHESTRATOR_INTERVAL` | `30` | Watch mode interval (seconds) |
| `DRY_RUN` | `false` | Skip real execution |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

## Logs

Location: `AI-Employee-Vault/Logs/orchestrator-YYYY-MM-DD.log`

Example entry:
```json
{
  "timestamp": "2026-02-25T12:00:00Z",
  "approval_id": "5f700bcd",
  "action": "execute",
  "status": "success",
  "action_type": "email_process",
  "plan_id": "69ee8d56"
}
```

## Troubleshooting

### Approval rejected
Check validation errors in logs. Common issues:
- Missing required fields
- Expired approval (>24 hours)
- Invalid risk_level or item_type

### Execution failed
Check error details in logs. May need to:
- Retry (file stays in /Approved)
- Fix MCP server configuration
- Check network connectivity

### No files processed
Ensure:
- Files are in `/Approved` (not `/Pending_Approval`)
- Files have `.md` extension
- Frontmatter is valid YAML
