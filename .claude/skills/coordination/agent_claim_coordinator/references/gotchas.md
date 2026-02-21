# Gotchas and Edge Cases for Agent Claim Coordinator

## 1. Clock Skew Between Agents

**Problem:**
Agents running on different machines may have different system times, causing incorrect staleness calculations:

```javascript
// Agent A (local machine): claimed at 10:00:00 local time
task.claimed_at = "2025-01-15T10:00:00.000Z";

// Agent B (remote machine): checks staleness at 09:55:00 remote time (5 min behind)
// Coordinator thinks claim is 5 minutes older than it actually is
const staleness = Date.now() - new Date(task.claimed_at).getTime();
// staleness = 300000ms (5 minutes), even though claim just happened
```

**Impact:**
- Premature reclaims (coordinator thinks claim is stale when it's not)
- Delayed reclaims (coordinator thinks claim is recent when it's actually stale)
- Incorrect conflict resolution (timestamp-based policies use wrong order)

**Mitigation:**

1. **Use NTP for time synchronization:**
   ```bash
   # Install NTP on all agent machines
   sudo apt-get install ntp
   sudo systemctl enable ntp
   sudo systemctl start ntp

   # Verify sync status
   timedatectl status
   ```

2. **Add clock skew tolerance:**
   ```javascript
   const CLOCK_SKEW_TOLERANCE_MS = 60000; // 1 minute

   function isClaimStale(task) {
     const lastHeartbeat = new Date(task.last_heartbeat);
     const staleness = Date.now() - lastHeartbeat.getTime();

     // Add tolerance before declaring stale
     return staleness > (CLAIM_TIMEOUT_MS + CLOCK_SKEW_TOLERANCE_MS);
   }
   ```

3. **Use server time for critical operations:**
   ```javascript
   // Fetch authoritative time from NTP server
   const ntpClient = require('ntp-client');

   async function getServerTime() {
     return new Promise((resolve, reject) => {
       ntpClient.getNetworkTime('pool.ntp.org', 123, (err, date) => {
         if (err) reject(err);
         else resolve(date);
       });
     });
   }

   // Use server time for claim timestamps
   const serverTime = await getServerTime();
   task.claimed_at = serverTime.toISOString();
   ```

---

## 2. Network Filesystem Atomicity Issues

**Problem:**
Network filesystems (NFS, SMB) may not provide strong atomicity guarantees for `fs.rename()`:

```javascript
// Agent A: Attempt to claim via rename
await fs.rename(
  'Needs_Action/task-123.json',
  'In_Progress/task-123.json'
);
// ✅ Success (from Agent A's perspective)

// Agent B: Also attempt to claim (race condition)
await fs.rename(
  'Needs_Action/task-123.json',
  'In_Progress/task-123.json'
);
// ✅ Also success?! (Network filesystem didn't properly serialize)
```

**Impact:**
- Both agents think they claimed the task
- File corruption (concurrent writes)
- Lost updates (one agent's changes overwrite another's)

**Mitigation:**

1. **Use file locking for network filesystems:**
   ```javascript
   const lockfile = require('proper-lockfile');

   async function claimTaskWithLock(taskId, agentName) {
     const lockPath = `${VAULT_PATH}/Needs_Action/${taskId}.lock`;

     // Acquire lock
     let release;
     try {
       release = await lockfile.lock(lockPath, {
         stale: 10000, // 10 seconds
         retries: 3
       });
     } catch (err) {
       if (err.code === 'ELOCKED') {
         return { success: false, reason: 'already_claimed' };
       }
       throw err;
     }

     try {
       // Perform claim
       const task = await readTaskFile(`Needs_Action/${taskId}.json`);
       task.claimed_by = agentName;
       // ... update claim metadata

       await atomicMove(`Needs_Action/${taskId}.json`, `In_Progress/${taskId}.json`);

       return { success: true };

     } finally {
       // Release lock
       await release();
     }
   }
   ```

2. **Validate claim after move:**
   ```javascript
   async function claimTask(taskId, agentName) {
     // Attempt atomic move
     await fs.rename(
       `Needs_Action/${taskId}.json`,
       `In_Progress/${taskId}.json`
     );

     // Read back and verify
     await sleep(100); // Small delay for filesystem sync

     const task = await readTaskFile(`In_Progress/${taskId}.json`);

     if (task.claimed_by !== agentName) {
       // Another agent won the race; release claim
       console.warn(`Claim verification failed for ${taskId}; another agent won`);
       await releaseClaim(taskId, agentName, 'verification_failed');
       return { success: false, reason: 'race_lost' };
     }

     return { success: true };
   }
   ```

3. **Use local filesystem for critical operations:**
   ```bash
   # Mount local SSD for In_Progress/ folder
   sudo mkdir -p /mnt/local_ssd/In_Progress
   sudo mount /dev/sdb1 /mnt/local_ssd

   # Use local path for claims
   VAULT_PATH_LOCAL="/mnt/local_ssd"
   ```

---

## 3. Heartbeat Update Race Condition

**Problem:**
Agent updates heartbeat at same time coordinator checks for staleness:

```
Time  | Agent                     | Coordinator
------|---------------------------|---------------------------
T0    | last_heartbeat = T0       |
T1    |                           | Check heartbeat (T0)
T2    |                           | Calculate staleness (T2-T0)
T3    | Update heartbeat (T3)     |
T4    |                           | Declare stale & reclaim
T5    | Heartbeat write completes |
T6    | Agent continues working   | (task already reclaimed!)
```

**Impact:**
- Agent thinks it owns task (heartbeat just updated)
- Coordinator reclaimed task (heartbeat appeared stale)
- Duplicate work or conflicting updates

**Mitigation:**

1. **Grace period before reclaim:**
   ```javascript
   const RECLAIM_GRACE_PERIOD_MS = 10000; // 10 seconds

   async function reclaimStaleTask(taskId) {
     const task = await readTaskFile(`In_Progress/${taskId}.json`);
     const staleness = Date.now() - new Date(task.last_heartbeat).getTime();

     if (staleness < CLAIM_TIMEOUT_MS + RECLAIM_GRACE_PERIOD_MS) {
       // Within grace period; don't reclaim yet
       return { reclaimed: false, reason: 'grace_period' };
     }

     // Proceed with reclaim
     await reclaimStaleTaskImpl(taskId);
   }
   ```

2. **Two-phase reclaim (tentative + confirmed):**
   ```javascript
   async function reclaimStaleTask(taskId) {
     // Phase 1: Mark as tentatively reclaimed
     const task = await readTaskFile(`In_Progress/${taskId}.json`);
     task.reclaim_tentative = {
       marked_at: new Date().toISOString(),
       reason: 'stale_heartbeat'
     };
     await writeTaskFile(`In_Progress/${taskId}.json`, task);

     // Wait for one heartbeat interval
     await sleep(CLAIM_HEARTBEAT_INTERVAL_MS);

     // Phase 2: Check if agent updated heartbeat
     const taskAfterWait = await readTaskFile(`In_Progress/${taskId}.json`);

     if (taskAfterWait.last_heartbeat !== task.last_heartbeat) {
       // Agent updated heartbeat; cancel reclaim
       delete taskAfterWait.reclaim_tentative;
       await writeTaskFile(`In_Progress/${taskId}.json`, taskAfterWait);
       return { reclaimed: false, reason: 'heartbeat_updated' };
     }

     // Proceed with reclaim
     await reclaimStaleTaskImpl(taskId);
   }
   ```

3. **Agent validates ownership after each heartbeat:**
   ```javascript
   async function updateHeartbeat(taskId, agentName) {
     const task = await readTaskFile(`In_Progress/${taskId}.json`);

     // Check if we still own the task
     if (task.claimed_by !== agentName) {
       throw new Error('Task no longer owned by us; stopping work');
     }

     // Check for tentative reclaim marker
     if (task.reclaim_tentative) {
       console.warn(`Tentative reclaim detected for ${taskId}; proving we're alive`);
     }

     task.last_heartbeat = new Date().toISOString();
     await writeTaskFile(`In_Progress/${taskId}.json`, task);
   }
   ```

---

## 4. Concurrent Conflict Detection

**Problem:**
Two coordinators detect same conflict simultaneously and apply different resolutions:

```
Time  | Coordinator A             | Coordinator B
------|---------------------------|---------------------------
T0    | Detect conflict (task-123)|
T1    |                           | Detect conflict (task-123)
T2    | Resolve: winner = lex     |
T3    |                           | Resolve: winner = orch
T4    | Write task (claimed_by=lex)|
T5    |                           | Write task (claimed_by=orch)
T6    | (Both think resolved!)    | (Both think resolved!)
```

**Impact:**
- Conflicting resolutions (task ownership unclear)
- Lost updates (last write wins, but incorrectly)
- Both agents think they won

**Mitigation:**

1. **Single coordinator instance:**
   ```yaml
   # Kubernetes deployment: 1 replica
   replicas: 1

   # Or use leader election
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: claim-coordinator
   spec:
     replicas: 1 # Only one coordinator
     strategy:
       type: Recreate # Don't overlap during updates
   ```

2. **Optimistic locking with version field:**
   ```javascript
   async function resolveConflict(conflict) {
     const task = await readTaskFile(`In_Progress/${conflict.task_id}.json`);

     // Determine winner
     const { winner, losers } = applyResolutionPolicy(task, conflict.competing_agents);

     // Update task with version check
     const originalVersion = task.version || 0;
     task.version = originalVersion + 1;
     task.claimed_by = winner;

     // Write with version check
     const tempPath = `${VAULT_PATH}/In_Progress/${conflict.task_id}.tmp`;
     await fs.writeFile(tempPath, JSON.stringify(task, null, 2));

     try {
       // Atomic compare-and-swap
       await atomicMoveIfVersionMatches(
         tempPath,
         `In_Progress/${conflict.task_id}.json`,
         originalVersion
       );

       return { success: true, winner, losers };

     } catch (err) {
       if (err.code === 'VERSION_MISMATCH') {
         // Another coordinator already resolved
         console.warn(`Conflict already resolved by another coordinator`);
         return { success: false, reason: 'already_resolved' };
       }
       throw err;
     }
   }
   ```

3. **Distributed lock for conflict resolution:**
   ```javascript
   const Redlock = require('redlock');
   const redlock = new Redlock([redisClient]);

   async function resolveConflict(conflict) {
     const lockKey = `conflict_lock:${conflict.task_id}`;

     // Acquire lock
     let lock;
     try {
       lock = await redlock.lock(lockKey, 10000); // 10 second TTL
     } catch (err) {
       console.warn(`Another coordinator is resolving conflict for ${conflict.task_id}`);
       return { success: false, reason: 'locked_by_another' };
     }

     try {
       // Resolve conflict
       const result = await resolveConflictImpl(conflict);
       return result;

     } finally {
       // Release lock
       await lock.unlock();
     }
   }
   ```

---

## 5. Agent Permission Validation Race

**Problem:**
Agent's permissions change (revoked) while it's claiming a task:

```
Time  | Agent                     | Permission System
------|---------------------------|---------------------------
T0    | Check permissions: OK     |
T1    | Start claim process       |
T2    |                           | Revoke agent permissions
T3    | Complete claim (success)  |
T4    | (Agent has no permission!)| (Agent shouldn't have claimed!)
```

**Impact:**
- Unauthorized agent owns task
- Security violation
- Audit log shows improper claim

**Mitigation:**

1. **Re-validate permissions after claim:**
   ```javascript
   async function claimTask(taskId, agentName) {
     // Check permissions before claim
     if (!canAgentClaimTask(agentName, task)) {
       return { success: false, reason: 'permission_denied' };
     }

     // Perform claim
     await atomicMove(`Needs_Action/${taskId}.json`, `In_Progress/${taskId}.json`);

     // Re-validate permissions after claim
     if (!canAgentClaimTask(agentName, task)) {
       console.warn(`Permissions changed during claim; releasing`);
       await releaseClaim(taskId, agentName, 'permission_revoked');
       return { success: false, reason: 'permission_revoked' };
     }

     return { success: true };
   }
   ```

2. **Permission check during heartbeat:**
   ```javascript
   async function updateHeartbeat(taskId, agentName) {
     // Check permissions on every heartbeat
     const task = await readTaskFile(`In_Progress/${taskId}.json`);

     if (!canAgentClaimTask(agentName, task)) {
       throw new Error('Permissions revoked; releasing claim');
     }

     task.last_heartbeat = new Date().toISOString();
     await writeTaskFile(`In_Progress/${taskId}.json`, task);
   }
   ```

3. **Permission revocation notification:**
   ```javascript
   // Permission system notifies coordinator when permissions change
   permissionSystem.on('permissions_revoked', async (agentName) => {
     // Find all tasks claimed by this agent
     const tasks = await findTasksByOwner(agentName);

     for (const task of tasks) {
       console.warn(`Revoking claim for ${task.task_id} (permissions revoked)`);
       await releaseClaim(task.task_id, agentName, 'permission_revoked');
     }
   });
   ```

---

## 6. Orphaned Claim After Process Kill

**Problem:**
Agent process killed (SIGKILL, power failure) without releasing claim:

```
Time  | Agent                     | Coordinator
------|---------------------------|---------------------------
T0    | Claim task-123            |
T1    | Start working             |
T2    | (SIGKILL) Process killed  |
T3    |                           | Heartbeat check: T0 (stale)
T4    |                           | Reclaim task (delayed)
T5    |                           | Task back in Needs_Action
```

**Impact:**
- Task stuck in In_Progress/ until heartbeat timeout
- Delayed task processing (wait for CLAIM_TIMEOUT_MS)
- Wasted capacity (task not being worked)

**Mitigation:**

1. **Shorter heartbeat timeout:**
   ```bash
   # Reduce timeout for faster recovery
   CLAIM_TIMEOUT_MS="60000"  # 1 minute (instead of 5)
   CLAIM_HEARTBEAT_INTERVAL_MS="15000"  # 15 seconds
   ```

2. **Process monitoring with immediate reclaim:**
   ```javascript
   const pidusage = require('pidusage');

   // Track which agent process owns which task
   const taskOwnership = new Map(); // taskId -> { agent, pid }

   async function monitorAgentProcesses() {
     for (const [taskId, owner] of taskOwnership.entries()) {
       try {
         // Check if process still exists
         process.kill(owner.pid, 0); // Signal 0 = check existence
         // Process exists; continue
       } catch (err) {
         if (err.code === 'ESRCH') {
           // Process doesn't exist; immediate reclaim
           console.warn(`Agent process ${owner.pid} died; reclaiming ${taskId}`);
           await reclaimStaleTask(taskId);
           taskOwnership.delete(taskId);
         }
       }
     }
   }

   // Run every 10 seconds
   setInterval(monitorAgentProcesses, 10000);
   ```

3. **Graceful shutdown handler:**
   ```javascript
   // Agent registers shutdown handler
   process.on('SIGTERM', async () => {
     console.log('Received SIGTERM; releasing claims');

     // Release all claims
     for (const taskId of ownedTasks) {
       await releaseClaim(taskId, agentName, 'shutdown');
     }

     process.exit(0);
   });

   // Note: SIGKILL cannot be caught; use SIGTERM for graceful shutdown
   ```

---

## 7. Claim Thrashing (Repeated Conflicts)

**Problem:**
Same agents repeatedly compete for same task, causing claim thrashing:

```
Iteration 1: lex claims → orch conflicts → lex wins
Iteration 2: orch claims → lex conflicts → orch wins
Iteration 3: lex claims → orch conflicts → lex wins
... (infinite loop)
```

**Impact:**
- Task never gets processed (constant claiming/releasing)
- Wasted CPU cycles
- Conflict log accumulation

**Mitigation:**

1. **Backoff after conflict loss:**
   ```javascript
   const conflictBackoffs = new Map(); // agentName -> backoff_ms

   async function claimTask(taskId, agentName) {
     // Check if agent has backoff penalty
     const backoff = conflictBackoffs.get(agentName) || 0;
     if (backoff > 0) {
       console.log(`Agent ${agentName} in backoff; waiting ${backoff}ms`);
       await sleep(backoff);
     }

     // Attempt claim
     const result = await claimTaskImpl(taskId, agentName);

     if (!result.success && result.reason === 'conflict_lost') {
       // Exponential backoff (1s, 2s, 4s, 8s, ...)
       const newBackoff = Math.min((backoff || 1000) * 2, 60000);
       conflictBackoffs.set(agentName, newBackoff);

       console.log(`Agent ${agentName} lost conflict; backoff = ${newBackoff}ms`);
     } else if (result.success) {
       // Clear backoff on success
       conflictBackoffs.delete(agentName);
     }

     return result;
   }
   ```

2. **Sticky resolution (winner keeps winning):**
   ```javascript
   const conflictWinners = new Map(); // taskId -> winner_agent

   function resolveConflict(task, competingAgents) {
     // Check if we already resolved this task's conflict
     const previousWinner = conflictWinners.get(task.task_id);

     if (previousWinner && competingAgents.includes(previousWinner)) {
       // Sticky: previous winner wins again
       const losers = competingAgents.filter(a => a !== previousWinner);
       return { winner: previousWinner, losers, sticky: true };
     }

     // First conflict; apply policy
     const { winner, losers } = applyResolutionPolicy(task, competingAgents);

     // Remember winner for next conflict
     conflictWinners.set(task.task_id, winner);

     return { winner, losers };
   }
   ```

3. **Rate limiting per agent:**
   ```javascript
   const claimAttempts = new Map(); // agentName -> { count, reset_at }

   async function claimTask(taskId, agentName) {
     // Check rate limit
     const now = Date.now();
     let attempts = claimAttempts.get(agentName);

     if (!attempts || now > attempts.reset_at) {
       // Reset counter
       attempts = { count: 0, reset_at: now + 60000 }; // 1 minute window
       claimAttempts.set(agentName, attempts);
     }

     if (attempts.count >= 10) { // Max 10 claims per minute
       console.warn(`Agent ${agentName} rate limited (${attempts.count} claims/min)`);
       return { success: false, reason: 'rate_limited' };
     }

     attempts.count++;

     // Proceed with claim
     return await claimTaskImpl(taskId, agentName);
   }
   ```

---

## 8. Heartbeat Update Failure Cascade

**Problem:**
Filesystem full or network issue causes heartbeat updates to fail for all agents:

```
Time  | Agent A           | Agent B           | Coordinator
------|-------------------|-------------------|-------------
T0    | Heartbeat write   | Heartbeat write   |
T1    | (ENOSPC) Failed!  | (ENOSPC) Failed!  |
T2    | Retry failed      | Retry failed      |
T3    |                   |                   | Check heartbeats
T4    |                   |                   | All stale! Reclaim all!
T5    | (All agents lose all tasks)            |
```

**Impact:**
- Mass reclaim event (all tasks released)
- System-wide disruption
- Agents restart work from scratch

**Mitigation:**

1. **Health check before reclaim:**
   ```javascript
   async function reclaimStaleTasks() {
     // Check filesystem health first
     try {
       const testPath = `${VAULT_PATH}/.health_check`;
       await fs.writeFile(testPath, 'OK');
       await fs.unlink(testPath);
     } catch (err) {
       console.error(`Filesystem unhealthy; skipping reclaim: ${err.message}`);
       return; // Don't reclaim if we can't write
     }

     // Proceed with reclaim
     await reclaimStaleTasksImpl();
   }
   ```

2. **Threshold-based reclaim:**
   ```javascript
   const MASS_RECLAIM_THRESHOLD = 0.5; // 50%

   async function reclaimStaleTasks() {
     const tasks = await listTasksInProgress();
     const staleTasks = tasks.filter(isStale);

     const staleRatio = staleTasks.length / tasks.length;

     if (staleRatio > MASS_RECLAIM_THRESHOLD) {
       console.error(`Mass stale detected (${staleRatio * 100}%); possible filesystem issue`);
       console.error(`Skipping reclaim to prevent cascade failure`);

       // Alert human
       await notifyHuman({
         type: 'mass_stale_detected',
         stale_count: staleTasks.length,
         total_count: tasks.length,
         message: 'Possible filesystem issue; investigate before reclaiming'
       });

       return; // Don't reclaim
     }

     // Normal reclaim
     for (const task of staleTasks) {
       await reclaimStaleTask(task.task_id);
     }
   }
   ```

3. **Circuit breaker pattern:**
   ```javascript
   const CircuitBreaker = require('opossum');

   const heartbeatCircuit = new CircuitBreaker(updateHeartbeatImpl, {
     timeout: 5000, // 5 second timeout
     errorThresholdPercentage: 50, // Open circuit if 50% fail
     resetTimeout: 30000 // Retry after 30 seconds
   });

   async function updateHeartbeat(taskId, agentName) {
     try {
       await heartbeatCircuit.fire(taskId, agentName);
     } catch (err) {
       if (heartbeatCircuit.opened) {
         console.error(`Circuit open; heartbeat system down. Stopping work.`);
         stopWork();
       } else {
         throw err;
       }
     }
   }
   ```

---

## Summary

Key gotchas to watch for:
1. **Clock skew** - Use NTP, add tolerance
2. **Network filesystem atomicity** - Use file locking or validate after claim
3. **Heartbeat race conditions** - Use grace period or two-phase reclaim
4. **Concurrent conflict detection** - Single coordinator or distributed locks
5. **Permission validation race** - Re-validate after claim, check on heartbeat
6. **Orphaned claims** - Process monitoring, shorter timeouts
7. **Claim thrashing** - Backoff, sticky resolution, rate limiting
8. **Heartbeat failure cascade** - Health checks, thresholds, circuit breakers

Each gotcha has mitigation strategies; choose based on your operational requirements and risk tolerance.
