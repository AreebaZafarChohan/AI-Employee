# Ralph Wiggum Loop Controller

Support looping tasks until completion based on Stop-Hook patterns. Checks mission completion conditions and re-injects prompts until TASK_COMPLETE.

## Overview

The Ralph Wiggum Loop Controller implements intelligent task looping with Stop-Hook pattern support for the Digital FTE workflow. Named after Ralph Wiggum's famous "I'm helping!" enthusiasm, this controller persistently works toward task completion with configurable safety limits.

It monitors mission completion conditions, handles retry logic with backoff, and automatically re-injects prompts until tasks reach a terminal state (TASK_COMPLETE, MAX_RETRIES, or STOP_HOOK_TRIGGERED).

## Key Features

1. **Stop-Hook Pattern**: Flexible completion detection (file exists, exit code, timeout, resource limits, custom scripts)
2. **Intelligent Retry**: Exponential/linear/Fibonacci backoff with jitter
3. **Prompt Re-injection**: Automatic prompt re-injection to agent until completion
4. **Circuit Breaker**: Prevents infinite loops from failing tasks
5. **Checkpoint Recovery**: Resume long-running loops after crashes
6. **Resource Limits**: Memory, CPU, timeout protection
7. **Zombie Detection**: Automatically reclaim loops from crashed agents
8. **Full Audit Trail**: Complete loop history with metrics

## Quick Start

### Basic Loop

```javascript
const { startLoop } = require('./ralph_wiggum_loop_controller');

const { loop_id } = await startLoop({
  task_id: 'email-processing',
  mission_description: 'Process all emails until inbox empty',
  prompt_template: 'Process emails in {{inbox_path}}',
  prompt_variables: {
    inbox_path: '/vault/Needs_Action/emails/'
  },
  stop_hooks: [
    {
      type: 'success',
      condition: 'file_exists',
      value: 'Completed/email-processing.json',
      description: 'All emails processed'
    },
    {
      type: 'timeout',
      condition: 'elapsed_time_ms',
      value: 600000,  // 10 minutes
      operator: 'gte'
    }
  ]
});

console.log(`Loop started: ${loop_id}`);
```

### Loop with Retry

```javascript
const { loop_id } = await startLoop({
  task_id: 'api-sync',
  mission_description: 'Sync with external API',
  prompt_template: 'Call API at {{api_url}}',
  prompt_variables: {
    api_url: 'https://api.example.com/sync'
  },
  stop_hooks: [
    {
      type: 'success',
      condition: 'file_exists',
      value: 'Completed/api-sync.json'
    },
    {
      type: 'retry',
      condition: 'exit_code',
      value: 1,
      max_retries: 5,
      backoff_ms: [1000, 2000, 4000, 8000, 16000],
      backoff_strategy: 'exponential',
      description: 'Retry on transient API failure'
    },
    {
      type: 'failure',
      condition: 'exit_code',
      value: 2,
      description: 'Auth failed, do not retry'
    }
  ]
});
```

## Core Operations

### 1. Start Loop

Initialize task loop with mission parameters.

**API:**
```javascript
const { loop_id } = await startLoop({
  task_id: string,
  mission_description: string,
  prompt_template: string,
  prompt_variables: object,
  stop_hooks: array,
  limits: object
});
```

### 2. Check Stop Hooks

Evaluate all stop hooks to determine if loop should continue.

**API:**
```javascript
const result = await checkStopHooks({ loop_id });
// → { should_continue: true/false, hooks_triggered: [...], next_action: 'inject_prompt' }
```

### 3. Inject Prompt

Re-inject prompt to agent to continue task execution.

**API:**
```javascript
const result = await injectPrompt({ loop_id });
// → { prompt_injected: true, signal_file: 'path/to/signal.json', attempt_number: 1 }
```

### 4. Stop Loop

Manually stop a running loop.

**API:**
```javascript
await stopLoop({
  loop_id: 'loop-abc',
  reason: 'User requested stop'
});
```

## Stop Hook Types

### Success Hook

Triggers when task completes successfully.

```javascript
{
  "type": "success",
  "condition": "file_exists",
  "value": "Completed/task-123.json",
  "description": "Task marked complete"
}
```

### Retry Hook

Triggers on transient failure, retries with backoff.

```javascript
{
  "type": "retry",
  "condition": "exit_code",
  "value": 1,
  "max_retries": 5,
  "backoff_ms": [1000, 2000, 4000, 8000, 16000],
  "backoff_strategy": "exponential",
  "description": "Retry on temporary failure"
}
```

### Failure Hook

Triggers on permanent failure, does not retry.

```javascript
{
  "type": "failure",
  "condition": "exit_code",
  "value": 2,
  "description": "Critical error, do not retry"
}
```

### Timeout Hook

Triggers when elapsed time exceeds limit.

```javascript
{
  "type": "timeout",
  "condition": "elapsed_time_ms",
  "value": 600000,  // 10 minutes
  "operator": "gte",
  "description": "Task exceeded time limit"
}
```

### Resource Hook

Triggers when resource usage exceeds limit.

```javascript
{
  "type": "resource",
  "condition": "memory_mb",
  "value": 512,
  "operator": "gte",
  "description": "Memory usage exceeded"
}
```

### Custom Script Hook

Triggers based on custom script exit code.

```javascript
{
  "type": "success",
  "condition": "custom",
  "script": {
    "path": "/vault/scripts/check_completion.sh",
    "args": ["--task-id", "task-123"],
    "timeout_ms": 5000,
    "success_exit_code": 0
  },
  "description": "Custom completion check"
}
```

## Architecture

### File Organization

```
Loops/
├── Active/                  # Currently running loops
│   ├── loop-abc.json
│   └── loop-def.json
├── Archive/                 # Completed/stopped loops
│   └── 2025-01-15/
│       ├── loop-abc.json   # SUCCESS
│       └── loop-xyz.json   # TIMEOUT
└── Checkpoints/            # Recovery checkpoints
    └── loop-abc-checkpoint-5.json

Signals/
├── Pending/
│   ├── lex/                # Signals for local agent
│   │   └── prompt-loop-abc-1642244400000.json
│   └── cex/                # Signals for cloud agent
└── Responses/              # Agent responses
```

### Loop Lifecycle

```
START → PENDING → RUNNING → (check hooks) → SUCCESS/FAILED/TIMEOUT
           ↑                      ↓
           └──── RETRY_BACKOFF ←──┘
```

### Hook Evaluation Priority

1. **Timeout hooks** (highest priority) - always check first
2. **Resource hooks** - prevent resource exhaustion
3. **Failure hooks** - permanent failures
4. **Success hooks** - task completion
5. **Retry hooks** (lowest priority) - transient failures

## Backoff Strategies

### Exponential Backoff

Doubles delay each retry: 1s → 2s → 4s → 8s → 16s

```javascript
{
  "backoff_strategy": "exponential",
  "backoff_ms": [1000, 2000, 4000, 8000, 16000]
}
```

### Linear Backoff

Constant increment: 2s → 4s → 6s → 8s → 10s

```javascript
{
  "backoff_strategy": "linear",
  "backoff_ms": [2000, 4000, 6000, 8000, 10000]
}
```

### Fibonacci Backoff

Fibonacci sequence: 1s → 1s → 2s → 3s → 5s → 8s

```javascript
{
  "backoff_strategy": "fibonacci",
  "backoff_ms": [1000, 1000, 2000, 3000, 5000, 8000]
}
```

## Safety Features

### Circuit Breaker

Automatically stops loops after repeated failures:

```javascript
// Configured via environment variables
CIRCUIT_BREAKER_ENABLED=true
CIRCUIT_BREAKER_THRESHOLD=5
CIRCUIT_BREAKER_RESET_TIMEOUT_MS=60000
```

### Zombie Loop Detection

Detects and reclaims loops from crashed agents:

```javascript
// Runs automatically every minute
async function checkZombieLoops() {
  // Checks for loops with stale heartbeats
  // Automatically stops and archives zombie loops
}
```

### Resource Limits

Per-loop and global resource protection:

```javascript
{
  "limits": {
    "max_duration_ms": 600000,    // 10 minutes
    "max_memory_mb": 512,         // 512 MB
    "max_cpu_percent": 80,        // 80% CPU
    "max_retries": 5              // 5 attempts
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
    "total_duration_ms": 75000,
    "prompt_injections": 3,
    "hooks_triggered": [...]
  }
}
```

### System Metrics

```javascript
{
  "system_metrics": {
    "active_loops": 5,
    "archived_loops": 123,
    "success_rate": 0.95,
    "average_loop_duration_ms": 45000
  }
}
```

## Integration with Other Skills

### agent_delegation_manager

```javascript
// Loop delegates to cloud agent
const { loop_id } = await startLoop({
  prompt_template: 'Delegate {{task}} to cex',
  stop_hooks: [{
    type: 'success',
    condition: 'file_exists',
    value: 'Signals/Responses/delegation-response-{{task_id}}.json'
  }]
});
```

### audit_log_writer

```javascript
// Log every loop iteration
await logAction({
  actor: { type: 'agent', name: 'loop_controller' },
  action: { type: 'loop_iteration', category: 'control_flow' },
  resource: { type: 'loop', id: loop_id },
  result: { status: 'success', duration_ms: 5000 },
  details: { iteration: 5 }
});
```

### agent_claim_coordinator

```javascript
// Ensure single-agent execution
const claimed = await claimTask({ task_id, agent_id: 'loop_controller' });
if (claimed) {
  await startLoop({ task_id, ... });
}
```

## Troubleshooting

### Loop Not Stopping

**Problem:** Loop continues despite completion condition met.

**Fix:**
```bash
# Check hook configuration
cat Loops/Active/loop-abc.json | jq '.mission.stop_hooks'

# Verify completion file exists
ls -la /vault/Completed/task-123.json

# Manually trigger hook evaluation
node -e "require('./ralph_wiggum_loop_controller').checkStopHooks({loop_id: 'loop-abc'})"
```

### Prompt Not Injected

**Problem:** Agent not receiving prompts.

**Fix:**
```bash
# Check signal files
ls -la Signals/Pending/lex/

# Verify signal not expired
cat Signals/Pending/lex/prompt-*.json | jq '.expires_at'

# Manually inject prompt
node -e "require('./ralph_wiggum_loop_controller').injectPrompt({loop_id: 'loop-abc'})"
```

### Infinite Loop

**Problem:** Loop exceeds max iterations.

**Fix:**
```javascript
// Always include timeout hook
{
  "type": "timeout",
  "condition": "elapsed_time_ms",
  "value": 300000,  // 5 minutes
  "operator": "gte"
}

// Manually stop loop
await stopLoop({ loop_id: 'loop-abc', reason: 'Manual stop' });
```

## Best Practices

1. **Always Include Timeout Hook**: Prevent infinite loops
2. **Use Exponential Backoff**: For retry hooks
3. **Monitor Resource Usage**: Include memory/CPU hooks for long tasks
4. **Test Hooks First**: Verify hook conditions before deploying
5. **Enable Circuit Breaker**: In production environments
6. **Use Checkpoints**: For loops > 5 minutes
7. **Integrate Audit Logging**: For compliance and debugging

## Files

- `SKILL.md` - Complete technical specification
- `EXAMPLES.md` - 10 practical usage examples
- `references/patterns.md` - 8 design patterns
- `references/gotchas.md` - 10 edge cases with mitigations
- `references/impact-checklist.md` - Deployment readiness checklist
- `assets/.env.example` - Configuration template
- `assets/loop-task.template.json` - Loop task template
- `assets/prompt-signal.template.json` - Prompt signal template

## Related Skills

- **agent_delegation_manager**: Coordinate local ↔ cloud task delegation
- **agent_claim_coordinator**: Ensure single-agent task ownership
- **audit_log_writer**: Structured audit logging

---

Named after Ralph Wiggum because, like Ralph, this controller is always enthusiastically "helping!" - persistently working toward completion with unwavering determination (and sometimes needing a timeout to know when to stop). 🎉
