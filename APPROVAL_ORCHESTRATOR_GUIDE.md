# Approval Orchestrator Guide

**Version:** Silver Tier  
**Last Updated:** March 2026  
**Status:** Production Ready

## Overview

The Approval Orchestrator is an automated system that monitors the `/Approved` folder, processes approval requests, executes actions via MCP servers, and manages file lifecycle. It handles email drafting, LinkedIn post publishing, and WhatsApp replies with built-in safety features.

## Features

### Core Capabilities

- **Automated Processing**: Monitors `/Approved` folder and processes files automatically
- **Multi-Action Support**: Handles `send_email`, `publish_post`, `reply_whatsapp` actions
- **Safety First**: Rejects expired approvals, validates all fields, requires proper approval
- **Retry Logic**: Exponential backoff retry wrapper for transient failures
- **Failure Quarantine**: Moves problematic files to `/Quarantine` for investigation
- **Audit Logging**: Comprehensive audit trail with file locking
- **Concurrent Processing**: Parallel execution with configurable workers
- **Webhook Notifications**: Real-time notifications on completion

### Safety Features

| Feature | Description | Default |
|---------|-------------|---------|
| Approval Expiry | Rejects approvals older than threshold | 24 hours |
| Retry Attempts | Retries failed operations with backoff | 3 retries |
| Validation | Schema validation for all required fields | Always on |
| Dry Run Mode | Test without executing real actions | Configurable |
| Quarantine | Isolates failed files for review | Automatic |

## Installation

### Prerequisites

- Python 3.8+
- Required packages in `requirements.txt`
- MCP Server running (for production use)
- Vault directory structure

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Create vault structure (auto-created on first run)
# AI-Employee-Vault/
# ├── Approved/
# ├── Done/
# ├── Quarantine/
# ├── Rejected/
# ├── Logs/
# └── Audit/
```

## Configuration

### Environment Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `VAULT_PATH` | Path to vault directory | `./AI-Employee-Vault` | `/opt/vault` |
| `APPROVAL_EXPIRY_HOURS` | Max age of approval | `24` | `48` |
| `MAX_RETRIES` | Max retry attempts | `3` | `5` |
| `RETRY_DELAY_SECONDS` | Base retry delay | `5` | `10` |
| `DRY_RUN` | Test mode (no real actions) | `false` | `true` |
| `LOG_LEVEL` | Logging verbosity | `INFO` | `DEBUG` |
| `MCP_SERVER_URL` | MCP server endpoint | `http://localhost:8080` | `https://mcp.example.com` |
| `MCP_TIMEOUT_SECONDS` | MCP request timeout | `30` | `60` |
| `MAX_CONCURRENT_EXECUTIONS` | Parallel workers | `3` | `5` |
| `WEBHOOK_URL` | Notification endpoint | (empty) | `https://hooks.slack.com/...` |

### Example `.env` File

```bash
# Approval Orchestrator Configuration
VAULT_PATH=/opt/ai-employee/AI-Employee-Vault
APPROVAL_EXPIRY_HOURS=24
MAX_RETRIES=3
RETRY_DELAY_SECONDS=5
DRY_RUN=false
LOG_LEVEL=INFO
MCP_SERVER_URL=http://localhost:8080
MCP_TIMEOUT_SECONDS=30
MAX_CONCURRENT_EXECUTIONS=3
WEBHOOK_URL=https://hooks.slack.com/services/XXX/YYY/ZZZ
```

## Usage

### Basic Commands

```bash
# Run one processing cycle
python approval_orchestrator.py

# Run in continuous watch mode (polls every 30s)
python approval_orchestrator.py --watch

# Custom watch interval (60 seconds)
python approval_orchestrator.py --watch --interval 60

# Dry run (test without executing)
DRY_RUN=true python approval_orchestrator.py

# Override dry run via CLI
python approval_orchestrator.py --dry-run

# Custom concurrent workers
python approval_orchestrator.py --max-workers 5

# Combine options
python approval_orchestrator.py --watch --interval 60 --max-workers 5
```

### CLI Options

```
usage: approval_orchestrator.py [-h] [--watch] [--interval INTERVAL]
                                [--dry-run] [--max-workers MAX_WORKERS]

Approval Orchestrator — Silver Tier

options:
  -h, --help            Show help message and exit
  --watch               Run in continuous watch mode
  --interval INTERVAL   Watch mode interval in seconds (default: 30)
  --dry-run             Override DRY_RUN env var to enable test mode
  --max-workers MAX_WORKERS
                        Maximum concurrent workers (default: from env or 3)
```

## File Formats

### Approval File Structure

Approval files must be Markdown with YAML frontmatter:

```markdown
---
approval_id: appr-20260301-001
plan_file: Plans/plan-20260301-001.md
source_file: Done/email-20260301-001.md
risk_level: low
requested_at: 2026-03-01T10:00:00Z
status: approved
action_type: send_email
---

# Approval Request

**Reason:** Customer inquiry response

**Requested by:** AI Employee System  
**Approved by:** Human Reviewer  
**Approved at:** 2026-03-01T11:00:00Z

---

## Notes

This approval is for responding to a customer inquiry about pricing.
```

### Required Approval Fields

| Field | Type | Description | Valid Values |
|-------|------|-------------|--------------|
| `approval_id` | string | Unique identifier | Any unique string |
| `plan_file` | string | Path to plan file | `Plans/*.md` |
| `source_file` | string | Path to source file | `Done/*.md` |
| `risk_level` | string | Risk assessment | `low`, `medium`, `high` |
| `requested_at` | ISO8601 | Request timestamp | `2026-03-01T10:00:00Z` |
| `status` | string | Approval status | `approved` |
| `action_type` | string | Action to execute | `send_email`, `publish_post`, `reply_whatsapp` |

### Plan File Structure

```markdown
---
plan_id: plan-20260301-001
item_type: email
risk_level: low
requires_approval: true
source_file: Done/email-20260301-001.md
---

# Action Plan

## Objective

Respond to customer inquiry about pricing.

## Steps

1. Acknowledge receipt of inquiry
2. Provide pricing information
3. Offer follow-up call
```

### Required Plan Fields

| Field | Type | Description | Valid Values |
|-------|------|-------------|--------------|
| `plan_id` | string | Unique identifier | Any unique string |
| `item_type` | string | Content type | `email`, `file_drop`, `whatsapp`, `linkedin_post` |
| `risk_level` | string | Risk assessment | `low`, `medium`, `high` |
| `requires_approval` | boolean | Approval required | `true`, `false` |

## Action Types

### 1. send_email

Drafts and sends email responses.

**MCP Tool:** `draft_email`  
**Parameters:**
- `to`: Recipient email
- `subject`: Email subject
- `body`: Email content

**Example Flow:**
1. Approval file in `/Approved` with `action_type: send_email`
2. Orchestrator loads source email from `/Done`
3. Extracts recipient and subject
4. Calls MCP `draft_email` tool
5. Moves approval to `/Done` on success

### 2. publish_post

Publishes LinkedIn posts.

**MCP Tool:** `publish_linkedin_post`  
**Parameters:**
- `content`: Post content
- `platform`: `linkedin`
- `scheduled_at`: Optional schedule time

**Example Flow:**
1. Approval file with `action_type: publish_post`
2. Loads post content from plan or source
3. Calls MCP `publish_linkedin_post` tool
4. Logs publication result
5. Moves to `/Done`

### 3. reply_whatsapp

Sends WhatsApp messages.

**MCP Tool:** `send_whatsapp_message`  
**Parameters:**
- `recipient`: Phone number or contact
- `message`: Message content

**Example Flow:**
1. Approval file with `action_type: reply_whatsapp`
2. Loads message content and recipient
3. Calls MCP `send_whatsapp_message` tool
4. Logs delivery status
5. Moves to `/Done`

## File Lifecycle

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Pending_   │────▶│  Approved   │────▶│    Done     │
│   Approval  │     │             │     │             │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
                    ┌──────┴──────┐
                    ▼             ▼
            ┌─────────────┐ ┌─────────────┐
            │  Rejected   │ │ Quarantine  │
            │             │ │             │
            └─────────────┘ └─────────────┘
```

### States

| State | Directory | Description |
|-------|-----------|-------------|
| Pending | `/Pending_Approval` | Awaiting human review |
| Approved | `/Approved` | Ready for processing |
| Done | `/Done` | Successfully processed |
| Rejected | `/Rejected` | Failed validation or expired |
| Quarantine | `/Quarantine` | Failed execution (retry exhausted) |

## Error Handling

### Validation Errors

Files are **rejected** for:
- Missing required fields
- Invalid field types
- Invalid risk levels (`low`, `medium`, `high` only)
- Invalid action types (`send_email`, `publish_post`, `reply_whatsapp` only)
- Expired approvals (older than `APPROVAL_EXPIRY_HOURS`)
- Missing plan file

### Execution Errors

Files are **quarantined** for:
- MCP server connection failures (after all retries)
- Unexpected exceptions during execution
- File system errors

### Retry Behavior

```
Attempt 1: Execute immediately
Attempt 2: Wait 5s (base_delay * 2^0)
Attempt 3: Wait 10s (base_delay * 2^1)
Attempt 4: Wait 20s (base_delay * 2^2)
→ Quarantine if all fail
```

## Audit Logging

### Audit Log Location

```
AI-Employee-Vault/
└── Audit/
    ├── audit-2026-03-01.json
    ├── audit-2026-03-02.json
    └── ...
```

### Audit Entry Format

```json
{
  "timestamp": "2026-03-01T10:00:00Z",
  "approval_id": "appr-001",
  "file": "appr-001.md",
  "stage": "executed",
  "orchestrator": "approval_orchestrator",
  "metadata": {
    "action_type": "send_email",
    "risk_level": "low",
    "plan_file": "Plans/plan-001.md"
  },
  "result": {
    "status": "success",
    "action_type": "email_draft",
    "tool": "draft_email"
  }
}
```

### Operation Logs

```
AI-Employee-Vault/
└── Logs/
    ├── orchestrator-2026-03-01.log
    └── ...
```

**Log Entry Format (JSON Lines):**
```json
{"timestamp": "2026-03-01T10:00:00Z", "approval_id": "appr-001", "action": "execute", "status": "completed", "dry_run": false}
```

## Webhook Notifications

### Configuration

Set `WEBHOOK_URL` environment variable:

```bash
WEBHOOK_URL=https://hooks.slack.com/services/XXX/YYY/ZZZ
```

### Event Types

| Event | Trigger |
|-------|---------|
| `cycle_completed` | Processing cycle finished |

### Payload Format

```json
{
  "event_type": "cycle_completed",
  "timestamp": "2026-03-01T10:00:00Z",
  "orchestrator": "approval_orchestrator",
  "vault": "/opt/vault",
  "total_files": 5,
  "succeeded": 4,
  "failed": 0,
  "quarantined": 1
}
```

## Testing

### Run Tests

```bash
# Run all tests
pytest tests/test_approval_orchestrator.py -v

# Run specific test class
pytest tests/test_approval_orchestrator.py::TestValidation -v

# Run with coverage
pytest tests/test_approval_orchestrator.py --cov=approval_orchestrator
```

### Test Categories

| Test Class | Coverage |
|------------|----------|
| `TestFrontmatterParsing` | YAML parsing, file loading |
| `TestValidation` | Field validation, expiry checks |
| `TestRetryWrapper` | Retry logic, backoff |
| `TestFileOperations` | Move to done/quarantine/rejected |
| `TestAuditLogging` | Audit trail, operation logs |
| `TestMCPIntegration` | MCP tool calls, HTTP errors |
| `TestActionExecution` | Action routing |
| `TestIntegration` | End-to-end flows |

### Dry Run Testing

```bash
# Test without real MCP calls
DRY_RUN=true python approval_orchestrator.py

# Verify files would be processed
python approval_orchestrator.py --dry-run --watch
```

## Monitoring

### Health Checks

```bash
# Check vault directories exist
ls -la AI-Employee-Vault/{Approved,Done,Quarantine,Rejected,Logs,Audit}

# Check recent audit logs
tail -f AI-Employee-Vault/Audit/audit-*.json

# Check operation logs
tail -f AI-Employee-Vault/Logs/orchestrator-*.log
```

### Key Metrics

| Metric | Location | Description |
|--------|----------|-------------|
| Files processed | Logs | Count per cycle |
| Success rate | Logs | Successful / Total |
| Quarantine count | Directory | Failed files |
| Average processing time | Logs | Time per file |
| Retry rate | Logs | Files requiring retries |

### Alerting

Set up alerts for:
- Quarantine directory has files (investigate failures)
- No processing cycles in last hour (orchestrator stopped)
- High failure rate (>10% of files)
- MCP server connection errors

## Troubleshooting

### Common Issues

**Issue: Files stuck in Approved/**
- Check orchestrator is running: `ps aux | grep approval_orchestrator`
- Check logs for errors: `tail AI-Employee-Vault/Logs/orchestrator-*.log`
- Verify MCP server is accessible

**Issue: All files going to Quarantine**
- Check MCP server URL: `echo $MCP_SERVER_URL`
- Test MCP connectivity: `curl $MCP_SERVER_URL/health`
- Check retry logs for error details

**Issue: Approval expired errors**
- Check `requested_at` timestamp in approval file
- Increase `APPROVAL_EXPIRY_HOURS` if needed
- Ensure system clocks are synchronized

**Issue: Validation failures**
- Verify all required fields present
- Check field types match schema
- Validate risk_level and action_type values

### Debug Mode

```bash
# Enable debug logging
LOG_LEVEL=DEBUG python approval_orchestrator.py

# Check detailed audit trail
cat AI-Employee-Vault/Audit/audit-*.json | jq .
```

## Production Deployment

### Systemd Service

```ini
# /etc/systemd/system/approval-orchestrator.service
[Unit]
Description=Approval Orchestrator
After=network.target mcp-server.service

[Service]
Type=simple
User=ai-employee
WorkingDirectory=/opt/ai-employee
Environment=VAULT_PATH=/opt/ai-employee/AI-Employee-Vault
Environment=MCP_SERVER_URL=http://localhost:8080
Environment=WEBHOOK_URL=https://hooks.example.com/webhook
ExecStart=/usr/bin/python3 /opt/ai-employee/approval_orchestrator.py --watch --interval 30
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl enable approval-orchestrator
sudo systemctl start approval-orchestrator
sudo systemctl status approval-orchestrator
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY approval_orchestrator.py .

ENV VAULT_PATH=/vault
ENV MCP_SERVER_URL=http://mcp-server:8080

CMD ["python", "approval_orchestrator.py", "--watch"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  approval-orchestrator:
    build: .
    volumes:
      - vault_data:/vault
    environment:
      - MCP_SERVER_URL=http://mcp-server:8080
      - WEBHOOK_URL=https://hooks.example.com/webhook
    depends_on:
      - mcp-server

  mcp-server:
    image: mcp-server:latest
    ports:
      - "8080:8080"

volumes:
  vault_data:
```

## Security Considerations

### Access Control

- Restrict vault directory permissions: `chmod 700 AI-Employee-Vault`
- Run orchestrator as dedicated user: `useradd -r ai-employee`
- Use secrets management for webhook URLs

### Audit Trail

- Audit logs are append-only (file locking)
- Never delete audit logs (compliance requirement)
- Archive logs periodically

### MCP Server Security

- Use HTTPS for MCP server communication
- Implement authentication tokens
- Set appropriate timeouts

## API Reference

### Internal Functions

#### `parse_frontmatter(content: str) -> tuple[dict, str]`
Parse YAML frontmatter from markdown content.

#### `validate_approval(metadata: dict, path: Path) -> list[str]`
Validate approval metadata. Returns list of errors (empty if valid).

#### `process_approval_file(approval_path: Path) -> bool`
Process single approval file. Returns True if successful.

#### `run_orchestrator_cycle() -> int`
Run one processing cycle. Returns count of successful processes.

#### `write_audit_log(audit_entry: dict, logs_dir: Path) -> Path`
Write audit log entry with file locking.

## Changelog

### v1.0.0 (March 2026)
- Initial release
- Core approval processing
- Retry wrapper with exponential backoff
- Quarantine and rejection handling
- Audit logging
- Concurrent processing
- Webhook notifications
- MCP server integration

## Support

For issues or questions:
1. Check logs in `AI-Employee-Vault/Logs/`
2. Review audit trail in `AI-Employee-Vault/Audit/`
3. Consult `CLAUDE.md` or `AGENTS.md` for project context
4. Run tests to verify installation

---

**Document Version:** 1.0  
**Maintained By:** AI Employee Team  
**Review Cycle:** Quarterly
