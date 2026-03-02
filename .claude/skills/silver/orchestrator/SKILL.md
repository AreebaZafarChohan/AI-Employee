# Orchestrator Skill

## Overview

**Skill Name:** `orchestrator`
**Domain:** `silver`
**Purpose:** Monitor `/Approved` folder, execute approved plans via MCP tools, log results, and archive to `/Done`.

**Core Capabilities:**
- Approval file parsing and validation
- Plan file validation
- Action routing by item type (email, file_drop, whatsapp)
- MCP tool integration (send_email, draft_email, etc.)
- Comprehensive logging and audit trail
- Safety: expiry checks, field validation, failure handling

## Schemas

### Approval File Schema

```yaml
approval_id: string (required, unique)
plan_file: string (required, path to plan)
source_file: string (required, original item)
risk_level: enum[low, medium, high] (required)
requested_at: ISO8601 timestamp (required)
status: enum[pending, approved, rejected] (required)
```

### Plan File Schema

```yaml
plan_id: string (required, unique)
item_type: enum[email, file_drop, whatsapp] (required)
risk_level: enum[low, medium, high] (required)
requires_approval: boolean (required)
status: string (required)
created_at: ISO8601 timestamp (required)
```

## Validation Rules

### Required Fields
- All fields in schemas above must be present
- Type checking enforced (string, boolean, enum)

### Expiry Check
- Approvals expire after 24 hours (configurable via `APPROVAL_EXPIRY_HOURS`)
- Expired approvals are rejected and moved to `/Rejected`

### Risk Level Validation
- Must be one of: `low`, `medium`, `high`
- High risk items always require approval

### Item Type Validation
- Must be one of: `email`, `file_drop`, `whatsapp`
- Determines which action executor is used

## Action Executors

### Email Actions
- **Trigger:** `item_type: email`
- **MCP Tools:** `send_email`, `draft_email`, `search_inbox`
- **Flow:**
  1. Parse email content from source file
  2. Determine action (reply, forward, archive)
  3. Call appropriate MCP tool
  4. Log result

### File Drop Actions
- **Trigger:** `item_type: file_drop`
- **Flow:**
  1. Process file from source location
  2. Execute file operations
  3. Log result

### WhatsApp Actions
- **Trigger:** `item_type: whatsapp`
- **Flow:**
  1. Parse WhatsApp message
  2. Determine response
  3. Send via WhatsApp API (future)
  4. Log result

## Flow Diagram

```
┌─────────────┐
│ /Approved   │
│ *.md files  │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────┐
│ 1. Parse Approval Frontmatter│
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ 2. Validate Approval         │
│   - Required fields          │
│   - Expiry check             │
│   - Risk level valid         │
└──────┬──────────────────────┘
       │
       ├───────► Reject (move to /Rejected)
       │
       ▼
┌─────────────────────────────┐
│ 3. Load & Validate Plan      │
│   - Plan exists              │
│   - Required fields          │
│   - Item type valid          │
└──────┬──────────────────────┘
       │
       ├───────► Reject (move to /Rejected)
       │
       ▼
┌─────────────────────────────┐
│ 4. Execute Action            │
│   - Route by item_type       │
│   - Call MCP tool            │
│   - Log result               │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ 5. Move to /Done             │
│   - Add execution metadata   │
│   - Archive approval file    │
└─────────────────────────────┘
```

## Logging

All actions are logged to `/Logs/orchestrator-YYYY-MM-DD.log`:

```json
{
  "timestamp": "2026-02-25T12:00:00Z",
  "approval_id": "5f700bcd",
  "action": "execute",
  "status": "success",
  "dry_run": false,
  "action_type": "email_process",
  "plan_id": "69ee8d56"
}
```

## Error Handling

### Validation Failures
- Log error with details
- Move file to `/Rejected`
- Add rejection reason to metadata

### Execution Failures
- Log error with stack trace
- Keep file in `/Approved` for retry
- Alert on repeated failures

### Missing Files
- Log "File not found" error
- Move to `/Rejected` with reason

## Configuration

| Env Var | Default | Description |
|---------|---------|-------------|
| `VAULT_PATH` | `./AI-Employee-Vault` | Path to vault directory |
| `APPROVAL_EXPIRY_HOURS` | `24` | Hours before approval expires |
| `DRY_RUN` | `false` | If true, skip real execution |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `ORCHESTRATOR_INTERVAL` | `30` | Watch mode interval (seconds) |

## Usage

```bash
# Run one cycle
python orchestrator.py

# Watch mode (continuous)
python orchestrator.py --watch --interval 30

# Dry run (test without executing)
DRY_RUN=true python orchestrator.py

# Custom expiry
APPROVAL_EXPIRY_HOURS=48 python orchestrator.py
```

## MCP Integration

### Email MCP Server
The orchestrator integrates with the Email MCP server for email actions:

```python
# Example: Send email via MCP
from mcp_email_client import send_email

result = send_email(
    to="recipient@example.com",
    subject="Re: Original Subject",
    body="Email body",
    thread_id="abc123"
)
```

### Future MCP Integrations
- File system MCP (for file_drop actions)
- WhatsApp MCP (for whatsapp actions)
- Calendar MCP (for meeting scheduling)

## Safety Guarantees

1. **Never executes without approval** - Only processes files in `/Approved`
2. **Expiry enforcement** - Rejects stale approvals
3. **Field validation** - Rejects incomplete metadata
4. **Audit trail** - Logs every action
5. **Dry run support** - Test without real execution
6. **Idempotent** - Safe to retry failed executions
