# Error Recovery Planner - Usage Patterns

This document provides concrete code examples for common recovery scenarios.

---

## Pattern 1: Network Timeout Recovery

**Scenario:** HTTP request times out after 30 seconds

**Code:**
```javascript
const { planRecovery } = require('./error_recovery_planner');
const taskLifecycle = require('./task_lifecycle_manager');

async function executeApiCall(taskId, url) {
  try {
    const response = await fetch(url, { timeout: 30000 });
    return await response.json();
  } catch (error) {
    // Error occurred - plan recovery
    const recoveryPlan = await planRecovery(taskId, error, 'lex');

    console.log(`Recovery plan created: ${recoveryPlan.recovery_plan_id}`);
    console.log(`Error type: ${recoveryPlan.classification.error_type}`);
    console.log(`Action: ${recoveryPlan.recovery_strategy.action}`);

    if (recoveryPlan.recovery_strategy.action === 'retry') {
      // Wait for backoff period
      const backoffMs = recoveryPlan.recovery_strategy.backoff_ms;
      console.log(`Retrying in ${Math.round(backoffMs/1000)} seconds...`);

      await new Promise(resolve => setTimeout(resolve, backoffMs));

      // Retry execution
      return executeApiCall(taskId, url);
    } else if (recoveryPlan.recovery_strategy.action === 'escalate') {
      // Escalate to human
      await taskLifecycle.transitionTask(
        taskId,
        'in_progress',
        'pending_approval',
        'lex',
        recoveryPlan.escalation_policy.escalation_reason
      );

      throw new Error(`Task escalated: ${recoveryPlan.escalation_policy.escalation_reason}`);
    }
  }
}
```

**Output:**
```
Recovery plan created: REC-20250204-143022-ABC123
Error type: transient
Action: retry
Retrying in 2 seconds...
```

---

## Pattern 2: Rate Limit Handling

**Scenario:** API returns 429 Too Many Requests with Retry-After header

**Code:**
```javascript
async function executeRateLimitedCall(taskId, apiEndpoint) {
  try {
    const response = await apiClient.post(apiEndpoint, data);
    return response.data;
  } catch (error) {
    if (error.response?.status === 429) {
      // Rate limit error - plan recovery
      const recoveryPlan = await planRecovery(taskId, {
        message: 'Rate limit exceeded',
        status: 429,
        headers: error.response.headers,
        code: 'RATE_LIMIT_EXCEEDED'
      }, 'lex');

      // Recovery planner reads Retry-After header
      const retryAfterMs = recoveryPlan.recovery_strategy.backoff_ms;
      console.log(`Rate limit hit. Waiting ${Math.round(retryAfterMs/1000)}s as instructed by server.`);

      // Wait and retry
      await new Promise(resolve => setTimeout(resolve, retryAfterMs));
      return executeRateLimitedCall(taskId, apiEndpoint);
    }

    throw error;
  }
}
```

**Recovery Plan (Rate Limit):**
```json
{
  "recovery_plan_id": "REC-20250204-144500-XYZ789",
  "task_id": "TASK-67890",
  "classification": {
    "error_type": "transient",
    "category": "rate_limit",
    "confidence": "high"
  },
  "recovery_strategy": {
    "action": "retry",
    "max_retries": 5,
    "current_attempt": 1,
    "backoff_strategy": "rate_limit_aware",
    "backoff_ms": 60000,
    "next_retry_at": "2025-02-04T14:46:00Z"
  },
  "recommended_actions": [
    {
      "priority": 1,
      "action": "retry_after_cooldown",
      "description": "Wait 60 seconds as indicated by Retry-After header",
      "automated": true
    }
  ]
}
```

---

## Pattern 3: Permanent Error Detection

**Scenario:** Authentication failure (401) - no point retrying

**Code:**
```javascript
async function executeAuthenticatedRequest(taskId, credentials) {
  try {
    const response = await authenticatedClient.get('/api/resource', {
      headers: { Authorization: `Bearer ${credentials.token}` }
    });
    return response.data;
  } catch (error) {
    if (error.response?.status === 401) {
      // Authentication error - plan recovery
      const recoveryPlan = await planRecovery(taskId, {
        message: 'Authentication failed: Invalid or expired token',
        status: 401,
        code: 'AUTH_FAILED'
      }, 'lex');

      // Permanent error detected - escalate immediately
      if (recoveryPlan.classification.error_type === 'permanent') {
        console.log('Permanent error detected. Escalating to human...');

        await taskLifecycle.transitionTask(
          taskId,
          'in_progress',
          'pending_approval',
          'lex',
          'Authentication credentials invalid - manual review required'
        );

        // Log escalation
        console.log(`Task ${taskId} escalated. Recovery plan: ${recoveryPlan.recovery_plan_id}`);
        return null;
      }
    }

    throw error;
  }
}
```

**Recovery Plan (Permanent Error):**
```json
{
  "recovery_plan_id": "REC-20250204-150000-DEF456",
  "task_id": "TASK-11111",
  "classification": {
    "error_type": "permanent",
    "category": "authentication_failure",
    "confidence": "high",
    "reasoning": "401 errors indicate invalid credentials and will not resolve with retry"
  },
  "recovery_strategy": {
    "action": "escalate",
    "reason": "Permanent authentication failure"
  },
  "recommended_actions": [
    {
      "priority": 1,
      "action": "escalate_to_human",
      "description": "Manual intervention required to update credentials",
      "automated": true,
      "requires_approval": false
    },
    {
      "priority": 2,
      "action": "verify_credentials",
      "description": "Check if API token has expired or been revoked",
      "automated": false
    }
  ],
  "escalation_policy": {
    "escalate_immediately": true,
    "escalation_reason": "Authentication credentials invalid",
    "escalation_target": "human_operator"
  }
}
```

---

## Pattern 4: File Lock Conflict

**Scenario:** Task fails due to file being locked by another process

**Code:**
```javascript
async function updateTaskFile(taskId, filePath, content) {
  let attempts = 0;
  const maxAttempts = 5;

  while (attempts < maxAttempts) {
    try {
      await fs.promises.writeFile(filePath, content, { flag: 'wx' });
      console.log('File written successfully');
      return;
    } catch (error) {
      if (error.code === 'EEXIST' || error.code === 'EBUSY') {
        // File locked - plan recovery
        const recoveryPlan = await planRecovery(taskId, {
          message: `File locked: ${error.message}`,
          code: error.code,
          filePath: filePath
        }, 'lex');

        attempts++;

        if (recoveryPlan.recovery_strategy.action === 'retry') {
          const backoffMs = recoveryPlan.recovery_strategy.backoff_ms;
          console.log(`File locked. Retrying in ${Math.round(backoffMs/1000)}s (attempt ${attempts}/${maxAttempts})`);

          await new Promise(resolve => setTimeout(resolve, backoffMs));
        } else {
          throw new Error(`Unable to acquire file lock after ${attempts} attempts`);
        }
      } else {
        throw error;  // Different error
      }
    }
  }

  // Max attempts exceeded
  throw new Error(`File lock conflict persisted after ${maxAttempts} attempts`);
}
```

---

## Pattern 5: Dependency Failure Recovery

**Scenario:** Task depends on external service that is down

**Code:**
```javascript
async function executeWithDependencyCheck(taskId, dependencyService) {
  try {
    // Check dependency health
    const healthCheck = await dependencyService.ping();
    if (!healthCheck.ok) {
      throw new Error(`Dependency unhealthy: ${dependencyService.name}`);
    }

    // Execute task
    const result = await dependencyService.execute(taskData);
    return result;
  } catch (error) {
    // Dependency failed - plan recovery
    const recoveryPlan = await planRecovery(taskId, {
      message: error.message,
      code: 'DEPENDENCY_UNAVAILABLE',
      dependency: dependencyService.name
    }, 'lex');

    if (recoveryPlan.classification.error_type === 'transient') {
      // Dependency may recover - retry with backoff
      console.log(`Dependency ${dependencyService.name} unavailable. Retrying...`);

      const backoffMs = recoveryPlan.recovery_strategy.backoff_ms;
      await new Promise(resolve => setTimeout(resolve, backoffMs));

      return executeWithDependencyCheck(taskId, dependencyService);
    } else {
      // Dependency permanently unavailable - escalate
      console.log('Dependency failure appears permanent. Escalating...');

      await taskLifecycle.transitionTask(
        taskId,
        'in_progress',
        'pending_approval',
        'lex',
        `Dependency ${dependencyService.name} unavailable`
      );
    }
  }
}
```

---

## Pattern 6: Exponential Backoff with Jitter

**Scenario:** Multiple tasks retrying simultaneously - avoid thundering herd

**Code:**
```javascript
async function executeWithJitter(taskId, operation) {
  let attempt = 1;

  while (attempt <= 5) {
    try {
      return await operation();
    } catch (error) {
      const recoveryPlan = await planRecovery(taskId, error, 'lex');

      if (recoveryPlan.recovery_strategy.action === 'retry') {
        // Backoff already includes jitter (configured in env)
        const backoffMs = recoveryPlan.recovery_strategy.backoff_ms;

        console.log(`Attempt ${attempt} failed. Retrying in ${Math.round(backoffMs/1000)}s (with jitter)`);

        await new Promise(resolve => setTimeout(resolve, backoffMs));
        attempt++;
      } else {
        throw error;
      }
    }
  }

  throw new Error('Max retries exceeded');
}
```

**Backoff Schedule (with jitter):**
```json
{
  "backoff_schedule": [
    { "attempt": 1, "delay_ms": 980, "retry_at": "2025-02-04T14:30:23Z" },
    { "attempt": 2, "delay_ms": 2150, "retry_at": "2025-02-04T14:32:25Z" },
    { "attempt": 3, "delay_ms": 3820, "retry_at": "2025-02-04T14:34:29Z" },
    { "attempt": 4, "delay_ms": 8200, "retry_at": "2025-02-04T14:38:37Z" },
    { "attempt": 5, "delay_ms": 16100, "retry_at": "2025-02-04T14:46:53Z" }
  ]
}
```

---

## Pattern 7: Batch Recovery Planning

**Scenario:** Multiple tasks failed - plan recovery for all

**Code:**
```javascript
async function recoverFailedTasks(failedTasks, agentName) {
  const recoveryPlans = [];

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

  console.log(`Recovery summary:
  - Retry: ${grouped.retry.length} tasks
  - Escalate: ${grouped.escalate.length} tasks
  - Abandon: ${grouped.abandon.length} tasks
  `);

  // Process retries with staggered scheduling
  for (const [index, plan] of grouped.retry.entries()) {
    const staggerMs = index * 500;  // 500ms stagger between retries
    const totalBackoff = plan.recovery_strategy.backoff_ms + staggerMs;

    console.log(`Task ${plan.task_id} scheduled to retry in ${Math.round(totalBackoff/1000)}s`);

    setTimeout(async () => {
      await retryTask(plan.task_id);
    }, totalBackoff);
  }

  // Escalate tasks immediately
  for (const plan of grouped.escalate) {
    await taskLifecycle.transitionTask(
      plan.task_id,
      'in_progress',
      'pending_approval',
      agentName,
      plan.escalation_policy.escalation_reason
    );
  }

  return recoveryPlans;
}
```

---

## Pattern 8: Recovery Plan Audit

**Scenario:** Review all recovery plans for a task

**Code:**
```javascript
async function auditTaskRecovery(taskId) {
  const recoveryPlansPath = `${process.env.VAULT_PATH}/Recovery_Plans`;

  // Find all recovery plans for this task
  const files = await fs.promises.readdir(recoveryPlansPath);
  const taskPlans = [];

  for (const file of files) {
    if (file.includes(taskId)) {
      const content = await fs.promises.readFile(`${recoveryPlansPath}/${file}`, 'utf-8');
      const plan = JSON.parse(content);
      taskPlans.push(plan);
    }
  }

  // Sort by creation time
  taskPlans.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));

  console.log(`Recovery history for task ${taskId}:`);
  console.log(`Total recovery attempts: ${taskPlans.length}`);

  for (const [index, plan] of taskPlans.entries()) {
    console.log(`
Attempt ${index + 1}:
  - Time: ${plan.created_at}
  - Error Type: ${plan.classification.error_type}
  - Category: ${plan.classification.category}
  - Action: ${plan.recovery_strategy.action}
  - Status: ${plan.status}
    `);
  }

  return taskPlans;
}
```

**Output:**
```
Recovery history for task TASK-12345:
Total recovery attempts: 3

Attempt 1:
  - Time: 2025-02-04T14:30:22Z
  - Error Type: transient
  - Category: network_timeout
  - Action: retry
  - Status: completed

Attempt 2:
  - Time: 2025-02-04T14:32:25Z
  - Error Type: transient
  - Category: network_timeout
  - Action: retry
  - Status: completed

Attempt 3:
  - Time: 2025-02-04T14:34:29Z
  - Error Type: transient
  - Category: network_timeout
  - Action: escalate
  - Status: active
```

---

## Integration with Task Lifecycle Manager

**Complete workflow:**
```javascript
const taskLifecycle = require('./task_lifecycle_manager');
const { planRecovery } = require('./error_recovery_planner');

async function executeTaskWithRecovery(taskId, operation, agentName) {
  try {
    // Execute task
    const result = await operation();

    // Mark task as completed
    await taskLifecycle.transitionTask(taskId, 'in_progress', 'pending_approval', agentName);

    return result;
  } catch (error) {
    // Task failed - plan recovery
    const recoveryPlan = await planRecovery(taskId, error, agentName);

    // Update task with recovery metadata
    await taskLifecycle.handleTaskFailure(taskId, error, agentName, recoveryPlan);

    // Execute recovery strategy
    if (recoveryPlan.recovery_strategy.action === 'retry') {
      const backoffMs = recoveryPlan.recovery_strategy.backoff_ms;
      await new Promise(resolve => setTimeout(resolve, backoffMs));

      // Recursive retry
      return executeTaskWithRecovery(taskId, operation, agentName);
    } else if (recoveryPlan.recovery_strategy.action === 'escalate') {
      console.log(`Task ${taskId} escalated: ${recoveryPlan.escalation_policy.escalation_reason}`);
      return null;
    } else {
      throw new Error(`Task ${taskId} abandoned after max retries`);
    }
  }
}
```

---

## Environment Configuration Examples

### Aggressive Retry (Development)
```bash
RECOVERY_MAX_RETRIES="5"
RECOVERY_BASE_BACKOFF_MS="500"
RECOVERY_STRATEGY="linear"
RECOVERY_ESCALATE_AFTER_ATTEMPTS="5"
```

### Conservative Retry (Production)
```bash
RECOVERY_MAX_RETRIES="3"
RECOVERY_BASE_BACKOFF_MS="2000"
RECOVERY_MAX_BACKOFF_MS="60000"
RECOVERY_STRATEGY="exponential"
RECOVERY_JITTER_FACTOR="0.3"
RECOVERY_ESCALATE_AFTER_ATTEMPTS="3"
RECOVERY_ESCALATE_PERMANENT_ERRORS="true"
```

### High-Availability Setup
```bash
RECOVERY_MAX_RETRIES="10"
RECOVERY_BASE_BACKOFF_MS="1000"
RECOVERY_MAX_BACKOFF_MS="300000"
RECOVERY_STRATEGY="fibonacci"
RECOVERY_AUTO_ABANDON_THRESHOLD="10"
```
