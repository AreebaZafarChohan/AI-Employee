# Vault State Manager Gotchas

This document captures known issues, failure modes, and mitigation strategies for the Vault State Manager skill.

---

## Filesystem Gotchas

### Gotcha 1: Cross-Filesystem Moves Are Not Atomic

**Problem:**

If the vault spans multiple filesystems (e.g., vault root on SSD, but `Archive/` on HDD), `fs.rename()` will fail or fall back to copy+delete, which is NOT atomic.

**Symptoms:**
- Move operations fail with `EXDEV` error
- Partial moves leave duplicate files

**Mitigation:**

```javascript
async function atomicMove(src, dst) {
  try {
    await fs.rename(src, dst);
  } catch (err) {
    if (err.code === 'EXDEV') {
      // Cross-filesystem move: use copy+delete
      await fs.copyFile(src, dst);
      await fs.unlink(src);
      console.warn('Cross-filesystem move detected, using copy+delete');
    } else {
      throw err;
    }
  }
}
```

**Best Practice:** Keep entire vault on single filesystem.

---

### Gotcha 2: Network Filesystems Break Atomic Guarantees

**Problem:**

NFS, SMB/CIFS, and other network filesystems may NOT guarantee atomic renames, especially under concurrent access.

**Symptoms:**
- Race conditions during file moves
- Files appear twice (in both src and dst folders)
- Concurrent agents claim same file

**Mitigation:**

1. **Use file locks** (flock) if available:
```javascript
const lockfile = require('proper-lockfile');

async function claimWithLock(src, dst) {
  const release = await lockfile.lock(src);
  try {
    await fs.rename(src, dst);
  } finally {
    await release();
  }
}
```

2. **Avoid network filesystems** for vault (use local storage)

3. **Run only one agent** if network filesystem required

---

### Gotcha 3: Windows File Locking Behavior

**Problem:**

Windows locks open files, preventing renames or deletes. If an agent has a file open for reading, another agent cannot move it.

**Symptoms:**
- `EPERM` or `EBUSY` errors on Windows
- Works on Linux/Mac, fails on Windows

**Mitigation:**

```javascript
async function readFileQuickly(path) {
  // Read entire file, then immediately close handle
  const content = await fs.readFile(path, 'utf8');
  // File handle closed automatically
  return content;
}

// DON'T keep streams open
// const stream = fs.createReadStream(path);  // Holds lock
```

**Best Practice:** Always read entire file and close handle immediately.

---

### Gotcha 4: Case-Insensitive Filesystems (macOS, Windows)

**Problem:**

On macOS (default) and Windows, `file.json` and `File.json` are the same file. Plan ID collisions may not be detected.

**Symptoms:**
- Plan IDs appear unique but collide on case-insensitive FS
- File overwrites instead of conflict error

**Mitigation:**

```javascript
function normalizePlanId(id) {
  return id.toLowerCase();  // Enforce lowercase IDs
}

function generatePlanId() {
  // Use timestamp + random suffix (lowercase hex)
  const ts = Date.now();
  const rand = Math.random().toString(36).substring(2, 8);
  return `plan-${ts}-${rand}`.toLowerCase();
}
```

**Best Practice:** Always use lowercase IDs; never rely on case for uniqueness.

---

## Concurrency Gotchas

### Gotcha 5: TOCTOU Race (Time-of-Check to Time-of-Use)

**Problem:**

Checking if file exists, then moving it is NOT atomic. Another agent can claim file between check and move.

**Symptoms:**
- `FileNotFoundError` despite successful existence check
- Agent thinks file exists but move fails

**Broken Pattern:**
```javascript
// WRONG: Race condition
if (await fileExists(src)) {
  await moveFile(src, dst);  // May fail if another agent moved it
}
```

**Correct Pattern:**
```javascript
// CORRECT: Attempt move directly, handle failure
try {
  await moveFile(src, dst);
} catch (err) {
  if (err instanceof FileNotFoundError) {
    console.log('Already claimed by another agent');
  }
}
```

**Best Practice:** Never check-then-act; just act and handle errors.

---

### Gotcha 6: Stale File List

**Problem:**

Listing files returns a snapshot. By the time agent processes list, files may have moved.

**Symptoms:**
- Agent tries to process file that no longer exists
- `FileNotFoundError` after successful list

**Mitigation:**

```javascript
async function processAllPending() {
  const files = await listFolderFiles('Needs_Action');

  for (const file of files) {
    try {
      await claimAndProcess(file.name);
    } catch (err) {
      if (err instanceof FileNotFoundError) {
        // File claimed by another agent, skip
        continue;
      }
      throw err;
    }
  }
}
```

**Best Practice:** Always handle `FileNotFoundError` gracefully when processing lists.

---

### Gotcha 7: Multiple lex Instances

**Problem:**

Running multiple lex instances may cause conflicts if they process same work.

**Symptoms:**
- Duplicate plans created
- Concurrent execution of same action
- Resource conflicts (e.g., both try to send same email)

**Mitigation:**

1. **Bronze/Silver tier:** Only run ONE lex instance

2. **Gold/Platinum tier:** Use distributed locks or partition work:

```javascript
async function claimWithAgentId(file, agentId) {
  const claimed = `${file}-claimed-by-${agentId}`;

  try {
    // Try to create claim marker
    await fs.writeFile(claimed, agentId, { flag: 'wx' });  // Fail if exists
    await moveFile(file, dst);
    await fs.unlink(claimed);  // Clean up marker
  } catch (err) {
    if (err.code === 'EEXIST') {
      console.log('Already claimed by another lex instance');
    }
  }
}
```

**Best Practice:** Run single lex unless using distributed coordination.

---

## Data Integrity Gotchas

### Gotcha 8: Partial JSON Writes

**Problem:**

If process crashes during write, JSON file may be corrupted (incomplete).

**Symptoms:**
- `JSON.parse()` fails
- File contains partial data

**Mitigation:**

```javascript
async function writeJSONAtomic(path, data) {
  const tempPath = `${path}.tmp`;
  const content = JSON.stringify(data, null, 2);

  try {
    await fs.writeFile(tempPath, content, 'utf8');
    await fs.fsync(tempPath);  // Force flush to disk
    await fs.rename(tempPath, path);
  } catch (err) {
    await fs.unlink(tempPath).catch(() => {});
    throw err;
  }
}
```

**Best Practice:** Always write to temp file, fsync, then rename.

---

### Gotcha 9: Lost Updates

**Problem:**

Agent reads file, modifies it, writes back. If another agent writes in between, first agent's changes overwrite second's.

**Symptoms:**
- Status updates lost
- Progress resets unexpectedly

**Mitigation:**

```javascript
async function updateFileWithRetry(path, updateFn, maxRetries = 3) {
  let retries = 0;

  while (retries < maxRetries) {
    const { content, metadata } = await readVaultFile(path);
    const data = JSON.parse(content);
    const originalMtime = metadata.modified;

    // Apply updates
    const updated = updateFn(data);

    // Check if file changed since read
    const currentMtime = (await fs.stat(path)).mtime;
    if (currentMtime.getTime() !== originalMtime.getTime()) {
      // File changed, retry
      retries++;
      continue;
    }

    // Write atomically
    await writeVaultFile(path, JSON.stringify(updated, null, 2));
    return;
  }

  throw new Error('Max retries exceeded (concurrent updates)');
}
```

**Best Practice:** Use optimistic locking (check mtime before write).

---

### Gotcha 10: Filesystem Caching (Stale Reads)

**Problem:**

OS filesystem cache may return stale data if another process just wrote file.

**Symptoms:**
- Agent reads old version of file
- Status changes not visible immediately

**Mitigation:**

```javascript
// Force cache invalidation (Linux)
const fd = await fs.open(path, 'r');
await fs.fsync(fd);  // Flush cache
const content = await fs.readFile(fd, 'utf8');
await fs.close(fd);
```

Or wait briefly:
```javascript
await new Promise(resolve => setTimeout(resolve, 100));  // 100ms delay
const content = await fs.readFile(path, 'utf8');
```

**Best Practice:** If reading immediately after write by another agent, add small delay or flush cache.

---

## Permission Gotchas

### Gotcha 11: Container User Mismatch

**Problem:**

Container runs as user ID 1000, but vault owned by host user ID 1001. File permissions prevent writes.

**Symptoms:**
- `EACCES` (Permission denied) errors in Docker
- Works locally, fails in container

**Mitigation:**

1. **Match UIDs:** Run container as same UID as host:
```bash
docker run --user $(id -u):$(id -g) ...
```

2. **Fix ownership:** Chown vault to container user:
```bash
chown -R 1000:1000 /path/to/vault
```

3. **Use Docker volumes with correct permissions:**
```yaml
volumes:
  - ./vault:/vault:rw
```

**Best Practice:** Always match container user with vault ownership.

---

### Gotcha 12: Windows Permission Model

**Problem:**

Windows NTFS permissions differ from POSIX. Agents running as Windows service may lack file access.

**Symptoms:**
- `EPERM` on Windows
- Works when run manually, fails as service

**Mitigation:**

Grant "Full Control" to service account:
```powershell
icacls C:\vault /grant "NT AUTHORITY\NETWORK SERVICE:(OI)(CI)F" /T
```

**Best Practice:** Test agent as service, not just manual execution.

---

## Workflow Gotchas

### Gotcha 13: Human Forgets to Approve

**Problem:**

Plans stuck in `Pending_Approval/` because human doesn't check regularly.

**Symptoms:**
- Work halts
- Agent loops idle
- No progress

**Mitigation:**

1. **Alert on old pending plans:**
```javascript
async function checkStalePlans(maxAgeMinutes = 60) {
  const files = await listFolderFiles('Pending_Approval');
  const now = Date.now();

  for (const file of files) {
    const ageMinutes = (now - file.created.getTime()) / 60000;
    if (ageMinutes > maxAgeMinutes) {
      console.warn(`Plan stale: ${file.name} (age: ${ageMinutes}min)`);
      // Send notification to human
    }
  }
}
```

2. **Dashboard integration:** Show pending count prominently

**Best Practice:** Monitor `Pending_Approval/` and alert on stale items.

---

### Gotcha 14: Agent Permissions Violated

**Problem:**

lex accidentally writes to `Approved/`, violating AGENTS.md §3.

**Symptoms:**
- Security invariants broken
- Orchestrator processes unapproved actions

**Mitigation:**

```javascript
function canAgentWrite(agentName, folderPath) {
  const permissions = {
    'lex': ['Plans', 'In_Progress', 'Pending_Approval', 'Logs'],
    'cex': [],  // No writes allowed
    'orch': ['In_Progress', 'Done', 'Logs'],  // Only via moves
    'watcher-gmail': ['Needs_Action/emails', 'Logs'],
    'human': ['*']  // All folders
  };

  const allowed = permissions[agentName] || [];
  return allowed.includes('*') || allowed.some(p => folderPath.includes(p));
}

// Enforce before EVERY write
if (!canAgentWrite(agentName, targetPath)) {
  throw new PermissionError(`${agentName} cannot write to ${targetPath}`);
}
```

**Best Practice:** Enforce permissions in vault manager, not trust agents.

---

### Gotcha 15: Orchestrator Skips Approval

**Problem:**

Bug in code causes orchestrator to process files from `Pending_Approval/` instead of `Approved/`.

**Symptoms:**
- Actions execute without human approval
- Serious security issue

**Mitigation:**

1. **Strict folder checks:**
```javascript
async function orchestratorLoop() {
  // ONLY process Approved folder
  const files = await listFolderFiles('Approved');
  // ...
}
```

2. **Test unapproved plans are blocked:**
```javascript
// Unit test
it('should reject plans from Pending_Approval', async () => {
  await fs.writeFile('Pending_Approval/test.json', '{}');
  const files = await listFolderFiles('Approved');
  expect(files).not.toContainFile('test.json');
});
```

**Best Practice:** Never read from `Pending_Approval/` in orchestrator.

---

## Error Handling Gotchas

### Gotcha 16: Silent Failures

**Problem:**

Agent catches error but doesn't log it; failure goes unnoticed.

**Symptoms:**
- Work stops
- No errors visible
- Hard to debug

**Mitigation:**

```javascript
try {
  await processFile(file);
} catch (err) {
  // ALWAYS log before handling
  console.error('Failed to process file:', file, err);

  // Log to audit trail
  await appendLog('lex-errors.json', {
    timestamp: new Date().toISOString(),
    error: err.message,
    file: file,
    stack: err.stack
  });

  // Then decide: retry, skip, or escalate
  if (err instanceof PermissionError) {
    throw err;  // Escalate
  }
  // Skip file
}
```

**Best Practice:** Log ALL errors, even if handled.

---

### Gotcha 17: Error Messages Leak Paths

**Problem:**

Error messages include absolute paths, leaking filesystem structure.

**Example:**
```javascript
throw new Error(`File not found: /Users/john/vault/Plans/file.json`);
```

**Mitigation:**

```javascript
function sanitizeError(err, basePath) {
  let message = err.message;
  if (message.includes(basePath)) {
    message = message.replace(basePath, '<vault>');
  }
  return new Error(message);
}

try {
  await readVaultFile(path);
} catch (err) {
  throw sanitizeError(err, VAULT_PATH);
}
```

**Best Practice:** Always use relative paths in errors.

---

## Performance Gotchas

### Gotcha 18: Polling Too Frequently

**Problem:**

Agent polls `Needs_Action/` every 100ms, causing high CPU and disk I/O.

**Symptoms:**
- High CPU usage even when idle
- Disk constantly spinning
- Poor laptop battery life

**Mitigation:**

```javascript
const POLL_INTERVAL_MS = 5000;  // 5 seconds, not 100ms

async function pollLoop() {
  while (true) {
    await processNewFiles();
    await new Promise(resolve => setTimeout(resolve, POLL_INTERVAL_MS));
  }
}
```

**Best Practice:** Poll no more than once per 5 seconds.

---

### Gotcha 19: Log Files Grow Unbounded

**Problem:**

Append-only logs never rotated; disk fills up.

**Symptoms:**
- Out of disk space
- Writes fail with `ENOSPC`

**Mitigation:**

```javascript
async function rotateLogs(maxSizeMB = 100) {
  const logFiles = await listFolderFiles('Logs');

  for (const file of logFiles) {
    if (file.size > maxSizeMB * 1024 * 1024) {
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const archived = `${file.path}.${timestamp}.gz`;

      // Compress and archive
      await compressFile(file.path, archived);
      await fs.writeFile(file.path, '');  // Truncate log
    }
  }
}
```

**Best Practice:** Rotate logs daily or when exceeding size limit.

---

### Gotcha 20: Large File Reads Block Event Loop

**Problem:**

Synchronous read of large file (e.g., 10MB log) blocks Node.js event loop.

**Symptoms:**
- Agent becomes unresponsive
- Other operations delayed

**Mitigation:**

```javascript
// Stream large files
async function readLargeFile(path) {
  const stream = fs.createReadStream(path, { encoding: 'utf8' });
  let content = '';

  for await (const chunk of stream) {
    content += chunk;
    // Event loop can process other work between chunks
  }

  return content;
}
```

**Best Practice:** Stream files over 1MB; use `fs.readFile` for smaller files.

---

## Known Issues & Workarounds

### Issue 1: Cannot Detect Folder Deletions

**Problem:**

If human deletes a lifecycle folder (e.g., `Approved/`), agents fail silently.

**Workaround:**

Validate folder structure on startup:
```javascript
async function validateVaultStructure() {
  const required = [
    'Needs_Action', 'Plans', 'In_Progress',
    'Pending_Approval', 'Approved', 'Rejected',
    'Done', 'Updates', 'Logs', 'Archive'
  ];

  for (const folder of required) {
    const path = `${VAULT_PATH}/${folder}`;
    if (!await fs.pathExists(path)) {
      throw new Error(`Missing required folder: ${folder}`);
    }
  }
}
```

---

### Issue 2: No Deadlock Detection

**Problem:**

If two agents wait on each other's files, system deadlocks.

**Workaround:**

Implement timeout for claims:
```javascript
async function claimWithTimeout(src, dst, timeoutMs = 5000) {
  return Promise.race([
    moveFile(src, dst),
    new Promise((_, reject) =>
      setTimeout(() => reject(new Error('Claim timeout')), timeoutMs)
    )
  ]);
}
```

---

### Issue 3: No Transaction Support

**Problem:**

Multi-step workflows (move file A, write file B) are not atomic. If step 2 fails, step 1 is not rolled back.

**Workaround:**

Implement manual rollback:
```javascript
async function atomicWorkflow(file) {
  let claimed = false;

  try {
    await moveFile('Needs_Action', file, 'Plans', 'lex');
    claimed = true;

    await createPlanFromFile(file);
    // Success
  } catch (err) {
    if (claimed) {
      // Rollback: move back to Needs_Action
      await moveFile('Plans', file, 'Needs_Action', 'lex').catch(() => {
        console.error('Rollback failed, manual intervention needed');
      });
    }
    throw err;
  }
}
```

---

## Emergency Procedures

### Procedure 1: Agent Stuck in Infinite Loop

**Symptoms:** High CPU, no progress

**Steps:**
1. Create `HALT` file: `touch vault/Pending_Approval/HALT`
2. Agent should detect and halt
3. Review logs: `cat vault/Logs/lex-decisions.json | tail -50`
4. Fix issue, remove `HALT` file

---

### Procedure 2: Vault Corrupted

**Symptoms:** Files in wrong folders, orphaned temp files

**Steps:**
1. Stop all agents
2. Audit vault structure: `find vault -name '*.tmp'`
3. Clean temp files: `find vault -name '*.tmp' -delete`
4. Verify file integrity: `find vault -name '*.json' -exec jq . {} \;`
5. Manually move misplaced files
6. Restart agents

---

### Procedure 3: Disk Full

**Symptoms:** `ENOSPC` errors

**Steps:**
1. Check disk usage: `df -h /path/to/vault`
2. Archive old plans: `mv vault/Done/* vault/Archive/`
3. Compress logs: `gzip vault/Logs/*.json`
4. Increase disk quota or clean up Archive

---

## Summary

**Top 5 Gotchas to Remember:**

1. ✅ Always use atomic moves (not copy+delete)
2. ✅ Never check-then-act (TOCTOU race)
3. ✅ Enforce agent permissions in vault manager
4. ✅ Log all errors (even handled ones)
5. ✅ Poll reasonably (5s+, not 100ms)

**When in Doubt:**
- Read AGENTS.md §3 (jurisdictions)
- Read AGENTS.md §4 (vault protocol)
- Check logs: `vault/Logs/`
- Test locally before deploying
