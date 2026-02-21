# Error Recovery Planner - Examples

This document provides complete, runnable examples for common error recovery scenarios.

---

## Example 1: Basic Network Timeout Recovery

**Scenario**: Fetch data from external API, handle timeout gracefully

```javascript
const { planRecovery } = require('./error_recovery_planner');
const axios = require('axios');

async function fetchUserData(userId) {
  const taskId = `fetch-user-${userId}`;
  const url = `https://api.example.com/users/${userId}`;

  try {
    const response = await axios.get(url, { timeout: 30000 });
    return response.data;
  } catch (error) {
    // Network error occurred
    console.error(`API call failed: ${error.message}`);

    // Plan recovery
    const recoveryPlan = await planRecovery(taskId, error, 'lex');

    console.log(`Recovery Plan ID: ${recoveryPlan.recovery_plan_id}`);
    console.log(`Error Type: ${recoveryPlan.classification.error_type}`);
    console.log(`Recovery Action: ${recoveryPlan.recovery_strategy.action}`);

    if (recoveryPlan.recovery_strategy.action === 'retry') {
      // Retry with backoff
      const backoffMs = recoveryPlan.recovery_strategy.backoff_ms;
      console.log(`Retrying in ${Math.round(backoffMs/1000)}s (attempt ${recoveryPlan.recovery_strategy.current_attempt}/${recoveryPlan.recovery_strategy.max_retries})`);

      await new Promise(resolve => setTimeout(resolve, backoffMs));
      return fetchUserData(userId);  // Recursive retry
    } else {
      // Escalate or abandon
      throw new Error(`Failed to fetch user ${userId}: ${recoveryPlan.escalation_policy.escalation_reason}`);
    }
  }
}

// Usage
fetchUserData('user-123')
  .then(data => console.log('User data:', data))
  .catch(err => console.error('Final error:', err));
```

**Output (transient error)**:
```
API call failed: ETIMEDOUT
Recovery Plan ID: REC-20250204-143022-ABC123
Error Type: transient
Recovery Action: retry
Retrying in 2s (attempt 2/3)
User data: { id: 'user-123', name: 'John Doe', ... }
```

---

## Example 2: Rate Limit Handling with Retry-After

**Scenario**: API returns 429 with Retry-After header

```javascript
const { planRecovery } = require('./error_recovery_planner');
const axios = require('axios');

async function createPost(postData, attemptNumber = 1) {
  const taskId = `create-post-${postData.id}`;

  try {
    const response = await axios.post('https://api.example.com/posts', postData);
    console.log(`Post created: ${response.data.id}`);
    return response.data;
  } catch (error) {
    if (error.response?.status === 429) {
      // Rate limit hit
      console.log('Rate limit exceeded');

      // Plan recovery (includes Retry-After header parsing)
      const recoveryPlan = await planRecovery(taskId, {
        message: 'Rate limit exceeded',
        status: 429,
        code: 'RATE_LIMIT_EXCEEDED',
        headers: error.response.headers
      }, 'lex');

      if (recoveryPlan.recovery_strategy.action === 'retry') {
        const retryAfterMs = recoveryPlan.recovery_strategy.backoff_ms;
        const retryAfterSec = Math.round(retryAfterMs / 1000);

        console.log(`Rate limit: waiting ${retryAfterSec}s as instructed by server`);
        console.log(`Next retry: ${recoveryPlan.recovery_strategy.next_retry_at}`);

        await new Promise(resolve => setTimeout(resolve, retryAfterMs));
        return createPost(postData, attemptNumber + 1);
      } else {
        throw new Error('Rate limit persisted after max retries');
      }
    }

    throw error;  // Different error type
  }
}

// Usage
createPost({ id: 'post-456', title: 'Hello World', body: '...' })
  .then(post => console.log('Success:', post.id))
  .catch(err => console.error('Failed:', err.message));
```

**Output**:
```
Rate limit exceeded
Rate limit: waiting 60s as instructed by server
Next retry: 2025-02-04T14:46:22Z
Post created: post-456
Success: post-456
```

---

## Example 3: Permanent Error Detection

**Scenario**: Authentication fails (401) - immediate escalation

```javascript
const { planRecovery } = require('./error_recovery_planner');
const taskLifecycle = require('./task_lifecycle_manager');

async function fetchProtectedResource(taskId, authToken) {
  try {
    const response = await fetch('https://api.example.com/protected', {
      headers: { Authorization: `Bearer ${authToken}` }
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    // Plan recovery
    const recoveryPlan = await planRecovery(taskId, {
      message: error.message,
      status: error.status,
      code: 'AUTH_FAILED'
    }, 'lex');

    if (recoveryPlan.classification.error_type === 'permanent') {
      console.log('Permanent error detected - no retry');
      console.log(`Reason: ${recoveryPlan.classification.reasoning}`);

      // Escalate to human immediately
      await taskLifecycle.transitionTask(
        taskId,
        'in_progress',
        'pending_approval',
        'lex',
        recoveryPlan.escalation_policy.escalation_reason
      );

      console.log(`Task ${taskId} escalated for manual review`);
      return null;
    }

    throw error;
  }
}

// Usage
fetchProtectedResource('TASK-789', 'invalid-token')
  .then(data => console.log('Data:', data))
  .catch(err => console.error('Error:', err));
```

**Output**:
```
Permanent error detected - no retry
Reason: 401 errors indicate invalid credentials and will not resolve with retry
Task TASK-789 escalated for manual review
```

---

## Example 4: File Lock Retry with Linear Backoff

**Scenario**: Multiple processes trying to write to same file

```javascript
const { planRecovery } = require('./error_recovery_planner');
const fs = require('fs').promises;

async function writeConfigFile(taskId, filePath, content, attemptNumber = 1) {
  const maxAttempts = 5;

  try {
    // Try exclusive write (fail if file exists)
    await fs.writeFile(filePath, content, { flag: 'wx' });
    console.log('File written successfully');
    return true;
  } catch (error) {
    if (error.code === 'EEXIST' || error.code === 'EBUSY') {
      // File locked or exists
      console.log(`File locked (attempt ${attemptNumber}/${maxAttempts})`);

      // Plan recovery with linear backoff
      const recoveryPlan = await planRecovery(taskId, {
        message: `File locked: ${error.message}`,
        code: error.code,
        filePath: filePath
      }, 'lex', {
        backoff_strategy: 'linear',  // Override: use linear for file locks
        base_backoff_ms: 500  // Short intervals
      });

      if (attemptNumber < maxAttempts && recoveryPlan.recovery_strategy.action === 'retry') {
        const backoffMs = recoveryPlan.recovery_strategy.backoff_ms;
        console.log(`Waiting ${backoffMs}ms before retry...`);

        await new Promise(resolve => setTimeout(resolve, backoffMs));
        return writeConfigFile(taskId, filePath, content, attemptNumber + 1);
      } else {
        throw new Error(`Unable to acquire file lock after ${maxAttempts} attempts`);
      }
    }

    throw error;  // Different error
  }
}

// Usage
writeConfigFile('TASK-111', '/tmp/config.json', '{"setting": "value"}')
  .then(() => console.log('Config saved'))
  .catch(err => console.error('Failed to save config:', err.message));
```

**Output**:
```
File locked (attempt 1/5)
Waiting 500ms before retry...
File locked (attempt 2/5)
Waiting 1000ms before retry...
File locked (attempt 3/5)
Waiting 1500ms before retry...
File written successfully
Config saved
```

---

## Example 5: Batch Recovery Planning

**Scenario**: Multiple tasks failed simultaneously - recover all

```javascript
const { planRecovery } = require('./error_recovery_planner');

async function recoverFailedTasks(failedTasks, agentName) {
  const recoveryPlans = [];

  console.log(`Planning recovery for ${failedTasks.length} failed tasks...`);

  // Create recovery plan for each task
  for (const task of failedTasks) {
    const plan = await planRecovery(task.task_id, task.error, agentName);
    recoveryPlans.push(plan);
  }

  // Group by action
  const grouped = {
    retry: recoveryPlans.filter(p => p.recovery_strategy.action === 'retry'),
    escalate: recoveryPlans.filter(p => p.recovery_strategy.action === 'escalate'),
    abandon: recoveryPlans.filter(p => p.recovery_strategy.action === 'abandon')
  };

  console.log('\n=== Recovery Summary ===');
  console.log(`Retry: ${grouped.retry.length} tasks`);
  console.log(`Escalate: ${grouped.escalate.length} tasks`);
  console.log(`Abandon: ${grouped.abandon.length} tasks`);

  // Schedule retries with staggering (prevent thundering herd)
  console.log('\n=== Scheduling Retries ===');
  for (const [index, plan] of grouped.retry.entries()) {
    const staggerMs = index * 500;  // 500ms stagger
    const totalBackoff = plan.recovery_strategy.backoff_ms + staggerMs;

    console.log(`Task ${plan.task_id}: retry in ${Math.round(totalBackoff/1000)}s`);

    setTimeout(async () => {
      console.log(`Retrying task ${plan.task_id}...`);
      await retryTask(plan.task_id);
    }, totalBackoff);
  }

  // Escalate tasks immediately
  console.log('\n=== Escalating Tasks ===');
  for (const plan of grouped.escalate) {
    console.log(`Escalating ${plan.task_id}: ${plan.escalation_policy.escalation_reason}`);
    await escalateTask(plan.task_id, plan.escalation_policy.escalation_reason);
  }

  return recoveryPlans;
}

// Example failed tasks
const failedTasks = [
  { task_id: 'TASK-001', error: { message: 'ETIMEDOUT', code: 'ETIMEDOUT' } },
  { task_id: 'TASK-002', error: { message: 'ETIMEDOUT', code: 'ETIMEDOUT' } },
  { task_id: 'TASK-003', error: { message: 'Unauthorized', status: 401 } },
  { task_id: 'TASK-004', error: { message: 'Not found', status: 404 } },
  { task_id: 'TASK-005', error: { message: 'Service unavailable', status: 503 } }
];

// Usage
recoverFailedTasks(failedTasks, 'lex')
  .then(plans => console.log(`\nRecovery plans created: ${plans.length}`));
```

**Output**:
```
Planning recovery for 5 failed tasks...

=== Recovery Summary ===
Retry: 3 tasks
Escalate: 2 tasks
Abandon: 0 tasks

=== Scheduling Retries ===
Task TASK-001: retry in 1s
Task TASK-002: retry in 3s
Task TASK-005: retry in 5s

=== Escalating Tasks ===
Escalating TASK-003: Permanent authentication failure
Escalating TASK-004: Permanent error detected

Recovery plans created: 5
```

---

## Example 6: Recovery Plan Audit

**Scenario**: Review recovery history for a specific task

```javascript
const { auditTaskRecovery } = require('./error_recovery_planner');

async function reviewTaskRecovery(taskId) {
  const history = await auditTaskRecovery(taskId);

  console.log(`\n=== Recovery History: ${taskId} ===`);
  console.log(`Total attempts: ${history.length}`);

  if (history.length === 0) {
    console.log('No recovery attempts recorded.');
    return;
  }

  // Summarize attempts
  for (const [index, plan] of history.entries()) {
    console.log(`\nAttempt ${index + 1}:`);
    console.log(`  Time: ${plan.created_at}`);
    console.log(`  Error: ${plan.classification.category}`);
    console.log(`  Type: ${plan.classification.error_type}`);
    console.log(`  Action: ${plan.recovery_strategy.action}`);
    console.log(`  Backoff: ${plan.recovery_strategy.backoff_ms}ms`);
    console.log(`  Status: ${plan.status}`);
  }

  // Analyze patterns
  const errorTypes = history.map(p => p.classification.error_type);
  const uniqueErrors = [...new Set(errorTypes)];

  console.log(`\n=== Analysis ===`);
  console.log(`Unique error types: ${uniqueErrors.join(', ')}`);
  console.log(`Retry success rate: ${calculateRetrySuccessRate(history)}%`);
  console.log(`Average backoff: ${calculateAvgBackoff(history)}ms`);

  // Recommendations
  if (history.length > 5) {
    console.log(`\n⚠️  Warning: Task has failed ${history.length} times`);
    console.log(`Recommendation: Review task logic or dependencies`);
  }
}

// Helper functions
function calculateRetrySuccessRate(history) {
  const completed = history.filter(p => p.status === 'completed').length;
  return Math.round((completed / history.length) * 100);
}

function calculateAvgBackoff(history) {
  const backoffs = history
    .filter(p => p.recovery_strategy.backoff_ms)
    .map(p => p.recovery_strategy.backoff_ms);

  if (backoffs.length === 0) return 0;

  const sum = backoffs.reduce((a, b) => a + b, 0);
  return Math.round(sum / backoffs.length);
}

// Usage
reviewTaskRecovery('TASK-12345');
```

**Output**:
```
=== Recovery History: TASK-12345 ===
Total attempts: 3

Attempt 1:
  Time: 2025-02-04T14:30:22Z
  Error: network_timeout
  Type: transient
  Action: retry
  Backoff: 1000ms
  Status: completed

Attempt 2:
  Time: 2025-02-04T14:32:25Z
  Error: network_timeout
  Type: transient
  Action: retry
  Backoff: 2000ms
  Status: completed

Attempt 3:
  Time: 2025-02-04T14:34:29Z
  Error: network_timeout
  Type: transient
  Action: escalate
  Backoff: 0ms
  Status: active

=== Analysis ===
Unique error types: transient
Retry success rate: 67%
Average backoff: 1500ms
```

---

## Example 7: Custom Error Patterns

**Scenario**: Add application-specific error patterns

```javascript
const { planRecovery, registerErrorPattern } = require('./error_recovery_planner');

// Register custom transient error pattern
registerErrorPattern({
  type: 'transient',
  pattern: /database connection pool exhausted/i,
  category: 'db_pool_exhausted',
  backoff_strategy: 'linear',
  base_backoff_ms: 5000  // 5 second intervals
});

// Register custom permanent error pattern
registerErrorPattern({
  type: 'permanent',
  pattern: /schema validation failed/i,
  category: 'invalid_schema',
  escalate_immediately: true
});

async function executeWithCustomErrors(taskId, operation) {
  try {
    return await operation();
  } catch (error) {
    const recoveryPlan = await planRecovery(taskId, error, 'lex');

    if (recoveryPlan.classification.category === 'db_pool_exhausted') {
      console.log('Database pool exhausted - waiting for connection availability');
      // Custom handling for this error type
    }

    // Standard recovery execution
    if (recoveryPlan.recovery_strategy.action === 'retry') {
      await sleep(recoveryPlan.recovery_strategy.backoff_ms);
      return executeWithCustomErrors(taskId, operation);
    }
  }
}
```

---

## Example 8: Integration with Circuit Breaker

**Scenario**: Combine recovery planner with circuit breaker pattern

```javascript
const { planRecovery } = require('./error_recovery_planner');
const circuitBreaker = require('./circuit_breaker');

async function executeWithCircuitBreaker(taskId, serviceName, operation) {
  // Check if circuit is open
  if (circuitBreaker.isOpen(serviceName)) {
    console.log(`Circuit open for ${serviceName} - skipping execution`);

    // Create recovery plan for circuit open state
    const recoveryPlan = await planRecovery(taskId, {
      message: `Circuit breaker open for ${serviceName}`,
      code: 'CIRCUIT_OPEN',
      service: serviceName
    }, 'lex');

    // Wait for circuit to close
    const resetTime = circuitBreaker.getResetTime(serviceName);
    const waitMs = resetTime - Date.now();

    console.log(`Waiting ${Math.round(waitMs/1000)}s for circuit to close...`);
    await sleep(waitMs);

    // Retry once circuit closes
    return executeWithCircuitBreaker(taskId, serviceName, operation);
  }

  // Circuit closed - try execution
  try {
    const result = await operation();
    circuitBreaker.recordSuccess(serviceName);
    return result;
  } catch (error) {
    // Record failure in circuit breaker
    circuitBreaker.recordFailure(serviceName);

    // Plan recovery
    const recoveryPlan = await planRecovery(taskId, error, 'lex');

    if (recoveryPlan.recovery_strategy.action === 'retry') {
      await sleep(recoveryPlan.recovery_strategy.backoff_ms);
      return executeWithCircuitBreaker(taskId, serviceName, operation);
    }

    throw error;
  }
}

// Usage
executeWithCircuitBreaker('TASK-999', 'external-api', async () => {
  return await fetch('https://api.example.com/data');
});
```

---

## Environment Configuration Examples

### Development (Fast Feedback)
```bash
RECOVERY_MAX_RETRIES="5"
RECOVERY_BASE_BACKOFF_MS="500"
RECOVERY_STRATEGY="linear"
RECOVERY_JITTER_FACTOR="0.0"
RECOVERY_DEBUG_LOGGING="true"
```

### Production (Conservative)
```bash
RECOVERY_MAX_RETRIES="3"
RECOVERY_BASE_BACKOFF_MS="2000"
RECOVERY_MAX_BACKOFF_MS="60000"
RECOVERY_STRATEGY="exponential"
RECOVERY_JITTER_FACTOR="0.3"
```

### High-Availability (Aggressive Retry)
```bash
RECOVERY_MAX_RETRIES="10"
RECOVERY_BASE_BACKOFF_MS="1000"
RECOVERY_MAX_BACKOFF_MS="300000"
RECOVERY_STRATEGY="fibonacci"
RECOVERY_AUTO_ABANDON_THRESHOLD="10"
```

---

## Testing Examples

### Unit Test: Error Classification
```javascript
const { classifyError } = require('./error_recovery_planner');

describe('Error Classification', () => {
  test('classifies timeout as transient', () => {
    const error = { message: 'ETIMEDOUT', code: 'ETIMEDOUT' };
    const result = classifyError(error);
    expect(result.error_type).toBe('transient');
    expect(result.confidence).toBe('high');
  });

  test('classifies 401 as permanent', () => {
    const error = { status: 401, message: 'Unauthorized' };
    const result = classifyError(error);
    expect(result.error_type).toBe('permanent');
    expect(result.confidence).toBe('high');
  });
});
```

### Integration Test: Full Recovery Flow
```javascript
const { planRecovery } = require('./error_recovery_planner');
const taskLifecycle = require('./task_lifecycle_manager');

describe('Recovery Flow', () => {
  test('retries transient error with backoff', async () => {
    const error = { code: 'ETIMEDOUT', message: 'Timeout' };
    const plan = await planRecovery('TASK-TEST', error, 'lex');

    expect(plan.recovery_strategy.action).toBe('retry');
    expect(plan.recovery_strategy.backoff_ms).toBeGreaterThan(0);

    // Wait and verify task can be retried
    await sleep(plan.recovery_strategy.backoff_ms);
    const task = await taskLifecycle.getTask('TASK-TEST');
    expect(task.status).toBe('needs_action');  // Ready for retry
  });
});
```

---

These examples demonstrate the full range of error recovery planner capabilities. See `references/patterns.md` for more advanced usage patterns.
