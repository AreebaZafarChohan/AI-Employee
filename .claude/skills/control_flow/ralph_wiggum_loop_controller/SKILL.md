---
name: ralph_wiggum_loop_controller
description: Support looping tasks until completion based on Stop-Hook patterns. Checks mission completion conditions and re-injects prompts until TASK_COMPLETE.
---

# Ralph Wiggum Loop Controller

## Purpose

This skill implements intelligent task looping with Stop-Hook pattern support for the Digital FTE workflow. It monitors mission completion conditions, handles retry logic with backoff, and automatically re-injects prompts until tasks reach a terminal state (TASK_COMPLETE, MAX_RETRIES, or STOP_HOOK_TRIGGERED).

Named after Ralph Wiggum's famous "I'm helping!" enthusiasm, this controller persistently works toward task completion with configurable safety limits.

## Core Concepts

### Stop-Hook Pattern

A Stop-Hook is a condition that signals task completion or termination. The controller continuously checks these hooks and decides whether to continue, retry, or terminate.

**Hook Types:**
1. **Success Hooks**: Task completed successfully
2. **Failure Hooks**: Task failed permanently (don't retry)
3. **Retry Hooks**: Transient failure (retry with backoff)
4. **Timeout Hooks**: Time limit exceeded
5. **Resource Hooks**: System resources exhausted

### Loop States

```
PENDING → RUNNING → (checking hooks) → SUCCESS/FAILED/TIMEOUT
   ↑                                         ↓
   └─────────────── RETRY_BACKOFF ←─────────┘
```

**States:**
- `PENDING`: Task queued, not started
- `RUNNING`: Currently executing
- `RETRY_BACKOFF`: Waiting before retry
- `SUCCESS`: Completed successfully
- `FAILED`: Failed permanently
- `TIMEOUT`: Exceeded max duration
- `STOPPED`: Manually stopped by user

## Blueprint

### Core Data Structures

```javascript
// Loop Task Configuration
{
  "task_id": "task-123",
  "loop_id": "loop-abc",
  "created_at": "2025-01-15T10:00:00.000Z",
  "state": "PENDING",

  // Mission definition
  "mission": {
    "description": "Process all pending emails",
    "stop_hooks": [
      {
        "type": "success",
        "condition": "file_exists",
        "path": "Completed/task-123.json",
        "description": "Task marked complete"
      },
      {
        "type": "retry",
        "condition": "exit_code",
        "value": 1,
        "max_retries": 3,
        "backoff_ms": [1000, 2000, 4000],
        "description": "Temporary failure, retry with exponential backoff"
      },
      {
        "type": "failure",
        "condition": "exit_code",
        "value": 2,
        "description": "Permanent failure, do not retry"
      },
      {
        "type": "timeout",
        "condition": "elapsed_time_ms",
        "value": 300000,
        "description": "Task exceeded 5 minute limit"
      }
    ]
  },

  // Execution tracking
  "execution": {
    "attempts": 0,
    "max_attempts": 5,
    "last_attempt_at": null,
    "next_attempt_at": null,
    "total_duration_ms": 0,
    "last_exit_code": null,
    "last_output": null,
    "last_error": null
  },

  // Prompt injection
  "prompt": {
    "template": "Process emails in inbox {{inbox_path}}",
    "variables": {
      "inbox_path": "/vault/Needs_Action"
    },
    "inject_to": "lex",
    "inject_method": "signal_file"
  },

  // Safety limits
  "limits": {
    "max_duration_ms": 600000,
    "max_memory_mb": 512,
    "max_cpu_percent": 80,
    "max_retries": 5,
    "retry_backoff_ms": [1000, 2000, 4000, 8000, 16000]
  },

  // Monitoring
  "metrics": {
    "loop_iterations": 0,
    "successful_checks": 0,
    "failed_checks": 0,
    "hooks_triggered": []
  }
}
```

### Stop Hook Schema

```javascript
{
  "type": "success|retry|failure|timeout|resource",
  "condition": "file_exists|exit_code|elapsed_time_ms|memory_mb|cpu_percent|custom",
  "value": "expected_value_for_comparison",
  "operator": "eq|ne|gt|lt|gte|lte|contains|regex",
  "description": "Human-readable explanation",

  // Retry-specific (optional)
  "max_retries": 3,
  "backoff_ms": [1000, 2000, 4000],
  "backoff_strategy": "exponential|linear|fibonacci",

  // Custom script hook (optional)
  "script": {
    "path": "/path/to/check_completion.sh",
    "args": ["--task-id", "{{task_id}}"],
    "timeout_ms": 5000,
    "success_exit_code": 0
  }
}
```

## Operations

### 1. Start Loop

**Purpose:** Initialize task loop with mission parameters.

**Input:**
```javascript
{
  "task_id": "task-123",
  "mission_description": "Process all pending emails",
  "prompt_template": "Process emails in {{inbox_path}}",
  "prompt_variables": {"inbox_path": "/vault/Needs_Action"},
  "stop_hooks": [...],
  "limits": {...}
}
```

**Process:**
1. Generate unique `loop_id`
2. Create loop task file: `Loops/Active/loop-{loop_id}.json`
3. Set initial state to `PENDING`
4. Schedule first prompt injection
5. Log loop start

**Output:**
```javascript
{
  "loop_id": "loop-abc",
  "state": "PENDING",
  "next_check_at": "2025-01-15T10:00:00.000Z"
}
```

**Example:**
```javascript
const { startLoop } = require('./ralph_wiggum_loop_controller');

const loopConfig = {
  task_id: 'task-123',
  mission_description: 'Process all emails until inbox empty',
  prompt_template: 'Check inbox at {{path}} and process all emails',
  prompt_variables: { path: '/vault/Needs_Action' },
  stop_hooks: [
    {
      type: 'success',
      condition: 'file_exists',
      value: 'Completed/task-123.json'
    },
    {
      type: 'timeout',
      condition: 'elapsed_time_ms',
      value: 600000 // 10 minutes
    }
  ]
};

const result = await startLoop(loopConfig);
// → { loop_id: 'loop-abc', state: 'PENDING', ... }
```

### 2. Check Stop Hooks

**Purpose:** Evaluate all stop hooks to determine if loop should continue.

**Input:**
```javascript
{
  "loop_id": "loop-abc"
}
```

**Process:**
1. Read loop task file
2. Check each stop hook in priority order:
   - Timeout hooks (highest priority)
   - Resource hooks
   - Failure hooks
   - Success hooks
   - Retry hooks (lowest priority)
3. Evaluate hook conditions:
   - File exists: `fs.existsSync(path)`
   - Exit code: Compare with last execution
   - Elapsed time: `Date.now() - created_at`
   - Memory/CPU: Read from system metrics
   - Custom script: Execute and check exit code
4. If hook triggered, update state and stop
5. If no hooks triggered, schedule next check

**Output:**
```javascript
{
  "loop_id": "loop-abc",
  "should_continue": true,
  "hooks_triggered": [],
  "next_action": "inject_prompt",
  "next_check_at": "2025-01-15T10:00:05.000Z"
}
```

**Example:**
```javascript
const { checkStopHooks } = require('./ralph_wiggum_loop_controller');

const result = await checkStopHooks({ loop_id: 'loop-abc' });

if (result.should_continue) {
  console.log('Loop continues, next check:', result.next_check_at);
} else {
  console.log('Loop stopped, hooks triggered:', result.hooks_triggered);
}
```

### 3. Inject Prompt

**Purpose:** Re-inject prompt to agent to continue task execution.

**Input:**
```javascript
{
  "loop_id": "loop-abc"
}
```

**Process:**
1. Read loop task file
2. Render prompt template with current variables
3. Create signal file for target agent:
   ```json
   {
     "signal_type": "prompt_injection",
     "loop_id": "loop-abc",
     "task_id": "task-123",
     "prompt": "Process emails in /vault/Needs_Action",
     "created_at": "2025-01-15T10:00:00.000Z",
     "expires_at": "2025-01-15T10:05:00.000Z"
   }
   ```
4. Write to: `Signals/Pending/{agent_name}/prompt-{loop_id}-{timestamp}.json`
5. Update loop execution tracking:
   - Increment `attempts`
   - Set `last_attempt_at`
   - Calculate `next_attempt_at` (with backoff if retry)
6. Update state to `RUNNING`

**Output:**
```javascript
{
  "loop_id": "loop-abc",
  "prompt_injected": true,
  "signal_file": "Signals/Pending/lex/prompt-loop-abc-1642244400000.json",
  "attempt_number": 1,
  "next_check_at": "2025-01-15T10:00:05.000Z"
}
```

### 4. Handle Completion

**Purpose:** Process loop completion (success, failure, or timeout).

**Input:**
```javascript
{
  "loop_id": "loop-abc",
  "final_state": "SUCCESS",
  "triggered_hooks": ["success:file_exists"],
  "reason": "Task marked complete in Completed/ folder"
}
```

**Process:**
1. Read loop task file
2. Update state to final state
3. Calculate total metrics:
   - Total duration
   - Total iterations
   - Success/failure rate
4. Move to archive: `Loops/Archive/loop-{loop_id}.json`
5. Clean up signal files
6. Log completion event
7. Notify monitoring systems

**Output:**
```javascript
{
  "loop_id": "loop-abc",
  "final_state": "SUCCESS",
  "total_duration_ms": 45000,
  "total_attempts": 3,
  "archived_at": "2025-01-15T10:00:45.000Z"
}
```

### 5. Stop Loop (Manual)

**Purpose:** Manually stop a running loop.

**Input:**
```javascript
{
  "loop_id": "loop-abc",
  "reason": "User requested stop"
}
```

**Process:**
1. Read loop task file
2. Verify loop is active
3. Update state to `STOPPED`
4. Cancel pending prompt injections
5. Archive loop with manual stop flag
6. Log stop event

**Output:**
```javascript
{
  "loop_id": "loop-abc",
  "state": "STOPPED",
  "stopped_by": "user",
  "reason": "User requested stop"
}
```

## Hook Condition Examples

### File Exists Hook

```javascript
{
  "type": "success",
  "condition": "file_exists",
  "value": "Completed/task-123.json",
  "description": "Task marked complete"
}
```

Check: `fs.existsSync('/vault/Completed/task-123.json')`

### Exit Code Hook

```javascript
{
  "type": "retry",
  "condition": "exit_code",
  "value": 1,
  "operator": "eq",
  "max_retries": 3,
  "backoff_ms": [1000, 2000, 4000],
  "description": "Retry on transient failure"
}
```

Check: `lastExecution.exit_code === 1`

### Timeout Hook

```javascript
{
  "type": "timeout",
  "condition": "elapsed_time_ms",
  "value": 600000,
  "operator": "gte",
  "description": "Task exceeded 10 minute limit"
}
```

Check: `(Date.now() - loopTask.created_at) >= 600000`

### Resource Hook (Memory)

```javascript
{
  "type": "resource",
  "condition": "memory_mb",
  "value": 512,
  "operator": "gte",
  "description": "Memory usage exceeded limit"
}
```

Check: `process.memoryUsage().heapUsed / 1024 / 1024 >= 512`

### Custom Script Hook

```javascript
{
  "type": "success",
  "condition": "custom",
  "script": {
    "path": "/vault/.specify/scripts/check_inbox_empty.sh",
    "args": ["--path", "Needs_Action/"],
    "timeout_ms": 5000,
    "success_exit_code": 0
  },
  "description": "Check if inbox is empty via custom script"
}
```

Check: Execute script and verify exit code === 0

## Backoff Strategies

### Exponential Backoff

```javascript
{
  "backoff_strategy": "exponential",
  "backoff_ms": [1000, 2000, 4000, 8000, 16000],
  "max_retries": 5
}
```

Delays: 1s → 2s → 4s → 8s → 16s

### Linear Backoff

```javascript
{
  "backoff_strategy": "linear",
  "backoff_ms": [2000, 4000, 6000, 8000, 10000],
  "max_retries": 5
}
```

Delays: 2s → 4s → 6s → 8s → 10s

### Fibonacci Backoff

```javascript
{
  "backoff_strategy": "fibonacci",
  "backoff_ms": [1000, 1000, 2000, 3000, 5000, 8000],
  "max_retries": 6
}
```

Delays: 1s → 1s → 2s → 3s → 5s → 8s

## Safety Limits

### Per-Loop Limits

```javascript
{
  "limits": {
    "max_duration_ms": 600000,      // 10 minutes total
    "max_memory_mb": 512,            // 512 MB memory
    "max_cpu_percent": 80,           // 80% CPU
    "max_retries": 5,                // 5 retry attempts
    "max_iterations": 100,           // 100 loop checks
    "check_interval_ms": 5000        // Check every 5 seconds
  }
}
```

### Global System Limits

```javascript
{
  "global_limits": {
    "max_concurrent_loops": 10,      // Max 10 loops running
    "max_loops_per_agent": 3,        // Max 3 loops per agent
    "max_total_memory_mb": 2048,     // Max 2GB total
    "max_signal_queue_size": 50      // Max 50 pending signals
  }
}
```

## Monitoring & Metrics

### Per-Loop Metrics

```javascript
{
  "metrics": {
    "loop_iterations": 15,
    "successful_checks": 12,
    "failed_checks": 3,
    "hooks_triggered": [
      {
        "hook_type": "retry",
        "triggered_at": "2025-01-15T10:00:10.000Z",
        "condition": "exit_code",
        "value": 1
      }
    ],
    "total_duration_ms": 75000,
    "average_check_duration_ms": 5000,
    "prompt_injections": 3,
    "backoff_delays_ms": [1000, 2000]
  }
}
```

### System Metrics

```javascript
{
  "system_metrics": {
    "active_loops": 5,
    "archived_loops": 123,
    "total_prompt_injections": 456,
    "average_loop_duration_ms": 45000,
    "success_rate": 0.95,
    "timeout_rate": 0.03,
    "failure_rate": 0.02
  }
}
```

## Error Handling

### Graceful Degradation

1. **Signal File Write Failure**: Retry with exponential backoff
2. **Loop Task Corruption**: Restore from last checkpoint
3. **Hook Evaluation Error**: Skip hook and log error
4. **Resource Limit Exceeded**: Gracefully stop loop
5. **Agent Crash**: Detect via heartbeat and restart loop

### Recovery Strategies

```javascript
// Loop task with checkpoints
{
  "checkpoints": [
    {
      "iteration": 5,
      "state": "RUNNING",
      "saved_at": "2025-01-15T10:00:25.000Z",
      "metrics": {...}
    }
  ],
  "recovery": {
    "last_checkpoint_iteration": 5,
    "recovery_attempts": 0,
    "max_recovery_attempts": 3
  }
}
```

## File Organization

```
Loops/
├── Active/                          # Currently running loops
│   ├── loop-abc.json
│   └── loop-def.json
├── Archive/                         # Completed/stopped loops
│   └── 2025-01-15/
│       ├── loop-abc.json           # SUCCESS
│       └── loop-xyz.json           # TIMEOUT
└── Checkpoints/                    # Recovery checkpoints
    └── loop-abc-checkpoint-5.json
```

## Security Considerations

### Prompt Injection Safety

- Validate prompt templates before rendering
- Escape variables to prevent injection attacks
- Limit prompt length (max 10,000 characters)
- Sanitize file paths in variables

### Resource Protection

- Enforce per-loop memory limits
- Cap concurrent loops per agent
- Rate limit prompt injections
- Monitor CPU usage and throttle if needed

### Audit Trail

All loop operations logged:
```javascript
{
  "timestamp": "2025-01-15T10:00:00.000Z",
  "loop_id": "loop-abc",
  "operation": "inject_prompt",
  "actor": "loop_controller",
  "result": "success",
  "details": {...}
}
```

## Best Practices

1. **Define Clear Success Hooks**: Always include at least one success hook
2. **Set Timeout Limits**: Prevent infinite loops with timeout hooks
3. **Use Exponential Backoff**: For retry hooks, use exponential backoff
4. **Monitor Resource Usage**: Include memory/CPU hooks for long-running tasks
5. **Test Hooks First**: Verify hook conditions work before deploying loops
6. **Archive Old Loops**: Clean up archive directory periodically
7. **Use Checkpoints**: For long loops, create checkpoints every N iterations

## Integration with Other Skills

### With agent_delegation_manager

```javascript
// Loop delegates to cloud for heavy processing
{
  "mission_description": "Analyze large dataset",
  "prompt_template": "Delegate analysis of {{dataset}} to cex",
  "stop_hooks": [
    {
      "type": "success",
      "condition": "file_exists",
      "value": "Signals/Responses/delegation-response-{{task_id}}.json"
    }
  ]
}
```

### With audit_log_writer

```javascript
// Log every loop iteration
const { logAction } = require('./audit_log_writer');

await logAction({
  actor: { type: 'agent', name: 'loop_controller' },
  action: { type: 'loop_iteration', category: 'control_flow' },
  resource: { type: 'loop', id: loopId },
  result: { status: 'success', duration_ms: 5000 },
  details: { iteration: 5, hooks_checked: 3 }
});
```

### With agent_claim_coordinator

```javascript
// Ensure only one agent runs loop at a time
const { claimTask } = require('./agent_claim_coordinator');

const claimed = await claimTask({
  task_id: loopTask.task_id,
  agent_id: 'loop_controller'
});

if (!claimed) {
  console.log('Loop already running, skipping');
  return;
}
```

## Testing Strategies

### Unit Tests

```javascript
describe('ralph_wiggum_loop_controller', () => {
  test('evaluates file_exists hook correctly', async () => {
    const hook = {
      type: 'success',
      condition: 'file_exists',
      value: 'test/completed.json'
    };

    fs.writeFileSync('test/completed.json', '{}');

    const result = await evaluateHook(hook);
    expect(result.triggered).toBe(true);
  });

  test('applies exponential backoff correctly', () => {
    const backoff = calculateBackoff(3, 'exponential', [1000, 2000, 4000]);
    expect(backoff).toBe(4000);
  });
});
```

### Integration Tests

```javascript
test('loop completes on success hook', async () => {
  const loopId = await startLoop({
    task_id: 'test-123',
    mission_description: 'Test mission',
    stop_hooks: [{
      type: 'success',
      condition: 'file_exists',
      value: 'test/done.json'
    }]
  });

  // Simulate task completion
  fs.writeFileSync('test/done.json', '{}');

  await waitForLoopCompletion(loopId, 5000);

  const loopTask = await readLoopTask(loopId);
  expect(loopTask.state).toBe('SUCCESS');
});
```

## Troubleshooting

### Loop Not Stopping

**Symptom:** Loop continues despite completion condition met.

**Diagnosis:**
1. Check hook condition logic
2. Verify file paths are absolute
3. Check hook evaluation order

**Fix:**
```bash
# Manually check hook condition
cat Loops/Active/loop-abc.json | jq '.mission.stop_hooks'
ls -la /vault/Completed/task-123.json  # Verify file exists

# Manually trigger hook evaluation
node -e "require('./ralph_wiggum_loop_controller').checkStopHooks({loop_id: 'loop-abc'})"
```

### Prompt Not Injected

**Symptom:** Agent not receiving prompts.

**Diagnosis:**
1. Check signal file exists
2. Verify agent is monitoring Signals/Pending/
3. Check signal expiry

**Fix:**
```bash
# Check signal files
ls -la Signals/Pending/lex/

# Manually inject prompt
node -e "require('./ralph_wiggum_loop_controller').injectPrompt({loop_id: 'loop-abc'})"
```

### Infinite Loop

**Symptom:** Loop exceeds max iterations.

**Diagnosis:**
1. Check if timeout hook is configured
2. Verify max_iterations limit
3. Check for logic errors in hooks

**Fix:**
```javascript
// Add timeout hook
{
  "type": "timeout",
  "condition": "elapsed_time_ms",
  "value": 300000,  // 5 minutes
  "operator": "gte"
}

// Manually stop loop
const { stopLoop } = require('./ralph_wiggum_loop_controller');
await stopLoop({ loop_id: 'loop-abc', reason: 'Manual stop' });
```

---

## Appendix: Complete Example

```javascript
const { startLoop, checkStopHooks, injectPrompt, stopLoop } = require('./ralph_wiggum_loop_controller');
const { logAction } = require('./audit_log_writer');

// Start loop for email processing
const loopConfig = {
  task_id: 'email-processing-001',
  mission_description: 'Process all pending emails until inbox empty',
  prompt_template: 'Check {{inbox_path}} and process all emails. Mark complete when done.',
  prompt_variables: {
    inbox_path: '/vault/Needs_Action/emails/'
  },
  stop_hooks: [
    {
      type: 'success',
      condition: 'custom',
      script: {
        path: '/vault/.specify/scripts/check_inbox_empty.sh',
        args: ['--path', 'Needs_Action/emails/'],
        success_exit_code: 0
      },
      description: 'All emails processed, inbox empty'
    },
    {
      type: 'retry',
      condition: 'exit_code',
      value: 1,
      max_retries: 3,
      backoff_ms: [2000, 4000, 8000],
      description: 'Email processing failed, retry with backoff'
    },
    {
      type: 'timeout',
      condition: 'elapsed_time_ms',
      value: 600000,  // 10 minutes
      operator: 'gte',
      description: 'Task exceeded time limit'
    }
  ],
  limits: {
    max_duration_ms: 600000,
    max_retries: 3,
    check_interval_ms: 10000  // Check every 10 seconds
  }
};

// Start the loop
const { loop_id } = await startLoop(loopConfig);
console.log(`Loop started: ${loop_id}`);

// Log loop start
await logAction({
  actor: { type: 'agent', name: 'loop_controller' },
  action: { type: 'start_loop', category: 'control_flow' },
  resource: { type: 'loop', id: loop_id },
  result: { status: 'success' },
  details: { mission: loopConfig.mission_description }
});

// Main loop execution (runs until completion)
while (true) {
  await new Promise(resolve => setTimeout(resolve, loopConfig.limits.check_interval_ms));

  const result = await checkStopHooks({ loop_id });

  if (!result.should_continue) {
    console.log('Loop completed:', result.hooks_triggered);
    break;
  }

  if (result.next_action === 'inject_prompt') {
    await injectPrompt({ loop_id });
    console.log('Prompt injected, attempt:', result.attempt_number);
  }
}

console.log('Loop finished successfully');
```
