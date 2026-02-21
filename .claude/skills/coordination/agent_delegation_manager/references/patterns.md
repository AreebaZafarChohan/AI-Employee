# Design Patterns for Agent Delegation Manager

## Pattern: Signal-Based Async Coordination

**Problem:** lex and cex run in different execution contexts (local vs cloud) with no direct communication channel.

**Solution:** Use signal files as message passing mechanism:
- Signal files written to `.signals/` directory
- Cloud sync tool (Dropbox, rsync, git) replicates signals between environments
- Agents poll signal directories for new messages
- Claim-by-move semantics prevent race conditions

**Implementation:**
```javascript
// lex: Create delegation signal
async function delegateTaskToCloud(taskId) {
  const signalPath = `${SIGNALS_DIR_LOCAL}/${taskId}.delegate.json`;
  const signal = {
    signal_type: "delegation_request",
    task_id: taskId,
    from_agent: "lex",
    to_agent: "cex",
    created_at: new Date().toISOString(),
    timeout_at: new Date(Date.now() + DELEGATION_TIMEOUT_MS).toISOString(),
    request: { action: "plan_task", task_path: `Needs_Action/${taskId}.json` }
  };

  await writeFileAtomic(signalPath, JSON.stringify(signal, null, 2));
  return signalPath;
}

// cex: Poll and claim signal
async function pollForDelegationRequests() {
  const signals = await listFiles(SIGNALS_DIR_CLOUD, "*.delegate.json");

  for (const signalPath of signals) {
    try {
      // Attempt to claim by moving to processing directory
      const claimPath = signalPath.replace(".delegate.json", ".processing.json");
      await moveFileAtomic(signalPath, claimPath);

      // Successfully claimed! Process the delegation
      const signal = await readFile(claimPath);
      await processDelegation(signal);

    } catch (err) {
      // Another agent claimed it first; try next signal
      if (err.code === "ENOENT") continue;
      throw err;
    }
  }
}
```

**Benefits:**
- No network infrastructure required
- Atomic operations via filesystem guarantees
- Natural queueing via directory listing
- Crash-resistant (signals persist across restarts)

**Trade-offs:**
- Latency depends on sync tool refresh rate
- Not suitable for real-time coordination
- Signal file cleanup required

---

## Pattern: Sync Policy as Metadata

**Problem:** Some files contain secrets and must never leave local environment, but metadata needs to be visible for coordination.

**Solution:** Embed sync policy in file metadata; enforce at delegation boundaries:
```json
{
  "task_id": "task-123",
  "title": "Deploy API service",
  "sync_policy": "local_only",
  "created_by": "lex",
  "content": {
    "api_key": "${API_KEY_FROM_ENV}",
    "deployment_steps": [...]
  }
}
```

**Enforcement Points:**

1. **At delegation time** (lex):
   ```javascript
   function canDelegateToCloud(task) {
     if (task.sync_policy === "local_only") {
       return { allowed: false, reason: "Task contains local-only data" };
     }
     return { allowed: true };
   }
   ```

2. **At sync time** (Dropbox/rsync):
   ```bash
   # .dropboxignore or rsync filter
   # Exclude files marked as local-only
   **/local_only_marker.*
   ```

3. **At read time** (cex):
   ```javascript
   function readTaskContent(taskId, agentName) {
     const task = readTaskMetadata(taskId);

     if (agentName === "cex" && task.sync_policy === "local_only") {
       // Sanitize: return metadata only, no content
       return {
         task_id: task.task_id,
         title: task.title,
         sync_policy: "local_only",
         message: "Content restricted to local execution"
       };
     }

     return task;
   }
   ```

**Benefits:**
- Explicit security boundaries
- Self-documenting file restrictions
- Programmatically enforceable
- No reliance on filename patterns

**Trade-offs:**
- Requires metadata parsing before access
- Metadata itself must be trusted (tamper-proof)

---

## Pattern: Timeout-Based Cleanup

**Problem:** Signal files can become orphaned if:
- cex crashes before responding
- Sync layer fails
- Clock skew causes timestamp mismatch

**Solution:** Embed timeout in signal metadata; lex cleans up expired signals:

```javascript
// lex: Create signal with timeout
const signal = {
  signal_type: "delegation_request",
  task_id: taskId,
  created_at: new Date().toISOString(),
  timeout_at: new Date(Date.now() + DELEGATION_TIMEOUT_MS).toISOString(),
  // ... rest of signal
};

// lex: Periodic cleanup job
async function cleanupExpiredSignals() {
  const now = new Date();
  const signals = await listFiles(SIGNALS_DIR_LOCAL, "*.delegate.json");

  for (const signalPath of signals) {
    const signal = await readFile(signalPath);
    const timeoutAt = new Date(signal.timeout_at);

    if (now > timeoutAt) {
      console.warn(`Signal ${signal.task_id} expired; deleting`);
      await deleteFile(signalPath);

      // Log timeout event for monitoring
      await appendToLog("delegation_timeouts.log", {
        task_id: signal.task_id,
        expired_at: now.toISOString(),
        reason: "timeout"
      });
    }
  }
}

// Run cleanup every 60 seconds
setInterval(cleanupExpiredSignals, 60000);
```

**Benefits:**
- Prevents signal file accumulation
- Provides observability (timeout logs)
- Self-healing (no manual intervention needed)

**Trade-offs:**
- Relies on accurate system clocks
- Timeout must be tuned to sync latency

---

## Pattern: Claim-by-Move for Coordination

**Problem:** Multiple agents might try to process same signal concurrently.

**Solution:** Use atomic file rename to claim ownership:

```javascript
// Agent attempts to claim signal
async function claimSignal(signalPath) {
  const claimPath = signalPath.replace(/\.json$/, ".claimed.json");

  try {
    // Atomic rename; only one agent succeeds
    await fs.rename(signalPath, claimPath);
    return { success: true, claimedPath: claimPath };

  } catch (err) {
    if (err.code === "ENOENT") {
      // Another agent claimed it first
      return { success: false, reason: "already_claimed" };
    }
    throw err; // Unexpected error
  }
}

// Usage
const result = await claimSignal(signalPath);
if (result.success) {
  const signal = await readFile(result.claimedPath);
  await processSignal(signal);
  await deleteFile(result.claimedPath); // Cleanup after processing
} else {
  console.log(`Signal already claimed by another agent`);
}
```

**Benefits:**
- Atomic operation (POSIX filesystem guarantee)
- No coordination protocol needed
- Works across different agent instances
- Natural conflict resolution (first claimer wins)

**Trade-offs:**
- Requires writable filesystem
- Not suitable for network filesystems with weak consistency (e.g., NFS)

---

## Pattern: Secret Detection with Whitelisting

**Problem:** Automatically detect secrets in task content without false positives.

**Solution:** Multi-stage detection with whitelist overrides:

```javascript
// Stage 1: Pattern matching
const SECRET_PATTERNS = [
  /API[_-]?KEY/i,
  /SECRET[_-]?TOKEN/i,
  /PASSWORD/i,
  /CREDENTIALS/i,
  /PRIVATE[_-]?KEY/i,
  /\b[A-Za-z0-9]{32,}\b/  // Long random strings
];

// Stage 2: Whitelist (known safe patterns)
const WHITELIST_PATTERNS = [
  /PUBLIC_KEY/i,
  /TEST_API_KEY/i,
  /EXAMPLE_SECRET/i
];

function detectSecrets(content) {
  const contentStr = JSON.stringify(content);

  // Check whitelist first
  for (const pattern of WHITELIST_PATTERNS) {
    if (pattern.test(contentStr)) {
      // Known safe pattern; skip
      continue;
    }
  }

  // Check for secret patterns
  for (const pattern of SECRET_PATTERNS) {
    if (pattern.test(contentStr)) {
      return {
        hasSecrets: true,
        matchedPattern: pattern.toString(),
        recommendation: "local_only"
      };
    }
  }

  return { hasSecrets: false };
}

// Stage 3: User override (explicit annotation)
function createTask(content, userAnnotation = {}) {
  const detection = detectSecrets(content);

  // User can explicitly override
  const syncPolicy = userAnnotation.sync_policy
    || (detection.hasSecrets ? "local_only" : "sync");

  return {
    ...content,
    sync_policy: syncPolicy,
    secret_detection: {
      detected: detection.hasSecrets,
      overridden: !!userAnnotation.sync_policy
    }
  };
}
```

**Benefits:**
- Automated security (default-safe)
- Escape hatch for false positives (whitelist)
- User can override (explicit control)
- Auditable (logs detection results)

**Trade-offs:**
- False positives possible (overly cautious)
- Regex patterns require maintenance
- Can't detect semantic secrets (e.g., "set password to admin123")

---

## Pattern: Approval Sync with Signature Validation

**Problem:** Approval decisions made in cloud vault must be trusted before syncing to local vault.

**Solution:** Approval signals include human signature (timestamp + user ID); validate before applying:

```javascript
// cex: Create approval signal when human approves
async function createApprovalSignal(taskId, decision, humanUser) {
  const signal = {
    signal_type: "approval_sync",
    task_id: taskId,
    from_agent: "human",
    to_agent: "lex",
    created_at: new Date().toISOString(),
    approval: {
      decision: decision, // "approved" | "rejected"
      reason: "Human approved via cloud vault",
      approved_by: humanUser,
      task_path: `Approved/${taskId}.json`,
      sync_policy: "sync"
    },
    signature: {
      user: humanUser,
      timestamp: new Date().toISOString(),
      // Optional: HMAC signature for tamper-proofing
      hmac: computeHMAC(taskId + decision + humanUser)
    }
  };

  await writeFile(`${SIGNALS_DIR_CLOUD}/${taskId}.approval.json`, signal);
}

// lex: Validate and apply approval
async function syncApproval(signalPath) {
  const signal = await readFile(signalPath);

  // Validate signature
  if (!signal.signature || !signal.signature.user) {
    throw new Error("Approval signal missing signature");
  }

  // Optional: Verify HMAC (if configured)
  if (ENABLE_APPROVAL_HMAC) {
    const expectedHMAC = computeHMAC(
      signal.task_id + signal.approval.decision + signal.signature.user
    );
    if (signal.signature.hmac !== expectedHMAC) {
      throw new Error("Approval signature invalid (HMAC mismatch)");
    }
  }

  // Validate timestamp (not too old)
  const signatureAge = Date.now() - new Date(signal.signature.timestamp).getTime();
  if (signatureAge > APPROVAL_MAX_AGE_MS) {
    throw new Error(`Approval signature expired (age: ${signatureAge}ms)`);
  }

  // Apply approval to local vault
  const task = await readTaskFile(signal.task_id);
  task.approval = signal.approval;

  const targetFolder = signal.approval.decision === "approved"
    ? "Approved"
    : "Rejected";

  await moveFile(
    `Pending_Approval/${signal.task_id}.json`,
    `${targetFolder}/${signal.task_id}.json`
  );

  // Log approval event
  await appendToLog("approvals.log", {
    task_id: signal.task_id,
    decision: signal.approval.decision,
    approved_by: signal.signature.user,
    synced_at: new Date().toISOString()
  });

  // Cleanup signal
  await deleteFile(signalPath);
}
```

**Benefits:**
- Tamper-resistant (HMAC signature)
- Time-bounded (approval expiration)
- Auditable (logs all approvals)
- Trustworthy (validates before applying)

**Trade-offs:**
- Requires shared secret for HMAC (if enabled)
- Clock skew can cause false rejections
- Signature validation adds latency

---

## Pattern: Info Request with Safe Redaction

**Problem:** cex needs information from local environment (e.g., "what's the production API URL?") but must not receive secrets.

**Solution:** Info request protocol with safe-data filtering:

```javascript
// cex: Request information from lex
async function requestLocalInfo(taskId, infoType, query) {
  const signal = {
    signal_type: "info_request",
    task_id: taskId,
    from_agent: "cex",
    to_agent: "lex",
    created_at: new Date().toISOString(),
    request: {
      info_type: infoType, // "env_var" | "file_metadata" | "secret_reference"
      query: query,
      required_for: "Planning task execution"
    }
  };

  await writeFile(`${SIGNALS_DIR_CLOUD}/${taskId}.info_request.json`, signal);

  // Wait for response (with timeout)
  return await waitForSignal(`${SIGNALS_DIR_CLOUD}/${taskId}.info_response.json`, 10000);
}

// lex: Respond to info request
async function handleInfoRequest(signalPath) {
  const signal = await readFile(signalPath);

  let response;

  switch (signal.request.info_type) {
    case "env_var":
      response = handleEnvVarRequest(signal.request.query);
      break;
    case "file_metadata":
      response = handleFileMetadataRequest(signal.request.query);
      break;
    case "secret_reference":
      response = handleSecretReferenceRequest(signal.request.query);
      break;
    default:
      response = { error: "Unknown info_type" };
  }

  // Write response signal
  const responseSignal = {
    signal_type: "info_response",
    task_id: signal.task_id,
    from_agent: "lex",
    to_agent: "cex",
    created_at: new Date().toISOString(),
    in_response_to: signalPath,
    response: response
  };

  await writeFile(
    `${SIGNALS_DIR_LOCAL}/${signal.task_id}.info_response.json`,
    responseSignal
  );

  // Cleanup request
  await deleteFile(signalPath);
}

// Safe handlers
function handleEnvVarRequest(varName) {
  const SAFE_VARS = ["NODE_ENV", "API_URL", "LOG_LEVEL"];

  if (!SAFE_VARS.includes(varName)) {
    return {
      error: "Variable not in safe list",
      allowed_vars: SAFE_VARS
    };
  }

  return {
    var_name: varName,
    var_value: process.env[varName] || null
  };
}

function handleSecretReferenceRequest(secretName) {
  // Never return secret value; return reference name only
  const SECRET_MAP = {
    "production_api_key": "USE_PROD_API_KEY_FROM_LOCAL_ENV",
    "database_password": "USE_DB_PASSWORD_FROM_LOCAL_ENV"
  };

  return {
    secret_name: secretName,
    reference: SECRET_MAP[secretName] || "SECRET_NOT_FOUND",
    instruction: "Reference this in your plan; lex will substitute at runtime"
  };
}
```

**Benefits:**
- Explicit allow-list for safe data
- Never leaks secrets
- Structured request/response format
- Timeout protection

**Trade-offs:**
- Adds round-trip latency
- Requires maintaining safe-data allow-list
- Can't handle dynamic queries (fixed set of info types)

---

## Anti-Pattern: Direct Secret Transmission

**NEVER DO THIS:**

```javascript
// BAD: Sending secret to cloud
async function delegateTaskToCloud(taskId) {
  const task = await readTaskFile(taskId);

  const signal = {
    task_id: taskId,
    task_content: task, // ❌ Contains secrets!
    api_key: process.env.API_KEY // ❌ Direct secret transmission!
  };

  await writeFile(`${SIGNALS_DIR_LOCAL}/${taskId}.delegate.json`, signal);
}
```

**Why it's bad:**
- Secrets written to Dropbox/cloud storage
- Violates security boundary
- Can't be revoked easily
- Audit trail shows secret in plaintext

**Correct approach:**

```javascript
// GOOD: Redact secrets before delegation
async function delegateTaskToCloud(taskId) {
  const task = await readTaskFile(taskId);

  // Check sync policy
  if (task.sync_policy === "local_only") {
    throw new Error("Cannot delegate local-only task");
  }

  // Sanitize: remove sensitive fields
  const sanitizedTask = {
    task_id: task.task_id,
    title: task.title,
    description: task.description,
    // Omit: api_key, secrets, credentials
  };

  const signal = {
    task_id: taskId,
    task_summary: sanitizedTask, // ✅ No secrets
    instruction: "Plan this task; lex will provide secrets at execution"
  };

  await writeFile(`${SIGNALS_DIR_LOCAL}/${taskId}.delegate.json`, signal);
}
```

---

## Pattern: Sync Conflict Resolution

**Problem:** Local and cloud vaults can diverge if:
- Network partition during sync
- Concurrent edits in both environments
- Sync tool fails silently

**Solution:** Detect conflicts via version vectors; resolve via policy:

```javascript
// Embed version vector in task metadata
const task = {
  task_id: "task-123",
  title: "Deploy service",
  version: {
    local: 5,  // Incremented on each local edit
    cloud: 3,  // Incremented on each cloud edit
    last_sync: "2025-01-15T10:30:00Z"
  },
  // ... rest of task
};

// Detect conflict
function detectSyncConflict(localTask, cloudTask) {
  if (!localTask || !cloudTask) {
    return { conflict: false }; // One side missing (not a conflict)
  }

  const localVersion = localTask.version.local;
  const cloudVersion = cloudTask.version.cloud;
  const localCloudVersion = localTask.version.cloud;
  const cloudLocalVersion = cloudTask.version.local;

  // Check for divergence
  if (localVersion > cloudLocalVersion && cloudVersion > localCloudVersion) {
    return {
      conflict: true,
      reason: "Both sides modified since last sync",
      localVersion,
      cloudVersion
    };
  }

  return { conflict: false };
}

// Resolve conflict
async function resolveSyncConflict(localTask, cloudTask, policy) {
  const conflict = detectSyncConflict(localTask, cloudTask);

  if (!conflict.conflict) {
    return; // No conflict
  }

  switch (policy) {
    case "local_wins":
      await overwriteCloudTask(localTask);
      break;

    case "cloud_wins":
      await overwriteLocalTask(cloudTask);
      break;

    case "last_write_wins":
      const localModified = new Date(localTask.modified_at);
      const cloudModified = new Date(cloudTask.modified_at);
      if (localModified > cloudModified) {
        await overwriteCloudTask(localTask);
      } else {
        await overwriteLocalTask(cloudTask);
      }
      break;

    case "merge":
      const merged = mergeTaskFields(localTask, cloudTask);
      await overwriteBothTasks(merged);
      break;

    case "human_resolve":
      await createConflictMarker(localTask, cloudTask);
      await notifyHuman(`Sync conflict: ${localTask.task_id}`);
      break;

    default:
      throw new Error(`Unknown conflict policy: ${policy}`);
  }

  // Log conflict resolution
  await appendToLog("sync_conflicts.log", {
    task_id: localTask.task_id,
    resolved_at: new Date().toISOString(),
    policy,
    local_version: conflict.localVersion,
    cloud_version: conflict.cloudVersion
  });
}
```

**Benefits:**
- Explicit conflict detection
- Multiple resolution policies
- Auditable (logs all conflicts)
- Human escalation path

**Trade-offs:**
- Version vectors add overhead
- Requires conflict policy configuration
- Merge strategy can be complex

---

## Summary

These patterns provide:
- **Async coordination** via signal files
- **Security boundaries** via sync policies
- **Crash resilience** via timeouts and cleanup
- **Conflict resolution** via claim-by-move and version vectors
- **Secret protection** via redaction and validation

Use these patterns as building blocks for reliable local ↔ cloud agent coordination.
