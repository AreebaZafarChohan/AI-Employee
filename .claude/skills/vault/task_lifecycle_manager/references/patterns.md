# Task Lifecycle Manager Patterns

This document provides concrete code examples for managing task lifecycles in the Digital FTE workflow.

## Table of Contents

1. [Basic Lifecycle Operations](#basic-lifecycle-operations)
2. [Claim Semantics](#claim-semantics)
3. [State Transitions](#state-transitions)
4. [Retry Logic](#retry-logic)
5. [Conflict Resolution](#conflict-resolution)
6. [Recovery Mechanisms](#recovery-mechanisms)

---

## Basic Lifecycle Operations

### Pattern 1: Claim Task from Needs_Action

**Use Case:** Lex claims a new task to process

```javascript
const taskLifecycle = require('./task-lifecycle-manager');

async function claimAndProcess(taskFile, agentName) {
  // Step 1: Attempt to claim task
  const claimResult = await taskLifecycle.claimTask(taskFile, agentName);

  if (!claimResult.success) {
    if (claimResult.reason === 'already_claimed') {
      console.log(`Task ${taskFile} already claimed by another agent`);
      return null;  // Not an error, just concurrent access
    }
    throw new Error(`Failed to claim task: ${claimResult.reason}`);
  }

  console.log(`Successfully claimed task: ${claimResult.taskId}`);

  // Step 2: Start work on claimed task
  await taskLifecycle.startWork(claimResult.taskId, agentName);

  return claimResult.taskId;
}

// Usage
const taskId = await claimAndProcess('2024-01-15T10:30:00Z-abc123.json', 'lex');
if (taskId) {
  console.log(`Now working on: ${taskId}`);
}
```

**Expected Output:**
```
Successfully claimed task: plan-1705320000000
Now working on: plan-1705320000000
```

---

### Pattern 2: Complete Work and Request Approval

**Use Case:** Lex finishes work and requests human approval

```javascript
async function completeAndRequestApproval(taskId, agentName, workResult) {
  // Step 1: Update task with work results
  const taskPath = `In_Progress/${taskId}.json`;
  const { content } = await vaultManager.readVaultFile(taskPath, agentName);
  const task = JSON.parse(content);

  // Add completion metadata
  task.work_result = workResult;
  task.completed_at = new Date().toISOString();

  await vaultManager.writeVaultFile(
    taskPath,
    JSON.stringify(task, null, 2),
    agentName
  );

  // Step 2: Transition to Pending_Approval
  const result = await taskLifecycle.transitionTask(
    taskId,
    'in_progress',
    'pending_approval',
    agentName
  );

  console.log(`Task ${taskId} moved to Pending_Approval`);
  console.log(`  Old path: ${result.oldPath}`);
  console.log(`  New path: ${result.newPath}`);

  return result;
}

// Usage
const workResult = {
  summary: 'Email drafted and ready to send',
  details: 'Invoice attached, recipient verified',
  confidence: 0.95
};

await completeAndRequestApproval('plan-1705320000000', 'lex', workResult);
```

---

### Pattern 3: Execute Approved Task (Orchestrator)

**Use Case:** Orchestrator processes approved task

```javascript
async function executeApprovedTask(taskFile, agentName) {
  // Step 1: Claim task from Approved/
  const claimResult = await taskLifecycle.claimFromApproved(taskFile, agentName);

  if (!claimResult.success) {
    console.log(`Task ${taskFile} already claimed`);
    return null;
  }

  const taskId = claimResult.taskId;

  // Step 2: Read task details
  const taskPath = `In_Progress/${taskFile}`;
  const { content } = await vaultManager.readVaultFile(taskPath, agentName);
  const task = JSON.parse(content);

  // Step 3: Execute task via MCP
  let outcome = 'success';
  let error = null;

  try {
    await executePlanViaMCP(task);
  } catch (err) {
    outcome = 'failure';
    error = err;
  }

  // Step 4: Handle result
  if (outcome === 'success') {
    await taskLifecycle.completeTask(taskId, agentName);
    console.log(`Task ${taskId} completed successfully`);
  } else {
    await taskLifecycle.handleTaskFailure(taskId, error, agentName);
    console.log(`Task ${taskId} failed: ${error.message}`);
  }

  return { taskId, outcome };
}
```

---

## Claim Semantics

### Pattern 4: Claim with Conflict Detection

**Use Case:** Multiple agents try to claim same task

```javascript
async function claimWithConflictHandling(taskFile, agentName) {
  try {
    const result = await taskLifecycle.claimTask(taskFile, agentName);

    if (result.success) {
      console.log(`${agentName}: Claimed ${taskFile}`);
      return result.taskId;
    } else {
      console.log(`${agentName}: ${result.reason}`);
      return null;
    }
  } catch (err) {
    console.error(`${agentName}: Unexpected error:`, err.message);
    throw err;
  }
}

// Simulate concurrent claims
async function simulateConcurrentClaims() {
  const taskFile = '2024-01-15T10:30:00Z-abc123.json';

  // Two agents try to claim same task
  const [result1, result2] = await Promise.all([
    claimWithConflictHandling(taskFile, 'lex-1'),
    claimWithConflictHandling(taskFile, 'lex-2')
  ]);

  console.log('Results:', { result1, result2 });
  // Only one will have a taskId, other will be null
}
```

**Expected Output:**
```
lex-1: Claimed 2024-01-15T10:30:00Z-abc123.json
lex-2: already_claimed
Results: { result1: 'plan-1705320000000', result2: null }
```

---

### Pattern 5: Claim with Validation

**Use Case:** Ensure task is valid before claiming

```javascript
async function claimWithValidation(taskFile, agentName) {
  // Step 1: Read task without claiming
  const previewPath = `Needs_Action/${taskFile}`;

  let task;
  try {
    const { content } = await vaultManager.readVaultFile(previewPath, agentName);
    task = JSON.parse(content);
  } catch (err) {
    if (err instanceof vaultManager.FileNotFoundError) {
      return { success: false, reason: 'already_claimed' };
    }
    throw err;
  }

  // Step 2: Validate task
  if (!task.data || !task.data.subject) {
    console.warn(`Invalid task: ${taskFile} (missing subject)`);
    return { success: false, reason: 'invalid_task' };
  }

  if (task.priority === 'critical' && agentName !== 'lex-priority') {
    console.log(`Task ${taskFile} requires priority agent`);
    return { success: false, reason: 'permission_denied' };
  }

  // Step 3: Claim task
  return await taskLifecycle.claimTask(taskFile, agentName);
}
```

---

## State Transitions

### Pattern 6: Full Task Lifecycle (Lex Perspective)

**Use Case:** Lex processes a task from start to finish

```javascript
async function processTaskFullLifecycle(taskFile, agentName) {
  console.log('=== Starting Task Lifecycle ===');

  // Stage 1: Claim from Needs_Action
  console.log('Stage 1: Claiming task...');
  const claimResult = await taskLifecycle.claimTask(taskFile, agentName);

  if (!claimResult.success) {
    console.log(`Cannot claim: ${claimResult.reason}`);
    return;
  }

  const taskId = claimResult.taskId;
  console.log(`✓ Claimed: ${taskId}`);

  // Stage 2: Move to In_Progress
  console.log('Stage 2: Starting work...');
  await taskLifecycle.startWork(taskId, agentName);
  console.log(`✓ Task in progress`);

  // Stage 3: Execute work
  console.log('Stage 3: Executing steps...');
  try {
    await executeTaskSteps(taskId, agentName);
    console.log(`✓ Work completed`);
  } catch (err) {
    console.error(`✗ Work failed: ${err.message}`);
    await taskLifecycle.handleTaskFailure(taskId, err, agentName);
    return;
  }

  // Stage 4: Request approval
  console.log('Stage 4: Requesting approval...');
  await taskLifecycle.requestApproval(taskId, agentName);
  console.log(`✓ Awaiting human approval`);

  console.log('=== Task Lifecycle Complete (Pending Approval) ===');
}

async function executeTaskSteps(taskId, agentName) {
  const taskPath = `In_Progress/${taskId}.json`;
  const { content } = await vaultManager.readVaultFile(taskPath, agentName);
  const task = JSON.parse(content);

  for (let i = 0; i < task.steps.length; i++) {
    console.log(`  Executing step ${i + 1}/${task.steps.length}: ${task.steps[i].action}`);

    // Simulate work
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Update step status
    task.steps[i].status = 'completed';
    task.steps[i].completed_at = new Date().toISOString();

    await vaultManager.writeVaultFile(
      taskPath,
      JSON.stringify(task, null, 2),
      agentName
    );
  }
}
```

**Expected Output:**
```
=== Starting Task Lifecycle ===
Stage 1: Claiming task...
✓ Claimed: plan-1705320000000
Stage 2: Starting work...
✓ Task in progress
Stage 3: Executing steps...
  Executing step 1/3: Query accounting system
  Executing step 2/3: Generate PDF invoice
  Executing step 3/3: Draft email response
✓ Work completed
Stage 4: Requesting approval...
✓ Awaiting human approval
=== Task Lifecycle Complete (Pending Approval) ===
```

---

### Pattern 7: Orchestrator Execution Cycle

**Use Case:** Orchestrator continuously processes approved tasks

```javascript
async function orchestratorLoop(agentName) {
  console.log('Orchestrator started, polling for approved tasks...');

  while (true) {
    // Step 1: Check for approved tasks
    const approvedFiles = await vaultManager.listFolderFiles('Approved');

    if (approvedFiles.length === 0) {
      await new Promise(resolve => setTimeout(resolve, 5000));  // Wait 5s
      continue;
    }

    console.log(`Found ${approvedFiles.length} approved tasks`);

    // Step 2: Process oldest task first
    const file = approvedFiles[0];

    try {
      const result = await executeApprovedTask(file.name, agentName);

      if (result) {
        console.log(`Processed: ${result.taskId} (${result.outcome})`);
      }
    } catch (err) {
      console.error(`Failed to process ${file.name}:`, err.message);
    }
  }
}

// Run orchestrator
orchestratorLoop('orch').catch(err => {
  console.error('Orchestrator crashed:', err);
  process.exit(1);
});
```

---

## Retry Logic

### Pattern 8: Task Failure with Automatic Retry

**Use Case:** Task fails due to transient error

```javascript
async function executeTaskWithRetry(taskId, agentName) {
  const taskPath = `In_Progress/${taskId}.json`;
  const { content } = await vaultManager.readVaultFile(taskPath, agentName);
  const task = JSON.parse(content);

  try {
    // Simulate work that might fail
    await performTaskAction(task);

    // Success: mark as completed
    await taskLifecycle.completeTask(taskId, agentName);
    return { success: true };
  } catch (err) {
    console.error(`Task ${taskId} failed: ${err.message}`);

    // Handle failure (retry or permanent failure)
    const retryResult = await taskLifecycle.handleTaskFailure(taskId, err, agentName);

    if (retryResult.action === 'retry') {
      console.log(`Task will retry (attempt ${retryResult.attempts})`);
      return { success: false, willRetry: true, attempts: retryResult.attempts };
    } else {
      console.log(`Task failed permanently: ${retryResult.reason}`);
      return { success: false, willRetry: false, reason: retryResult.reason };
    }
  }
}

async function performTaskAction(task) {
  // Simulate transient failure (e.g., API timeout)
  if (Math.random() < 0.3) {
    throw new Error('API timeout (transient)');
  }

  console.log('Task action completed');
}
```

**Example Execution (with retry):**

```
Task plan-1705320000000 failed: API timeout (transient)
Task will retry (attempt 1)

[Task moved back to Needs_Action, will be picked up again]

Task plan-1705320000000 failed: API timeout (transient)
Task will retry (attempt 2)

[Task picked up again after backoff]

Task action completed
Task plan-1705320000000 completed successfully
```

---

### Pattern 9: Max Retries Exceeded

**Use Case:** Task fails permanently after max retries

```javascript
async function taskWithMaxRetries(taskId, agentName) {
  const maxRetries = 3;
  let attempt = 0;

  while (attempt < maxRetries) {
    try {
      await performUnreliableOperation();
      return { success: true };
    } catch (err) {
      attempt++;
      console.log(`Attempt ${attempt}/${maxRetries} failed`);

      if (attempt >= maxRetries) {
        // Permanently fail
        await taskLifecycle.handleTaskFailure(taskId, err, agentName);
        return { success: false, reason: 'max_retries' };
      }

      // Exponential backoff
      const delay = Math.pow(2, attempt) * 1000;
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
}
```

---

## Conflict Resolution

### Pattern 10: Detect and Resolve Stale Claims

**Use Case:** Task stuck in Plans/ for too long

```javascript
async function recoverStaleClaimsJob() {
  console.log('Running stale claims recovery...');

  const staleThresholdMinutes = 60;
  const recovered = await taskLifecycle.recoverStaleClaims(staleThresholdMinutes);

  console.log(`Recovered ${recovered} stale claims`);

  return recovered;
}

// Run recovery job every 5 minutes
setInterval(async () => {
  try {
    await recoverStaleClaimsJob();
  } catch (err) {
    console.error('Recovery job failed:', err);
  }
}, 300000);  // 5 minutes
```

---

### Pattern 11: Detect and Recover Orphaned Tasks

**Use Case:** Agent crashed while processing task

```javascript
async function recoverOrphanedTasks(orphanThresholdMinutes = 30) {
  console.log('Checking for orphaned tasks...');

  const inProgressFiles = await vaultManager.listFolderFiles('In_Progress');
  const orphanTime = Date.now() - (orphanThresholdMinutes * 60 * 1000);

  let recovered = 0;

  for (const file of inProgressFiles) {
    // Check if task has been in In_Progress for too long without updates
    if (file.modified.getTime() < orphanTime) {
      const { content } = await vaultManager.readVaultFile(
        `In_Progress/${file.name}`,
        'system'
      );
      const task = JSON.parse(content);

      // Check if task has heartbeat (if implemented)
      const lastHeartbeat = task.last_heartbeat
        ? new Date(task.last_heartbeat).getTime()
        : file.modified.getTime();

      if (lastHeartbeat < orphanTime) {
        console.log(`Orphaned task detected: ${file.name}`);

        // Move back to Needs_Action for retry
        task.status = 'needs_action';
        task.orphan_recovery = {
          recovered_at: new Date().toISOString(),
          was_owned_by: task.claimed_by,
          reason: 'no_heartbeat_timeout'
        };

        await vaultManager.writeVaultFile(
          `In_Progress/${file.name}`,
          JSON.stringify(task, null, 2),
          'system'
        );

        await vaultManager.moveFile(
          'In_Progress',
          file.name,
          'Needs_Action',
          'system'
        );

        recovered++;
      }
    }
  }

  console.log(`Recovered ${recovered} orphaned tasks`);
  return recovered;
}
```

---

### Pattern 12: Detect Duplicate Tasks

**Use Case:** Same task appears in multiple folders

```javascript
async function detectDuplicateTasks() {
  console.log('Scanning for duplicate tasks...');

  const allTasks = {};
  const duplicates = [];

  const folders = ['Needs_Action', 'Plans', 'In_Progress', 'Pending_Approval', 'Approved'];

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

  if (duplicates.length > 0) {
    console.warn(`Found ${duplicates.length} duplicate tasks:`);
    duplicates.forEach(dup => {
      console.warn(`  ${dup.taskId}:`);
      dup.locations.forEach(loc => console.warn(`    - ${loc}`));
    });

    // Resolve duplicates: keep oldest, reject rest
    for (const dup of duplicates) {
      await resolveDuplicate(dup);
    }
  } else {
    console.log('No duplicates found');
  }

  return duplicates;
}

async function resolveDuplicate(duplicate) {
  const locations = duplicate.locations;

  // Keep first location (oldest), reject rest
  const toKeep = locations[0];
  const toReject = locations.slice(1);

  console.log(`Keeping: ${toKeep}`);

  for (const loc of toReject) {
    const [folder, filename] = loc.split('/');

    // Add -duplicate suffix
    const newFilename = filename.replace('.json', '-duplicate.json');

    // Move to Rejected
    await vaultManager.moveFile(folder, filename, 'Rejected', 'system');

    console.log(`Rejected duplicate: ${loc} → Rejected/${newFilename}`);
  }
}
```

---

## Recovery Mechanisms

### Pattern 13: Comprehensive Health Check

**Use Case:** Run all recovery mechanisms periodically

```javascript
async function runHealthCheck() {
  console.log('=== Task Lifecycle Health Check ===');

  const results = {
    staleClaims: 0,
    orphanedTasks: 0,
    duplicates: 0,
    corruptedFiles: 0
  };

  try {
    // 1. Recover stale claims
    results.staleClaims = await taskLifecycle.recoverStaleClaims(60);

    // 2. Recover orphaned tasks
    results.orphanedTasks = await recoverOrphanedTasks(30);

    // 3. Detect duplicates
    const dups = await detectDuplicateTasks();
    results.duplicates = dups.length;

    // 4. Detect corrupted files
    results.corruptedFiles = await detectCorruptedFiles();

    console.log('=== Health Check Complete ===');
    console.log(`  Stale claims recovered: ${results.staleClaims}`);
    console.log(`  Orphaned tasks recovered: ${results.orphanedTasks}`);
    console.log(`  Duplicates resolved: ${results.duplicates}`);
    console.log(`  Corrupted files moved: ${results.corruptedFiles}`);

    return results;
  } catch (err) {
    console.error('Health check failed:', err);
    throw err;
  }
}

async function detectCorruptedFiles() {
  const folders = ['Needs_Action', 'Plans', 'In_Progress', 'Pending_Approval', 'Approved', 'Done'];
  let corrupted = 0;

  for (const folder of folders) {
    const files = await vaultManager.listFolderFiles(folder);

    for (const file of files) {
      try {
        const { content } = await vaultManager.readVaultFile(`${folder}/${file.name}`, 'system');
        JSON.parse(content);  // Validate JSON
      } catch (err) {
        console.warn(`Corrupted file: ${folder}/${file.name}`);

        // Move to Rejected with reason
        await vaultManager.moveFile(folder, file.name, 'Rejected', 'system');

        // Add rejection reason
        const rejectionPath = `Rejected/${file.name.replace('.json', '.rejection.md')}`;
        await vaultManager.writeVaultFile(
          rejectionPath,
          `# Corruption Detected\n\nFile corrupted (invalid JSON): ${err.message}\n\nMoved by health check at ${new Date().toISOString()}`,
          'system'
        );

        corrupted++;
      }
    }
  }

  return corrupted;
}

// Run health check every 10 minutes
setInterval(async () => {
  try {
    await runHealthCheck();
  } catch (err) {
    console.error('Health check failed:', err);
  }
}, 600000);  // 10 minutes
```

---

## Best Practices Summary

1. **Always check claim results** - handle `already_claimed` gracefully
2. **Use lifecycle manager for transitions** - don't bypass state machine
3. **Implement retry logic** - transient failures are expected
4. **Run periodic recovery jobs** - detect and fix stale/orphaned tasks
5. **Log all transitions** - audit trail for debugging
6. **Sanitize sensitive data** - don't leak secrets in logs
7. **Handle conflicts deterministically** - first mover wins
8. **Validate tasks before claiming** - reject invalid tasks early
9. **Use exponential backoff** - prevent retry storms
10. **Monitor health metrics** - track recovery job effectiveness
