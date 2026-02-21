# Control Flow Skills

Skills for managing task execution flow, loops, retries, and completion detection.

## Skills in this Category

### ralph_wiggum_loop_controller

Support looping tasks until completion based on Stop-Hook patterns. Checks mission completion conditions and re-injects prompts until TASK_COMPLETE.

**Key Features:**
- Stop-Hook pattern for flexible completion detection
- Intelligent retry with exponential/linear/Fibonacci backoff
- Automatic prompt re-injection to agent
- Circuit breaker to prevent infinite loops
- Checkpoint recovery for long-running tasks
- Resource limits (memory, CPU, timeout)
- Zombie loop detection and cleanup

**Use Cases:**
- Processing tasks until inbox empty
- API sync with retry logic
- Batch processing with checkpoints
- Delegated tasks with cloud agents
- Any task requiring "keep trying until done" logic

**Files:**
- `ralph_wiggum_loop_controller/SKILL.md` - Complete specification
- `ralph_wiggum_loop_controller/README.md` - Usage guide
- `ralph_wiggum_loop_controller/EXAMPLES.md` - 10 practical examples
- `ralph_wiggum_loop_controller/references/patterns.md` - 8 design patterns
- `ralph_wiggum_loop_controller/references/gotchas.md` - 10 edge cases
- `ralph_wiggum_loop_controller/references/impact-checklist.md` - Deployment checklist
- `ralph_wiggum_loop_controller/assets/.env.example` - Configuration
- `ralph_wiggum_loop_controller/assets/loop-task.template.json` - Loop task template
- `ralph_wiggum_loop_controller/assets/prompt-signal.template.json` - Prompt signal template

## Control Flow Patterns

### Stop-Hook Pattern

Define conditions that signal task completion or termination:

```javascript
{
  "stop_hooks": [
    {
      "type": "success",
      "condition": "file_exists",
      "value": "Completed/task-123.json",
      "description": "Task completed successfully"
    },
    {
      "type": "retry",
      "condition": "exit_code",
      "value": 1,
      "max_retries": 3,
      "backoff_ms": [1000, 2000, 4000],
      "description": "Retry on transient failure"
    },
    {
      "type": "timeout",
      "condition": "elapsed_time_ms",
      "value": 600000,
      "operator": "gte",
      "description": "Task exceeded time limit"
    }
  ]
}
```

### Loop Lifecycle

```
START → PENDING → RUNNING → (check hooks) → SUCCESS/FAILED/TIMEOUT
           ↑                      ↓
           └──── RETRY_BACKOFF ←──┘
```

### Hook Priority

1. **Timeout** (highest) - prevent runaway loops
2. **Resource** - prevent resource exhaustion
3. **Failure** - permanent failures, stop immediately
4. **Success** - task completion
5. **Retry** (lowest) - transient failures, try again

## Common Workflows

### Workflow 1: Email Processing Loop

```javascript
const { startLoop } = require('./ralph_wiggum_loop_controller');

await startLoop({
  task_id: 'email-processing',
  mission_description: 'Process all emails until inbox empty',
  prompt_template: 'Process emails in {{inbox_path}}',
  prompt_variables: { inbox_path: '/vault/Needs_Action/emails/' },
  stop_hooks: [
    {
      type: 'success',
      condition: 'custom',
      script: {
        path: '/vault/scripts/check_inbox_empty.sh',
        success_exit_code: 0
      }
    },
    { type: 'timeout', condition: 'elapsed_time_ms', value: 1800000 }  // 30 min
  ]
});
```

### Workflow 2: API Sync with Retry

```javascript
await startLoop({
  task_id: 'api-sync',
  mission_description: 'Sync with external API',
  prompt_template: 'Call API at {{api_url}} and sync results',
  prompt_variables: { api_url: 'https://api.example.com/sync' },
  stop_hooks: [
    { type: 'success', condition: 'file_exists', value: 'Completed/api-sync.json' },
    {
      type: 'retry',
      condition: 'exit_code',
      value: 1,
      max_retries: 5,
      backoff_ms: [1000, 2000, 4000, 8000, 16000],
      backoff_strategy: 'exponential'
    },
    { type: 'failure', condition: 'exit_code', value: 2 },  // Auth failed, don't retry
    { type: 'timeout', condition: 'elapsed_time_ms', value: 600000 }
  ]
});
```

### Workflow 3: Batch Processing with Checkpoints

```javascript
await startLoop({
  task_id: 'batch-processing',
  mission_description: 'Process large batch with checkpoints',
  prompt_template: 'Process batch {{batch_number}}',
  prompt_variables: { batch_number: 1 },
  stop_hooks: [
    {
      type: 'success',
      condition: 'custom',
      script: { path: '/vault/scripts/check_batch_complete.sh', success_exit_code: 0 }
    },
    { type: 'resource', condition: 'memory_mb', value: 512, operator: 'gte' },
    { type: 'timeout', condition: 'elapsed_time_ms', value: 1800000 }
  ],
  limits: {
    checkpoint_interval_iterations: 10  // Checkpoint every 10 iterations
  }
});
```

### Workflow 4: Delegated Task Loop

```javascript
await startLoop({
  task_id: 'cloud-delegation',
  mission_description: 'Delegate to cloud and wait for results',
  prompt_template: 'Delegate analysis of {{dataset}} to cex',
  prompt_variables: { dataset: 'large-data.csv' },
  stop_hooks: [
    {
      type: 'success',
      condition: 'file_exists',
      value: 'Signals/Responses/delegation-response-cloud-delegation.json'
    },
    { type: 'timeout', condition: 'elapsed_time_ms', value: 600000 }
  ]
});
```

## Backoff Strategies

### Exponential Backoff

Best for: Transient failures, API rate limits

```javascript
{
  "backoff_strategy": "exponential",
  "backoff_ms": [1000, 2000, 4000, 8000, 16000]
}
// Delays: 1s → 2s → 4s → 8s → 16s
```

### Linear Backoff

Best for: Predictable retry intervals

```javascript
{
  "backoff_strategy": "linear",
  "backoff_ms": [2000, 4000, 6000, 8000, 10000]
}
// Delays: 2s → 4s → 6s → 8s → 10s
```

### Fibonacci Backoff

Best for: Gradual escalation

```javascript
{
  "backoff_strategy": "fibonacci",
  "backoff_ms": [1000, 1000, 2000, 3000, 5000, 8000]
}
// Delays: 1s → 1s → 2s → 3s → 5s → 8s
```

## Safety Features

### Circuit Breaker

Automatically stops failing loops after threshold:

```bash
# Environment variables
CIRCUIT_BREAKER_ENABLED=true
CIRCUIT_BREAKER_THRESHOLD=5
CIRCUIT_BREAKER_RESET_TIMEOUT_MS=60000
```

### Zombie Loop Detection

Detects crashed loops via heartbeat monitoring:

```bash
# Runs every minute
ZOMBIE_CHECK_INTERVAL_MS=60000
LOOP_HEARTBEAT_TIMEOUT_MS=60000
```

### Resource Limits

Per-loop and global protection:

```bash
DEFAULT_MEMORY_LIMIT_MB=512
DEFAULT_CPU_LIMIT_PERCENT=80
GLOBAL_MEMORY_LIMIT_MB=2048
MAX_CONCURRENT_LOOPS=10
```

## Integration with Other Skills

### With agent_delegation_manager

Loop waits for delegation response:

```javascript
{
  "stop_hooks": [{
    "type": "success",
    "condition": "file_exists",
    "value": "Signals/Responses/delegation-response-{{task_id}}.json"
  }]
}
```

### With agent_claim_coordinator

Prevent duplicate loops:

```javascript
const { claimTask } = require('./agent_claim_coordinator');

const claimed = await claimTask({ task_id, agent_id: 'loop_controller' });
if (claimed) {
  await startLoop({ task_id, ... });
}
```

### With audit_log_writer

Full audit trail:

```javascript
const { logAction } = require('./audit_log_writer');

await logAction({
  actor: { type: 'agent', name: 'loop_controller' },
  action: { type: 'loop_iteration', category: 'control_flow' },
  resource: { type: 'loop', id: loop_id },
  details: { iteration: 5, hooks_checked: 3 }
});
```

## Best Practices

1. **Always Include Timeout Hook**: Prevent infinite loops
2. **Use Exponential Backoff**: For transient failures
3. **Monitor Resources**: Include memory/CPU hooks for long tasks
4. **Test Hooks First**: Verify conditions work before deployment
5. **Enable Circuit Breaker**: In production
6. **Use Checkpoints**: For loops > 5 minutes
7. **Integrate Audit Logging**: For compliance
8. **Set Reasonable Limits**: Don't make timeouts too long
9. **Clean Up Signals**: Enable automatic signal cleanup
10. **Monitor Metrics**: Track success rate, duration, failures

## Monitoring

### Key Metrics to Track

- **Active Loops**: Number of currently running loops
- **Success Rate**: Percentage of loops completing successfully
- **Average Duration**: Mean time to completion
- **Timeout Rate**: Percentage of loops timing out
- **Retry Rate**: Average retries per loop
- **Resource Usage**: Memory and CPU consumption

### Alerts to Configure

- Loop timeout exceeded
- Loop failure rate > 10%
- Zombie loops detected
- Resource limit exceeded
- Circuit breaker opened
- Signal queue size > 50

## Troubleshooting

### Loop Not Stopping

```bash
# Check hooks
cat Loops/Active/loop-abc.json | jq '.mission.stop_hooks'

# Verify completion condition
ls -la /vault/Completed/task-123.json

# Manually stop
node -e "require('./ralph_wiggum_loop_controller').stopLoop({loop_id: 'loop-abc', reason: 'manual'})"
```

### Prompt Not Injected

```bash
# Check signals
ls -la Signals/Pending/lex/

# Check expiry
cat Signals/Pending/lex/prompt-*.json | jq '.expires_at'

# Manually inject
node -e "require('./ralph_wiggum_loop_controller').injectPrompt({loop_id: 'loop-abc'})"
```

### Infinite Loop

```javascript
// Always include timeout hook
{
  "type": "timeout",
  "condition": "elapsed_time_ms",
  "value": 300000,
  "operator": "gte"
}
```

## Related Documentation

- [agent_delegation_manager](../coordination/agent_delegation_manager/README.md)
- [agent_claim_coordinator](../coordination/agent_claim_coordinator/README.md)
- [audit_log_writer](../logging/audit_log_writer/README.md)

---

Control flow skills enable autonomous, resilient task execution with intelligent retry logic and safety limits. Use them to build robust, self-healing workflows! 🔄
