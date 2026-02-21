---
name: audit_log_writer
description: Write structured JSON logs for every action taken (actor, type, result). Appends to date-based log files in /Logs/YYYY-MM-DD.json for audit trail and compliance.
---

# Audit Log Writer

## Purpose

This skill provides structured, tamper-resistant audit logging for all agent actions in the Digital FTE workflow. It creates immutable audit trails that track who did what, when, and with what result, enabling compliance, debugging, and security analysis.

The skill ensures:
- Every action is logged with complete context
- Logs are append-only (tamper-resistant)
- Log entries are timestamped with ISO 8601 UTC
- Logs are organized by date for easy querying
- Structured JSON format for machine parsing
- Human-readable event descriptions

## When to Use This Skill

Use `audit_log_writer` when:

- **Logging agent actions**: Task claims, releases, delegations, approvals
- **Security events**: Permission violations, unauthorized access attempts
- **State transitions**: Task lifecycle changes, file moves, status updates
- **Critical operations**: Deployments, deletions, configuration changes
- **Error tracking**: Failures, exceptions, timeouts
- **Compliance requirements**: GDPR, SOC2, HIPAA audit trails
- **Debugging**: Tracing agent behavior, investigating issues
- **Performance monitoring**: Tracking operation durations, throughput

Do NOT use this skill when:

- **Console logging**: Use console.log() for development debugging
- **Metrics collection**: Use dedicated metrics system (Prometheus, StatsD)
- **Application logs**: Use standard logging library for app-level logs
- **Real-time monitoring**: Use streaming log aggregators (ELK, Splunk)

## Impact Analysis Workflow

### 1. Environment Variable Strategy

**Build-Time vs Runtime Variables:**

This skill operates at runtime only. No build-time variables required.

**Runtime variables:**
```bash
# Required
VAULT_PATH="/absolute/path/to/vault"        # Vault root directory
LOGS_DIR="${VAULT_PATH}/Logs"               # Log directory

# Optional: Log rotation
LOG_ROTATION_DAYS="90"                      # Archive logs older than 90 days
ENABLE_LOG_COMPRESSION="true"               # Gzip old logs
LOG_ARCHIVE_DIR="${VAULT_PATH}/Logs/archive"

# Optional: Log validation
ENABLE_LOG_INTEGRITY_CHECK="true"           # Detect log tampering
LOG_CHECKSUM_ALGORITHM="sha256"             # Checksum algorithm

# Optional: Performance
LOG_BUFFER_SIZE="100"                       # Buffer entries before flush
LOG_FLUSH_INTERVAL_MS="5000"                # Flush buffer every 5 seconds
ENABLE_ASYNC_LOGGING="true"                 # Async writes (non-blocking)

# Optional: Privacy
ENABLE_PII_REDACTION="true"                 # Redact PII from logs
PII_PATTERNS="email|ssn|phone|credit_card"  # Patterns to redact

# Optional: Retention
LOG_RETENTION_DAYS="365"                    # Delete logs older than 1 year
ENABLE_AUTO_CLEANUP="true"                  # Auto-delete old logs
```

**Secrets Management:**

- This skill does NOT log secrets (redacts automatically)
- Logs may contain references to secrets (e.g., "used API key from .env")
- Never log API keys, tokens, passwords, or credentials

**Variable Discovery Process:**
```bash
# Check audit log configuration
cat .env | grep -E "(LOGS_DIR|LOG_ROTATION|LOG_RETENTION)"

# Verify logs directory
test -d "$LOGS_DIR" || echo "Logs directory missing"

# Check log files
ls -lh "$LOGS_DIR"/*.json

# Verify log integrity
sha256sum "$LOGS_DIR/2025-01-15.json" > "$LOGS_DIR/2025-01-15.json.sha256"
```

### 2. Network & Topology Implications

**Port Discovery:**

No network ports required. This skill operates on local filesystem only.

**Dependency Topology:**

```
Audit Log Writer
  └── Filesystem (local disk)
      ├── Logs/ (daily log files)
      ├── Logs/archive/ (compressed old logs)
      └── Logs/.checksums/ (integrity verification)
```

**Topology Notes:**
- All operations are append-only writes (no reads during logging)
- No external services or network dependencies
- Works in Docker containers if Logs/ mounted as volume
- Compatible with log forwarding tools (Fluentd, Filebeat)

**Docker/K8s Implications:**

When containerizing:
- Mount logs directory: `-v /host/logs:/vault/Logs`
- Use persistent volumes for log retention
- Consider sidecar container for log forwarding
- Set log rotation policy (avoid filling disk)

### 3. Auth / CORS / Security Impact

**Authentication Pattern Analysis:**

- No authentication required (local filesystem)
- Log writes must be append-only (no modifications allowed)
- Read access controlled by OS-level file permissions

**Security Considerations:**

| Risk | Mitigation |
|------|-----------|
| **Log tampering** | Append-only files; integrity checksums |
| **Log deletion** | Immutable flag (chattr +a); backup to remote |
| **PII leakage** | Auto-redact sensitive data before logging |
| **Secret exposure** | Blacklist patterns; never log credentials |
| **Disk exhaustion** | Log rotation; size limits; auto-cleanup |
| **Unauthorized access** | File permissions (600); encryption at rest |

**Validation Rules:**

Before logging:
```javascript
function sanitizeLogEntry(entry) {
  // Redact PII
  if (ENABLE_PII_REDACTION) {
    entry = redactPII(entry);
  }

  // Redact secrets
  entry = redactSecrets(entry);

  // Validate structure
  if (!entry.timestamp || !entry.actor || !entry.action) {
    throw new Error('Invalid log entry structure');
  }

  // Prevent log injection
  entry.message = escapeLogInjection(entry.message);

  return entry;
}
```

**Audit Requirements:**

Every log entry MUST include:
- `timestamp`: ISO 8601 UTC (e.g., "2025-01-15T10:30:00.000Z")
- `actor`: Agent or user who performed action
- `action`: Action type (claim, release, delegate, approve, etc.)
- `resource`: Resource affected (task ID, file path, etc.)
- `result`: Outcome (success, failure, error)
- `details`: Additional context (metadata, error message, etc.)
- `trace_id`: Optional correlation ID for multi-step operations

## Blueprints & Templates Used

### Blueprint: Log Entry Structure

**Purpose:** Standardize audit log entry format

**Template Variables:**
```json
{
  "timestamp": "{{TIMESTAMP_ISO}}",
  "trace_id": "{{TRACE_ID}}",
  "actor": {
    "type": "{{ACTOR_TYPE}}",
    "name": "{{ACTOR_NAME}}",
    "id": "{{ACTOR_ID}}",
    "ip_address": "{{IP_ADDRESS}}"
  },
  "action": {
    "type": "{{ACTION_TYPE}}",
    "verb": "{{ACTION_VERB}}",
    "category": "{{CATEGORY}}"
  },
  "resource": {
    "type": "{{RESOURCE_TYPE}}",
    "id": "{{RESOURCE_ID}}",
    "path": "{{RESOURCE_PATH}}"
  },
  "result": {
    "status": "{{STATUS}}",
    "code": "{{RESULT_CODE}}",
    "message": "{{RESULT_MESSAGE}}",
    "duration_ms": {{DURATION}}
  },
  "context": {
    "session_id": "{{SESSION_ID}}",
    "request_id": "{{REQUEST_ID}}",
    "parent_trace_id": "{{PARENT_TRACE_ID}}"
  },
  "details": {
    "{{KEY_1}}": "{{VALUE_1}}",
    "{{KEY_2}}": "{{VALUE_2}}"
  },
  "metadata": {
    "hostname": "{{HOSTNAME}}",
    "process_id": {{PID}},
    "version": "{{APP_VERSION}}"
  }
}
```

**Field Definitions:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `timestamp` | ISO 8601 | Yes | When action occurred (UTC) |
| `trace_id` | UUID | Yes | Unique ID for this log entry |
| `actor.type` | String | Yes | agent \| human \| system |
| `actor.name` | String | Yes | Agent name (lex, cex, orch) or username |
| `action.type` | String | Yes | claim \| release \| delegate \| approve \| etc. |
| `action.verb` | String | Yes | HTTP-style verb (GET, POST, PUT, DELETE) |
| `action.category` | String | No | task_management \| security \| system |
| `resource.type` | String | Yes | task \| file \| config \| user |
| `resource.id` | String | Yes | Resource identifier (task-123, file.json) |
| `result.status` | String | Yes | success \| failure \| error |
| `result.code` | String/Number | No | Error code or status code |
| `result.duration_ms` | Number | No | Operation duration in milliseconds |
| `details` | Object | No | Additional context (flexible schema) |

**Impact Notes:**
- All timestamps MUST be UTC (no local time)
- Trace IDs must be unique (UUID v4 recommended)
- Actor names must be consistent (use canonical names)
- Result status must be one of: success, failure, error

### Blueprint: Daily Log File Format

**Purpose:** Organize logs by date for easy querying and rotation

**File Structure:**
```
Logs/
├── 2025-01-15.json          # Today's logs
├── 2025-01-14.json          # Yesterday's logs
├── 2025-01-13.json
├── .checksums/
│   ├── 2025-01-15.json.sha256
│   ├── 2025-01-14.json.sha256
│   └── 2025-01-13.json.sha256
└── archive/
    ├── 2024-12.json.gz      # Archived December logs
    └── 2024-11.json.gz
```

**Log File Format:**

Each daily log file is a JSON Lines file (one JSON object per line):

```json
{"timestamp":"2025-01-15T10:00:00.000Z","trace_id":"a1b2c3","actor":{"type":"agent","name":"lex"},"action":{"type":"claim"},"resource":{"type":"task","id":"task-123"},"result":{"status":"success"}}
{"timestamp":"2025-01-15T10:05:00.000Z","trace_id":"d4e5f6","actor":{"type":"agent","name":"lex"},"action":{"type":"release"},"resource":{"type":"task","id":"task-123"},"result":{"status":"success"}}
```

**Benefits:**
- One line per entry (easy to parse with `jq`, `grep`)
- Append-only (efficient writes)
- Easy rotation (one file per day)
- Compression-friendly (gzip archives)

### Blueprint: Log Rotation Policy

**Purpose:** Prevent disk exhaustion; archive old logs

**Rotation Rules:**

```yaml
retention:
  active_days: 90            # Keep uncompressed for 90 days
  archive_days: 365          # Keep compressed for 1 year
  delete_after_days: 730     # Delete after 2 years

rotation:
  schedule: "daily"          # Rotate at midnight UTC
  compression: "gzip"        # Compress archived logs
  checksum: "sha256"         # Verify integrity before/after

cleanup:
  enable: true
  schedule: "weekly"         # Run cleanup weekly
  dry_run: false
```

**Rotation Process:**

```
1. At midnight UTC:
   - Close current log file (2025-01-15.json)
   - Compute checksum (2025-01-15.json.sha256)
   - Create new log file (2025-01-16.json)

2. For logs older than 90 days:
   - Compress: 2024-10-15.json → archive/2024-10-15.json.gz
   - Verify checksum before compression
   - Compute checksum after compression
   - Delete original uncompressed file

3. For logs older than 365 days:
   - Delete archived log: archive/2023-10-15.json.gz
   - Delete checksum: .checksums/2023-10-15.json.sha256
```

**Impact Notes:**
- Rotation happens at midnight UTC (avoid mid-day disruption)
- Checksums verify integrity (detect tampering or corruption)
- Compressed logs save ~90% disk space
- Deleted logs are gone forever (backup first!)

## Core Operations

### Operation: Log Action

**Purpose:** Append structured log entry to daily log file

**Preconditions:**
- Logs directory exists and is writable
- Log entry is valid (all required fields present)
- PII/secrets have been redacted

**Steps:**
1. Generate trace_id (UUID v4)
2. Add timestamp (current time in ISO 8601 UTC)
3. Sanitize entry (redact PII, secrets)
4. Validate entry structure
5. Determine log file path (Logs/YYYY-MM-DD.json)
6. Append entry as single JSON line
7. Flush buffer (if buffering enabled)
8. Return trace_id for correlation

**Postconditions:**
- Log entry appended to file
- File integrity maintained (append-only)
- Trace ID returned to caller

**Error Handling:**
- If logs directory doesn't exist: create it
- If file not writable: log to stderr and continue
- If entry invalid: throw error (don't log malformed entries)
- If disk full: log critical alert, stop logging (prevent corruption)

**Example:**
```javascript
async function logAction(actor, action, resource, result, details = {}) {
  const traceId = uuidv4();
  const timestamp = new Date().toISOString();

  const entry = {
    timestamp,
    trace_id: traceId,
    actor: {
      type: actor.type,
      name: actor.name,
      id: actor.id || null
    },
    action: {
      type: action.type,
      verb: action.verb || 'EXECUTE',
      category: action.category || 'general'
    },
    resource: {
      type: resource.type,
      id: resource.id,
      path: resource.path || null
    },
    result: {
      status: result.status,
      code: result.code || null,
      message: result.message || null,
      duration_ms: result.duration_ms || null
    },
    details: sanitizeDetails(details),
    metadata: {
      hostname: os.hostname(),
      process_id: process.pid,
      version: process.env.APP_VERSION || 'unknown'
    }
  };

  // Sanitize
  const sanitized = sanitizeLogEntry(entry);

  // Validate
  validateLogEntry(sanitized);

  // Determine log file
  const logDate = timestamp.split('T')[0]; // YYYY-MM-DD
  const logPath = `${LOGS_DIR}/${logDate}.json`;

  // Append to file
  await appendToLogFile(logPath, sanitized);

  return traceId;
}
```

### Operation: Append to Log File

**Purpose:** Atomically append log entry to daily log file

**Preconditions:**
- Log entry is valid JSON
- Log file path is valid
- Logs directory is writable

**Steps:**
1. Serialize entry to JSON string
2. Add newline character
3. Open log file in append mode (O_APPEND)
4. Write JSON string atomically
5. Close file (or keep file handle open for buffering)
6. Update in-memory checksum (if integrity checking enabled)

**Postconditions:**
- Entry appended to file
- File closed (or buffered)
- Checksum updated

**Error Handling:**
- If file doesn't exist: create it
- If write fails: retry once, then log to stderr
- If disk full: log critical alert, return error

**Example:**
```javascript
async function appendToLogFile(logPath, entry) {
  const jsonLine = JSON.stringify(entry) + '\n';

  try {
    // Atomic append (O_APPEND flag ensures atomicity)
    await fs.appendFile(logPath, jsonLine, { flag: 'a' });

    // Update checksum (if enabled)
    if (ENABLE_LOG_INTEGRITY_CHECK) {
      await updateChecksum(logPath, jsonLine);
    }

  } catch (err) {
    if (err.code === 'ENOSPC') {
      // Disk full
      console.error('CRITICAL: Disk full; cannot write logs');
      throw new Error('Disk full');
    } else if (err.code === 'ENOENT') {
      // Directory doesn't exist
      await fs.mkdir(path.dirname(logPath), { recursive: true });
      await fs.appendFile(logPath, jsonLine, { flag: 'a' });
    } else {
      // Other error; retry once
      console.error(`Log write failed: ${err.message}; retrying`);
      await sleep(100);
      await fs.appendFile(logPath, jsonLine, { flag: 'a' });
    }
  }
}
```

### Operation: Rotate Logs

**Purpose:** Archive old logs, compress, clean up

**Preconditions:**
- Logs directory exists
- Current date advanced past rotation threshold

**Steps:**
1. Identify logs older than LOG_ROTATION_DAYS
2. For each old log:
   - Compute final checksum
   - Compress to archive/ directory
   - Verify compressed file integrity
   - Delete original uncompressed file
3. Identify archived logs older than LOG_RETENTION_DAYS
4. Delete expired archived logs
5. Update rotation metadata

**Postconditions:**
- Old logs compressed and archived
- Expired logs deleted
- Disk space freed

**Error Handling:**
- If compression fails: keep original, log error
- If checksum mismatch: don't delete original, alert admin
- If deletion fails: log error, continue (don't block rotation)

**Example:**
```javascript
async function rotateLogs() {
  const now = new Date();
  const logFiles = await fs.readdir(LOGS_DIR);

  for (const logFile of logFiles) {
    if (!logFile.endsWith('.json')) continue;

    const logPath = `${LOGS_DIR}/${logFile}`;
    const logDate = logFile.replace('.json', '');
    const ageInDays = daysBetween(parseDate(logDate), now);

    // Archive old logs
    if (ageInDays > LOG_ROTATION_DAYS) {
      console.log(`Archiving ${logFile} (age: ${ageInDays} days)`);

      // Compute checksum
      const checksum = await computeChecksum(logPath);
      await fs.writeFile(`${LOGS_DIR}/.checksums/${logFile}.sha256`, checksum);

      // Compress
      const archivePath = `${LOG_ARCHIVE_DIR}/${logFile}.gz`;
      await compressFile(logPath, archivePath);

      // Verify compressed file
      const verifyChecksum = await computeChecksum(archivePath);
      if (!verifyChecksum) {
        console.error(`Compression verification failed for ${logFile}`);
        continue; // Don't delete original
      }

      // Delete original
      await fs.unlink(logPath);
    }
  }

  // Delete expired archives
  const archiveFiles = await fs.readdir(LOG_ARCHIVE_DIR);

  for (const archiveFile of archiveFiles) {
    if (!archiveFile.endsWith('.json.gz')) continue;

    const archiveDate = archiveFile.replace('.json.gz', '');
    const ageInDays = daysBetween(parseDate(archiveDate), now);

    if (ageInDays > LOG_RETENTION_DAYS) {
      console.log(`Deleting expired archive: ${archiveFile} (age: ${ageInDays} days)`);
      await fs.unlink(`${LOG_ARCHIVE_DIR}/${archiveFile}`);
      await fs.unlink(`${LOGS_DIR}/.checksums/${archiveFile}.sha256`).catch(() => {});
    }
  }
}

// Run daily at midnight UTC
scheduleJob('0 0 * * *', rotateLogs);
```

### Operation: Query Logs

**Purpose:** Search logs for specific events, actors, or time ranges

**Preconditions:**
- Log files exist and are readable
- Query parameters are valid

**Steps:**
1. Parse query parameters (date range, actor, action, etc.)
2. Identify relevant log files (based on date range)
3. For each log file:
   - Read line by line
   - Parse JSON
   - Filter entries matching query
   - Collect matching entries
4. Sort results by timestamp
5. Return results

**Postconditions:**
- Matching log entries returned
- No modification to log files

**Error Handling:**
- If log file doesn't exist: skip, log warning
- If JSON parse fails: skip entry, log warning
- If query invalid: return error

**Example:**
```javascript
async function queryLogs(query) {
  const { startDate, endDate, actor, action, resource, status } = query;

  const results = [];

  // Determine log files to search
  const logFiles = await getLogFilesInRange(startDate, endDate);

  for (const logFile of logFiles) {
    const logPath = `${LOGS_DIR}/${logFile}`;

    try {
      const content = await fs.readFile(logPath, 'utf-8');
      const lines = content.split('\n').filter(line => line.trim());

      for (const line of lines) {
        try {
          const entry = JSON.parse(line);

          // Filter by query
          if (actor && entry.actor.name !== actor) continue;
          if (action && entry.action.type !== action) continue;
          if (resource && entry.resource.id !== resource) continue;
          if (status && entry.result.status !== status) continue;

          results.push(entry);

        } catch (err) {
          console.warn(`Failed to parse log entry: ${err.message}`);
        }
      }

    } catch (err) {
      console.warn(`Failed to read log file ${logFile}: ${err.message}`);
    }
  }

  // Sort by timestamp
  results.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

  return results;
}

// Usage
const logs = await queryLogs({
  startDate: '2025-01-01',
  endDate: '2025-01-15',
  actor: 'lex',
  action: 'claim',
  status: 'failure'
});
```

### Operation: Verify Log Integrity

**Purpose:** Detect log tampering using checksums

**Preconditions:**
- Log files exist
- Checksums exist for each log file

**Steps:**
1. List all log files
2. For each log file:
   - Read file content
   - Compute checksum (SHA256)
   - Load stored checksum from .checksums/
   - Compare computed vs stored
   - Report mismatch if different
3. Return integrity report

**Postconditions:**
- Integrity status for each log file
- Tampering detected (if any)

**Error Handling:**
- If checksum file missing: warn, skip verification
- If file unreadable: error, report as unverified

**Example:**
```javascript
async function verifyLogIntegrity() {
  const report = {
    verified: [],
    tampered: [],
    missing_checksum: [],
    errors: []
  };

  const logFiles = await fs.readdir(LOGS_DIR);

  for (const logFile of logFiles) {
    if (!logFile.endsWith('.json')) continue;

    const logPath = `${LOGS_DIR}/${logFile}`;
    const checksumPath = `${LOGS_DIR}/.checksums/${logFile}.sha256`;

    try {
      // Compute current checksum
      const computedChecksum = await computeChecksum(logPath);

      // Load stored checksum
      let storedChecksum;
      try {
        storedChecksum = (await fs.readFile(checksumPath, 'utf-8')).trim();
      } catch (err) {
        if (err.code === 'ENOENT') {
          report.missing_checksum.push(logFile);
          continue;
        }
        throw err;
      }

      // Compare
      if (computedChecksum === storedChecksum) {
        report.verified.push(logFile);
      } else {
        report.tampered.push({
          file: logFile,
          computed: computedChecksum,
          stored: storedChecksum
        });
        console.error(`TAMPERING DETECTED: ${logFile}`);
      }

    } catch (err) {
      report.errors.push({
        file: logFile,
        error: err.message
      });
    }
  }

  return report;
}

// Run weekly
scheduleJob('0 2 * * 0', async () => {
  const report = await verifyLogIntegrity();

  if (report.tampered.length > 0) {
    await notifyAdmin({
      type: 'log_tampering',
      count: report.tampered.length,
      files: report.tampered
    });
  }
});
```

## Integration with Existing Skills

### With vault_state_manager

- Log all file operations (create, move, delete)
- Log permission checks and violations
- Track vault state transitions

### With task_lifecycle_manager

- Log task state transitions
- Track task ownership changes
- Record lifecycle events

### With agent_claim_coordinator

- Log claim attempts (success/failure)
- Track conflict detections and resolutions
- Record heartbeat failures and reclaims

### With agent_delegation_manager

- Log delegation requests and responses
- Track approval syncs
- Record info requests and responses

## Common Log Patterns

### Pattern: Task Claim

```json
{
  "timestamp": "2025-01-15T10:00:00.000Z",
  "trace_id": "a1b2c3d4-e5f6-7890",
  "actor": {"type": "agent", "name": "lex"},
  "action": {"type": "claim", "verb": "PUT", "category": "task_management"},
  "resource": {"type": "task", "id": "task-123", "path": "In_Progress/task-123.json"},
  "result": {"status": "success", "duration_ms": 45},
  "details": {"from_folder": "Needs_Action", "to_folder": "In_Progress"}
}
```

### Pattern: Permission Violation

```json
{
  "timestamp": "2025-01-15T10:05:00.000Z",
  "trace_id": "b2c3d4e5-f6g7-8901",
  "actor": {"type": "agent", "name": "cex"},
  "action": {"type": "claim", "verb": "PUT", "category": "security"},
  "resource": {"type": "task", "id": "task-456", "path": "Needs_Action/task-456.json"},
  "result": {"status": "failure", "code": "PERMISSION_DENIED", "message": "Agent cex cannot claim tasks"},
  "details": {"required_permission": "claim_task", "actual_permissions": ["read_task"]}
}
```

### Pattern: Approval

```json
{
  "timestamp": "2025-01-15T10:10:00.000Z",
  "trace_id": "c3d4e5f6-g7h8-9012",
  "actor": {"type": "human", "name": "alice", "id": "alice@example.com"},
  "action": {"type": "approve", "verb": "POST", "category": "workflow"},
  "resource": {"type": "task", "id": "task-789", "path": "Approved/task-789.json"},
  "result": {"status": "success", "duration_ms": 120},
  "details": {"decision": "approved", "reason": "Looks good; proceed", "from_folder": "Pending_Approval"}
}
```

## Gotchas & Edge Cases

See `references/gotchas.md` for detailed edge case handling:
- Concurrent writes to same log file
- Clock skew causing out-of-order timestamps
- Disk full during log write
- Log file corruption
- Race conditions in log rotation
- Missing log entries after crash

## Success Metrics

- **Log write latency**: Average time to write log entry (target: < 10ms)
- **Log write failure rate**: % of log writes that fail (target: < 0.01%)
- **Log integrity pass rate**: % of logs that pass integrity check (target: 100%)
- **Disk usage**: Log directory size (monitor, set alerts)
- **Query performance**: Average time to query logs (target: < 1s for 1 day of logs)

## Testing Checklist

- [ ] Log action (success case)
- [ ] Log action (failure case)
- [ ] Append to existing log file
- [ ] Create new log file (first write of day)
- [ ] Handle concurrent writes (multiple agents)
- [ ] Redact PII from logs
- [ ] Redact secrets from logs
- [ ] Rotate logs (compress old logs)
- [ ] Delete expired logs (retention policy)
- [ ] Verify log integrity (checksums)
- [ ] Detect log tampering
- [ ] Query logs (date range)
- [ ] Query logs (actor filter)
- [ ] Query logs (action filter)
- [ ] Handle disk full scenario
- [ ] Handle log file corruption

---

**Related Skills:**
- `vault_state_manager` - File operations logging
- `task_lifecycle_manager` - Lifecycle event logging
- `agent_claim_coordinator` - Claim event logging
- `agent_delegation_manager` - Delegation event logging

**Related Documents:**
- `AGENTS.md` - Agent roles and permissions
- `VAULT_SKILLS_INTEGRATION.md` - Skill integration patterns
