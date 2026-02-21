# Task Lifecycle Manager Gotchas

This document captures known issues, edge cases, and mitigation strategies specific to task lifecycle management.

---

## State Transition Gotchas

### Gotcha 1: Skipping Required Approval Stage

**Problem:**

Agent tries to move task directly from In_Progress to Done, bypassing human approval.

**Symptoms:**
- Security violation (auto-execution without approval)
- Audit trail shows illegal transition
- Permission error thrown

**Broken Pattern:**
```javascript
// WRONG - skips approval
await vaultManager.moveFile('In_Progress', 'task.json', 'Done', 'lex');
```

**Correct Pattern:**
```javascript
// CORRECT - goes through approval
await taskLifecycle.requestApproval(taskId, 'lex');
// Human approves → Approved/
// Orchestrator executes → Done/
```

**Mitigation:**

Always use lifecycle manager functions, which enforce state machine:
```javascript
// This will throw IllegalTransitionError
try {
  await taskLifecycle.transitionTask(taskId, 'in_progress', 'done', 'lex');
} catch (err) {
  if (err instanceof IllegalTransitionError) {
    console.error('Cannot skip approval stage');
  }
}
```

---

### Gotcha 2: Modifying Read-Only Stages

**Problem:**

Agent tries to update task file while it's in Pending_Approval (read-only).

**Symptoms:**
- PermissionError thrown
- Task not updated
- Agent confused why write failed

**Why It's Read-Only:**

Tasks in Pending_Approval/ are awaiting human decision. Agents must NOT modify them because:
1. Human is reviewing current state
2. Modifications would invalidate human's decision
3. Only human can move file (approve/reject)

**Correct Pattern:**

If agent wants to update task, must reject and recreate:
```javascript
// Human rejects task
// mv Pending_Approval/task.json Rejected/

// Lex reads rejection reason, creates NEW plan with updates
const newPlan = await createUpdatedPlan(originalTask, updates);
await taskLifecycle.claimTask(newPlan, 'lex');
```

---

### Gotcha 3: Multiple Agents Transition Same Task

**Problem:**

Two agents both think they own task, both try to transition it.

**Symptoms:**
- FileNotFoundError (task moved by first agent)
- Second agent thinks task disappeared
- Race condition

**Mitigation:**

Check ownership before transition:
```javascript
async function safeTransition(taskId, fromState, toState, agentName) {
  // Read task to verify ownership
  const folder = stateToFolder(fromState);
  const taskPath = `${folder}/${taskId}.json`;

  const { content } = await vaultManager.readVaultFile(taskPath, agentName);
  const task = JSON.parse(content);

  if (task.claimed_by !== agentName) {
    throw new OwnershipError(`Task ${taskId} owned by ${task.claimed_by}, not ${agentName}`);
  }

  // Proceed with transition
  return await taskLifecycle.transitionTask(taskId, fromState, toState, agentName);
}
```

---

## Claim Gotchas

### Gotcha 4: Claiming Already-Claimed Task

**Problem:**

Agent lists tasks, sees file, tries to claim it, but another agent claimed it first.

**Symptoms:**
- FileNotFoundError on move
- Agent thinks file disappeared
- Confusion in logs

**This Is NOT An Error:**

This is normal concurrent operation. The claim-by-move protocol means:
- First agent's move succeeds
- Second agent's move fails with FileNotFoundError
- Second agent should skip and try next task

**Correct Pattern:**
```javascript
const result = await taskLifecycle.claimTask(taskFile, agentName);

if (!result.success) {
  if (result.reason === 'already_claimed') {
    // Not an error, just concurrent access
    console.log('Task already claimed, trying next');
    return null;
  }
  throw new Error(`Unexpected claim failure: ${result.reason}`);
}
```

---

### Gotcha 5: Stale Claim Not Recovered

**Problem:**

Agent claims task, crashes before starting work. Task stuck in Plans/ forever.

**Symptoms:**
- Task never processed
- User reports "nothing happening"
- Plans/ folder grows

**Why It Happens:**

Agent claimed task (moved to Plans/) but crashed before:
1. Updating metadata (claimed_by)
2. Moving to In_Progress/
3. Starting work

**Mitigation:**

Run periodic stale claim recovery:
```javascript
// Every 10 minutes
setInterval(async () => {
  const staleThresholdMinutes = 60;
  await taskLifecycle.recoverStaleClaims(staleThresholdMinutes);
}, 600000);
```

**Detection Logic:**

Task in Plans/ AND (created_at > threshold) AND (no progress) → move back to Needs_Action

---

### Gotcha 6: Claim Metadata Not Updated

**Problem:**

Agent claims task (moves file) but forgets to update claimed_by metadata.

**Symptoms:**
- Ownership ambiguous
- Other agents think task is unclaimed
- Recovery jobs may incorrectly reclaim task

**Correct Pattern:**

Always update metadata immediately after claiming:
```javascript
async function claimTask(taskFile, agentName) {
  // Step 1: Move file (atomic claim)
  await vaultManager.moveFile('Needs_Action', taskFile, 'Plans', agentName);

  // Step 2: Update metadata (CRITICAL)
  const taskPath = `Plans/${taskFile}`;
  const { content } = await vaultManager.readVaultFile(taskPath, agentName);
  const task = JSON.parse(content);

  task.claimed_by = agentName;
  task.claimed_at = new Date().toISOString();
  task.status = 'planned';

  await vaultManager.writeVaultFile(taskPath, JSON.stringify(task, null, 2), agentName);

  return { success: true, taskId: task.plan_id };
}
```

---

## Retry Gotchas

### Gotcha 7: Infinite Retry Loop

**Problem:**

Task fails permanently (e.g., invalid input), but retry logic keeps retrying forever.

**Symptoms:**
- High CPU usage
- Task never completes
- Logs full of same error

**Mitigation:**

Distinguish transient vs permanent errors:
```javascript
async function handleTaskFailure(taskId, error, agentName) {
  // Permanent errors: don't retry
  if (error instanceof ValidationError ||
      error instanceof AuthenticationError ||
      error instanceof PermissionError) {
    // Reject immediately
    await rejectTask(taskId, error.message, agentName);
    return { action: 'failed', reason: 'permanent_error' };
  }

  // Transient errors: retry with limit
  if (task.retry_metadata.attempts < MAX_RETRIES) {
    return await retryTask(taskId, agentName);
  }

  // Max retries exceeded
  await rejectTask(taskId, 'Max retries exceeded', agentName);
  return { action: 'failed', reason: 'max_retries' };
}
```

---

### Gotcha 8: Retry Counter Lost

**Problem:**

Task fails, moves back to Needs_Action, but retry counter is reset to 0.

**Symptoms:**
- Task retries infinitely (counter never increments)
- Max retries never reached
- Task loops forever

**Mitigation:**

Preserve retry metadata across transitions:
```javascript
async function retryTask(taskId, agentName) {
  const taskPath = `In_Progress/${taskId}.json`;
  const { content } = await vaultManager.readVaultFile(taskPath, agentName);
  const task = JSON.parse(content);

  // Increment retry counter (CRITICAL - don't reset!)
  if (!task.retry_metadata) {
    task.retry_metadata = { attempts: 0, max_retries: 3 };
  }
  task.retry_metadata.attempts += 1;

  // Move back to Needs_Action
  await vaultManager.writeVaultFile(taskPath, JSON.stringify(task, null, 2), agentName);
  await vaultManager.moveFile('In_Progress', `${taskId}.json`, 'Needs_Action', agentName);
}
```

---

### Gotcha 9: No Exponential Backoff

**Problem:**

Task fails, retries immediately, fails again, retries immediately. Creates retry storm.

**Symptoms:**
- High CPU usage
- API rate limits hit
- Logs flooded with retries

**Mitigation:**

Implement exponential backoff:
```javascript
async function retryTask(taskId, agentName) {
  // ... update retry_metadata ...

  // Calculate backoff delay
  const attempt = task.retry_metadata.attempts;
  const baseDelay = 1000;  // 1 second
  const delay = Math.pow(2, attempt) * baseDelay;  // 2s, 4s, 8s, 16s...

  task.retry_metadata.next_retry_at = new Date(Date.now() + delay).toISOString();

  await vaultManager.writeVaultFile(taskPath, JSON.stringify(task, null, 2), agentName);

  // Agent should respect next_retry_at before reclaiming
}

// In claim logic
async function claimTask(taskFile, agentName) {
  const { content } = await vaultManager.readVaultFile(`Needs_Action/${taskFile}`, agentName);
  const task = JSON.parse(content);

  // Check if retry is due
  if (task.retry_metadata?.next_retry_at) {
    const nextRetry = new Date(task.retry_metadata.next_retry_at).getTime();
    if (Date.now() < nextRetry) {
      console.log(`Task ${taskFile} not ready for retry yet`);
      return { success: false, reason: 'retry_not_due' };
    }
  }

  // Proceed with claim
  // ...
}
```

---

## Recovery Gotchas

### Gotcha 10: Recovery Job Runs Too Frequently

**Problem:**

Recovery job runs every second, constantly reclaiming tasks.

**Symptoms:**
- High CPU usage
- Tasks never complete (constantly reclaimed)
- Logs flooded with recovery messages

**Mitigation:**

Set reasonable recovery intervals:
```javascript
// WRONG - runs every second
setInterval(async () => {
  await taskLifecycle.recoverStaleClaims(60);
}, 1000);  // Too frequent!

// CORRECT - runs every 5 minutes
setInterval(async () => {
  await taskLifecycle.recoverStaleClaims(60);
}, 300000);  // 5 minutes
```

**Recommended Intervals:**
- Stale claim recovery: Every 5-10 minutes
- Orphaned task recovery: Every 5-10 minutes
- Duplicate detection: Every 30 minutes
- Health check: Every 10-15 minutes

---

### Gotcha 11: Recovery Threshold Too Aggressive

**Problem:**

Stale threshold set to 5 minutes. Tasks that legitimately take 10 minutes are constantly reclaimed.

**Symptoms:**
- Tasks never complete
- Agent A starts work, recovery job reclaims after 5 min, Agent B starts, reclaimed again
- Infinite loop

**Mitigation:**

Set conservative thresholds:
```javascript
// WRONG - too aggressive
await taskLifecycle.recoverStaleClaims(5);  // 5 minutes

// CORRECT - conservative
await taskLifecycle.recoverStaleClaims(60);  // 60 minutes

// Better: Make it configurable
const threshold = parseInt(process.env.TASK_STALE_THRESHOLD_MINUTES || '60');
await taskLifecycle.recoverStaleClaims(threshold);
```

**Recommended Thresholds:**
- Stale claims (Plans/): 60 minutes
- Orphaned tasks (In_Progress/): 30 minutes
- Stuck in Pending_Approval: 4 hours (alert only)

---

### Gotcha 12: Recovery Job Doesn't Check Heartbeat

**Problem:**

Task actively being processed, but recovery job reclaims it because modified time is old.

**Symptoms:**
- Agent loses work mid-processing
- Logs show "recovered orphan" for active task
- Confusion and wasted work

**Mitigation:**

Implement heartbeat mechanism:
```javascript
// Agent updates heartbeat periodically
async function updateHeartbeat(taskId, agentName) {
  const taskPath = `In_Progress/${taskId}.json`;
  const { content } = await vaultManager.readVaultFile(taskPath, agentName);
  const task = JSON.parse(content);

  task.last_heartbeat = new Date().toISOString();

  await vaultManager.writeVaultFile(taskPath, JSON.stringify(task, null, 2), agentName);
}

// Update heartbeat every minute while processing
const heartbeatInterval = setInterval(async () => {
  await updateHeartbeat(taskId, agentName);
}, 60000);

// Recovery job checks heartbeat
async function recoverOrphanedTasks(orphanThresholdMinutes) {
  // ...
  const lastHeartbeat = task.last_heartbeat
    ? new Date(task.last_heartbeat).getTime()
    : file.modified.getTime();

  if (lastHeartbeat < orphanTime) {
    // Truly orphaned
    await recoverTask(task);
  }
}
```

---

## Conflict Resolution Gotchas

### Gotcha 13: Duplicate Not Detected (Different Folders)

**Problem:**

Same task appears in Plans/ and In_Progress/ (duplicate), but detection misses it.

**Symptoms:**
- Two agents process same task
- Duplicate actions (e.g., same email sent twice)
- Inconsistent results

**Why It Happens:**

Duplicate detection only scans one folder at a time.

**Mitigation:**

Scan ALL folders in duplicate detection:
```javascript
async function detectDuplicateTasks() {
  const allTasks = {};
  const duplicates = [];

  // CRITICAL: Scan ALL lifecycle folders
  const folders = [
    'Needs_Action',
    'Plans',
    'In_Progress',
    'Pending_Approval',
    'Approved',
    'Done'  // Include Done to detect historical duplicates
  ];

  for (const folder of folders) {
    const files = await vaultManager.listFolderFiles(folder);

    for (const file of files) {
      const { content } = await vaultManager.readVaultFile(`${folder}/${file.name}`, 'system');
      const task = JSON.parse(content);

      if (allTasks[task.plan_id]) {
        // Duplicate found!
        duplicates.push({
          taskId: task.plan_id,
          locations: [allTasks[task.plan_id], `${folder}/${file.name}`]
        });
      } else {
        allTasks[task.plan_id] = `${folder}/${file.name}`;
      }
    }
  }

  return duplicates;
}
```

---

### Gotcha 14: Circular Dependencies Not Detected

**Problem:**

Task A waits for Task B, Task B waits for Task A. Both stuck forever.

**Symptoms:**
- Tasks never complete
- Both in In_Progress/ forever
- No progress despite no errors

**Mitigation:**

Detect dependency cycles before starting work:
```javascript
async function detectCircularDependencies(taskId, visited = new Set()) {
  if (visited.has(taskId)) {
    // Cycle detected!
    return visited;
  }

  visited.add(taskId);

  const task = await readTask(taskId);

  if (task.dependencies) {
    for (const depId of task.dependencies) {
      const cycle = await detectCircularDependencies(depId, visited);
      if (cycle) return cycle;
    }
  }

  visited.delete(taskId);
  return null;
}

// Before starting work
async function startWork(taskId, agentName) {
  const cycle = await detectCircularDependencies(taskId);

  if (cycle) {
    throw new CircularDependencyError(`Task ${taskId} has circular dependency: ${Array.from(cycle).join(' → ')}`);
  }

  // Proceed with work
  // ...
}
```

---

## Performance Gotchas

### Gotcha 15: Listing Files on Every Claim Attempt

**Problem:**

Agent lists Needs_Action/ every second to check for new tasks. High I/O.

**Symptoms:**
- High disk I/O
- Slow responses
- Filesystem contention

**Mitigation:**

Cache file list and poll periodically:
```javascript
let cachedTaskList = [];
let lastListTime = 0;
const LIST_CACHE_MS = 5000;  // 5 seconds

async function listTasksWithCache() {
  const now = Date.now();

  if (now - lastListTime > LIST_CACHE_MS) {
    cachedTaskList = await vaultManager.listFolderFiles('Needs_Action');
    lastListTime = now;
  }

  return cachedTaskList;
}

// Agent loop
while (true) {
  const tasks = await listTasksWithCache();

  for (const task of tasks) {
    const result = await claimTask(task.name, agentName);
    if (result.success) {
      // Process task
      break;
    }
  }

  await new Promise(resolve => setTimeout(resolve, 5000));  // Wait 5s
}
```

---

### Gotcha 16: Loading All Task Files Into Memory

**Problem:**

Health check loads all task files from all folders into memory. Runs out of memory.

**Symptoms:**
- OutOfMemoryError
- Agent crashes
- High memory usage

**Mitigation:**

Process files one at a time:
```javascript
async function detectDuplicateTasks() {
  const seenIds = new Set();
  const duplicates = [];

  const folders = ['Needs_Action', 'Plans', 'In_Progress', ...];

  for (const folder of folders) {
    const files = await vaultManager.listFolderFiles(folder);

    // Process files one at a time (don't load all into array)
    for (const file of files) {
      try {
        const { content } = await vaultManager.readVaultFile(`${folder}/${file.name}`, 'system');
        const task = JSON.parse(content);

        if (seenIds.has(task.plan_id)) {
          duplicates.push({ taskId: task.plan_id, file: `${folder}/${file.name}` });
        } else {
          seenIds.add(task.plan_id);
        }

        // Release task object (let GC collect it)
      } catch (err) {
        console.error(`Failed to process ${file.name}:`, err.message);
      }
    }
  }

  return duplicates;
}
```

---

## Security Gotchas

### Gotcha 17: Agent Bypasses Lifecycle Manager

**Problem:**

Agent uses vault_state_manager directly to move task, bypassing permission checks.

**Symptoms:**
- Security violation (lex approves own task)
- Audit trail incomplete
- State machine violated

**Example:**
```javascript
// WRONG - bypasses lifecycle manager
await vaultManager.moveFile('In_Progress', 'task.json', 'Approved', 'lex');
// lex just approved its own task!

// CORRECT - use lifecycle manager
await taskLifecycle.requestApproval(taskId, 'lex');
// Task goes to Pending_Approval/, human must approve
```

**Mitigation:**

Enforce usage of lifecycle manager:
- Code review: flag direct vault_state_manager usage for state transitions
- Linting: detect `vaultManager.moveFile()` calls in agent code
- Runtime checks: vault_state_manager logs all moves, detect illegal patterns

---

### Gotcha 18: Sensitive Data in Task Metadata

**Problem:**

Task metadata contains API keys, passwords, or PII. Logged to audit trail.

**Symptoms:**
- Secrets leaked in logs
- Privacy violation
- Security issue

**Mitigation:**

Sanitize metadata before logging:
```javascript
function sanitizeTask(task) {
  const sanitized = {
    plan_id: task.plan_id,
    status: task.status,
    title: task.title,
    priority: task.priority,
    steps: task.steps.map(s => ({
      action: s.action,  // Don't include step details
      status: s.status
    }))
    // Don't log: data, result, work_result (may contain secrets)
  };

  return sanitized;
}

async function logTransition(taskId, fromState, toState, agentName) {
  const task = await readTask(taskId);
  const sanitized = sanitizeTask(task);

  await appendLog('task-transitions.json', {
    timestamp: new Date().toISOString(),
    event: 'transition',
    task: sanitized,
    from: fromState,
    to: toState,
    by: agentName
  });
}
```

---

## Known Issues & Workarounds

### Issue 1: Cannot Transition Task Back (No Undo)

**Problem:**

Task accidentally moved to wrong state. No undo function.

**Workaround:**

Manually move file back:
```bash
# Oops, moved to Approved by mistake
mv vault/Approved/task.json vault/Pending_Approval/

# Update metadata manually
jq '.status = "pending_approval"' vault/Pending_Approval/task.json > tmp && mv tmp vault/Pending_Approval/task.json
```

**Future Enhancement:**

Implement transition history and rollback:
```javascript
task.transition_history = [
  { from: 'planned', to: 'in_progress', at: '2024-01-15T10:00:00Z' },
  { from: 'in_progress', to: 'pending_approval', at: '2024-01-15T11:00:00Z' },
  { from: 'pending_approval', to: 'approved', at: '2024-01-15T12:00:00Z' }  // Mistake
];

// Rollback to previous state
await taskLifecycle.rollback(taskId, 1);  // Go back 1 step
```

---

### Issue 2: No Atomic Multi-File Transitions

**Problem:**

Task depends on another task. Both must transition together. Not atomic.

**Workaround:**

Use dependency tracking:
```javascript
task.dependencies = ['plan-1705320000001'];  // Wait for this task

// Before starting work, check dependencies
async function checkDependencies(taskId) {
  const task = await readTask(taskId);

  for (const depId of task.dependencies) {
    const dep = await readTask(depId);
    if (dep.status !== 'done') {
      throw new DependencyNotMetError(`Task ${taskId} depends on ${depId} which is ${dep.status}`);
    }
  }
}
```

---

## Emergency Procedures

### Procedure 1: Task Stuck in In_Progress

**Symptoms:** Task in In_Progress/ for hours, no progress

**Steps:**
1. Check if agent is still running: `ps aux | grep lex`
2. Check task heartbeat: `jq '.last_heartbeat' vault/In_Progress/task.json`
3. If agent dead or heartbeat stale, move back to Needs_Action:
   ```bash
   mv vault/In_Progress/task.json vault/Needs_Action/
   jq '.status = "needs_action"' vault/Needs_Action/task.json > tmp && mv tmp vault/Needs_Action/task.json
   ```

---

### Procedure 2: Duplicate Tasks Executing

**Symptoms:** Same action happens twice (e.g., same email sent twice)

**Steps:**
1. Run duplicate detection: `node scripts/detect-duplicates.js`
2. Identify duplicate locations
3. Keep oldest, reject rest:
   ```bash
   mv vault/In_Progress/task-duplicate.json vault/Rejected/
   echo "Duplicate of task-original.json" > vault/Rejected/task-duplicate.rejection.md
   ```

---

## Summary

**Top 5 Gotchas to Remember:**

1. ✅ Always use lifecycle manager (not raw vault manager for transitions)
2. ✅ Check claim results (handle already_claimed gracefully)
3. ✅ Distinguish transient vs permanent errors (don't retry forever)
4. ✅ Set conservative recovery thresholds (don't reclaim active tasks)
5. ✅ Sanitize task metadata before logging (no secrets in logs)

**When in Doubt:**
- Read state machine diagram (SKILL.md)
- Check agent permissions (AGENTS.md §3)
- Review patterns (references/patterns.md)
- Run health check (detect issues early)
