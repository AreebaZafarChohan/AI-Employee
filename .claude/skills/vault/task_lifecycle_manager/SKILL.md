---
name: task_lifecycle_manager
description: Manages the lifecycle of tasks in the Obsidian vault for Digital FTE. Implements claim-by-move semantics, state transitions, conflict avoidance, and predictable outcomes for each transition stage.
---

# Task Lifecycle Manager

## Purpose

This skill provides agents with structured task lifecycle management for the Digital FTE workflow. It builds on the `vault_state_manager` skill to implement higher-level task state transitions, claim semantics, conflict resolution, and workflow orchestration.

While `vault_state_manager` provides low-level file operations, `task_lifecycle_manager` provides task-aware workflows that understand the business logic of task processing.

## When to Use This Skill

Use `task_lifecycle_manager` when:

- **Claiming work**: Agent wants to claim a task from Needs_Action
- **Starting work**: Move task from Plans to In_Progress
- **Requesting approval**: Move task from In_Progress to Pending_Approval
- **Completing work**: Move task from Approved to Done (via orchestrator)
- **Handling conflicts**: Multiple agents try to claim same task
- **Managing retries**: Task failed and needs to be retried
- **Tracking progress**: Update task status within current stage
- **Enforcing workflows**: Ensure state transitions follow business rules

Do NOT use this skill when:

- **Low-level file ops**: Use `vault_state_manager` for simple read/write/move
- **Non-task files**: This is for task/plan files only (JSON with lifecycle metadata)
- **Human operations**: Humans can move files directly; this is for agent automation
- **Log management**: Use dedicated logging functions

## Impact Analysis Workflow

### 1. Environment Variable Strategy

**Build-Time vs Runtime Variables:**

This skill operates at runtime only. No build-time variables required.

**Runtime variables:**
```bash
# Required (inherited from vault_state_manager)
VAULT_PATH="/absolute/path/to/vault"

# Optional: Task lifecycle tuning
TASK_CLAIM_TIMEOUT_MS="5000"           # Timeout for claiming tasks
TASK_MAX_RETRIES="3"                   # Max retries for failed tasks
TASK_RETRY_BACKOFF_MS="1000"           # Exponential backoff base
TASK_CONFLICT_STRATEGY="skip"          # skip | retry | fail

# Optional: Workflow policies
TASK_AUTO_APPROVE_SAFE_ACTIONS="false" # Auto-approve low-risk tasks (Gold/Platinum tier)
TASK_PARALLEL_LIMIT="1"                # Max parallel tasks per agent (Bronze=1, Gold=3)
TASK_STALE_THRESHOLD_MINUTES="60"      # Alert if task stuck in stage
```

**Secrets Management:**

- This skill does NOT handle secrets
- Task metadata may contain references to secrets (e.g., "use API key from .env") but never the secrets themselves
- Agent credentials managed outside task lifecycle

**Variable Discovery Process:**
```bash
# Check task lifecycle configuration
cat .env | grep TASK_

# Audit task statuses
find "$VAULT_PATH" -name '*.json' -exec jq -r '.status' {} \; | sort | uniq -c
```

### 2. Network & Topology Implications

**Port Discovery:**

No network ports required. This skill operates on local filesystem only (via vault_state_manager).

**Dependency Topology:**

```
Task Lifecycle Manager
  └── Vault State Manager (file operations)
      └── Filesystem (local disk)
```

**Integration Points:**

This skill coordinates with:
- **Watcher agents**: Process their outputs from Needs_Action/
- **Local Executive Agent (lex)**: Orchestrates task lifecycle
- **Cloud Executive Agent (cex)**: Plans tasks (via lex proxy)
- **Orchestrator agent**: Executes approved tasks
- **Human**: Approves/rejects tasks via file moves

**Concurrency Considerations:**

- Multiple agents may claim tasks concurrently (handled via claim-by-move)
- Tasks are single-writer (only owning agent can update)
- State transitions are atomic (file moves)

### 3. Auth / CORS / Security Impact

**Authentication Pattern Analysis:**

- No authentication required (local filesystem)
- Agent authorization enforced by `vault_state_manager` permission system
- Task ownership tracked in metadata (created_by, assigned_to fields)

**Security Considerations:**

| Risk | Mitigation |
|------|-----------|
| **Task hijacking** | Only owning agent can update task in In_Progress/ |
| **Status tampering** | All transitions logged to audit trail |
| **Privilege escalation** | Agents cannot approve their own tasks (human-only) |
| **Replay attacks** | Task IDs are unique; duplicate processing detected |
| **Information leakage** | Task metadata sanitized before logging |

**Workflow Security Rules:**

Per AGENTS.md §3, enforce these invariants:

1. **lex cannot approve its own tasks** - must move to Pending_Approval/
2. **orch cannot create new tasks** - only executes approved tasks
3. **cex cannot execute tasks** - only provides recommendations
4. **Watchers cannot claim tasks** - only write to Needs_Action/
5. **Humans have override authority** - can move files anywhere

**Audit Requirements:**

Every state transition must log:
- Timestamp (ISO 8601, UTC)
- Task ID
- Previous state
- New state
- Agent identity
- Reason (if rejection or failure)

## Blueprints & Templates Used

### Blueprint: Task State Machine

**Purpose:** Define legal state transitions and their semantics

**State Diagram:**

```
┌─────────────┐
│Needs_Action │ (Inbox from watchers)
└──────┬──────┘
       │ claim (lex)
       v
   ┌───────┐
   │ Plans │ (Draft plan created)
   └───┬───┘
       │ start_work (lex)
       v
┌──────────────┐
│ In_Progress  │ (Active work)
└──────┬───────┘
       │ request_approval (lex)
       v
┌───────────────────┐
│Pending_Approval   │ (Awaiting human review)
└────────┬──────────┘
         │
    ┌────┴────┐
    v         v
┌────────┐ ┌─────────┐
│Approved│ │Rejected │
└────┬───┘ └────┬────┘
     │          │
     │ execute  │ archive
     │ (orch)   │ (human)
     v          v
  ┌─────┐   ┌─────────┐
  │Done │   │ Archive │
  └─────┘   └─────────┘
```

**Legal Transitions:**

```javascript
const LEGAL_TRANSITIONS = {
  'needs_action': ['planned'],                    // Claim task
  'planned': ['in_progress', 'rejected'],         // Start work or reject
  'in_progress': ['pending_approval', 'rejected', 'needs_action'],  // Complete, fail, or retry
  'pending_approval': ['approved', 'rejected'],   // Human decision
  'approved': ['in_progress'],                    // Orchestrator claims
  'rejected': ['archive'],                        // Clean up
  'done': ['archive']                            // Clean up old tasks
};
```

**Transition Rules:**

| Transition | Agent | Conditions | Side Effects |
|------------|-------|------------|--------------|
| needs_action → planned | lex | Task not claimed | Create plan file, log claim |
| planned → in_progress | lex | Plan approved internally | Update status, log start |
| in_progress → pending_approval | lex | Work completed | Set completed_at, log completion |
| pending_approval → approved | human | Manual approval | Move file to Approved/ |
| pending_approval → rejected | human | Manual rejection | Move to Rejected/, add reason |
| approved → in_progress | orch | Ready to execute | Claim for execution |
| in_progress → done | orch | Execution success | Set outcome, log result |
| in_progress → needs_action | lex/orch | Execution failure, retry | Reset status, increment retry count |

### Blueprint: Claim-by-Move Semantics

**Purpose:** Ensure only one agent processes each task

**Implementation:**

```javascript
async function claimTask(taskFile, agentName) {
  // Step 1: Atomic move (only first mover succeeds)
  try {
    await vaultManager.moveFile(
      'Needs_Action',
      taskFile,
      'Plans',
      agentName
    );
  } catch (err) {
    if (err instanceof FileNotFoundError) {
      // Another agent claimed it
      return { success: false, reason: 'already_claimed' };
    }
    throw err;  // Unexpected error
  }

  // Step 2: Update metadata to mark ownership
  const { content } = await vaultManager.readVaultFile(`Plans/${taskFile}`, agentName);
  const task = JSON.parse(content);

  task.status = 'planned';
  task.claimed_at = new Date().toISOString();
  task.claimed_by = agentName;

  await vaultManager.writeVaultFile(
    `Plans/${taskFile}`,
    JSON.stringify(task, null, 2),
    agentName
  );

  // Step 3: Log claim
  await logTransition(task.plan_id, 'needs_action', 'planned', agentName);

  return { success: true, taskId: task.plan_id };
}
```

**Conflict Scenarios:**

| Scenario | Outcome | Agent Behavior |
|----------|---------|----------------|
| Two agents claim same task | First move succeeds, second gets FileNotFoundError | Second agent skips and tries next task |
| Agent crashes mid-claim | Task stuck in Plans/ | Recovery: detect stale claims, move back to Needs_Action |
| Task file corrupted | JSON parse fails | Log error, move to Rejected/ with reason |
| Duplicate task IDs | Second task gets -1, -2 suffix | Detect collision, regenerate ID |

### Blueprint: State Transition Function

**Purpose:** Centralized function for all state transitions

**Template:**

```javascript
async function transitionTask(taskId, fromState, toState, agentName, reason = null) {
  // Step 1: Validate transition is legal
  if (!isLegalTransition(fromState, toState)) {
    throw new IllegalTransitionError(
      `Cannot transition from ${fromState} to ${toState}`
    );
  }

  // Step 2: Check agent permissions
  if (!canAgentTransition(agentName, fromState, toState)) {
    throw new PermissionError(
      `${agentName} cannot transition task from ${fromState} to ${toState}`
    );
  }

  // Step 3: Map states to folders
  const srcFolder = stateToFolder(fromState);
  const dstFolder = stateToFolder(toState);

  // Step 4: Find task file
  const files = await vaultManager.listFolderFiles(srcFolder);
  const taskFile = files.find(f => f.name.includes(taskId));

  if (!taskFile) {
    throw new TaskNotFoundError(`Task ${taskId} not found in ${srcFolder}`);
  }

  // Step 5: Update task metadata
  const { content } = await vaultManager.readVaultFile(
    `${srcFolder}/${taskFile.name}`,
    agentName
  );
  const task = JSON.parse(content);

  // Update status and transition metadata
  task.status = toState;
  task.last_transition = {
    from: fromState,
    to: toState,
    at: new Date().toISOString(),
    by: agentName,
    reason: reason
  };

  // Write updated task back
  await vaultManager.writeVaultFile(
    `${srcFolder}/${taskFile.name}`,
    JSON.stringify(task, null, 2),
    agentName
  );

  // Step 6: Move file atomically
  await vaultManager.moveFile(
    srcFolder,
    taskFile.name,
    dstFolder,
    agentName
  );

  // Step 7: Log transition
  await logTransition(taskId, fromState, toState, agentName, reason);

  return {
    success: true,
    taskId: taskId,
    oldPath: `${srcFolder}/${taskFile.name}`,
    newPath: `${dstFolder}/${taskFile.name}`
  };
}
```

**Impact Notes:**
- All transitions go through single function (consistent logging, validation)
- Atomic updates (metadata + file move)
- Audit trail for every transition
- Structured error handling

### Blueprint: Retry Logic for Failed Tasks

**Purpose:** Handle transient failures and retry tasks safely

**Template:**

```javascript
async function handleTaskFailure(taskId, error, agentName) {
  const taskPath = `In_Progress/${taskId}.json`;
  const { content } = await vaultManager.readVaultFile(taskPath, agentName);
  const task = JSON.parse(content);

  // Initialize retry metadata if needed
  if (!task.retry_metadata) {
    task.retry_metadata = {
      attempts: 0,
      max_retries: parseInt(process.env.TASK_MAX_RETRIES || '3'),
      last_error: null,
      first_failure_at: null
    };
  }

  // Record failure
  task.retry_metadata.attempts += 1;
  task.retry_metadata.last_error = {
    message: error.message,
    at: new Date().toISOString()
  };

  if (!task.retry_metadata.first_failure_at) {
    task.retry_metadata.first_failure_at = new Date().toISOString();
  }

  // Decide: retry or fail permanently?
  if (task.retry_metadata.attempts < task.retry_metadata.max_retries) {
    // Retry: move back to Needs_Action
    task.status = 'needs_action';
    task.retry_metadata.next_retry_at = new Date(
      Date.now() + Math.pow(2, task.retry_metadata.attempts) * 1000
    ).toISOString();

    await vaultManager.writeVaultFile(
      taskPath,
      JSON.stringify(task, null, 2),
      agentName
    );

    await vaultManager.moveFile(
      'In_Progress',
      `${taskId}.json`,
      'Needs_Action',
      agentName
    );

    await logTransition(taskId, 'in_progress', 'needs_action', agentName,
      `Retry ${task.retry_metadata.attempts}/${task.retry_metadata.max_retries}`);

    return { action: 'retry', attempts: task.retry_metadata.attempts };
  } else {
    // Max retries exceeded: move to Rejected
    task.status = 'rejected';
    task.rejection_reason = `Max retries (${task.retry_metadata.max_retries}) exceeded. Last error: ${error.message}`;

    await vaultManager.writeVaultFile(
      taskPath,
      JSON.stringify(task, null, 2),
      agentName
    );

    await vaultManager.moveFile(
      'In_Progress',
      `${taskId}.json`,
      'Rejected',
      agentName
    );

    await logTransition(taskId, 'in_progress', 'rejected', agentName,
      'Max retries exceeded');

    return { action: 'failed', reason: 'max_retries' };
  }
}
```

**Impact Notes:**
- Exponential backoff prevents retry storms
- Max retries configurable via environment
- Permanent failures moved to Rejected/ (not lost)
- Full error history preserved in metadata

### Blueprint: Conflict Resolution Strategy

**Purpose:** Handle edge cases and conflicts deterministically

**Strategies:**

| Conflict Type | Detection | Resolution |
|---------------|-----------|------------|
| **Duplicate claim** | FileNotFoundError on move | Skip task, log "already_claimed" |
| **Stale claim** | Task in Plans/ > 60 min, no progress | Move back to Needs_Action, log "stale_claim_recovered" |
| **Orphaned task** | Task in In_Progress/, agent crashed | Detect via heartbeat, move to Needs_Action, log "orphan_recovered" |
| **Duplicate task ID** | Same plan_id in multiple folders | Keep oldest, reject duplicates with -duplicate suffix |
| **Corrupted task file** | JSON parse fails | Move to Rejected/ with reason "corrupted_file" |
| **Circular dependency** | Task A waits for B, B waits for A | Detect cycle, reject both with reason "circular_dependency" |

**Implementation Example (Stale Claim Recovery):**

```javascript
async function recoverStaleClaims(staleThresholdMinutes = 60) {
  const staleTime = Date.now() - (staleThresholdMinutes * 60 * 1000);

  const plansFiles = await vaultManager.listFolderFiles('Plans');

  let recovered = 0;

  for (const file of plansFiles) {
    if (file.created.getTime() < staleTime) {
      // Task claimed but not started for > threshold
      const { content } = await vaultManager.readVaultFile(`Plans/${file.name}`, 'system');
      const task = JSON.parse(content);

      // Reset status
      task.status = 'needs_action';
      task.stale_recovery = {
        recovered_at: new Date().toISOString(),
        was_claimed_by: task.claimed_by,
        was_claimed_at: task.claimed_at
      };
      delete task.claimed_by;
      delete task.claimed_at;

      await vaultManager.writeVaultFile(
        `Plans/${file.name}`,
        JSON.stringify(task, null, 2),
        'system'
      );

      await vaultManager.moveFile('Plans', file.name, 'Needs_Action', 'system');

      recovered++;
      console.log(`Recovered stale claim: ${file.name}`);
    }
  }

  if (recovered > 0) {
    console.log(`Recovered ${recovered} stale claims`);
  }

  return recovered;
}
```

## Validation Checklist

### Mandatory Checks (Skill Invalid If Failed)

- [x] Uses canonical folder structure: `SKILL.md`, `references/`, `assets/`
- [x] Contains complete impact analysis (Env, Network, Auth)
- [x] No `localhost` hardcoding (N/A - filesystem only)
- [x] No secrets or passwords in templates
- [x] Auth/CORS impact explicitly documented (filesystem permissions)
- [x] Supports containerization (Docker volume mounts)
- [x] Gotchas document has known failures and mitigation
- [x] Anti-patterns list common mistakes
- [x] All templates use parameterized placeholders
- [x] Templates include IMPACT NOTES comments
- [x] References folder has all three files
- [x] SKILL.md contains all 9 required sections

### Lifecycle-Specific Checks

- [x] State machine transitions are well-defined
- [x] Claim-by-move semantics enforced
- [x] Conflict resolution strategies documented
- [x] Retry logic with exponential backoff
- [x] Stale task recovery mechanism
- [x] All transitions logged to audit trail
- [x] Agent permissions enforced per AGENTS.md §3
- [x] Idempotent operations (safe to retry)
- [x] Predictable outcomes for each transition
- [x] Error handling for all failure modes

## Anti-Patterns

### ❌ Bypassing State Machine

**Problem:** Agent moves task directly from Needs_Action to Done

**Example:**
```javascript
// WRONG - skips required stages
await vaultManager.moveFile('Needs_Action', 'task.json', 'Done', 'lex');

// CORRECT - use lifecycle manager
await taskLifecycle.claimTask('task.json', 'lex');
await taskLifecycle.startWork('task-id', 'lex');
await taskLifecycle.requestApproval('task-id', 'lex');
// ... human approval ...
await taskLifecycle.completeTask('task-id', 'orch');
```

### ❌ Modifying Task in Wrong Stage

**Problem:** Agent updates task file while it's in Pending_Approval (read-only)

**Example:**
```javascript
// WRONG - task is read-only in Pending_Approval
const task = await readTask('Pending_Approval/task.json');
task.priority = 'critical';
await writeTask('Pending_Approval/task.json', task);  // Should fail

// CORRECT - cannot modify tasks in Pending_Approval
// Human must reject and lex must recreate with new priority
```

### ❌ Not Handling Claim Conflicts

**Problem:** Agent assumes claim always succeeds

**Example:**
```javascript
// WRONG - no error handling
await claimTask('task.json', 'lex');
await startWork('task-id', 'lex');  // May fail if claim failed

// CORRECT - check claim result
const result = await claimTask('task.json', 'lex');
if (result.success) {
  await startWork(result.taskId, 'lex');
} else {
  console.log('Task already claimed, trying next');
}
```

### ❌ Infinite Retry Loops

**Problem:** Task fails, retries forever

**Example:**
```javascript
// WRONG - no max retries
while (true) {
  try {
    await executeTask(taskId);
    break;
  } catch (err) {
    console.log('Retrying...');
    // Infinite loop!
  }
}

// CORRECT - use built-in retry logic
const result = await taskLifecycle.executeTaskWithRetry(taskId, agentName);
if (result.action === 'failed') {
  console.log('Task failed permanently:', result.reason);
}
```

### ❌ Not Logging Transitions

**Problem:** No audit trail for who did what

**Example:**
```javascript
// WRONG - silent transition
await vaultManager.moveFile('Plans', 'task.json', 'In_Progress', 'lex');

// CORRECT - use lifecycle manager (logs automatically)
await taskLifecycle.transitionTask('task-id', 'planned', 'in_progress', 'lex');
```

### ❌ Ignoring Stale Tasks

**Problem:** Tasks stuck in intermediate stages forever

**Example:**
```javascript
// WRONG - no recovery mechanism
// Task stuck in Plans/ for 2 hours, no one notices

// CORRECT - run periodic recovery
setInterval(async () => {
  await taskLifecycle.recoverStaleClaims(60);  // Recover tasks > 60 min old
  await taskLifecycle.recoverOrphanedTasks(30);  // Recover tasks > 30 min in In_Progress
}, 300000);  // Every 5 minutes
```

### ❌ Agent Approves Own Task

**Problem:** lex moves task directly to Approved/ (security violation)

**Example:**
```javascript
// WRONG - agent bypasses human approval
await vaultManager.moveFile('In_Progress', 'task.json', 'Approved', 'lex');

// CORRECT - use lifecycle manager (enforces permissions)
await taskLifecycle.requestApproval('task-id', 'lex');
// Task goes to Pending_Approval/, human must approve
```

### ❌ Not Sanitizing Task Metadata

**Problem:** Sensitive data leaked in logs

**Example:**
```javascript
// WRONG - logs entire task (may contain secrets)
console.log('Processing task:', task);

// CORRECT - sanitize before logging
const sanitized = {
  id: task.plan_id,
  status: task.status,
  title: task.title
  // Don't log: emails, API keys, personal info
};
console.log('Processing task:', sanitized);
```

## Enforcement Behavior

When this skill is active:

### Agent Responsibilities

1. **Always use lifecycle manager** for state transitions (not raw vault_state_manager)
2. **Check claim results** (handle already_claimed gracefully)
3. **Respect read-only stages** (cannot modify tasks in Pending_Approval, Approved)
4. **Log all transitions** (automatic via lifecycle manager)
5. **Handle failures** (use retry logic, don't crash)
6. **Run recovery jobs** (detect and fix stale/orphaned tasks)
7. **Sanitize sensitive data** before logging

### User Expectations

- All task transitions follow state machine
- Only one agent processes each task (no duplicates)
- Failed tasks retry automatically (up to max retries)
- Stale tasks recovered automatically
- Full audit trail for all transitions
- Agent permissions strictly enforced

### Error Handling

All lifecycle functions return structured results:

```typescript
interface TransitionResult {
  success: boolean;
  taskId?: string;
  oldPath?: string;
  newPath?: string;
  reason?: string;  // If success=false
}

interface ClaimResult {
  success: boolean;
  taskId?: string;
  reason?: 'already_claimed' | 'invalid_task' | 'permission_denied';
}

interface RetryResult {
  action: 'retry' | 'failed';
  attempts?: number;
  reason?: string;
}
```

Agents must check `success` field before proceeding.

## Integration with AGENTS.md

This skill implements the workflow orchestration defined in AGENTS.md §4:

- **§4.2 Claim-by-Move Rule**: Implemented via `claimTask()` function
- **§4.3 Single-Writer Rules**: Enforced via ownership tracking in metadata
- **§4.4 Conflict Avoidance**: Implemented via conflict resolution strategies
- **§4.5 Idempotency Expectations**: All operations safe to retry

All agents using this skill MUST respect the jurisdictions defined in AGENTS.md §3.

## Usage Examples

See `references/patterns.md` for concrete code examples and workflow patterns.
