# Gotchas and Edge Cases for Audit Log Writer

## 1. Concurrent Writes to Same Log File

**Problem:**
Multiple agents write to the same daily log file simultaneously, potentially causing interleaved writes or corruption.

```javascript
// Agent A writes: {"timestamp":"2025-01-15T10:00:00.000Z",...}
// Agent B writes: {"timestamp":"2025-01-15T10:00:00.001Z",...}
// Result: {"timestamp":"2025-01-15T10:00:00{"timestamp":"2025-01-15T10:00:00.001Z",...}
```

**Impact:**
- Corrupted log entries (invalid JSON)
- Lost log entries
- Unable to parse log file

**Mitigation:**

1. **Use append mode with O_APPEND flag:**
   ```javascript
   // Atomic append (OS-level guarantee)
   await fs.appendFile(logPath, jsonLine, { flag: 'a' });
   ```

2. **File locking (for network filesystems):**
   ```javascript
   const lockfile = require('proper-lockfile');

   async function appendWithLock(logPath, entry) {
     let release;
     try {
       release = await lockfile.lock(logPath, { stale: 5000 });
       await fs.appendFile(logPath, JSON.stringify(entry) + '\n', { flag: 'a' });
     } finally {
       if (release) await release();
     }
   }
   ```

3. **Buffered writes with single writer:**
   ```javascript
   class SingleWriterLogger {
     constructor() {
       this.writeQueue = [];
       this.isWriting = false;
     }

     async log(entry) {
       this.writeQueue.push(entry);
       await this.processQueue();
     }

     async processQueue() {
       if (this.isWriting) return;
       this.isWriting = true;

       while (this.writeQueue.length > 0) {
         const entries = this.writeQueue.splice(0, 100); // Batch
         const lines = entries.map(e => JSON.stringify(e)).join('\n') + '\n';
         await fs.appendFile(getCurrentLogPath(), lines, { flag: 'a' });
       }

       this.isWriting = false;
     }
   }
   ```

---

## 2. Clock Skew Causing Out-of-Order Timestamps

**Problem:**
Agents on different machines have different system clocks, causing log entries to appear out of chronological order.

```javascript
// Agent A (clock 5 minutes ahead): timestamp = "2025-01-15T10:05:00.000Z"
// Agent B (correct time):          timestamp = "2025-01-15T10:00:00.000Z"
// Logs appear in wrong order when sorted by timestamp
```

**Impact:**
- Misleading timeline in logs
- Difficulty correlating events
- Incorrect time-based queries

**Mitigation:**

1. **Use NTP for time synchronization:**
   ```bash
   # Install and enable NTP
   sudo apt-get install ntp
   sudo systemctl enable ntp
   sudo systemctl start ntp

   # Verify sync status
   timedatectl status
   ```

2. **Fetch server time for critical logs:**
   ```javascript
   const ntpClient = require('ntp-client');

   async function getServerTime() {
     return new Promise((resolve, reject) => {
       ntpClient.getNetworkTime('pool.ntp.org', 123, (err, date) => {
         if (err) reject(err);
         else resolve(date);
       });
     });
   }

   // Use server time for log entries
   const serverTime = await getServerTime();
   const entry = {
     timestamp: serverTime.toISOString(),
     // ... rest of entry
   };
   ```

3. **Sort by trace_id + sequence number:**
   ```javascript
   const entry = {
     timestamp: new Date().toISOString(),
     trace_id: parentTraceId,
     sequence: stepNumber, // 1, 2, 3...
     // ... rest of entry
   };

   // Query and sort by sequence
   const logs = await queryLogs({ trace_id: parentTraceId });
   logs.sort((a, b) => a.sequence - b.sequence);
   ```

---

## 3. Disk Full During Log Write

**Problem:**
Log write fails due to disk full (ENOSPC error), potentially losing log entries.

```javascript
// Write attempt
await fs.appendFile(logPath, jsonLine, { flag: 'a' });
// Error: ENOSPC: no space left on device
```

**Impact:**
- Lost log entries (not written to disk)
- Application may crash if not handled
- Audit trail incomplete

**Mitigation:**

1. **Graceful degradation:**
   ```javascript
   async function appendLogEntry(logPath, entry) {
     try {
       const jsonLine = JSON.stringify(entry) + '\n';
       await fs.appendFile(logPath, jsonLine, { flag: 'a' });
     } catch (err) {
       if (err.code === 'ENOSPC') {
         // Disk full; log to stderr and continue
         console.error('CRITICAL: Disk full; cannot write logs');
         console.error('Lost log entry:', entry);

         // Alert admin
         await notifyAdmin({
           type: 'disk_full',
           message: 'Logs cannot be written; disk full',
           severity: 'critical'
         });

         // Don't throw (allow application to continue)
         return;
       }
       throw err; // Re-throw other errors
     }
   }
   ```

2. **Monitor disk usage:**
   ```javascript
   const diskusage = require('diskusage');

   async function checkDiskUsage() {
     const info = await diskusage.check(LOGS_DIR);
     const usagePercent = (1 - info.available / info.total) * 100;

     if (usagePercent > 90) {
       console.warn(`Disk usage high: ${usagePercent.toFixed(1)}%`);

       // Trigger early rotation
       await rotateLogs();

       // Alert admin
       await notifyAdmin({
         type: 'disk_usage_high',
         usage_percent: usagePercent,
         available_bytes: info.available
       });
     }
   }

   // Check every hour
   setInterval(checkDiskUsage, 3600000);
   ```

3. **Automatic cleanup on disk full:**
   ```javascript
   async function emergencyCleanup() {
     console.warn('Emergency cleanup triggered due to disk space');

     // Compress uncompressed logs immediately
     await compressOldLogs();

     // Delete logs older than retention policy
     await deleteExpiredLogs();

     // If still full, delete oldest archives
     const archives = (await fs.readdir(LOG_ARCHIVE_DIR))
       .filter(f => f.endsWith('.gz'))
       .sort(); // Oldest first

     for (const archive of archives.slice(0, 10)) {
       await fs.unlink(`${LOG_ARCHIVE_DIR}/${archive}`);
       console.log(`Deleted archive: ${archive}`);
     }
   }
   ```

---

## 4. Log File Corruption (Partial Write)

**Problem:**
Application crashes mid-write, leaving incomplete JSON line in log file.

```json
{"timestamp":"2025-01-15T10:00:00.000Z","trace_id":"abc123","actor":{"type":"agent","name
```

**Impact:**
- Log parsing fails for entire file
- Cannot read subsequent entries
- Integrity check fails

**Mitigation:**

1. **Skip corrupted lines during parsing:**
   ```javascript
   async function readLogEntries(logPath) {
     const content = await fs.readFile(logPath, 'utf-8');
     const lines = content.split('\n');
     const entries = [];

     for (let i = 0; i < lines.length; i++) {
       const line = lines[i].trim();
       if (!line) continue;

       try {
         entries.push(JSON.parse(line));
       } catch (err) {
         console.warn(`Corrupted log entry at line ${i + 1}: ${err.message}`);
         console.warn(`Line content: ${line.substring(0, 100)}...`);
         // Skip corrupted line; continue parsing
       }
     }

     return entries;
   }
   ```

2. **Repair corrupted log files:**
   ```javascript
   async function repairLogFile(logPath) {
     const content = await fs.readFile(logPath, 'utf-8');
     const lines = content.split('\n');
     const validLines = [];

     for (const line of lines) {
       const trimmed = line.trim();
       if (!trimmed) continue;

       try {
         JSON.parse(trimmed); // Test parse
         validLines.push(trimmed);
       } catch (err) {
         console.warn(`Removed corrupted line: ${trimmed.substring(0, 100)}...`);
       }
     }

     // Write repaired file
     const repairedPath = `${logPath}.repaired`;
     await fs.writeFile(repairedPath, validLines.join('\n') + '\n');

     console.log(`Repaired log: ${logPath} → ${repairedPath}`);
     console.log(`Removed ${lines.length - validLines.length} corrupted lines`);
   }
   ```

3. **Atomic writes with temp file:**
   ```javascript
   async function atomicAppend(logPath, entry) {
     const jsonLine = JSON.stringify(entry) + '\n';
     const tempPath = `${logPath}.tmp.${process.pid}`;

     // Write to temp file
     await fs.writeFile(tempPath, jsonLine);

     // Append temp file to log file
     const tempContent = await fs.readFile(tempPath);
     await fs.appendFile(logPath, tempContent, { flag: 'a' });

     // Delete temp file
     await fs.unlink(tempPath);
   }
   ```

---

## 5. Race Condition in Log Rotation

**Problem:**
Log rotation job runs while logs are being written, causing file conflicts.

```
Time  | Writer Thread          | Rotation Thread
------|------------------------|------------------
T0    | Write to 2025-01-15.json |
T1    |                        | Move 2025-01-15.json → archive/
T2    | Write to 2025-01-15.json | (File doesn't exist!)
```

**Impact:**
- Write fails (file moved during write)
- Lost log entries
- Rotation incomplete

**Mitigation:**

1. **Lock file during rotation:**
   ```javascript
   const lockfile = require('proper-lockfile');

   async function rotateLogs() {
     const logFiles = (await fs.readdir(LOGS_DIR)).filter(f => f.endsWith('.json'));

     for (const logFile of logFiles) {
       const logPath = `${LOGS_DIR}/${logFile}`;
       const ageInDays = getLogAge(logFile);

       if (ageInDays > LOG_ROTATION_DAYS) {
         // Lock file before rotation
         let release;
         try {
           release = await lockfile.lock(logPath, { stale: 10000 });

           // Perform rotation
           await compressFile(logPath, `${LOG_ARCHIVE_DIR}/${logFile}.gz`);
           await fs.unlink(logPath);

         } finally {
           if (release) await release();
         }
       }
     }
   }
   ```

2. **Rotate only old files (not current day):**
   ```javascript
   async function rotateLogs() {
     const today = new Date().toISOString().split('T')[0];
     const logFiles = (await fs.readdir(LOGS_DIR)).filter(f => {
       // Skip today's log file
       return f.endsWith('.json') && !f.startsWith(today);
     });

     for (const logFile of logFiles) {
       const ageInDays = getLogAge(logFile);
       if (ageInDays > LOG_ROTATION_DAYS) {
         await compressAndArchive(logFile);
       }
     }
   }
   ```

3. **Graceful file not found handling:**
   ```javascript
   async function appendLogEntry(logPath, entry) {
     try {
       await fs.appendFile(logPath, JSON.stringify(entry) + '\n', { flag: 'a' });
     } catch (err) {
       if (err.code === 'ENOENT') {
         // File moved during rotation; create new file
         await fs.mkdir(path.dirname(logPath), { recursive: true });
         await fs.appendFile(logPath, JSON.stringify(entry) + '\n', { flag: 'a' });
       } else {
         throw err;
       }
     }
   }
   ```

---

## 6. Missing Log Entries After Crash

**Problem:**
Application crashes before buffered log entries are flushed to disk.

```javascript
// Buffered entries in memory
buffer = [entry1, entry2, entry3];

// Application crashes (SIGKILL)
// Entries lost (never written to disk)
```

**Impact:**
- Lost log entries (audit trail incomplete)
- Missing evidence for debugging
- Compliance violation (incomplete audit log)

**Mitigation:**

1. **Flush on critical events:**
   ```javascript
   class BufferedLogger {
     async log(entry) {
       this.buffer.push(entry);

       // Flush immediately for critical events
       if (entry.result?.status === 'error' || entry.action?.category === 'security') {
         await this.flush();
       }

       // Otherwise, flush when buffer full or on timer
       if (this.buffer.length >= this.bufferSize) {
         await this.flush();
       }
     }

     async flush() {
       if (this.buffer.length === 0) return;

       const entries = this.buffer.splice(0);
       const lines = entries.map(e => JSON.stringify(e)).join('\n') + '\n';
       await fs.appendFile(getCurrentLogPath(), lines, { flag: 'a' });
     }
   }
   ```

2. **Graceful shutdown handler:**
   ```javascript
   const logger = new BufferedLogger();

   // Flush on shutdown signals
   process.on('SIGTERM', async () => {
     console.log('Received SIGTERM; flushing logs...');
     await logger.flush();
     process.exit(0);
   });

   process.on('SIGINT', async () => {
     console.log('Received SIGINT; flushing logs...');
     await logger.flush();
     process.exit(0);
   });

   // Flush on uncaught exception
   process.on('uncaughtException', async (err) => {
     console.error('Uncaught exception:', err);
     await logger.flush();
     process.exit(1);
   });
   ```

3. **Reduce buffer size (trade performance for durability):**
   ```javascript
   // Small buffer (flush more frequently)
   const logger = new BufferedLogger({
     bufferSize: 10,          // Flush every 10 entries
     flushIntervalMs: 1000    // Flush every 1 second
   });
   ```

---

## 7. PII Detection False Positives

**Problem:**
PII detection regex flags non-sensitive data as PII, causing over-redaction.

```javascript
// False positive: email-like string in code
const code = "function sendEmail(to@example.com) { ... }";

// After redaction
const redacted = "function sendEmail([EMAIL_REDACTED]) { ... }";
```

**Impact:**
- Loss of useful debugging information
- False sense of security (real PII may not be detected)

**Mitigation:**

1. **Context-aware redaction:**
   ```javascript
   function redactPII(text, context) {
     // Don't redact in code blocks
     if (context === 'code') {
       return text;
     }

     // Don't redact email domains (keep for debugging)
     if (context === 'email_domain') {
       return text.replace(/([^@]+)@/, '[EMAIL_REDACTED]@');
     }

     // Full redaction for user data
     return text.replace(PII_PATTERNS.email, '[EMAIL_REDACTED]');
   }
   ```

2. **Allowlist known non-sensitive patterns:**
   ```javascript
   const SAFE_PATTERNS = {
     email: [
       'noreply@example.com',
       'test@test.com',
       /.*@localhost$/,
       /.*@example\.(com|org)$/
     ]
   };

   function shouldRedact(value, type) {
     const safePatterns = SAFE_PATTERNS[type] || [];

     for (const pattern of safePatterns) {
       if (pattern instanceof RegExp && pattern.test(value)) {
         return false;
       }
       if (pattern === value) {
         return false;
       }
     }

     return true;
   }
   ```

3. **Configurable redaction (opt-in for sensitive fields only):**
   ```javascript
   const REDACT_FIELDS = [
     'actor.email',
     'details.phone',
     'details.ssn',
     'details.credit_card'
   ];

   function redactLogEntry(entry) {
     const redacted = { ...entry };

     for (const field of REDACT_FIELDS) {
       const value = getNestedValue(redacted, field);
       if (value) {
         setNestedValue(redacted, field, '[REDACTED]');
       }
     }

     return redacted;
   }
   ```

---

## 8. Log Injection Attacks

**Problem:**
Attacker injects malicious data into log entry, potentially exploiting log analysis tools.

```javascript
// Attacker-controlled input
const userInput = 'alice\n{"timestamp":"2025-01-15T10:00:00.000Z","actor":{"type":"human","name":"attacker"},...}';

// Log entry
await logAction(
  { type: 'human', name: userInput }, // ❌ Logs two entries!
  { type: 'login', verb: 'POST' },
  { type: 'user', id: 'alice' },
  { status: 'success' }
);
```

**Impact:**
- Forged log entries
- Log parsing errors
- Security audit compromise

**Mitigation:**

1. **Escape newlines in user input:**
   ```javascript
   function escapeLogInjection(text) {
     return text
       .replace(/\n/g, '\\n')
       .replace(/\r/g, '\\r')
       .replace(/\t/g, '\\t');
   }

   function sanitizeLogEntry(entry) {
     // Recursively escape strings
     function escapeStrings(obj) {
       if (typeof obj === 'string') {
         return escapeLogInjection(obj);
       }
       if (Array.isArray(obj)) {
         return obj.map(escapeStrings);
       }
       if (obj && typeof obj === 'object') {
         const escaped = {};
         for (const [key, value] of Object.entries(obj)) {
           escaped[key] = escapeStrings(value);
         }
         return escaped;
       }
       return obj;
     }

     return escapeStrings(entry);
   }
   ```

2. **Validate log entry structure:**
   ```javascript
   function validateLogEntry(entry) {
     // Ensure entry is a single object (not array)
     if (Array.isArray(entry)) {
       throw new Error('Log entry must be object, not array');
     }

     // Ensure no nested log entries
     const stringified = JSON.stringify(entry);
     const nestedLogPattern = /"timestamp":\s*"[^"]+",\s*"trace_id":/g;
     const matches = stringified.match(nestedLogPattern);

     if (matches && matches.length > 1) {
       throw new Error('Nested log entries detected (possible injection)');
     }

     return true;
   }
   ```

3. **Use structured logging (don't concatenate strings):**
   ```javascript
   // BAD: String concatenation
   const message = `User ${userName} performed ${action}`; // ❌ Injection risk

   // GOOD: Structured fields
   const entry = {
     message: 'User performed action',
     details: {
       user: userName,
       action: action
     }
   };
   ```

---

## Summary

Key gotchas to watch for:
1. **Concurrent writes** - Use atomic append (O_APPEND)
2. **Clock skew** - Use NTP, add sequence numbers
3. **Disk full** - Monitor usage, graceful degradation
4. **Corruption** - Skip corrupted lines, atomic writes
5. **Rotation race** - Lock files, rotate old files only
6. **Lost entries** - Flush on critical events, graceful shutdown
7. **False positives** - Context-aware redaction, allowlists
8. **Log injection** - Escape newlines, validate structure

Each gotcha has mitigation strategies; choose based on your risk tolerance and operational requirements.
