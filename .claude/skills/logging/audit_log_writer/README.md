# Audit Log Writer

Write structured JSON logs for every action taken (actor, type, result). Appends to date-based log files in `/Logs/YYYY-MM-DD.json` for audit trail and compliance.

## Overview

The Audit Log Writer provides tamper-resistant, structured logging for all agent actions in the Digital FTE workflow. It creates immutable audit trails that track who did what, when, and with what result, enabling compliance, debugging, and security analysis.

## Key Features

- **Structured JSON Logs**: Machine-parseable format for analysis
- **Date-Based Organization**: One file per day (Logs/2025-01-15.json)
- **Append-Only**: Tamper-resistant logging
- **Integrity Verification**: SHA256 checksums detect tampering
- **Automatic Rotation**: Compress and archive old logs
- **PII Redaction**: Auto-redact sensitive data
- **Query Support**: Search logs by actor, action, date, status

## Quick Start

### 1. Configure

```bash
# Copy configuration template
cp .claude/skills/logging/audit_log_writer/assets/.env.example .env

# Edit configuration
VAULT_PATH="/path/to/vault"
LOGS_DIR="${VAULT_PATH}/Logs"
LOG_ROTATION_DAYS="90"
LOG_RETENTION_DAYS="365"
ENABLE_LOG_INTEGRITY_CHECK="true"
```

### 2. Create Logs Directory

```bash
mkdir -p "${VAULT_PATH}/Logs"
mkdir -p "${VAULT_PATH}/Logs/archive"
mkdir -p "${VAULT_PATH}/Logs/.checksums"
```

### 3. Log an Action

```javascript
const { logAction } = require('./audit_log_writer');

// Log task claim
await logAction(
  { type: 'agent', name: 'lex' },                    // Actor
  { type: 'claim', verb: 'PUT', category: 'task_management' },  // Action
  { type: 'task', id: 'task-123', path: 'In_Progress/task-123.json' },  // Resource
  { status: 'success', duration_ms: 45 },            // Result
  { from_folder: 'Needs_Action', to_folder: 'In_Progress' }  // Details
);
```

### 4. View Logs

```bash
# View today's logs
cat "${VAULT_PATH}/Logs/$(date -u +%Y-%m-%d).json" | jq

# View specific entries
cat "${VAULT_PATH}/Logs/2025-01-15.json" | jq 'select(.actor.name == "lex")'

# Count actions by actor
cat "${VAULT_PATH}/Logs/2025-01-15.json" | jq -r '.actor.name' | sort | uniq -c
```

## Log Entry Structure

Every log entry follows this structure:

```json
{
  "timestamp": "2025-01-15T10:00:00.000Z",
  "trace_id": "a1b2c3d4-e5f6-7890-abcd",
  "actor": {
    "type": "agent",
    "name": "lex",
    "id": null
  },
  "action": {
    "type": "claim",
    "verb": "PUT",
    "category": "task_management"
  },
  "resource": {
    "type": "task",
    "id": "task-123",
    "path": "In_Progress/task-123.json"
  },
  "result": {
    "status": "success",
    "code": null,
    "message": null,
    "duration_ms": 45
  },
  "details": {
    "from_folder": "Needs_Action",
    "to_folder": "In_Progress"
  },
  "metadata": {
    "hostname": "agent-server-01",
    "process_id": 12345,
    "version": "1.0.0"
  }
}
```

## Common Action Types

### Task Management

```javascript
// Claim task
await logAction(
  { type: 'agent', name: 'lex' },
  { type: 'claim', verb: 'PUT', category: 'task_management' },
  { type: 'task', id: 'task-123' },
  { status: 'success', duration_ms: 45 }
);

// Release task
await logAction(
  { type: 'agent', name: 'lex' },
  { type: 'release', verb: 'DELETE', category: 'task_management' },
  { type: 'task', id: 'task-123' },
  { status: 'success', duration_ms: 30 },
  { reason: 'completed' }
);
```

### Approvals

```javascript
// Approve task
await logAction(
  { type: 'human', name: 'alice', id: 'alice@example.com' },
  { type: 'approve', verb: 'POST', category: 'workflow' },
  { type: 'task', id: 'task-456' },
  { status: 'success', duration_ms: 120 },
  { decision: 'approved', reason: 'Looks good' }
);
```

### Delegation

```javascript
// Delegate task
await logAction(
  { type: 'agent', name: 'lex' },
  { type: 'delegate', verb: 'POST', category: 'coordination' },
  { type: 'task', id: 'task-789' },
  { status: 'success', duration_ms: 78 },
  { to_agent: 'cex', delegation_type: 'plan_task' }
);
```

### Security Events

```javascript
// Permission violation
await logAction(
  { type: 'agent', name: 'cex' },
  { type: 'claim', verb: 'PUT', category: 'security' },
  { type: 'task', id: 'task-101' },
  { status: 'failure', code: 'PERMISSION_DENIED', message: 'Agent cannot claim tasks' },
  { required_permission: 'claim_task', actual_permissions: ['read_task'] }
);
```

## Operations

### Query Logs

```javascript
const { queryLogs } = require('./audit_log_writer');

// Get all actions by actor
const logs = await queryLogs({
  startDate: '2025-01-01',
  endDate: '2025-01-15',
  actor: 'lex'
});

// Get failed operations
const failures = await queryLogs({
  startDate: '2025-01-15',
  endDate: '2025-01-15',
  status: 'failure'
});

// Get specific action type
const claims = await queryLogs({
  startDate: '2025-01-15',
  endDate: '2025-01-15',
  action: 'claim'
});
```

### Verify Integrity

```javascript
const { verifyLogIntegrity } = require('./audit_log_writer');

// Check all log files for tampering
const report = await verifyLogIntegrity();

console.log(`Verified: ${report.verified.length} files`);
console.log(`Tampered: ${report.tampered.length} files`);

if (report.tampered.length > 0) {
  console.error('TAMPERING DETECTED:');
  for (const t of report.tampered) {
    console.error(`  ${t.file}: expected ${t.stored}, got ${t.computed}`);
  }
}
```

### Rotate Logs

```javascript
const { rotateLogs } = require('./audit_log_writer');

// Manually rotate logs (compress old, delete expired)
await rotateLogs();

// Or schedule daily rotation
const schedule = require('node-schedule');
schedule.scheduleJob('0 0 * * *', rotateLogs); // Midnight UTC
```

## File Organization

```
Logs/
├── 2025-01-15.json              # Today's logs (active)
├── 2025-01-14.json              # Yesterday (uncompressed)
├── 2025-01-13.json
├── .checksums/
│   ├── 2025-01-15.json.sha256   # Integrity checksums
│   ├── 2025-01-14.json.sha256
│   └── 2025-01-13.json.sha256
└── archive/
    ├── 2024-12.json.gz          # Archived December logs (compressed)
    ├── 2024-12.json.sha256
    ├── 2024-11.json.gz
    └── 2024-11.json.sha256
```

## Log Rotation Schedule

```
Day 0-90:    Uncompressed logs in Logs/
Day 91-365:  Compressed logs in Logs/archive/
Day 366+:    Deleted (configurable retention)
```

## Command-Line Tools

### View Today's Logs

```bash
#!/bin/bash
LOG_DATE=$(date -u +%Y-%m-%d)
cat "${VAULT_PATH}/Logs/${LOG_DATE}.json" | jq -r '. | "\(.timestamp) [\(.actor.name)] \(.action.type) \(.resource.id) → \(.result.status)"'
```

### Search by Actor

```bash
#!/bin/bash
ACTOR="$1"
START="$2"
END="$3"

find "${VAULT_PATH}/Logs" -name "*.json" -newermt "$START" ! -newermt "$END" \
  -exec grep -h "\"name\":\"$ACTOR\"" {} \; \
  | jq -r '. | "\(.timestamp) \(.action.type) \(.resource.id) → \(.result.status)"'
```

### Verify Integrity

```bash
#!/bin/bash
for log in ${VAULT_PATH}/Logs/*.json; do
  checksum_file="${log}.sha256"
  if [ -f "$checksum_file" ]; then
    computed=$(sha256sum "$log" | awk '{print $1}')
    stored=$(cat "$checksum_file")
    [ "$computed" = "$stored" ] && echo "✓ $(basename $log)" || echo "✗ $(basename $log) TAMPERED"
  fi
done
```

### Count Actions by Type

```bash
#!/bin/bash
cat "${VAULT_PATH}/Logs/2025-01-15.json" | jq -r '.action.type' | sort | uniq -c | sort -rn
```

## Security Features

### PII Redaction

Automatically redacts:
- Email addresses: `user@example.com` → `[EMAIL_REDACTED]`
- Phone numbers: `555-123-4567` → `[PHONE_REDACTED]`
- SSN: `123-45-6789` → `[SSN_REDACTED]`
- Credit cards: `1234-5678-9012-3456` → `[CC_REDACTED]`

### Secret Redaction

Automatically redacts patterns:
- `API_KEY`, `TOKEN`, `PASSWORD`, `SECRET`, `CREDENTIAL`

### Integrity Verification

- SHA256 checksums for each log file
- Detect tampering or corruption
- Weekly automated verification

## Monitoring

### Metrics

- **Log write latency**: < 10ms (target)
- **Log write failure rate**: < 0.01% (target)
- **Log integrity pass rate**: 100% (target)
- **Disk usage**: Monitor, alert at 90%

### Alerts

```yaml
- name: high_log_write_failure_rate
  condition: failure_rate > 1%
  action: investigate_filesystem

- name: log_tampering_detected
  condition: integrity_check_failed
  action: page_security_team

- name: disk_usage_high
  condition: disk_usage > 90%
  action: rotate_logs_early
```

## Compliance

This skill supports compliance requirements for:

- **GDPR**: Right to be forgotten (delete logs containing user data)
- **SOC2**: Audit trail for access control and changes
- **HIPAA**: Audit log retention for healthcare data access
- **PCI-DSS**: Log all access to cardholder data

## Troubleshooting

### Logs not being written

```bash
# Check directory permissions
ls -la "${VAULT_PATH}/Logs"

# Check disk space
df -h "${VAULT_PATH}/Logs"

# Test write
echo "test" > "${VAULT_PATH}/Logs/test.txt" && rm "${VAULT_PATH}/Logs/test.txt"
```

### Disk full

```bash
# Run rotation early
node -e "require('./audit_log_writer').rotateLogs()"

# Delete old archives
find "${VAULT_PATH}/Logs/archive" -name "*.gz" -mtime +365 -delete
```

### Integrity check failed

```bash
# List tampered files
./verify-logs.sh | grep "TAMPERED"

# Restore from backup
cp /backup/Logs/2025-01-15.json "${VAULT_PATH}/Logs/"

# Recompute checksum
sha256sum "${VAULT_PATH}/Logs/2025-01-15.json" > "${VAULT_PATH}/Logs/.checksums/2025-01-15.json.sha256"
```

## Best Practices

1. **Log every action** (claims, releases, approvals, delegations)
2. **Use structured format** (don't log free-form text)
3. **Include context** (trace IDs, durations, details)
4. **Rotate regularly** (compress old logs to save space)
5. **Verify integrity** (weekly checksum validation)
6. **Monitor disk usage** (alert before disk fills)
7. **Backup logs** (off-site backup for disaster recovery)
8. **Test queries** (ensure you can find what you need)

## Related Skills

- [vault_state_manager](../vault/vault_state_manager/) - File operations to log
- [task_lifecycle_manager](../vault/task_lifecycle_manager/) - Lifecycle events to log
- [agent_claim_coordinator](../coordination/agent_claim_coordinator/) - Claim events to log
- [agent_delegation_manager](../coordination/agent_delegation_manager/) - Delegation events to log

## Related Documents

- [SKILL.md](./SKILL.md) - Complete skill specification
- [EXAMPLES.md](./EXAMPLES.md) - Usage examples and patterns

## License

This skill is part of the AI-Employee project. See LICENSE file for details.
