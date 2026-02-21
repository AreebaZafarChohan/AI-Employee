# Error Recovery Planner

Intelligent error analysis and recovery planning for failed or blocked tasks with automatic backoff logic and actionable next steps.

## Quick Start

### 1. Installation

The error recovery planner is file-based and requires no external dependencies.

```bash
# Ensure vault directory exists
export VAULT_PATH="/path/to/vault"

# Create Recovery_Plans folder (if not exists)
mkdir -p "$VAULT_PATH/Recovery_Plans"

# Copy environment configuration
cp assets/.env.example .env

# Configure environment variables
vim .env
```

### 2. Basic Usage

```javascript
const { planRecovery } = require('./error_recovery_planner');

// Task fails with an error
try {
  await executeTask(taskId);
} catch (error) {
  // Plan recovery
  const recoveryPlan = await planRecovery(taskId, error, 'lex');

  console.log(`Recovery action: ${recoveryPlan.recovery_strategy.action}`);
  console.log(`Error type: ${recoveryPlan.classification.error_type}`);

  // Execute recovery strategy
  if (recoveryPlan.recovery_strategy.action === 'retry') {
    const backoffMs = recoveryPlan.recovery_strategy.backoff_ms;
    console.log(`Retrying in ${Math.round(backoffMs/1000)} seconds...`);

    await sleep(backoffMs);
    await executeTask(taskId);  // Retry
  } else if (recoveryPlan.recovery_strategy.action === 'escalate') {
    await escalateToHuman(taskId, recoveryPlan.escalation_policy.escalation_reason);
  }
}
```

### 3. Configuration

Key environment variables:

```bash
# Retry limits
RECOVERY_MAX_RETRIES="3"
RECOVERY_MAX_BACKOFF_MS="300000"  # 5 minutes cap

# Backoff strategy
RECOVERY_STRATEGY="exponential"
RECOVERY_BASE_BACKOFF_MS="1000"
RECOVERY_JITTER_FACTOR="0.2"

# Escalation
RECOVERY_ESCALATE_AFTER_ATTEMPTS="3"
RECOVERY_ESCALATE_PERMANENT_ERRORS="true"
```

See `assets/.env.example` for full configuration options.

---

## Features

### ✅ Intelligent Error Classification

Automatically classifies errors as:
- **Transient**: Network timeouts, rate limits, temporary unavailability (retry with backoff)
- **Permanent**: Authentication failures, not found, invalid input (escalate immediately)
- **Ambiguous**: Unknown errors (conservative retry with manual review)

### ✅ Multiple Backoff Strategies

- **Exponential**: 1s → 2s → 4s → 8s (default, good for most cases)
- **Linear**: 5s → 10s → 15s (good for rate limits)
- **Fibonacci**: 1s → 1s → 2s → 3s → 5s (balanced growth)
- **Rate-Limit Aware**: Uses `Retry-After` header from API responses

### ✅ Thundering Herd Prevention

- Configurable jitter (randomization) prevents simultaneous retries
- Staggered scheduling for batch operations
- Exponential backoff reduces load on struggling services

### ✅ Sensitive Data Protection

- Automatic sanitization of error messages (tokens, passwords, emails redacted)
- Recovery plans safe to log and share
- Audit trail without exposing credentials

### ✅ Escalation Policies

- Permanent errors escalate immediately (no wasted retries)
- Configurable escalation thresholds
- Batch similar failures to reduce human workload
- Priority-based escalation queues

---

## Architecture

```
┌─────────────────┐
│  Task Fails     │
└────────┬────────┘
         │
         v
┌─────────────────────┐
│ Error Recovery      │
│ Planner             │
│                     │
│ 1. Classify Error   │
│ 2. Choose Strategy  │
│ 3. Generate Plan    │
│ 4. Persist Plan     │
└────────┬────────────┘
         │
         v
┌─────────────────────┐
│ Recovery Plan       │
│ (JSON file)         │
│                     │
│ - Action: retry     │
│ - Backoff: 2000ms   │
│ - Next retry: ...   │
└────────┬────────────┘
         │
         v
┌─────────────────────┐
│ Agent Executes      │
│ Recovery            │
│                     │
│ - Wait backoff      │
│ - Retry task        │
│ - Or escalate       │
└─────────────────────┘
```

---

## Use Cases

### 1. Network Timeout Recovery

**Scenario**: HTTP request times out after 30 seconds

**Recovery Plan**:
- Classification: `transient` (network timeout)
- Action: `retry`
- Backoff: Exponential (1s → 2s → 4s)
- Max Retries: 3
- Escalate: After 3 failed attempts

### 2. Rate Limit Handling

**Scenario**: API returns `429 Too Many Requests` with `Retry-After: 60`

**Recovery Plan**:
- Classification: `transient` (rate limit)
- Action: `retry`
- Backoff: Rate-limit aware (60 seconds as instructed by server)
- Max Retries: 5
- Escalate: If rate limit persists after 5 attempts

### 3. Authentication Failure

**Scenario**: API returns `401 Unauthorized`

**Recovery Plan**:
- Classification: `permanent` (authentication failure)
- Action: `escalate`
- Escalate: Immediately (no retry)
- Reason: "Invalid credentials - manual review required"

### 4. File Lock Conflict

**Scenario**: Task fails due to file being locked by another process

**Recovery Plan**:
- Classification: `transient` (file lock)
- Action: `retry`
- Backoff: Linear (500ms → 1s → 1.5s → 2s → 2.5s)
- Max Retries: 5
- Escalate: If lock persists after 5 attempts

---

## Integration

### With Task Lifecycle Manager

```javascript
const taskLifecycle = require('./task_lifecycle_manager');
const { planRecovery } = require('./error_recovery_planner');

async function executeTaskWithRecovery(taskId, operation, agentName) {
  try {
    const result = await operation();
    await taskLifecycle.transitionTask(taskId, 'in_progress', 'pending_approval', agentName);
    return result;
  } catch (error) {
    // Plan recovery
    const recoveryPlan = await planRecovery(taskId, error, agentName);

    // Update task with recovery metadata
    await taskLifecycle.handleTaskFailure(taskId, error, agentName, recoveryPlan);

    // Execute recovery strategy
    if (recoveryPlan.recovery_strategy.action === 'retry') {
      await sleep(recoveryPlan.recovery_strategy.backoff_ms);
      return executeTaskWithRecovery(taskId, operation, agentName);  // Recursive retry
    } else if (recoveryPlan.recovery_strategy.action === 'escalate') {
      await taskLifecycle.transitionTask(
        taskId,
        'in_progress',
        'pending_approval',
        agentName,
        recoveryPlan.escalation_policy.escalation_reason
      );
    }
  }
}
```

### With Vault State Manager

```javascript
const vaultManager = require('./vault_state_manager');

async function saveRecoveryPlan(plan) {
  const filename = `REC-${Date.now()}-${plan.task_id}.json`;
  const filePath = `Recovery_Plans/${filename}`;

  await vaultManager.writeVaultFile(
    filePath,
    JSON.stringify(plan, null, 2),
    plan.created_by
  );

  return filePath;
}
```

---

## Files

- **SKILL.md**: Complete skill specification with blueprints and validation
- **references/patterns.md**: Concrete code examples and usage patterns
- **references/gotchas.md**: Common pitfalls, edge cases, and known limitations
- **references/impact-checklist.md**: Pre-deployment impact assessment checklist
- **assets/.env.example**: Environment configuration template
- **assets/recovery-plan.template.json**: Recovery plan JSON schema

---

## Testing

### Unit Tests

```javascript
// Test error classification
test('classifies network timeout as transient', () => {
  const error = { message: 'ETIMEDOUT: Connection timeout', code: 'ETIMEDOUT' };
  const classification = classifyError(error);
  expect(classification.error_type).toBe('transient');
});

// Test backoff calculation
test('exponential backoff grows correctly', () => {
  expect(exponentialBackoff(1)).toBe(1000);
  expect(exponentialBackoff(2)).toBe(2000);
  expect(exponentialBackoff(3)).toBe(4000);
});

// Test sanitization
test('sanitizes bearer tokens in error messages', () => {
  const error = { message: 'Auth failed: Bearer abc123xyz' };
  const sanitized = sanitizeError(error);
  expect(sanitized.message).toBe('Auth failed: Bearer [REDACTED]');
});
```

### Integration Tests

```javascript
// Test with task lifecycle manager
test('escalates permanent errors immediately', async () => {
  const error = { status: 401, message: 'Unauthorized' };
  const plan = await planRecovery('TASK-123', error, 'lex');

  expect(plan.classification.error_type).toBe('permanent');
  expect(plan.recovery_strategy.action).toBe('escalate');

  // Verify task transitioned to pending_approval
  const task = await taskLifecycle.getTask('TASK-123');
  expect(task.status).toBe('pending_approval');
});
```

---

## Monitoring

### Key Metrics

- **Recovery plan creation rate**: Plans created per hour
- **Retry success rate**: % of retries that succeed
- **Escalation rate**: % of tasks that escalate
- **Average backoff duration**: Mean delay before retry
- **Retry distribution**: Histogram of retry counts

### Alerts

- Alert if recovery plan creation rate spikes (> 100/hour)
- Alert if retry success rate drops below 50%
- Alert if escalation queue grows > 50 tasks
- Alert if same error type occurs > 100 times (systemic issue)

### Dashboard

```javascript
// Example metrics query
const metrics = {
  total_recovery_plans: await countRecoveryPlans(),
  retry_success_rate: await calculateRetrySuccessRate(),
  escalation_rate: await calculateEscalationRate(),
  top_error_types: await getTopErrorTypes(10),
  avg_backoff_duration: await calculateAvgBackoff()
};
```

---

## Troubleshooting

### Problem: Tasks retry too aggressively

**Solution**: Increase base backoff or reduce max retries

```bash
RECOVERY_BASE_BACKOFF_MS="2000"  # Increase from 1000ms
RECOVERY_MAX_RETRIES="2"  # Reduce from 3
```

### Problem: Tasks escalate too quickly

**Solution**: Increase max retries or escalation threshold

```bash
RECOVERY_MAX_RETRIES="5"  # Increase from 3
RECOVERY_ESCALATE_AFTER_ATTEMPTS="5"  # Increase from 3
```

### Problem: Retry storms under high load

**Solution**: Enable jitter and increase backoff

```bash
RECOVERY_JITTER_FACTOR="0.3"  # 30% randomization
RECOVERY_BASE_BACKOFF_MS="2000"  # Longer delays
```

### Problem: Sensitive data in logs

**Solution**: Verify sanitization is enabled

```bash
# Check sanitization function
grep -A 20 "function sanitizeError" error_recovery_planner.js

# Review recovery plans for leaks
find "$VAULT_PATH/Recovery_Plans" -name '*.json' -exec grep -i "password\|token\|key" {} \;
```

---

## Contributing

### Adding Custom Error Patterns

Edit environment variables:

```bash
RECOVERY_TRANSIENT_ERROR_PATTERNS="ETIMEDOUT,ECONNRESET,YOUR_CUSTOM_ERROR"
RECOVERY_PERMANENT_ERROR_PATTERNS="401,403,YOUR_PERMANENT_ERROR"
```

### Adding New Backoff Strategies

Implement in `error_recovery_planner.js`:

```javascript
function customBackoff(attemptNumber) {
  // Your backoff logic here
  return delayMs;
}

// Register strategy
const backoffStrategies = {
  exponential: exponentialBackoff,
  linear: linearBackoff,
  fibonacci: fibonacciBackoff,
  custom: customBackoff  // Add here
};
```

---

## License

This skill is part of the Digital FTE project and follows the project's licensing terms.

---

## Support

- **Documentation**: See `references/` folder for detailed guides
- **Issues**: Report issues to project maintainer
- **Questions**: Check `references/gotchas.md` for common issues

---

## Version History

- **v1.0.0** (2025-02-04): Initial release
  - Error classification (transient, permanent, ambiguous)
  - Multiple backoff strategies (exponential, linear, fibonacci)
  - Rate-limit aware backoff
  - Sensitive data sanitization
  - Escalation policies
  - Integration with task lifecycle manager
