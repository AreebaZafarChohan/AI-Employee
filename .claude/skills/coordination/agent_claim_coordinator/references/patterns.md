# Design Patterns for Agent Claim Coordinator

## Pattern: Optimistic Locking with Heartbeat

**Problem:** Need to detect crashed or hung agents without complex distributed locking.

**Solution:** Agents update heartbeat field periodically; coordinator reclaims tasks with stale heartbeats.

**Implementation:**
```javascript
// Agent: Update heartbeat while working
class TaskWorker {
  constructor(taskId, agentName) {
    this.taskId = taskId;
    this.agentName = agentName;
    this.heartbeatInterval = null;
  }

  async start() {
    // Start heartbeat updates
    this.heartbeatInterval = setInterval(async () => {
      try {
        await this.updateHeartbeat();
      } catch (err) {
        console.error(`Heartbeat update failed: ${err.message}`);
        // Continue working; coordinator will reclaim if too many failures
      }
    }, CLAIM_HEARTBEAT_INTERVAL_MS);

    // Do actual work
    await this.processTask();

    // Stop heartbeat when done
    this.stop();
  }

  async updateHeartbeat() {
    const task = await readTaskFile(`In_Progress/${this.taskId}.json`);

    // Verify we still own the task
    if (task.claimed_by !== this.agentName) {
      throw new Error('Task no longer owned by us; stopping work');
    }

    task.last_heartbeat = new Date().toISOString();
    await writeTaskFile(`In_Progress/${this.taskId}.json`, task);
  }

  stop() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  async processTask() {
    // Actual task processing logic
    await sleep(60000); // Simulate work
  }
}

// Coordinator: Check for stale heartbeats
async function reclaimStaleTasks() {
  const tasks = await fs.readdir(`${VAULT_PATH}/In_Progress`);

  for (const taskFile of tasks) {
    if (!taskFile.endsWith('.json')) continue;

    const task = JSON.parse(
      await fs.readFile(`${VAULT_PATH}/In_Progress/${taskFile}`, 'utf-8')
    );

    if (!task.last_heartbeat) continue;

    const lastHeartbeat = new Date(task.last_heartbeat);
    const staleness = Date.now() - lastHeartbeat.getTime();

    if (staleness > CLAIM_TIMEOUT_MS) {
      console.warn(`Reclaiming stale task: ${task.task_id} (${Math.round(staleness/1000)}s old)`);
      await reclaimStaleTask(task.task_id);
    }
  }
}

// Run cleanup every minute
setInterval(reclaimStaleTasks, 60000);
```

**Benefits:**
- Simple to implement (no distributed locks)
- Crash-resistant (stale tasks auto-reclaimed)
- Low overhead (one field update per heartbeat)

**Trade-offs:**
- Requires clock synchronization (clock skew can cause false reclaims)
- Heartbeat interval vs timeout must be tuned (too short = overhead, too long = slow recovery)
- Network filesystem latency can cause heartbeat failures

---

## Pattern: Claim ID for Idempotency

**Problem:** Agent crashes and restarts; how to detect if it already claimed a task?

**Solution:** Generate unique claim_id when claiming; check claim_id before resuming work.

**Implementation:**
```javascript
// Agent claims task with unique ID
async function claimTask(taskId, agentName) {
  const claimId = uuidv4();
  const task = await readTaskFile(`Needs_Action/${taskId}.json`);

  task.claimed_by = agentName;
  task.claimed_at = new Date().toISOString();
  task.claim_id = claimId;
  task.claim_history.push({
    agent: agentName,
    action: 'claim',
    timestamp: new Date().toISOString(),
    claim_id: claimId
  });

  await atomicMove(`Needs_Action/${taskId}.json`, `In_Progress/${taskId}.json`);

  // Store claim ID locally
  await fs.writeFile(`/tmp/${agentName}_claim_${taskId}.txt`, claimId);

  return claimId;
}

// Agent resumes work after crash
async function resumeTask(taskId, agentName) {
  // Check if we have a claim ID for this task
  const claimIdPath = `/tmp/${agentName}_claim_${taskId}.txt`;

  let expectedClaimId;
  try {
    expectedClaimId = (await fs.readFile(claimIdPath, 'utf-8')).trim();
  } catch (err) {
    if (err.code === 'ENOENT') {
      // No claim ID found; we never claimed this task
      return { canResume: false, reason: 'no_claim_record' };
    }
    throw err;
  }

  // Read current task state
  const task = await readTaskFile(`In_Progress/${taskId}.json`);

  // Verify claim ID matches
  if (task.claim_id === expectedClaimId && task.claimed_by === agentName) {
    return { canResume: true, claimId: expectedClaimId };
  } else {
    return {
      canResume: false,
      reason: 'claim_id_mismatch',
      expected: expectedClaimId,
      actual: task.claim_id
    };
  }
}
```

**Benefits:**
- Idempotent claim verification
- Prevents duplicate work after agent restart
- Detects claim hijacking (claim_id mismatch)

**Trade-offs:**
- Requires persistent storage of claim ID (filesystem, database)
- Claim ID must survive agent crashes (use durable storage)

---

## Pattern: Priority Queue for Conflict Resolution

**Problem:** Multiple agents compete for same task; need fair but priority-aware resolution.

**Solution:** Agents have priority levels; conflicts resolved by priority first, then timestamp.

**Implementation:**
```javascript
// Parse agent priorities from config
function parsePriorities(configString) {
  // Format: "orch:1,lex:2,cex:3,watcher:4"
  const priorities = {};
  configString.split(',').forEach(pair => {
    const [agent, priority] = pair.split(':');
    priorities[agent.trim()] = parseInt(priority);
  });
  return priorities;
}

// Resolve conflict by priority + timestamp
function resolveByPriorityAndTime(task, competingAgents) {
  const priorities = parsePriorities(process.env.AGENT_PRIORITIES);

  const claims = competingAgents.map(agent => {
    const claimEntry = task.claim_history.find(h =>
      h.agent === agent && h.action === 'claim'
    );

    return {
      agent: agent,
      priority: priorities[agent] || 999, // Default low priority
      claimed_at: new Date(claimEntry.timestamp)
    };
  });

  // Sort by priority first (lower number = higher priority)
  // Then by timestamp (earlier = wins)
  claims.sort((a, b) => {
    if (a.priority !== b.priority) {
      return a.priority - b.priority;
    }
    return a.claimed_at - b.claimed_at;
  });

  const winner = claims[0].agent;
  const losers = claims.slice(1).map(c => c.agent);

  return { winner, losers };
}
```

**Benefits:**
- Fair resolution for equal-priority agents (timestamp-based)
- Respects agent hierarchy (orchestrator > executor > planner)
- Deterministic (same inputs = same output)

**Trade-offs:**
- Requires priority configuration (must be maintained)
- Lower-priority agents may be starved (always lose conflicts)

---

## Pattern: Conflict Marker Files

**Problem:** Human needs to manually resolve conflict; how to communicate conflict state?

**Solution:** Create `.conflict` marker file alongside task file with conflict details.

**Implementation:**
```javascript
async function escalateToHuman(task, competingAgents) {
  const conflictPath = `${VAULT_PATH}/In_Progress/${task.task_id}.conflict`;

  const conflictMarker = {
    task_id: task.task_id,
    task_title: task.title,
    competing_agents: competingAgents,
    detected_at: new Date().toISOString(),
    resolution_required: true,
    claims: competingAgents.map(agent => {
      const claimEntry = task.claim_history.find(h =>
        h.agent === agent && h.action === 'claim'
      );
      return {
        agent: agent,
        claimed_at: claimEntry.timestamp,
        claim_id: claimEntry.claim_id
      };
    }),
    instructions: `Multiple agents claim ownership of this task. To resolve:
1. Review claim timestamps above
2. Choose winning agent
3. Update ${task.task_id}.json: set claimed_by to winning agent
4. Delete this .conflict file
5. Notify losing agents to release claim`
  };

  await fs.writeFile(conflictPath, JSON.stringify(conflictMarker, null, 2));

  // Notify human via notification system
  await notifyHuman({
    type: 'claim_conflict',
    task_id: task.task_id,
    agents: competingAgents,
    message: `Conflict detected for task ${task.task_id}. Manual resolution required.`,
    action_url: `file://${conflictPath}`
  });

  // Freeze task (no agent can proceed)
  task.frozen = true;
  task.frozen_reason = 'awaiting_conflict_resolution';
  task.frozen_at = new Date().toISOString();

  await writeTaskFile(`In_Progress/${task.task_id}.json`, task);

  return { winner: null, losers: competingAgents, escalated: true };
}

// Human resolves conflict
async function resolveConflictManually(taskId, winningAgent) {
  const task = await readTaskFile(`In_Progress/${taskId}.json`);

  // Unfreeze task
  delete task.frozen;
  delete task.frozen_reason;
  delete task.frozen_at;

  // Set winner
  task.claimed_by = winningAgent;
  task.claim_expires_at = new Date(Date.now() + CLAIM_TIMEOUT_MS).toISOString();

  task.conflict = {
    detected: true,
    detected_at: task.conflict?.detected_at || new Date().toISOString(),
    competing_agents: task.conflict?.competing_agents || [],
    resolution_policy: 'human_resolve',
    resolved_by: winningAgent,
    resolved_at: new Date().toISOString(),
    resolved_manually: true
  };

  await writeTaskFile(`In_Progress/${taskId}.json`, task);

  // Delete conflict marker
  await fs.unlink(`${VAULT_PATH}/In_Progress/${taskId}.conflict`);

  console.log(`Conflict resolved manually: ${taskId} → ${winningAgent}`);
}
```

**Benefits:**
- Clear communication to human
- Self-documenting (instructions in marker file)
- Safe (task frozen until resolved)

**Trade-offs:**
- Requires human intervention (not autonomous)
- Delays task processing
- Marker files need cleanup

---

## Pattern: Graceful Degradation on Conflict

**Problem:** Conflict detected but cannot resolve immediately; how to prevent system deadlock?

**Solution:** Temporarily release both claims and move task back to Needs_Action/ for re-claiming.

**Implementation:**
```javascript
async function degradeOnConflict(task, competingAgents) {
  console.warn(`Conflict detected for ${task.task_id}; degrading to unclaimed state`);

  // Release all claims
  delete task.claimed_by;
  delete task.claimed_at;
  delete task.claim_expires_at;
  delete task.last_heartbeat;
  delete task.claim_id;

  // Mark conflict in history
  task.claim_history.push({
    action: 'conflict_degraded',
    timestamp: new Date().toISOString(),
    competing_agents: competingAgents,
    reason: 'Unable to resolve; releasing all claims for re-claiming'
  });

  // Add conflict metadata (for observability)
  task.conflict = {
    detected: true,
    detected_at: new Date().toISOString(),
    competing_agents: competingAgents,
    resolution_policy: 'graceful_degradation',
    resolved_by: null,
    resolved_at: null
  };

  // Move back to Needs_Action
  await fs.writeFile(`${VAULT_PATH}/In_Progress/${task.task_id}.json`, JSON.stringify(task, null, 2));
  await fs.rename(
    `${VAULT_PATH}/In_Progress/${task.task_id}.json`,
    `${VAULT_PATH}/Needs_Action/${task.task_id}.json`
  );

  // Log degradation event
  await appendToLog('claim_conflicts.log', {
    task_id: task.task_id,
    action: 'degrade_on_conflict',
    competing_agents: competingAgents,
    degraded_at: new Date().toISOString()
  });

  // Notify competing agents
  for (const agent of competingAgents) {
    await notifyAgent(agent, {
      type: 'claim_conflict',
      task_id: task.task_id,
      message: `Conflict detected; task released for re-claiming. Try again later.`
    });
  }

  return { success: true, degraded: true };
}
```

**Benefits:**
- Prevents deadlock (task available for re-claiming)
- Self-healing (system recovers without human intervention)
- Eventual consistency (task will be claimed by one agent eventually)

**Trade-offs:**
- May cause claim thrashing (repeated conflicts)
- Delays task processing
- Losing agents waste effort

---

## Pattern: Claim Lease with Renewal

**Problem:** Long-running tasks need extended claim duration without appearing stale.

**Solution:** Agents renew claim lease before expiration; coordinator accepts renewals.

**Implementation:**
```javascript
// Agent renews lease before expiration
async function renewClaimLease(taskId, agentName) {
  const task = await readTaskFile(`In_Progress/${taskId}.json`);

  // Verify ownership
  if (task.claimed_by !== agentName) {
    throw new Error('Cannot renew lease: not the owner');
  }

  // Check if renewal needed
  const expiresAt = new Date(task.claim_expires_at);
  const now = new Date();
  const timeUntilExpiry = expiresAt - now;

  if (timeUntilExpiry < CLAIM_TIMEOUT_MS / 2) {
    // Renew lease
    task.claim_expires_at = new Date(now.getTime() + CLAIM_TIMEOUT_MS).toISOString();
    task.last_heartbeat = now.toISOString();

    task.claim_history.push({
      agent: agentName,
      action: 'renew_lease',
      timestamp: now.toISOString(),
      previous_expiry: expiresAt.toISOString(),
      new_expiry: task.claim_expires_at
    });

    await writeTaskFile(`In_Progress/${taskId}.json`, task);

    console.log(`Lease renewed: ${taskId} (expires: ${task.claim_expires_at})`);
  }
}

// Agent periodically renews lease
setInterval(async () => {
  await renewClaimLease(currentTaskId, agentName);
}, CLAIM_HEARTBEAT_INTERVAL_MS);
```

**Benefits:**
- Supports long-running tasks (multi-hour processing)
- Clear expiration semantics (lease-based, not heartbeat-based)
- Prevents premature reclaims

**Trade-offs:**
- More complex than simple heartbeat
- Requires lease renewal logic in all agents

---

## Pattern: Claim Validation Before Action

**Problem:** Agent about to perform critical action; needs to verify it still owns task.

**Solution:** Re-read task and validate ownership before every critical action.

**Implementation:**
```javascript
async function performCriticalAction(taskId, agentName, action) {
  // Step 1: Re-read task to verify ownership
  const task = await readTaskFile(`In_Progress/${taskId}.json`);

  if (task.claimed_by !== agentName) {
    throw new Error(`Cannot perform action: task owned by ${task.claimed_by}, not ${agentName}`);
  }

  if (task.claim_id !== currentClaimId) {
    throw new Error(`Cannot perform action: claim_id mismatch (task was reclaimed)`);
  }

  // Step 2: Check if claim is still valid (not expired)
  const expiresAt = new Date(task.claim_expires_at);
  if (Date.now() > expiresAt.getTime()) {
    throw new Error(`Cannot perform action: claim expired at ${expiresAt.toISOString()}`);
  }

  // Step 3: Perform action
  console.log(`Performing action: ${action} on ${taskId}`);
  await action(task);

  // Step 4: Update heartbeat after action
  task.last_heartbeat = new Date().toISOString();
  await writeTaskFile(`In_Progress/${taskId}.json`, task);
}

// Usage
await performCriticalAction(taskId, agentName, async (task) => {
  // Deploy to production
  await deployToProduction(task.artifact);

  // Send notification
  await sendNotification(task.stakeholders, 'Deployment complete');
});
```

**Benefits:**
- Prevents actions by agents that lost ownership
- Safe for critical operations (deployments, notifications, etc.)
- Detects ownership changes immediately

**Trade-offs:**
- Extra filesystem reads (performance overhead)
- More verbose code (validation boilerplate)

---

## Anti-Pattern: Ignoring Heartbeat Failures

**NEVER DO THIS:**

```javascript
// BAD: Silently ignore heartbeat failures
setInterval(async () => {
  try {
    await updateHeartbeat();
  } catch (err) {
    // ❌ Swallow error and continue working
  }
}, CLAIM_HEARTBEAT_INTERVAL_MS);
```

**Why it's bad:**
- Coordinator will reclaim task (heartbeat appears stale)
- Agent continues working on reclaimed task (wasted effort)
- May cause duplicate work or conflicting updates

**Correct approach:**

```javascript
// GOOD: Abort work on repeated heartbeat failures
let heartbeatFailures = 0;
const MAX_HEARTBEAT_FAILURES = 3;

setInterval(async () => {
  try {
    await updateHeartbeat();
    heartbeatFailures = 0; // Reset on success
  } catch (err) {
    heartbeatFailures++;
    console.error(`Heartbeat failure ${heartbeatFailures}/${MAX_HEARTBEAT_FAILURES}: ${err.message}`);

    if (heartbeatFailures >= MAX_HEARTBEAT_FAILURES) {
      console.error(`Too many heartbeat failures; aborting work`);
      stopWork();
      process.exit(1); // Let orchestrator restart agent
    }
  }
}, CLAIM_HEARTBEAT_INTERVAL_MS);
```

---

## Summary

These patterns provide:
- **Optimistic locking** via heartbeat for crash detection
- **Idempotency** via claim IDs
- **Fair conflict resolution** via priority + timestamp
- **Human escalation** via conflict marker files
- **Graceful degradation** for unresolvable conflicts
- **Lease renewal** for long-running tasks
- **Validation** before critical actions

Use these patterns as building blocks for robust claim coordination.
