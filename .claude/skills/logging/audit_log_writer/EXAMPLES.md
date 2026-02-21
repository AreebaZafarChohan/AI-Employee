# Audit Log Writer - Usage Examples

This document provides practical examples for using the audit_log_writer skill in various scenarios.

## Example 1: Log Task Claim

```javascript
const { logAction } = require('./audit_log_writer');

// Agent claims task
async function claimTask(taskId, agentName) {
  const startTime = Date.now();

  try {
    // Perform claim
    await claimTaskImpl(taskId, agentName);

    // Log success
    await logAction(
      { type: 'agent', name: agentName },
      { type: 'claim', verb: 'PUT', category: 'task_management' },
      { type: 'task', id: taskId, path: `In_Progress/${taskId}.json` },
      { status: 'success', duration_ms: Date.now() - startTime },
      { from_folder: 'Needs_Action', to_folder: 'In_Progress' }
    );

  } catch (err) {
    // Log failure
    await logAction(
      { type: 'agent', name: agentName },
      { type: 'claim', verb: 'PUT', category: 'task_management' },
      { type: 'task', id: taskId, path: `Needs_Action/${taskId}.json` },
      { status: 'failure', code: err.code, message: err.message, duration_ms: Date.now() - startTime },
      { error: err.stack }
    );

    throw err;
  }
}
```

**Resulting Log Entry:**
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

---

## Example 2: Log Human Approval

```javascript
// Human approves task
async function approveTask(taskId, humanUser, reason) {
  const startTime = Date.now();

  await logAction(
    { type: 'human', name: humanUser, id: `${humanUser}@example.com` },
    { type: 'approve', verb: 'POST', category: 'workflow' },
    { type: 'task', id: taskId, path: `Approved/${taskId}.json` },
    { status: 'success', duration_ms: Date.now() - startTime },
    {
      decision: 'approved',
      reason: reason,
      from_folder: 'Pending_Approval',
      to_folder: 'Approved'
    }
  );
}

// Usage
await approveTask('task-456', 'alice', 'Looks good; proceed with deployment');
```

**Resulting Log Entry:**
```json
{
  "timestamp": "2025-01-15T10:10:00.000Z",
  "trace_id": "b2c3d4e5-f6g7-8901-bcde",
  "actor": {
    "type": "human",
    "name": "alice",
    "id": "alice@example.com"
  },
  "action": {
    "type": "approve",
    "verb": "POST",
    "category": "workflow"
  },
  "resource": {
    "type": "task",
    "id": "task-456",
    "path": "Approved/task-456.json"
  },
  "result": {
    "status": "success",
    "code": null,
    "message": null,
    "duration_ms": 120
  },
  "details": {
    "decision": "approved",
    "reason": "Looks good; proceed with deployment",
    "from_folder": "Pending_Approval",
    "to_folder": "Approved"
  },
  "metadata": {
    "hostname": "agent-server-01",
    "process_id": 12345,
    "version": "1.0.0"
  }
}
```

---

## Example 3: Log Permission Violation

```javascript
// Agent attempts unauthorized action
async function attemptUnauthorizedClaim(taskId, agentName) {
  const startTime = Date.now();

  // Check permissions
  if (!canAgentClaimTask(agentName, task)) {
    // Log permission denial
    await logAction(
      { type: 'agent', name: agentName },
      { type: 'claim', verb: 'PUT', category: 'security' },
      { type: 'task', id: taskId, path: `Needs_Action/${taskId}.json` },
      {
        status: 'failure',
        code: 'PERMISSION_DENIED',
        message: `Agent ${agentName} cannot claim tasks`,
        duration_ms: Date.now() - startTime
      },
      {
        required_permission: 'claim_task',
        actual_permissions: getAgentPermissions(agentName)
      }
    );

    throw new Error('Permission denied');
  }
}
```

**Resulting Log Entry:**
```json
{
  "timestamp": "2025-01-15T10:05:00.000Z",
  "trace_id": "c3d4e5f6-g7h8-9012-cdef",
  "actor": {
    "type": "agent",
    "name": "cex",
    "id": null
  },
  "action": {
    "type": "claim",
    "verb": "PUT",
    "category": "security"
  },
  "resource": {
    "type": "task",
    "id": "task-789",
    "path": "Needs_Action/task-789.json"
  },
  "result": {
    "status": "failure",
    "code": "PERMISSION_DENIED",
    "message": "Agent cex cannot claim tasks",
    "duration_ms": 5
  },
  "details": {
    "required_permission": "claim_task",
    "actual_permissions": ["read_task", "plan_task"]
  },
  "metadata": {
    "hostname": "agent-server-01",
    "process_id": 12345,
    "version": "1.0.0"
  }
}
```

---

## Example 4: Log Delegation

```javascript
// lex delegates task to cex
async function delegateTask(taskId, fromAgent, toAgent) {
  const startTime = Date.now();

  try {
    await createDelegationSignal(taskId, fromAgent, toAgent);

    await logAction(
      { type: 'agent', name: fromAgent },
      { type: 'delegate', verb: 'POST', category: 'coordination' },
      { type: 'task', id: taskId, path: `Needs_Action/${taskId}.json` },
      { status: 'success', duration_ms: Date.now() - startTime },
      {
        to_agent: toAgent,
        delegation_type: 'plan_task',
        signal_path: `.signals/${taskId}.delegate.json`
      }
    );

  } catch (err) {
    await logAction(
      { type: 'agent', name: fromAgent },
      { type: 'delegate', verb: 'POST', category: 'coordination' },
      { type: 'task', id: taskId, path: `Needs_Action/${taskId}.json` },
      { status: 'error', code: err.code, message: err.message, duration_ms: Date.now() - startTime },
      { to_agent: toAgent, error: err.stack }
    );

    throw err;
  }
}

// Usage
await delegateTask('task-101', 'lex', 'cex');
```

**Resulting Log Entry:**
```json
{
  "timestamp": "2025-01-15T10:15:00.000Z",
  "trace_id": "d4e5f6g7-h8i9-0123-defg",
  "actor": {
    "type": "agent",
    "name": "lex",
    "id": null
  },
  "action": {
    "type": "delegate",
    "verb": "POST",
    "category": "coordination"
  },
  "resource": {
    "type": "task",
    "id": "task-101",
    "path": "Needs_Action/task-101.json"
  },
  "result": {
    "status": "success",
    "code": null,
    "message": null,
    "duration_ms": 78
  },
  "details": {
    "to_agent": "cex",
    "delegation_type": "plan_task",
    "signal_path": ".signals/task-101.delegate.json"
  },
  "metadata": {
    "hostname": "agent-server-01",
    "process_id": 12345,
    "version": "1.0.0"
  }
}
```

---

## Example 5: Log File Operations

```javascript
// Log file move
async function moveTaskFile(taskId, fromFolder, toFolder) {
  const startTime = Date.now();
  const fromPath = `${fromFolder}/${taskId}.json`;
  const toPath = `${toFolder}/${taskId}.json`;

  try {
    await fs.rename(`${VAULT_PATH}/${fromPath}`, `${VAULT_PATH}/${toPath}`);

    await logAction(
      { type: 'system', name: 'vault_state_manager' },
      { type: 'move', verb: 'PUT', category: 'file_operations' },
      { type: 'file', id: taskId, path: toPath },
      { status: 'success', duration_ms: Date.now() - startTime },
      {
        operation: 'rename',
        from_path: fromPath,
        to_path: toPath
      }
    );

  } catch (err) {
    await logAction(
      { type: 'system', name: 'vault_state_manager' },
      { type: 'move', verb: 'PUT', category: 'file_operations' },
      { type: 'file', id: taskId, path: fromPath },
      { status: 'error', code: err.code, message: err.message, duration_ms: Date.now() - startTime },
      { operation: 'rename', from_path: fromPath, to_path: toPath, error: err.stack }
    );

    throw err;
  }
}
```

---

## Example 6: Log with Trace ID (Multi-Step Operation)

```javascript
// Parent operation
async function processTask(taskId, agentName) {
  const parentTraceId = uuidv4();

  // Step 1: Claim
  const claimTraceId = await logAction(
    { type: 'agent', name: agentName },
    { type: 'claim', verb: 'PUT', category: 'task_management' },
    { type: 'task', id: taskId },
    { status: 'success', duration_ms: 45 },
    { parent_trace_id: parentTraceId }
  );

  // Step 2: Process
  const processTraceId = await logAction(
    { type: 'agent', name: agentName },
    { type: 'process', verb: 'EXECUTE', category: 'task_execution' },
    { type: 'task', id: taskId },
    { status: 'success', duration_ms: 5000 },
    { parent_trace_id: parentTraceId, claim_trace_id: claimTraceId }
  );

  // Step 3: Release
  await logAction(
    { type: 'agent', name: agentName },
    { type: 'release', verb: 'DELETE', category: 'task_management' },
    { type: 'task', id: taskId },
    { status: 'success', duration_ms: 30 },
    { parent_trace_id: parentTraceId, process_trace_id: processTraceId, reason: 'completed' }
  );
}
```

---

## Example 7: Query Logs

```javascript
// Query logs for specific actor
async function getAgentActions(agentName, startDate, endDate) {
  const { queryLogs } = require('./audit_log_writer');

  const logs = await queryLogs({
    startDate: startDate,
    endDate: endDate,
    actor: agentName
  });

  console.log(`Found ${logs.length} actions by ${agentName}`);

  for (const log of logs) {
    console.log(`${log.timestamp}: ${log.action.type} ${log.resource.id} → ${log.result.status}`);
  }

  return logs;
}

// Usage
const lexActions = await getAgentActions('lex', '2025-01-01', '2025-01-15');
```

---

## Example 8: Query Failed Operations

```javascript
// Find all failed operations
async function getFailedOperations(startDate, endDate) {
  const { queryLogs } = require('./audit_log_writer');

  const logs = await queryLogs({
    startDate: startDate,
    endDate: endDate,
    status: 'failure'
  });

  // Group by actor
  const byActor = {};
  for (const log of logs) {
    const actor = log.actor.name;
    if (!byActor[actor]) byActor[actor] = [];
    byActor[actor].push(log);
  }

  // Report
  for (const [actor, failures] of Object.entries(byActor)) {
    console.log(`${actor}: ${failures.length} failures`);

    for (const failure of failures) {
      console.log(`  - ${failure.action.type} ${failure.resource.id}: ${failure.result.message}`);
    }
  }

  return logs;
}

// Usage
await getFailedOperations('2025-01-15', '2025-01-15');
```

---

## Example 9: Verify Log Integrity

```javascript
const { verifyLogIntegrity } = require('./audit_log_writer');

// Verify all log files
async function checkLogIntegrity() {
  const report = await verifyLogIntegrity();

  console.log(`Verified: ${report.verified.length} files`);
  console.log(`Tampered: ${report.tampered.length} files`);
  console.log(`Missing checksums: ${report.missing_checksum.length} files`);
  console.log(`Errors: ${report.errors.length} files`);

  if (report.tampered.length > 0) {
    console.error('TAMPERING DETECTED:');
    for (const tampered of report.tampered) {
      console.error(`  - ${tampered.file}`);
      console.error(`    Computed: ${tampered.computed}`);
      console.error(`    Stored:   ${tampered.stored}`);
    }

    // Alert admin
    await notifyAdmin({
      type: 'log_tampering',
      count: report.tampered.length,
      files: report.tampered.map(t => t.file)
    });
  }

  return report;
}

// Run weekly
scheduleJob('0 2 * * 0', checkLogIntegrity);
```

---

## Example 10: Log Rotation (Daily Job)

```javascript
const { rotateLogs } = require('./audit_log_writer');

// Rotate logs daily at midnight UTC
scheduleJob('0 0 * * *', async () => {
  console.log('Starting log rotation...');

  try {
    await rotateLogs();
    console.log('Log rotation completed successfully');

  } catch (err) {
    console.error(`Log rotation failed: ${err.message}`);

    await notifyAdmin({
      type: 'log_rotation_failure',
      error: err.message,
      timestamp: new Date().toISOString()
    });
  }
});
```

---

## Helper Functions

### Compute Checksum

```javascript
const crypto = require('crypto');
const fs = require('fs').promises;

async function computeChecksum(filePath) {
  const hash = crypto.createHash('sha256');
  const content = await fs.readFile(filePath);
  hash.update(content);
  return hash.digest('hex');
}
```

### Compress File

```javascript
const zlib = require('zlib');
const { pipeline } = require('stream/promises');

async function compressFile(inputPath, outputPath) {
  const gzip = zlib.createGzip();
  const source = fs.createReadStream(inputPath);
  const destination = fs.createWriteStream(outputPath);

  await pipeline(source, gzip, destination);
}
```

### Sanitize PII

```javascript
function redactPII(text) {
  // Redact email addresses
  text = text.replace(/\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g, '[EMAIL_REDACTED]');

  // Redact phone numbers
  text = text.replace(/\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g, '[PHONE_REDACTED]');

  // Redact SSN
  text = text.replace(/\b\d{3}-\d{2}-\d{4}\b/g, '[SSN_REDACTED]');

  // Redact credit cards
  text = text.replace(/\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b/g, '[CC_REDACTED]');

  return text;
}

function sanitizeLogEntry(entry) {
  const stringified = JSON.stringify(entry);
  const redacted = redactPII(stringified);
  return JSON.parse(redacted);
}
```

---

## Command-Line Tools

### View Today's Logs

```bash
#!/bin/bash
# view-logs.sh

LOG_DATE=$(date -u +%Y-%m-%d)
LOG_FILE="${VAULT_PATH}/Logs/${LOG_DATE}.json"

if [ -f "$LOG_FILE" ]; then
  cat "$LOG_FILE" | jq -r '. | "\(.timestamp) [\(.actor.name)] \(.action.type) \(.resource.id) → \(.result.status)"'
else
  echo "No logs for $LOG_DATE"
fi
```

### Search Logs

```bash
#!/bin/bash
# search-logs.sh <actor> <start-date> <end-date>

ACTOR="$1"
START_DATE="$2"
END_DATE="$3"

find "${VAULT_PATH}/Logs" -name "*.json" -newermt "$START_DATE" ! -newermt "$END_DATE" \
  -exec grep -h "\"name\":\"$ACTOR\"" {} \; \
  | jq -r '. | "\(.timestamp) \(.action.type) \(.resource.id) → \(.result.status)"'
```

### Check Log Integrity

```bash
#!/bin/bash
# verify-logs.sh

for log_file in ${VAULT_PATH}/Logs/*.json; do
  checksum_file="${log_file}.sha256"

  if [ -f "$checksum_file" ]; then
    computed=$(sha256sum "$log_file" | awk '{print $1}')
    stored=$(cat "$checksum_file")

    if [ "$computed" = "$stored" ]; then
      echo "✓ $(basename $log_file)"
    else
      echo "✗ $(basename $log_file) TAMPERED"
    fi
  else
    echo "? $(basename $log_file) (no checksum)"
  fi
done
```

---

These examples demonstrate the core workflows and patterns for using the audit_log_writer skill. Adapt them to your specific use case and compliance requirements.
