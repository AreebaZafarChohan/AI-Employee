# Audit Logs

This folder contains immutable audit logs for all system actions.

## Folder Structure

```
Audit/
├── 2026/
│   ├── 03/
│   │   ├── audit-2026-03-06.json
│   │   ├── audit-2026-03-07.json
│   │   └── ...
│   └── ...
```

## Audit Entry Schema

Every action in the Gold Tier system is logged with:

```json
{
  "audit_id": "uuid-v4",
  "timestamp": "2026-03-06T10:30:00Z",
  "event_type": "email_sent|post_published|invoice_created",
  "source": "gmail_watcher|whatsapp_watcher|social_watcher",
  "actor": "ralph_wiggum_loop|approval_orchestrator",
  "domain": "personal|business|accounting|social",
  "risk_level": "low|medium|high",
  "approval_required": true,
  "approval_id": "uuid-v4",
  "approved_by": "human-user-id",
  "action_details": {
    "tool": "send_email",
    "parameters": {...},
    "result": {...}
  },
  "execution_time_ms": 1234,
  "retry_count": 0,
  "error": null,
  "vault_path": "/Done/example.md",
  "correlation_id": "uuid-v4"
}
```

## Audit Log Properties

- **Immutable**: Append-only, never modified after creation
- **Daily Rotation**: New file created each day
- **Searchable**: Query via CLI tool
- **Exportable**: Export to CSV for external analysis

## Query Commands

```bash
# Query by date
python src/cli/audit_query.py --date 2026-03-06

# Query by event type
python src/cli/audit_query.py --event-type email_sent

# Query by approval ID
python src/cli/audit_query.py --approval-id uuid-v4

# Export to CSV
python src/cli/audit_query.py --export-csv --output audit-export.csv

# Query date range
python src/cli/audit_query.py --from 2026-03-01 --to 2026-03-31
```

## Retention Policy

| Log Type | Retention |
|----------|-----------|
| Daily audit logs | 365 days |
| Monthly summaries | 7 years |
| Annual reports | Permanent |

## Related Files

- `src/core/audit_logger.py` - Audit logging implementation
- `src/cli/audit_query.py` - Query CLI tool
- `.claude/skills/gold/audit_logging/` - Audit skills
