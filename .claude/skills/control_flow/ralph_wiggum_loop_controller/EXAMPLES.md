# Ralph Wiggum Loop Controller - Usage Examples

This document provides practical examples for using the ralph_wiggum_loop_controller skill in various scenarios.

## Example 1: Simple File Completion Loop

**Scenario**: Loop until a completion marker file appears.

```javascript
const { startLoop } = require('./ralph_wiggum_loop_controller');

const loopId = await startLoop({
  task_id: 'report-generation',
  mission_description: 'Generate quarterly report',
  prompt_template: 'Generate Q1 2025 report and save to Reports/ folder',
  prompt_variables: {},
  stop_hooks: [
    {
      type: 'success',
      condition: 'file_exists',
      value: 'Reports/Q1-2025-report.pdf',
      description: 'Report generated successfully'
    },
    {
      type: 'timeout',
      condition: 'elapsed_time_ms',
      value: 300000,  // 5 minutes
      operator: 'gte',
      description: 'Report generation timed out'
    }
  ],
  limits: {
    max_duration_ms: 300000,
    max_retries: 3,
    check_interval_ms: 5000
  }
});

console.log(`Loop started: ${loopId}`);
```

## Example 2: Retry with Exponential Backoff

**Scenario**: API call that may fail transiently, retry with backoff.

```javascript
const loopId = await startLoop({
  task_id: 'api-sync',
  mission_description: 'Sync data with external API',
  prompt_template: 'Call API at {{api_url}} and sync results',
  prompt_variables: {
    api_url: 'https://api.example.com/sync'
  },
  stop_hooks: [
    {
      type: 'success',
      condition: 'file_exists',
      value: 'Completed/api-sync.json',
      description: 'API sync completed'
    },
    {
      type: 'retry',
      condition: 'exit_code',
      value: 1,
      max_retries: 5,
      backoff_ms: [1000, 2000, 4000, 8000, 16000],
      backoff_strategy: 'exponential',
      description: 'API temporarily unavailable, retry with exponential backoff'
    },
    {
      type: 'failure',
      condition: 'exit_code',
      value: 2,
      description: 'API authentication failed, do not retry'
    }
  ]
});
```

## Example 3: Resource-Limited Loop

**Scenario**: Long-running task with memory and CPU limits.

```javascript
const loopId = await startLoop({
  task_id: 'batch-processing',
  mission_description: 'Process large batch of images',
  prompt_template: 'Process images in {{batch_folder}}',
  prompt_variables: {
    batch_folder: '/vault/Needs_Action/images/'
  },
  stop_hooks: [
    {
      type: 'success',
      condition: 'custom',
      script: {
        path: '/vault/scripts/check_batch_complete.sh',
        args: ['--folder', 'images'],
        success_exit_code: 0
      },
      description: 'All images processed'
    },
    {
      type: 'resource',
      condition: 'memory_mb',
      value: 512,
      operator: 'gte',
      description: 'Memory usage exceeded limit'
    },
    {
      type: 'resource',
      condition: 'cpu_percent',
      value: 80,
      operator: 'gte',
      description: 'CPU usage exceeded limit'
    },
    {
      type: 'timeout',
      condition: 'elapsed_time_ms',
      value: 1800000,  // 30 minutes
      operator: 'gte'
    }
  ],
  limits: {
    max_duration_ms: 1800000,
    max_memory_mb: 512,
    max_cpu_percent: 80,
    check_interval_ms: 10000
  }
});
```

## Example 4: Custom Script Hook

**Scenario**: Check completion using custom bash script.

```bash
#!/bin/bash
# check_inbox_empty.sh

INBOX_PATH="$1"
EMAIL_COUNT=$(find "$INBOX_PATH" -name "*.eml" | wc -l)

if [ "$EMAIL_COUNT" -eq 0 ]; then
  echo "Inbox empty"
  exit 0  # Success
else
  echo "Inbox has $EMAIL_COUNT emails remaining"
  exit 1  # Continue loop
fi
```

```javascript
const loopId = await startLoop({
  task_id: 'email-processing',
  mission_description: 'Process all emails until inbox empty',
  prompt_template: 'Process emails in {{inbox_path}}',
  prompt_variables: {
    inbox_path: '/vault/Needs_Action/emails/'
  },
  stop_hooks: [
    {
      type: 'success',
      condition: 'custom',
      script: {
        path: '/vault/scripts/check_inbox_empty.sh',
        args: ['Needs_Action/emails/'],
        timeout_ms: 5000,
        success_exit_code: 0
      },
      description: 'Inbox is empty'
    }
  ]
});
```

## Example 5: Multi-Hook Priority

**Scenario**: Multiple hooks with different priorities.

```javascript
const loopId = await startLoop({
  task_id: 'multi-step-task',
  mission_description: 'Complex multi-step processing',
  prompt_template: 'Execute step {{current_step}} of workflow',
  prompt_variables: {
    current_step: 1
  },
  stop_hooks: [
    // Priority 1: Timeout (always check first)
    {
      type: 'timeout',
      condition: 'elapsed_time_ms',
      value: 600000,
      operator: 'gte',
      description: 'Task exceeded time limit'
    },
    // Priority 2: Resource limits
    {
      type: 'resource',
      condition: 'memory_mb',
      value: 512,
      operator: 'gte',
      description: 'Memory exceeded'
    },
    // Priority 3: Permanent failure
    {
      type: 'failure',
      condition: 'exit_code',
      value: 2,
      description: 'Critical error, do not retry'
    },
    // Priority 4: Success
    {
      type: 'success',
      condition: 'file_exists',
      value: 'Completed/multi-step-task.json',
      description: 'All steps completed'
    },
    // Priority 5: Retry (lowest)
    {
      type: 'retry',
      condition: 'exit_code',
      value: 1,
      max_retries: 3,
      backoff_ms: [2000, 4000, 8000],
      description: 'Transient failure, retry'
    }
  ]
});
```

## Example 6: Loop with Checkpoints

**Scenario**: Long loop with periodic checkpoints for recovery.

```javascript
const { startLoop, createCheckpoint, recoverFromCheckpoint } = require('./ralph_wiggum_loop_controller');

// Start loop with checkpoint configuration
const loopId = await startLoop({
  task_id: 'long-processing',
  mission_description: 'Process large dataset with checkpoints',
  prompt_template: 'Process batch {{batch_number}} of data',
  prompt_variables: {
    batch_number: 1
  },
  stop_hooks: [
    {
      type: 'success',
      condition: 'file_exists',
      value: 'Completed/long-processing.json'
    }
  ],
  limits: {
    max_duration_ms: 3600000,  // 1 hour
    checkpoint_interval_iterations: 10  // Checkpoint every 10 iterations
  }
});

// Checkpoints created automatically every 10 iterations
// Recovery example:
const recovered = await recoverFromCheckpoint({
  loop_id: loopId,
  checkpoint_iteration: 50  // Resume from iteration 50
});
```

## Example 7: Delegated Loop with agent_delegation_manager

**Scenario**: Loop that delegates work to cloud agent.

```javascript
const { startLoop } = require('./ralph_wiggum_loop_controller');
const { delegateToCloud } = require('./agent_delegation_manager');

const loopId = await startLoop({
  task_id: 'cloud-analysis',
  mission_description: 'Delegate heavy analysis to cloud agent',
  prompt_template: 'Delegate analysis of {{dataset}} to cex and wait for results',
  prompt_variables: {
    dataset: 'large-dataset.csv'
  },
  stop_hooks: [
    {
      type: 'success',
      condition: 'file_exists',
      value: 'Signals/Responses/delegation-response-cloud-analysis.json',
      description: 'Cloud agent completed analysis'
    },
    {
      type: 'timeout',
      condition: 'elapsed_time_ms',
      value: 600000,  // 10 minutes
      operator: 'gte',
      description: 'Cloud delegation timed out'
    }
  ]
});

// The loop will automatically re-check for delegation response
```

## Example 8: Loop with Audit Logging

**Scenario**: Full audit trail of loop operations.

```javascript
const { startLoop, checkStopHooks, injectPrompt } = require('./ralph_wiggum_loop_controller');
const { logAction } = require('./audit_log_writer');

// Start loop
const { loop_id } = await startLoop({
  task_id: 'audited-task',
  mission_description: 'Task with full audit trail',
  prompt_template: 'Execute audited operation',
  stop_hooks: [
    {
      type: 'success',
      condition: 'file_exists',
      value: 'Completed/audited-task.json'
    }
  ]
});

// Log loop start
await logAction({
  actor: { type: 'agent', name: 'loop_controller' },
  action: { type: 'start_loop', category: 'control_flow' },
  resource: { type: 'loop', id: loop_id },
  result: { status: 'success' },
  details: { task_id: 'audited-task' }
});

// Main loop with logging
let iteration = 0;
while (true) {
  await new Promise(resolve => setTimeout(resolve, 5000));

  const result = await checkStopHooks({ loop_id });

  // Log each iteration
  await logAction({
    actor: { type: 'agent', name: 'loop_controller' },
    action: { type: 'loop_iteration', category: 'control_flow' },
    resource: { type: 'loop', id: loop_id },
    result: { status: 'success', duration_ms: 100 },
    details: {
      iteration: ++iteration,
      should_continue: result.should_continue,
      hooks_checked: result.hooks_triggered.length
    }
  });

  if (!result.should_continue) {
    // Log completion
    await logAction({
      actor: { type: 'agent', name: 'loop_controller' },
      action: { type: 'complete_loop', category: 'control_flow' },
      resource: { type: 'loop', id: loop_id },
      result: { status: 'success', duration_ms: iteration * 5000 },
      details: {
        final_state: result.final_state,
        total_iterations: iteration,
        hooks_triggered: result.hooks_triggered
      }
    });
    break;
  }

  if (result.next_action === 'inject_prompt') {
    await injectPrompt({ loop_id });

    // Log prompt injection
    await logAction({
      actor: { type: 'agent', name: 'loop_controller' },
      action: { type: 'inject_prompt', category: 'control_flow' },
      resource: { type: 'loop', id: loop_id },
      result: { status: 'success' },
      details: { iteration, attempt: result.attempt_number }
    });
  }
}

console.log('Loop completed with full audit trail');
```

## Example 9: Manual Loop Control

**Scenario**: Manually stop a running loop.

```javascript
const { startLoop, stopLoop, getLoopStatus } = require('./ralph_wiggum_loop_controller');

// Start loop
const { loop_id } = await startLoop({
  task_id: 'manual-control',
  mission_description: 'Task with manual control',
  prompt_template: 'Execute operation',
  stop_hooks: [
    {
      type: 'success',
      condition: 'file_exists',
      value: 'Completed/manual-control.json'
    }
  ]
});

// Check status
const status = await getLoopStatus({ loop_id });
console.log('Loop status:', status.state);

// Manually stop if needed
if (status.state === 'RUNNING') {
  await stopLoop({
    loop_id,
    reason: 'User requested manual stop',
    stopped_by: 'admin'
  });

  console.log('Loop stopped manually');
}
```

## Example 10: Fibonacci Backoff Strategy

**Scenario**: Use Fibonacci backoff for gradual retry escalation.

```javascript
const loopId = await startLoop({
  task_id: 'fibonacci-retry',
  mission_description: 'Task with Fibonacci backoff',
  prompt_template: 'Execute operation with Fibonacci retry',
  stop_hooks: [
    {
      type: 'success',
      condition: 'file_exists',
      value: 'Completed/fibonacci-retry.json'
    },
    {
      type: 'retry',
      condition: 'exit_code',
      value: 1,
      max_retries: 6,
      backoff_ms: [1000, 1000, 2000, 3000, 5000, 8000],
      backoff_strategy: 'fibonacci',
      description: 'Retry with Fibonacci backoff: 1s, 1s, 2s, 3s, 5s, 8s'
    }
  ]
});
```

## Testing Examples

### Unit Test: Hook Evaluation

```javascript
const { evaluateHook } = require('./ralph_wiggum_loop_controller');
const fs = require('fs');

describe('Hook Evaluation', () => {
  test('file_exists hook triggers when file exists', async () => {
    const hook = {
      type: 'success',
      condition: 'file_exists',
      value: '/tmp/test-completion.json'
    };

    fs.writeFileSync('/tmp/test-completion.json', '{}');

    const result = await evaluateHook(hook);
    expect(result.triggered).toBe(true);

    fs.unlinkSync('/tmp/test-completion.json');
  });

  test('timeout hook triggers when elapsed time exceeds limit', async () => {
    const hook = {
      type: 'timeout',
      condition: 'elapsed_time_ms',
      value: 1000,
      operator: 'gte'
    };

    const loopTask = {
      created_at: Date.now() - 2000  // 2 seconds ago
    };

    const result = await evaluateHook(hook, loopTask);
    expect(result.triggered).toBe(true);
  });
});
```

### Integration Test: Complete Loop

```javascript
test('loop completes on success hook', async () => {
  const { startLoop, checkStopHooks } = require('./ralph_wiggum_loop_controller');
  const fs = require('fs');

  const { loop_id } = await startLoop({
    task_id: 'integration-test',
    mission_description: 'Test loop completion',
    prompt_template: 'Test operation',
    stop_hooks: [
      {
        type: 'success',
        condition: 'file_exists',
        value: '/tmp/integration-test-done.json'
      }
    ],
    limits: {
      check_interval_ms: 1000,
      max_duration_ms: 10000
    }
  });

  // Simulate task completion after 3 seconds
  setTimeout(() => {
    fs.writeFileSync('/tmp/integration-test-done.json', '{}');
  }, 3000);

  // Wait for loop to complete
  let completed = false;
  while (!completed) {
    await new Promise(resolve => setTimeout(resolve, 1000));

    const result = await checkStopHooks({ loop_id });
    if (!result.should_continue) {
      completed = true;
      expect(result.final_state).toBe('SUCCESS');
    }
  }

  fs.unlinkSync('/tmp/integration-test-done.json');
});
```

---

These examples cover the major use cases for the ralph_wiggum_loop_controller skill. Adapt them to your specific requirements and integrate with other skills as needed!
