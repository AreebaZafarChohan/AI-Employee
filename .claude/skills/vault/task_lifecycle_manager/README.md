# Task Lifecycle Manager Skill

Manages the lifecycle of tasks in the Obsidian vault for Digital FTE. Implements claim-by-move semantics, state transitions, conflict avoidance, and predictable outcomes.

## Quick Start

```javascript
const taskLifecycle = require('./task-lifecycle-manager');

// 1. Claim task from Needs_Action
const claimResult = await taskLifecycle.claimTask('email-001.json', 'lex');
if (claimResult.success) {
  const taskId = claimResult.taskId;

  // 2. Start work
  await taskLifecycle.startWork(taskId, 'lex');

  // 3. Execute task steps
  await executeSteps(taskId);

  // 4. Request approval
  await taskLifecycle.requestApproval(taskId, 'lex');

  // Human approves → Approved/

  // 5. Orchestrator executes
  await taskLifecycle.executeApprovedTask(taskId, 'orch');
}
```

## State Machine

```
Needs_Action → Plans → In_Progress → Pending_Approval → Approved → Done
                         ↓              ↓                   ↓
                      Rejected ← Rejected            Rejected
```

## Key Features

✅ **Claim-by-Move Semantics**
- Atomic claiming (first mover wins)
- Conflict detection (already_claimed)
- Ownership tracking

✅ **State Machine Enforcement**
- Legal transitions only
- Permission checks per agent
- Audit trail for all transitions

✅ **Automatic Retry**
- Exponential backoff
- Max retries configurable
- Transient vs permanent error distinction

✅ **Recovery Mechanisms**
- Stale claim recovery
- Orphaned task recovery
- Duplicate detection
- Corrupted file handling

## Documentation

| Document | Purpose |
|----------|---------|
| [`SKILL.md`](./SKILL.md) | Complete specification |
| [`references/patterns.md`](./references/patterns.md) | Code examples (13 patterns) |
| [`references/impact-checklist.md`](./references/impact-checklist.md) | Deployment checklists |
| [`references/gotchas.md`](./references/gotchas.md) | Known issues (18 gotchas) |

## API Reference

### Claim Task

```javascript
await taskLifecycle.claimTask(taskFile, agentName)
```

**Returns:**
```typescript
{
  success: boolean;
  taskId?: string;
  reason?: 'already_claimed' | 'invalid_task' | 'permission_denied';
}
```

### Transition Task

```javascript
await taskLifecycle.transitionTask(taskId, fromState, toState, agentName, reason?)
```

**Legal Transitions:**
- `needs_action` → `planned`
- `planned` → `in_progress` | `rejected`
- `in_progress` → `pending_approval` | `rejected` | `needs_action` (retry)
- `pending_approval` → `approved` | `rejected`
- `approved` → `in_progress`
- `done` → `archive`

### Handle Failure

```javascript
await taskLifecycle.handleTaskFailure(taskId, error, agentName)
```

**Returns:**
```typescript
{
  action: 'retry' | 'failed';
  attempts?: number;
  reason?: string;
}
```

### Recovery Jobs

```javascript
// Recover stale claims (tasks stuck in Plans/)
await taskLifecycle.recoverStaleClaims(staleThresholdMinutes)

// Recover orphaned tasks (tasks stuck in In_Progress/)
await taskLifecycle.recoverOrphanedTasks(orphanThresholdMinutes)

// Detect duplicates
await taskLifecycle.detectDuplicateTasks()
```

## Configuration

```bash
# .env configuration
TASK_CLAIM_TIMEOUT_MS=5000           # Claim timeout
TASK_MAX_RETRIES=3                   # Max retry attempts
TASK_RETRY_BACKOFF_MS=1000           # Exponential backoff base
TASK_CONFLICT_STRATEGY=skip          # skip | retry | fail
TASK_STALE_THRESHOLD_MINUTES=60      # Stale claim threshold
```

## Workflows

### Agent Claims and Processes Task

```javascript
async function processTask(taskFile, agentName) {
  // Claim
  const result = await taskLifecycle.claimTask(taskFile, agentName);
  if (!result.success) return;

  // Work
  await taskLifecycle.startWork(result.taskId, agentName);
  await doWork(result.taskId);

  // Request approval
  await taskLifecycle.requestApproval(result.taskId, agentName);
}
```

### Human Approves Task

```bash
# Review
cat vault/Pending_Approval/plan-123.json

# Approve
mv vault/Pending_Approval/plan-123.json vault/Approved/
```

### Orchestrator Executes Approved Task

```javascript
async function executeApproved(agentName) {
  const files = await vaultManager.listFolderFiles('Approved');
  if (files.length === 0) return;

  const file = files[0];
  const result = await taskLifecycle.claimFromApproved(file.name, agentName);

  if (result.success) {
    try {
      await executePlanViaMCP(result.taskId);
      await taskLifecycle.completeTask(result.taskId, agentName);
    } catch (err) {
      await taskLifecycle.handleTaskFailure(result.taskId, err, agentName);
    }
  }
}
```

## Recovery Jobs

Run periodic recovery jobs to detect and fix issues:

```javascript
// Run every 5 minutes
setInterval(async () => {
  // Recover stale claims
  await taskLifecycle.recoverStaleClaims(60);

  // Recover orphaned tasks
  await taskLifecycle.recoverOrphanedTasks(30);

  // Detect duplicates
  await taskLifecycle.detectDuplicateTasks();

  // Detect corrupted files
  await taskLifecycle.detectCorruptedFiles();
}, 300000);
```

## Error Handling

```javascript
try {
  await taskLifecycle.transitionTask(taskId, fromState, toState, agentName);
} catch (err) {
  if (err instanceof IllegalTransitionError) {
    console.error('Invalid state transition:', err.message);
  } else if (err instanceof PermissionError) {
    console.error('Agent lacks permission:', err.message);
  } else if (err instanceof TaskNotFoundError) {
    console.error('Task not found:', err.message);
  } else {
    console.error('Unexpected error:', err);
  }
}
```

## Best Practices

1. ✅ **Always check claim results** - handle `already_claimed` gracefully
2. ✅ **Use lifecycle manager** for transitions (not raw vault_state_manager)
3. ✅ **Distinguish error types** - retry transient, reject permanent
4. ✅ **Run recovery jobs** - detect stale/orphaned tasks early
5. ✅ **Set conservative thresholds** - don't reclaim active tasks
6. ✅ **Update heartbeat** while processing (optional but recommended)
7. ✅ **Sanitize metadata** before logging (no secrets)
8. ✅ **Log all transitions** (automatic via lifecycle manager)
9. ✅ **Check dependencies** before starting work
10. ✅ **Use exponential backoff** for retries

## Common Issues

### Issue: Task Already Claimed

```
Error: FileNotFoundError
```

**Solution:** This is normal concurrent operation, not an error

```javascript
const result = await taskLifecycle.claimTask(taskFile, agentName);
if (!result.success && result.reason === 'already_claimed') {
  console.log('Task claimed by another agent, trying next');
}
```

### Issue: Task Stuck in In_Progress

**Solution:** Run orphaned task recovery

```javascript
await taskLifecycle.recoverOrphanedTasks(30);
```

### Issue: Max Retries Exceeded

```
Error: Max retries exceeded
```

**Solution:** Task failed permanently, review rejection reason

```bash
cat vault/Rejected/task.json | jq '.rejection_reason'
```

## Integration

This skill builds on:
- **vault_state_manager**: Low-level file operations
- **AGENTS.md §3**: Agent permissions
- **AGENTS.md §4**: Vault protocol

All agents using this skill MUST respect jurisdictions and workflows defined in AGENTS.md.

## Testing

```javascript
// Test claim conflict
const [r1, r2] = await Promise.all([
  taskLifecycle.claimTask('task.json', 'lex-1'),
  taskLifecycle.claimTask('task.json', 'lex-2')
]);
// Only one should succeed

// Test illegal transition
try {
  await taskLifecycle.transitionTask('task-id', 'needs_action', 'done', 'lex');
  // Should throw IllegalTransitionError
} catch (err) {
  assert(err instanceof IllegalTransitionError);
}

// Test retry logic
await taskLifecycle.handleTaskFailure('task-id', new Error('API timeout'), 'lex');
// Task should retry with backoff

// Test recovery
await taskLifecycle.recoverStaleClaims(60);
// Stale tasks moved back to Needs_Action
```

## Monitoring

Track these metrics:
- Task counts per stage (gauge)
- Transition latency (histogram)
- Retry rate (counter)
- Recovery effectiveness (stale/orphan counts)
- Error rates by type

## Related Skills

- [vault_state_manager](../vault_state_manager/) - Low-level vault operations
- [skill-standard-enforcer](../../meta/skill-standard-enforcer/) - Skill creation standard

## License

This skill follows the Digital FTE project license.
