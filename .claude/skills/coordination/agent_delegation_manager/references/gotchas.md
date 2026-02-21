# Gotchas and Edge Cases for Agent Delegation Manager

## 1. Clock Skew Between Local and Cloud

**Problem:**
Local machine and cloud environment may have different system times, causing timeout logic to fail:

```javascript
// lex (local) creates signal at 10:00:00 local time
const signal = {
  created_at: "2025-01-15T10:00:00.000Z", // Local clock
  timeout_at: "2025-01-15T10:05:00.000Z"  // +5 minutes
};

// cex (cloud) receives signal at 09:55:00 cloud time (5 min behind)
// cex thinks signal will timeout in 10 minutes, not 5
```

**Impact:**
- Signals may timeout prematurely or late
- Cleanup logic may delete active signals
- Response windows may be miscalculated

**Mitigation:**

1. **Use server time instead of local time:**
   ```javascript
   // Fetch server time from NTP or time API
   async function getServerTime() {
     const response = await fetch("https://worldtimeapi.org/api/timezone/Etc/UTC");
     const data = await response.json();
     return new Date(data.utc_datetime);
   }

   const signal = {
     created_at: (await getServerTime()).toISOString(),
     timeout_at: new Date((await getServerTime()).getTime() + 5 * 60 * 1000).toISOString()
   };
   ```

2. **Use relative timeouts instead of absolute:**
   ```javascript
   const signal = {
     created_at: Date.now(), // Milliseconds since epoch
     timeout_duration_ms: 300000 // 5 minutes (relative)
   };

   // Check timeout
   function isExpired(signal) {
     return (Date.now() - signal.created_at) > signal.timeout_duration_ms;
   }
   ```

3. **Add tolerance to timeout checks:**
   ```javascript
   const CLOCK_SKEW_TOLERANCE_MS = 60000; // 1 minute

   function isExpired(signal) {
     const now = new Date();
     const timeout = new Date(signal.timeout_at);
     return now > new Date(timeout.getTime() + CLOCK_SKEW_TOLERANCE_MS);
   }
   ```

---

## 2. Partial Sync Failures

**Problem:**
Sync tool (Dropbox, rsync) may sync signal file but not the referenced task file, or vice versa:

```
Local:
  ├── Needs_Action/task-123.json ✅
  ├── .signals/task-123.delegate.json ✅

Cloud (partial sync):
  ├── Needs_Action/task-123.json ❌ (not synced yet)
  ├── .signals/task-123.delegate.json ✅ (synced)
```

**Impact:**
- cex receives delegation signal but can't find task file
- cex crashes or rejects delegation
- Signal becomes orphaned

**Mitigation:**

1. **Embed task summary in signal:**
   ```javascript
   const signal = {
     task_id: "task-123",
     request: {
       action: "plan_task",
       task_path: "Needs_Action/task-123.json",
       // Embed minimal task data in signal for resilience
       task_summary: {
         title: task.title,
         description: task.description,
         priority: task.priority
       }
     }
   };
   ```

2. **Retry with backoff:**
   ```javascript
   async function readTaskWithRetry(taskPath, maxRetries = 3) {
     for (let i = 0; i < maxRetries; i++) {
       try {
         return await readFile(taskPath);
       } catch (err) {
         if (err.code === "ENOENT" && i < maxRetries - 1) {
           console.warn(`Task file not found; retrying in ${2 ** i} seconds`);
           await sleep(2 ** i * 1000); // Exponential backoff
         } else {
           throw err;
         }
       }
     }
   }
   ```

3. **Validate task file exists before creating signal:**
   ```javascript
   async function delegateTaskToCloud(taskId) {
     const taskPath = `${VAULT_PATH_LOCAL}/Needs_Action/${taskId}.json`;

     // Ensure task file exists
     if (!await fileExists(taskPath)) {
       throw new Error(`Task file not found: ${taskPath}`);
     }

     // Wait for sync to settle (optional)
     await sleep(5000);

     // Now create signal
     await createDelegationSignal(taskId);
   }
   ```

---

## 3. Signal File Race Conditions

**Problem:**
Multiple agents may try to claim the same signal file concurrently:

```
Time  | lex Agent 1           | lex Agent 2
------|-----------------------|----------------------
T0    | List signals          | List signals
T1    | Find task-123.json    | Find task-123.json
T2    | Attempt claim (move)  | Attempt claim (move)
T3    | Success!              | ENOENT error (lost race)
```

**Impact:**
- Second agent gets ENOENT error
- Error handling must distinguish "already claimed" from "genuine error"

**Mitigation:**

1. **Expect and handle ENOENT gracefully:**
   ```javascript
   async function claimSignal(signalPath) {
     try {
       await moveFile(signalPath, signalPath.replace(".json", ".claimed.json"));
       return { success: true };
     } catch (err) {
       if (err.code === "ENOENT") {
         // Expected: another agent claimed first
         return { success: false, reason: "already_claimed" };
       }
       // Unexpected error
       throw err;
     }
   }
   ```

2. **Use unique claim paths per agent:**
   ```javascript
   const agentId = process.env.AGENT_ID || uuidv4();
   const claimPath = signalPath.replace(".json", `.claimed-by-${agentId}.json`);

   // Each agent tries to claim with its own ID
   await moveFile(signalPath, claimPath);
   ```

3. **Implement claim timeout and release:**
   ```javascript
   // Agent claims signal
   const claimPath = signalPath.replace(".json", ".claimed.json");
   await moveFile(signalPath, claimPath);

   // Embed claim timeout
   const claim = await readFile(claimPath);
   claim.claimed_at = Date.now();
   claim.claim_timeout_at = Date.now() + 300000; // 5 minutes
   await writeFile(claimPath, claim);

   // Cleanup job: release expired claims
   async function releaseExpiredClaims() {
     const claims = await listFiles(SIGNALS_DIR, "*.claimed.json");
     for (const claimPath of claims) {
       const claim = await readFile(claimPath);
       if (Date.now() > claim.claim_timeout_at) {
         console.warn(`Releasing expired claim: ${claim.task_id}`);
         await moveFile(claimPath, claimPath.replace(".claimed.json", ".json"));
       }
     }
   }
   ```

---

## 4. Circular Delegation Loops

**Problem:**
cex delegates back to lex, which delegates back to cex, creating infinite loop:

```
lex: "cex, please plan this task"
cex: "This task requires local secrets; delegating back to lex"
lex: "This task requires planning; delegating back to cex"
... (infinite loop)
```

**Impact:**
- Signal files accumulate
- Agents waste cycles
- Task never completes

**Mitigation:**

1. **Track delegation depth:**
   ```javascript
   const signal = {
     task_id: "task-123",
     delegation_chain: [
       { agent: "lex", timestamp: "2025-01-15T10:00:00Z" },
       { agent: "cex", timestamp: "2025-01-15T10:01:00Z" }
     ],
     max_delegation_depth: 3
   };

   function canDelegate(signal, toAgent) {
     if (signal.delegation_chain.length >= signal.max_delegation_depth) {
       return { allowed: false, reason: "Max delegation depth reached" };
     }

     // Check for circular delegation
     const lastAgent = signal.delegation_chain[signal.delegation_chain.length - 1]?.agent;
     if (lastAgent === toAgent) {
       return { allowed: false, reason: "Circular delegation detected" };
     }

     return { allowed: true };
   }
   ```

2. **Require explicit capability declaration:**
   ```javascript
   const agentCapabilities = {
     lex: ["execute_local", "read_secrets", "file_operations"],
     cex: ["plan_task", "generate_code", "research"]
   };

   function canHandleTask(task, agent) {
     const requiredCapabilities = task.required_capabilities || [];
     const agentCaps = agentCapabilities[agent] || [];

     for (const required of requiredCapabilities) {
       if (!agentCaps.includes(required)) {
         return { capable: false, missing: required };
       }
     }

     return { capable: true };
   }
   ```

3. **Escalate to human after failed delegation:**
   ```javascript
   async function delegateWithFallback(taskId, toAgent) {
     const result = await delegateTask(taskId, toAgent);

     if (!result.success && result.reason === "circular_delegation") {
       // Escalate to human
       await moveFile(
         `Needs_Action/${taskId}.json`,
         `Pending_Approval/${taskId}.json`
       );

       await createNotification({
         type: "delegation_failed",
         task_id: taskId,
         reason: "Circular delegation detected; human intervention required"
       });
     }
   }
   ```

---

## 5. Orphaned Signal Files After Crashes

**Problem:**
If agent crashes after claiming signal but before processing, signal remains in "claimed" state indefinitely:

```
T0: cex claims task-123.delegate.json
T1: cex renames to task-123.claimed.json
T2: cex starts processing
T3: cex crashes (power failure, OOM, etc.)
T4: Signal remains as task-123.claimed.json forever
```

**Impact:**
- Task never gets processed
- Signal file accumulates
- No automatic recovery

**Mitigation:**

1. **Add heartbeat to claim:**
   ```javascript
   // Agent updates heartbeat while processing
   const claimPath = "signals/task-123.claimed.json";
   const claim = await readFile(claimPath);

   // Update heartbeat every 30 seconds
   setInterval(async () => {
     claim.last_heartbeat = Date.now();
     await writeFile(claimPath, claim);
   }, 30000);
   ```

2. **Cleanup job reclaims stale signals:**
   ```javascript
   async function reclaimStaleSignals() {
     const claims = await listFiles(SIGNALS_DIR, "*.claimed.json");

     for (const claimPath of claims) {
       const claim = await readFile(claimPath);
       const staleness = Date.now() - (claim.last_heartbeat || claim.claimed_at);

       if (staleness > 5 * 60 * 1000) { // 5 minutes without heartbeat
         console.warn(`Reclaiming stale signal: ${claim.task_id}`);

         // Release claim by renaming back to unclaimed
         await moveFile(
           claimPath,
           claimPath.replace(".claimed.json", ".json")
         );

         // Log orphan event
         await appendToLog("orphaned_signals.log", {
           task_id: claim.task_id,
           reclaimed_at: new Date().toISOString(),
           staleness_ms: staleness
         });
       }
     }
   }

   // Run every 60 seconds
   setInterval(reclaimStaleSignals, 60000);
   ```

3. **Use lockfiles with PID tracking:**
   ```javascript
   // Create lockfile with process ID
   const lockPath = "signals/task-123.lock";
   const lock = {
     task_id: "task-123",
     agent_id: "lex",
     process_id: process.pid,
     hostname: os.hostname(),
     locked_at: Date.now()
   };
   await writeFile(lockPath, lock);

   // Cleanup job checks if process still exists
   async function cleanupDeadLocks() {
     const locks = await listFiles(SIGNALS_DIR, "*.lock");

     for (const lockPath of locks) {
       const lock = await readFile(lockPath);

       // Check if process still exists
       try {
         process.kill(lock.process_id, 0); // Signal 0 = check existence
         // Process exists; leave lock alone
       } catch (err) {
         if (err.code === "ESRCH") {
           // Process doesn't exist; remove lock
           console.warn(`Removing dead lock: ${lock.task_id}`);
           await deleteFile(lockPath);
         }
       }
     }
   }
   ```

---

## 6. Secret Detection False Positives

**Problem:**
Secret detection regex may flag non-secrets as secrets:

```javascript
// False positives
const task = {
  title: "Implement API_KEY validation",  // ❌ Flagged as secret
  steps: [
    "Check if PASSWORD field is valid"    // ❌ Flagged as secret
  ],
  test_data: {
    example_api_key: "test_key_12345"     // ❌ Flagged as secret
  }
};
```

**Impact:**
- Legitimate tasks marked as `local_only`
- Prevents delegation to cloud
- Reduces automation effectiveness

**Mitigation:**

1. **Context-aware detection:**
   ```javascript
   function detectSecrets(content) {
     const text = JSON.stringify(content);

     // Ignore secrets in certain contexts
     const safeContexts = [
       /title.*API_KEY/i,           // "title": "Implement API_KEY..."
       /description.*PASSWORD/i,    // "description": "Check PASSWORD..."
       /test.*SECRET/i,             // "test_data": {"secret": "..."}
       /example.*TOKEN/i            // "example_token": "..."
     ];

     for (const pattern of safeContexts) {
       if (pattern.test(text)) {
         return { hasSecrets: false, reason: "Safe context detected" };
       }
     }

     // Now check for actual secrets
     return detectSecretsStrict(content);
   }
   ```

2. **Whitelist known test secrets:**
   ```javascript
   const TEST_SECRET_PATTERNS = [
     /test[_-]?api[_-]?key/i,
     /example[_-]?secret/i,
     /demo[_-]?token/i,
     /fake[_-]?password/i
   ];

   function isTestSecret(value) {
     for (const pattern of TEST_SECRET_PATTERNS) {
       if (pattern.test(value)) {
         return true;
       }
     }
     return false;
   }
   ```

3. **Allow user override:**
   ```javascript
   async function createTask(content, userOverride = {}) {
     const detection = detectSecrets(content);

     if (detection.hasSecrets && userOverride.force_sync) {
       console.warn(`User overrode secret detection for task ${content.task_id}`);
       return {
         ...content,
         sync_policy: "sync",
         secret_detection: {
           detected: true,
           overridden: true,
           override_reason: userOverride.reason
         }
       };
     }

     return {
       ...content,
       sync_policy: detection.hasSecrets ? "local_only" : "sync",
       secret_detection: { detected: detection.hasSecrets }
     };
   }
   ```

---

## 7. Sync Conflict During Approval

**Problem:**
Human approves task in cloud vault while lex is updating same task locally:

```
Time  | Local (lex)                        | Cloud (human)
------|------------------------------------|------------------
T0    | Update task-123.json status        |
T1    | Write task-123.json                |
T2    |                                    | Approve task-123
T3    |                                    | Move to Approved/
T4    | Sync (conflict!)                   | Sync (conflict!)
```

**Impact:**
- Last-write-wins may overwrite approval
- Task may end up in wrong folder
- Approval decision lost

**Mitigation:**

1. **Approval takes precedence:**
   ```javascript
   async function resolveSyncConflict(localTask, cloudTask) {
     // If cloud task is in Approved/ or Rejected/, cloud wins
     if (cloudTask.status === "approved" || cloudTask.status === "rejected") {
       console.log(`Approval detected in cloud; deferring to human decision`);
       await overwriteLocalTask(cloudTask);
       return;
     }

     // Otherwise, use normal conflict resolution
     await resolveConflictNormal(localTask, cloudTask);
   }
   ```

2. **Lock task during approval:**
   ```javascript
   // lex creates approval request
   async function requestApproval(taskId) {
     const task = await readTaskFile(taskId);

     // Lock task from local edits
     task.locked = true;
     task.locked_reason = "Awaiting human approval";
     task.locked_at = new Date().toISOString();

     await writeTaskFile(taskId, task);
     await moveFile(
       `In_Progress/${taskId}.json`,
       `Pending_Approval/${taskId}.json`
     );
   }

   // lex checks lock before editing
   async function updateTask(taskId, updates) {
     const task = await readTaskFile(taskId);

     if (task.locked) {
       throw new Error(`Task is locked: ${task.locked_reason}`);
     }

     // Safe to update
     Object.assign(task, updates);
     await writeTaskFile(taskId, task);
   }
   ```

3. **Use approval signal instead of direct file move:**
   ```javascript
   // Human approval doesn't move file directly; creates signal
   async function humanApprove(taskId, decision) {
     const signal = {
       signal_type: "approval_sync",
       task_id: taskId,
       approval: {
         decision: decision, // "approved" | "rejected"
         approved_by: "human",
         timestamp: new Date().toISOString()
       }
     };

     // Create signal instead of moving file
     await writeFile(`${SIGNALS_DIR_CLOUD}/${taskId}.approval.json`, signal);

     // lex will process signal and move file locally (single source of truth)
   }
   ```

---

## 8. Network Partition During Delegation

**Problem:**
Sync layer disconnects (no internet, Dropbox offline) while delegation is in progress:

```
T0: lex creates delegation signal (offline)
T1: lex waits for response...
T2: Sync layer offline; signal never reaches cloud
T3: Timeout expires
T4: lex retries (still offline)
... (infinite retries)
```

**Impact:**
- Delegation never completes
- Timeout doesn't help (signal never sent)
- Agent stuck waiting

**Mitigation:**

1. **Check sync status before delegating:**
   ```javascript
   async function isSyncOnline() {
     // Check if sync folder is mounted
     try {
       await fs.access(VAULT_PATH_CLOUD, fs.constants.W_OK);
     } catch (err) {
       return false;
     }

     // Check if Dropbox is running (platform-specific)
     if (process.platform === "darwin") {
       const result = await exec("pgrep Dropbox");
       return result.stdout.trim().length > 0;
     }

     // Add other platform checks as needed
     return true;
   }

   async function delegateTaskToCloud(taskId) {
     if (!await isSyncOnline()) {
       throw new Error("Sync layer offline; cannot delegate to cloud");
     }

     // Proceed with delegation
     await createDelegationSignal(taskId);
   }
   ```

2. **Fallback to local execution:**
   ```javascript
   async function delegateOrFallback(taskId) {
     try {
       return await delegateTaskToCloud(taskId);
     } catch (err) {
       if (err.message.includes("offline")) {
         console.warn(`Sync offline; handling task locally`);
         return await handleTaskLocally(taskId);
       }
       throw err;
     }
   }
   ```

3. **Add sync health check to signal:**
   ```javascript
   const signal = {
     task_id: "task-123",
     sync_health: {
       online: await isSyncOnline(),
       last_sync: await getLastSyncTime(),
       sync_latency_ms: await measureSyncLatency()
     }
   };

   // cex checks sync health before responding
   if (signal.sync_health.sync_latency_ms > 30000) {
     console.warn(`High sync latency; response may be delayed`);
   }
   ```

---

## Summary

Key gotchas to watch for:
1. **Clock skew** - Use relative timeouts or NTP
2. **Partial syncs** - Embed task summary in signals
3. **Race conditions** - Handle ENOENT gracefully
4. **Circular delegation** - Track delegation depth
5. **Orphaned signals** - Implement heartbeat + cleanup
6. **False positives** - Context-aware secret detection
7. **Approval conflicts** - Approval takes precedence
8. **Network partition** - Check sync status before delegating

Each gotcha has mitigation strategies; choose based on your risk tolerance and operational requirements.
