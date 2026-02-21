# Design Patterns for Audit Log Writer

## Pattern: Structured Logging with Consistent Schema

**Problem:** Logs need to be machine-parseable for analysis but human-readable for debugging.

**Solution:** Use consistent JSON schema with required fields for every log entry.

**Implementation:**
```javascript
// Define log schema
const LOG_SCHEMA = {
  timestamp: { type: 'string', format: 'iso8601', required: true },
  trace_id: { type: 'string', format: 'uuid', required: true },
  actor: {
    type: { type: 'string', enum: ['agent', 'human', 'system'], required: true },
    name: { type: 'string', required: true },
    id: { type: 'string', required: false }
  },
  action: {
    type: { type: 'string', required: true },
    verb: { type: 'string', enum: ['GET', 'POST', 'PUT', 'DELETE', 'EXECUTE'], required: true },
    category: { type: 'string', required: false }
  },
  resource: {
    type: { type: 'string', required: true },
    id: { type: 'string', required: true },
    path: { type: 'string', required: false }
  },
  result: {
    status: { type: 'string', enum: ['success', 'failure', 'error'], required: true },
    code: { type: 'string', required: false },
    message: { type: 'string', required: false },
    duration_ms: { type: 'number', required: false }
  },
  details: { type: 'object', required: false },
  metadata: { type: 'object', required: false }
};

// Validation function
function validateLogEntry(entry) {
  const errors = [];

  // Validate required fields
  if (!entry.timestamp) errors.push('Missing timestamp');
  if (!entry.trace_id) errors.push('Missing trace_id');
  if (!entry.actor?.type) errors.push('Missing actor.type');
  if (!entry.actor?.name) errors.push('Missing actor.name');
  if (!entry.action?.type) errors.push('Missing action.type');
  if (!entry.resource?.type) errors.push('Missing resource.type');
  if (!entry.resource?.id) errors.push('Missing resource.id');
  if (!entry.result?.status) errors.push('Missing result.status');

  // Validate enum values
  if (entry.actor?.type && !['agent', 'human', 'system'].includes(entry.actor.type)) {
    errors.push(`Invalid actor.type: ${entry.actor.type}`);
  }

  if (entry.result?.status && !['success', 'failure', 'error'].includes(entry.result.status)) {
    errors.push(`Invalid result.status: ${entry.result.status}`);
  }

  if (errors.length > 0) {
    throw new Error(`Log validation failed: ${errors.join(', ')}`);
  }

  return true;
}

// Usage
const entry = {
  timestamp: new Date().toISOString(),
  trace_id: uuidv4(),
  actor: { type: 'agent', name: 'lex' },
  action: { type: 'claim', verb: 'PUT', category: 'task_management' },
  resource: { type: 'task', id: 'task-123' },
  result: { status: 'success', duration_ms: 45 }
};

validateLogEntry(entry); // ✅ Valid
```

**Benefits:**
- Consistent format across all logs
- Easy to parse and query
- Type safety (validation catches errors)
- Self-documenting (schema defines structure)

**Trade-offs:**
- Less flexible (must conform to schema)
- Validation overhead
- Schema changes require migration

---

## Pattern: JSON Lines (JSONL) for Append-Only Logs

**Problem:** Need efficient append-only logging that's easy to parse line-by-line.

**Solution:** Use JSON Lines format (one JSON object per line, newline-separated).

**Implementation:**
```javascript
// Write log entry
async function appendLogEntry(logPath, entry) {
  const jsonLine = JSON.stringify(entry) + '\n';
  await fs.appendFile(logPath, jsonLine, { flag: 'a' });
}

// Read log entries
async function readLogEntries(logPath) {
  const content = await fs.readFile(logPath, 'utf-8');
  const lines = content.split('\n').filter(line => line.trim());

  return lines.map(line => {
    try {
      return JSON.parse(line);
    } catch (err) {
      console.warn(`Failed to parse log line: ${err.message}`);
      return null;
    }
  }).filter(entry => entry !== null);
}

// Stream processing (memory-efficient for large files)
const readline = require('readline');

async function streamLogEntries(logPath, callback) {
  const fileStream = fs.createReadStream(logPath);
  const rl = readline.createInterface({
    input: fileStream,
    crlfDelay: Infinity
  });

  for await (const line of rl) {
    if (line.trim()) {
      try {
        const entry = JSON.parse(line);
        await callback(entry);
      } catch (err) {
        console.warn(`Failed to parse log line: ${err.message}`);
      }
    }
  }
}

// Usage: Count actions by actor
const actorCounts = {};

await streamLogEntries('Logs/2025-01-15.json', (entry) => {
  const actor = entry.actor.name;
  actorCounts[actor] = (actorCounts[actor] || 0) + 1;
});

console.log(actorCounts); // { lex: 42, cex: 13, orch: 5 }
```

**Benefits:**
- Efficient append (no need to parse entire file)
- Easy line-by-line processing
- Compatible with standard tools (grep, awk, jq)
- Memory-efficient streaming

**Trade-offs:**
- Not human-readable (compared to pretty JSON)
- Corrupted line breaks entire entry
- No nested arrays of log entries

---

## Pattern: Date-Based Log File Rotation

**Problem:** Single log file grows too large; need to organize logs by date for easy querying and cleanup.

**Solution:** Create one log file per day; rotate at midnight UTC.

**Implementation:**
```javascript
// Get current log file path
function getCurrentLogPath() {
  const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD
  return `${LOGS_DIR}/${today}.json`;
}

// Log entry
async function logAction(actor, action, resource, result, details) {
  const entry = {
    timestamp: new Date().toISOString(),
    trace_id: uuidv4(),
    actor,
    action,
    resource,
    result,
    details,
    metadata: {
      hostname: os.hostname(),
      process_id: process.pid,
      version: process.env.APP_VERSION || 'unknown'
    }
  };

  const logPath = getCurrentLogPath();
  await appendLogEntry(logPath, entry);

  return entry.trace_id;
}

// Daily rotation job
const schedule = require('node-schedule');

schedule.scheduleJob('0 0 * * *', async () => {
  console.log('Starting daily log rotation...');

  // Compute checksum for yesterday's log
  const yesterday = new Date(Date.now() - 86400000).toISOString().split('T')[0];
  const yesterdayLogPath = `${LOGS_DIR}/${yesterday}.json`;

  if (await fileExists(yesterdayLogPath)) {
    const checksum = await computeChecksum(yesterdayLogPath);
    await fs.writeFile(`${LOGS_DIR}/.checksums/${yesterday}.json.sha256`, checksum);
    console.log(`Checksum created for ${yesterday}.json`);
  }

  // Compress logs older than 90 days
  await compressOldLogs();

  // Delete logs older than 365 days
  await deleteExpiredLogs();

  console.log('Log rotation completed');
});
```

**Benefits:**
- Easy to find logs by date
- Simple rotation policy (one file per day)
- Efficient querying (only load relevant dates)
- Natural archival strategy

**Trade-offs:**
- File switches at midnight (slight latency)
- Empty files for days with no activity
- Time zone considerations (always use UTC)

---

## Pattern: Integrity Verification with Checksums

**Problem:** Need to detect log tampering or corruption.

**Solution:** Compute SHA256 checksum for each log file; verify periodically.

**Implementation:**
```javascript
const crypto = require('crypto');

// Compute checksum
async function computeChecksum(filePath) {
  const hash = crypto.createHash('sha256');
  const content = await fs.readFile(filePath);
  hash.update(content);
  return hash.digest('hex');
}

// Store checksum
async function storeChecksum(logPath) {
  const checksum = await computeChecksum(logPath);
  const checksumPath = `${LOGS_DIR}/.checksums/${path.basename(logPath)}.sha256`;
  await fs.writeFile(checksumPath, checksum);
  return checksum;
}

// Verify checksum
async function verifyChecksum(logPath) {
  const computed = await computeChecksum(logPath);
  const checksumPath = `${LOGS_DIR}/.checksums/${path.basename(logPath)}.sha256`;

  try {
    const stored = (await fs.readFile(checksumPath, 'utf-8')).trim();
    return computed === stored;
  } catch (err) {
    if (err.code === 'ENOENT') {
      console.warn(`Checksum file not found for ${path.basename(logPath)}`);
      return null; // Unknown (checksum missing)
    }
    throw err;
  }
}

// Verify all logs
async function verifyAllLogs() {
  const report = {
    verified: [],
    tampered: [],
    missing_checksum: [],
    errors: []
  };

  const logFiles = (await fs.readdir(LOGS_DIR)).filter(f => f.endsWith('.json'));

  for (const logFile of logFiles) {
    const logPath = `${LOGS_DIR}/${logFile}`;

    try {
      const isValid = await verifyChecksum(logPath);

      if (isValid === true) {
        report.verified.push(logFile);
      } else if (isValid === false) {
        report.tampered.push(logFile);
        console.error(`TAMPERING DETECTED: ${logFile}`);
      } else {
        report.missing_checksum.push(logFile);
      }
    } catch (err) {
      report.errors.push({ file: logFile, error: err.message });
    }
  }

  return report;
}

// Weekly verification job
schedule.scheduleJob('0 2 * * 0', async () => {
  const report = await verifyAllLogs();

  if (report.tampered.length > 0) {
    await notifyAdmin({
      type: 'log_tampering',
      count: report.tampered.length,
      files: report.tampered
    });
  }

  console.log(`Verified: ${report.verified.length}, Tampered: ${report.tampered.length}`);
});
```

**Benefits:**
- Detect tampering or corruption
- Cryptographically secure (SHA256)
- Automated verification (weekly job)
- Compliance support (audit trail integrity)

**Trade-offs:**
- Extra disk space for checksums
- CPU overhead for hash computation
- Not real-time (periodic verification)

---

## Pattern: Buffered Logging for Performance

**Problem:** Frequent small writes are slow; need to batch writes for performance.

**Solution:** Buffer log entries in memory; flush periodically or when buffer fills.

**Implementation:**
```javascript
class BufferedLogger {
  constructor(flushIntervalMs = 5000, bufferSize = 100) {
    this.buffer = [];
    this.flushIntervalMs = flushIntervalMs;
    this.bufferSize = bufferSize;
    this.flushTimer = null;

    // Start periodic flush
    this.startPeriodicFlush();
  }

  async log(entry) {
    this.buffer.push(entry);

    // Flush if buffer full
    if (this.buffer.length >= this.bufferSize) {
      await this.flush();
    }
  }

  async flush() {
    if (this.buffer.length === 0) return;

    const logPath = getCurrentLogPath();
    const entries = this.buffer.splice(0); // Drain buffer

    // Write all entries at once
    const lines = entries.map(e => JSON.stringify(e)).join('\n') + '\n';
    await fs.appendFile(logPath, lines, { flag: 'a' });

    console.log(`Flushed ${entries.length} log entries`);
  }

  startPeriodicFlush() {
    this.flushTimer = setInterval(async () => {
      await this.flush();
    }, this.flushIntervalMs);
  }

  async shutdown() {
    // Flush remaining entries
    await this.flush();

    // Stop periodic flush
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
      this.flushTimer = null;
    }
  }
}

// Global logger instance
const logger = new BufferedLogger();

// Log entry (non-blocking)
async function logAction(actor, action, resource, result, details) {
  const entry = {
    timestamp: new Date().toISOString(),
    trace_id: uuidv4(),
    actor,
    action,
    resource,
    result,
    details
  };

  await logger.log(entry);
  return entry.trace_id;
}

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('Shutting down; flushing logs...');
  await logger.shutdown();
  process.exit(0);
});
```

**Benefits:**
- Better performance (batch writes)
- Reduced I/O operations
- Configurable buffer size and flush interval

**Trade-offs:**
- Entries buffered in memory (lost on crash)
- Slight delay before logs written to disk
- More complex shutdown logic (must flush)

---

## Pattern: PII Redaction with Allowlists

**Problem:** Need to redact sensitive data (PII) but allow specific non-sensitive patterns.

**Solution:** Use regex patterns to detect PII; check against allowlist before redacting.

**Implementation:**
```javascript
// PII patterns
const PII_PATTERNS = {
  email: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g,
  phone: /\b(\+\d{1,3}[- ]?)?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}\b/g,
  ssn: /\b\d{3}-\d{2}-\d{4}\b/g,
  credit_card: /\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b/g
};

// Allowlist (known non-sensitive patterns)
const PII_ALLOWLIST = {
  email: [
    'noreply@example.com',
    'support@company.com',
    /.*@test\.com$/
  ],
  phone: [
    '555-123-4567', // Test numbers
    /^555-/
  ]
};

// Check if value is allowlisted
function isAllowlisted(value, type) {
  const allowlist = PII_ALLOWLIST[type] || [];

  for (const pattern of allowlist) {
    if (pattern instanceof RegExp) {
      if (pattern.test(value)) return true;
    } else {
      if (pattern === value) return true;
    }
  }

  return false;
}

// Redact PII
function redactPII(text) {
  let redacted = text;

  for (const [type, pattern] of Object.entries(PII_PATTERNS)) {
    redacted = redacted.replace(pattern, (match) => {
      if (isAllowlisted(match, type)) {
        return match; // Keep allowlisted values
      }
      return `[${type.toUpperCase()}_REDACTED]`;
    });
  }

  return redacted;
}

// Sanitize log entry
function sanitizeLogEntry(entry) {
  const stringified = JSON.stringify(entry);
  const redacted = redactPII(stringified);
  return JSON.parse(redacted);
}

// Usage
const entry = {
  actor: { type: 'human', name: 'alice', email: 'alice@company.com' },
  details: { contact: 'Call 555-987-6543 or email support@company.com' }
};

const sanitized = sanitizeLogEntry(entry);
// Result:
// {
//   actor: { type: 'human', name: 'alice', email: 'alice@company.com' },
//   details: { contact: 'Call [PHONE_REDACTED] or email support@company.com' }
// }
```

**Benefits:**
- Protect user privacy (GDPR compliance)
- Configurable allowlists (preserve non-sensitive data)
- Multiple PII types supported

**Trade-offs:**
- Regex patterns may have false positives
- Allowlist maintenance required
- Performance overhead (regex processing)

---

## Pattern: Trace ID for Distributed Operations

**Problem:** Need to correlate logs across multiple steps or agents.

**Solution:** Use trace_id to link related log entries; propagate through operation chain.

**Implementation:**
```javascript
// Parent operation
async function processTask(taskId, agentName) {
  const parentTraceId = uuidv4();

  // Step 1: Claim
  const claimTraceId = await logAction(
    { type: 'agent', name: agentName },
    { type: 'claim', verb: 'PUT' },
    { type: 'task', id: taskId },
    { status: 'success', duration_ms: 45 },
    { parent_trace_id: parentTraceId, step: 1 }
  );

  // Step 2: Execute
  const executeTraceId = await logAction(
    { type: 'agent', name: agentName },
    { type: 'execute', verb: 'EXECUTE' },
    { type: 'task', id: taskId },
    { status: 'success', duration_ms: 5000 },
    { parent_trace_id: parentTraceId, claim_trace_id: claimTraceId, step: 2 }
  );

  // Step 3: Release
  await logAction(
    { type: 'agent', name: agentName },
    { type: 'release', verb: 'DELETE' },
    { type: 'task', id: taskId },
    { status: 'success', duration_ms: 30 },
    { parent_trace_id: parentTraceId, execute_trace_id: executeTraceId, step: 3 }
  );

  return parentTraceId;
}

// Query related logs
async function getRelatedLogs(parentTraceId) {
  const logs = await queryLogs({
    startDate: '2025-01-15',
    endDate: '2025-01-15'
  });

  return logs.filter(log =>
    log.trace_id === parentTraceId ||
    log.details?.parent_trace_id === parentTraceId
  );
}

// Usage
const parentTraceId = await processTask('task-123', 'lex');
const relatedLogs = await getRelatedLogs(parentTraceId);

console.log(`Found ${relatedLogs.length} related log entries`);
```

**Benefits:**
- Correlate multi-step operations
- Distributed tracing support
- Root cause analysis (trace entire operation)

**Trade-offs:**
- Must propagate trace IDs through call stack
- Requires consistent trace ID format (UUID)

---

## Pattern: Log Compression with Streaming

**Problem:** Need to compress large log files without loading entire file into memory.

**Solution:** Use streaming compression (gzip) for memory-efficient processing.

**Implementation:**
```javascript
const zlib = require('zlib');
const { pipeline } = require('stream/promises');

// Compress file (streaming)
async function compressFile(inputPath, outputPath) {
  const gzip = zlib.createGzip({ level: 9 }); // Max compression
  const source = fs.createReadStream(inputPath);
  const destination = fs.createWriteStream(outputPath);

  await pipeline(source, gzip, destination);

  console.log(`Compressed ${inputPath} → ${outputPath}`);

  // Verify compressed file integrity
  const originalSize = (await fs.stat(inputPath)).size;
  const compressedSize = (await fs.stat(outputPath)).size;
  const compressionRatio = (1 - compressedSize / originalSize) * 100;

  console.log(`Compression: ${originalSize} bytes → ${compressedSize} bytes (${compressionRatio.toFixed(1)}% saved)`);
}

// Decompress file (streaming)
async function decompressFile(inputPath, outputPath) {
  const gunzip = zlib.createGunzip();
  const source = fs.createReadStream(inputPath);
  const destination = fs.createWriteStream(outputPath);

  await pipeline(source, gunzip, destination);
}

// Compress old logs
async function compressOldLogs() {
  const now = new Date();
  const logFiles = (await fs.readdir(LOGS_DIR)).filter(f => f.endsWith('.json'));

  for (const logFile of logFiles) {
    const logDate = logFile.replace('.json', '');
    const ageInDays = daysBetween(parseDate(logDate), now);

    if (ageInDays > LOG_ROTATION_DAYS) {
      const inputPath = `${LOGS_DIR}/${logFile}`;
      const outputPath = `${LOG_ARCHIVE_DIR}/${logFile}.gz`;

      await compressFile(inputPath, outputPath);

      // Verify integrity
      const checksum = await computeChecksum(outputPath);
      await fs.writeFile(`${LOG_ARCHIVE_DIR}/${logFile}.gz.sha256`, checksum);

      // Delete original
      await fs.unlink(inputPath);
    }
  }
}
```

**Benefits:**
- Memory-efficient (streaming)
- High compression ratio (~90% for JSON)
- Preserves file integrity

**Trade-offs:**
- Slower than in-memory compression
- Requires extra disk space during compression
- Decompression needed for queries

---

## Anti-Pattern: Logging Secrets

**NEVER DO THIS:**

```javascript
// BAD: Logging API key
await logAction(
  { type: 'agent', name: 'lex' },
  { type: 'api_call', verb: 'POST' },
  { type: 'external_api', id: 'sendgrid' },
  { status: 'success' },
  { api_key: process.env.SENDGRID_API_KEY } // ❌ Secret exposed in logs!
);
```

**Why it's bad:**
- Secrets exposed in plaintext logs
- Logs may be backed up or forwarded insecurely
- Compliance violation (PCI-DSS, HIPAA)

**Correct approach:**

```javascript
// GOOD: Reference secret, don't log value
await logAction(
  { type: 'agent', name: 'lex' },
  { type: 'api_call', verb: 'POST' },
  { type: 'external_api', id: 'sendgrid' },
  { status: 'success' },
  { api_key_ref: 'SENDGRID_API_KEY' } // ✅ Reference only
);
```

---

## Summary

These patterns provide:
- **Structured logging** with consistent schema
- **Efficient storage** via JSON Lines format
- **Date-based rotation** for easy querying
- **Integrity verification** via checksums
- **Performance optimization** with buffering
- **Privacy protection** via PII redaction
- **Distributed tracing** via trace IDs
- **Compression** for long-term storage

Use these patterns as building blocks for robust audit logging.
