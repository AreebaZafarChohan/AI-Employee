# Logging Skills

Skills for structured logging, audit trails, and observability.

## Skills in this Category

### audit_log_writer

Write structured JSON logs for every action taken (actor, type, result). Appends to date-based log files in `/Logs/YYYY-MM-DD.json`.

**Key Features:**
- Structured JSON format (machine-parseable)
- Date-based organization (one file per day)
- Append-only (tamper-resistant)
- Integrity verification (SHA256 checksums)
- Automatic rotation and compression
- PII/secret redaction
- Query support

**When to Use:**
- Log agent actions (claims, releases, delegations)
- Track security events (permission violations)
- Record state transitions (task lifecycle)
- Compliance requirements (GDPR, SOC2, HIPAA)
- Debugging and troubleshooting
- Performance monitoring

**Example:**
```javascript
await logAction(
  { type: 'agent', name: 'lex' },
  { type: 'claim', verb: 'PUT', category: 'task_management' },
  { type: 'task', id: 'task-123' },
  { status: 'success', duration_ms: 45 }
);
```

[Full Documentation](./audit_log_writer/SKILL.md)

---

## Log Format

All logging skills use a consistent JSON format:

```json
{
  "timestamp": "2025-01-15T10:00:00.000Z",
  "trace_id": "a1b2c3d4-e5f6-7890",
  "actor": {
    "type": "agent|human|system",
    "name": "lex",
    "id": "optional-id"
  },
  "action": {
    "type": "claim|release|approve|delegate",
    "verb": "GET|POST|PUT|DELETE|EXECUTE",
    "category": "task_management|security|workflow"
  },
  "resource": {
    "type": "task|file|config|user",
    "id": "resource-id",
    "path": "optional-path"
  },
  "result": {
    "status": "success|failure|error",
    "code": "optional-error-code",
    "message": "optional-message",
    "duration_ms": 45
  },
  "details": {
    "key": "value"
  },
  "metadata": {
    "hostname": "server-01",
    "process_id": 12345,
    "version": "1.0.0"
  }
}
```

---

## Log Organization

```
vault/
└── Logs/
    ├── 2025-01-15.json              # Today's logs
    ├── 2025-01-14.json              # Yesterday
    ├── 2025-01-13.json
    ├── .checksums/
    │   ├── 2025-01-15.json.sha256   # Integrity checksums
    │   ├── 2025-01-14.json.sha256
    │   └── 2025-01-13.json.sha256
    └── archive/
        ├── 2024-12.json.gz          # Compressed archives
        ├── 2024-12.json.sha256
        ├── 2024-11.json.gz
        └── 2024-11.json.sha256
```

---

## Common Patterns

### 1. Log Task Claim

```javascript
const startTime = Date.now();

try {
  await claimTask(taskId, agentName);

  await logAction(
    { type: 'agent', name: agentName },
    { type: 'claim', verb: 'PUT', category: 'task_management' },
    { type: 'task', id: taskId },
    { status: 'success', duration_ms: Date.now() - startTime }
  );
} catch (err) {
  await logAction(
    { type: 'agent', name: agentName },
    { type: 'claim', verb: 'PUT', category: 'task_management' },
    { type: 'task', id: taskId },
    { status: 'failure', code: err.code, message: err.message, duration_ms: Date.now() - startTime }
  );
  throw err;
}
```

### 2. Log Human Approval

```javascript
await logAction(
  { type: 'human', name: 'alice', id: 'alice@example.com' },
  { type: 'approve', verb: 'POST', category: 'workflow' },
  { type: 'task', id: taskId },
  { status: 'success', duration_ms: 120 },
  { decision: 'approved', reason: 'Looks good' }
);
```

### 3. Log Security Event

```javascript
await logAction(
  { type: 'agent', name: 'cex' },
  { type: 'claim', verb: 'PUT', category: 'security' },
  { type: 'task', id: taskId },
  { status: 'failure', code: 'PERMISSION_DENIED', message: 'Agent cannot claim tasks' },
  { required_permission: 'claim_task', actual_permissions: ['read_task'] }
);
```

### 4. Log with Trace ID (Multi-Step)

```javascript
const parentTraceId = uuidv4();

// Step 1
const claimTraceId = await logAction(
  { type: 'agent', name: agentName },
  { type: 'claim', verb: 'PUT', category: 'task_management' },
  { type: 'task', id: taskId },
  { status: 'success', duration_ms: 45 },
  { parent_trace_id: parentTraceId }
);

// Step 2
await logAction(
  { type: 'agent', name: agentName },
  { type: 'process', verb: 'EXECUTE', category: 'task_execution' },
  { type: 'task', id: taskId },
  { status: 'success', duration_ms: 5000 },
  { parent_trace_id: parentTraceId, claim_trace_id: claimTraceId }
);
```

---

## Querying Logs

### Command-Line (jq)

```bash
# View today's logs
cat "${VAULT_PATH}/Logs/$(date -u +%Y-%m-%d).json" | jq

# Filter by actor
cat "${VAULT_PATH}/Logs/2025-01-15.json" | jq 'select(.actor.name == "lex")'

# Filter by action type
cat "${VAULT_PATH}/Logs/2025-01-15.json" | jq 'select(.action.type == "claim")'

# Filter by status
cat "${VAULT_PATH}/Logs/2025-01-15.json" | jq 'select(.result.status == "failure")'

# Count actions by actor
cat "${VAULT_PATH}/Logs/2025-01-15.json" | jq -r '.actor.name' | sort | uniq -c

# Count actions by type
cat "${VAULT_PATH}/Logs/2025-01-15.json" | jq -r '.action.type' | sort | uniq -c

# Extract specific fields
cat "${VAULT_PATH}/Logs/2025-01-15.json" | jq -r '"\(.timestamp) [\(.actor.name)] \(.action.type) \(.resource.id) → \(.result.status)"'
```

### Programmatic (JavaScript)

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

---

## Integrity Verification

### Verify All Logs

```javascript
const { verifyLogIntegrity } = require('./audit_log_writer');

const report = await verifyLogIntegrity();

console.log(`Verified: ${report.verified.length} files`);
console.log(`Tampered: ${report.tampered.length} files`);

if (report.tampered.length > 0) {
  console.error('TAMPERING DETECTED:');
  for (const t of report.tampered) {
    console.error(`  ${t.file}`);
  }
}
```

### Command-Line Verification

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

---

## Log Rotation

### Automatic Rotation (Daily)

```javascript
const schedule = require('node-schedule');
const { rotateLogs } = require('./audit_log_writer');

// Run at midnight UTC
schedule.scheduleJob('0 0 * * *', rotateLogs);
```

### Manual Rotation

```javascript
const { rotateLogs } = require('./audit_log_writer');

await rotateLogs();
```

### Rotation Policy

```
Day 0-90:    Uncompressed logs in Logs/
Day 91-365:  Compressed logs in Logs/archive/
Day 366+:    Deleted (configurable)
```

---

## Security & Compliance

### PII Redaction

Automatically redacts:
- Email addresses: `user@example.com` → `[EMAIL_REDACTED]`
- Phone numbers: `555-123-4567` → `[PHONE_REDACTED]`
- SSN: `123-45-6789` → `[SSN_REDACTED]`
- Credit cards: `1234-5678-9012-3456` → `[CC_REDACTED]`

### Secret Redaction

Automatically redacts patterns:
- `API_KEY`, `TOKEN`, `PASSWORD`, `SECRET`, `CREDENTIAL`

### Compliance Support

- **GDPR**: Right to be forgotten (delete logs with user data)
- **SOC2**: Audit trail for access control
- **HIPAA**: Audit log retention for healthcare data
- **PCI-DSS**: Log all cardholder data access

---

## Monitoring & Alerts

### Metrics

- **Log write latency**: < 10ms (target)
- **Log write failure rate**: < 0.01% (target)
- **Log integrity pass rate**: 100% (target)
- **Disk usage**: Monitor, alert at 90%

### Alerts

```yaml
alerts:
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

---

## Best Practices

1. **Log every action** (claims, releases, approvals, delegations)
2. **Use structured format** (JSON, not free-form text)
3. **Include context** (trace IDs, durations, details)
4. **Rotate regularly** (daily rotation, compression)
5. **Verify integrity** (weekly checksum validation)
6. **Monitor disk usage** (alert before disk fills)
7. **Backup logs** (off-site for disaster recovery)
8. **Test queries** (ensure you can find what you need)
9. **Redact sensitive data** (PII, secrets)
10. **Set retention policy** (comply with regulations)

---

## Troubleshooting

### Logs not being written

```bash
# Check permissions
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
```

---

## Related Skills

- [vault/vault_state_manager](../vault/vault_state_manager/) - File operations to log
- [vault/task_lifecycle_manager](../vault/task_lifecycle_manager/) - Lifecycle events to log
- [coordination/agent_claim_coordinator](../coordination/agent_claim_coordinator/) - Claim events to log
- [coordination/agent_delegation_manager](../coordination/agent_delegation_manager/) - Delegation events to log

---

## Future Enhancements

### Planned Features

- [ ] Real-time log streaming (WebSocket)
- [ ] Elasticsearch integration
- [ ] Kibana dashboards
- [ ] Alerting rules engine
- [ ] Log aggregation (multi-agent)
- [ ] Advanced query DSL

### Experimental Features

- [ ] Machine learning anomaly detection
- [ ] Predictive failure analysis
- [ ] Automated root cause analysis

---

## License

This skill category is part of the AI-Employee project. See LICENSE file for details.
