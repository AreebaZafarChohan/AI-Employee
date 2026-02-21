# Error Recovery Planner - Gotchas & Known Issues

This document lists common pitfalls, edge cases, and known limitations when using the Error Recovery Planner skill.

---

## 1. Exponential Backoff Can Grow Too Large

**Problem:**

Exponential backoff grows rapidly: 1s → 2s → 4s → 8s → 16s → 32s → 64s...

Without a cap, retry delays can become unreasonably long (hours or days).

**Mitigation:**

Always set `RECOVERY_MAX_BACKOFF_MS` to cap the maximum delay:

```bash
RECOVERY_MAX_BACKOFF_MS="300000"  # 5 minutes max
```

The skill enforces this limit automatically, but verify your configuration.

**Example:**
```javascript
// Attempt 10 with uncapped exponential backoff:
// delay = 1000 * 2^9 = 512,000ms = 8.5 minutes

// With cap of 300,000ms:
// delay = min(512000, 300000) = 300000ms = 5 minutes
```

---

## 2. Rate Limit Headers May Be Missing

**Problem:**

Some APIs return `429 Too Many Requests` without a `Retry-After` header.

Recovery planner expects this header for rate-limit aware backoff.

**Symptoms:**
- Recovery plan falls back to exponential backoff (may retry too soon)
- Repeated 429 errors without honoring rate limit window

**Mitigation:**

Configure default rate limit backoff in environment:

```bash
RECOVERY_RATE_LIMIT_DEFAULT_BACKOFF_MS="60000"  # Default to 1 minute
```

Or handle missing headers explicitly:

```javascript
function rateLimitBackoff(error, baseMs = 60000) {  // Higher default
  if (error.headers && error.headers['retry-after']) {
    return parseInt(error.headers['retry-after']) * 1000;
  }

  if (error.headers && error.headers['x-ratelimit-reset']) {
    const resetTime = parseInt(error.headers['x-ratelimit-reset']);
    const now = Math.floor(Date.now() / 1000);
    return Math.max((resetTime - now) * 1000, baseMs);
  }

  // No header - use conservative default
  console.warn('Rate limit error without Retry-After header. Using default backoff.');
  return baseMs;
}
```

---

## 3. Ambiguous Errors Default to Conservative Retry

**Problem:**

Errors that don't match transient or permanent patterns are classified as "ambiguous."

These get conservative retry logic (max 2 retries) to avoid wasting attempts.

**Symptoms:**
- Task escalates after only 2 retries (may be resolvable with more attempts)
- Recovery plan shows `classification.confidence: "low"`

**Mitigation:**

Add custom error patterns to environment variables:

```bash
RECOVERY_TRANSIENT_ERROR_PATTERNS="ETIMEDOUT,ECONNRESET,503,429,EAGAIN,YOUR_CUSTOM_ERROR"
```

Or improve error messages in your application to match known patterns.

**Example:**
```javascript
// Ambiguous error
throw new Error('Something went wrong');  // No pattern match

// Clear transient error
throw new Error('Request timeout after 30s');  // Matches /timeout/i pattern
```

---

## 4. Jitter Randomization Can Confuse Debugging

**Problem:**

Jitter adds random variance to backoff delays (e.g., 2000ms ± 20%).

This makes debugging harder because retry times are not deterministic.

**Symptoms:**
- Retry times vary between runs (expected behavior)
- Hard to reproduce timing-dependent bugs

**Mitigation:**

Disable jitter in development/testing:

```bash
RECOVERY_JITTER_FACTOR="0.0"  # No jitter in dev
```

Enable in production for thundering herd prevention:

```bash
RECOVERY_JITTER_FACTOR="0.2"  # 20% jitter in prod
```

**Debugging Tip:**

Recovery plans log exact backoff values used:

```json
{
  "backoff_schedule": [
    { "attempt": 1, "delay_ms": 980, "retry_at": "2025-02-04T14:30:23Z" },
    { "attempt": 2, "delay_ms": 2150, "retry_at": "2025-02-04T14:32:25Z" }
  ]
}
```

---

## 5. Sensitive Data May Leak in Error Messages

**Problem:**

Error messages can contain credentials, tokens, or PII:

```javascript
Error: Authentication failed for user john@example.com with token abc123xyz
```

If logged or stored unsanitized, this leaks sensitive data.

**Mitigation:**

Recovery planner sanitizes errors by default, but verify:

```javascript
const sanitized = sanitizeError(error);
console.log(sanitized.message);  // Credentials redacted
```

**Patterns automatically redacted:**
- Bearer tokens: `Bearer [REDACTED]`
- API keys: `api_key=[REDACTED]`
- Passwords: `password=[REDACTED]`
- Emails: `[EMAIL_REDACTED]`

**Custom Redaction:**

Add patterns to sanitization function if needed:

```javascript
const customPatterns = [
  { pattern: /session_id[=:]\s*['"]?[^\s'"]+['"]?/gi, replacement: 'session_id=[REDACTED]' }
];
```

---

## 6. Max Retries Config Can Be Overridden Per Task

**Problem:**

Global `RECOVERY_MAX_RETRIES` applies to all tasks, but some tasks may need different limits.

**Symptoms:**
- High-priority tasks fail after only 3 retries (could use more)
- Low-priority tasks waste resources with excessive retries

**Mitigation:**

Pass `max_retries` in recovery plan options:

```javascript
const plan = await planRecovery(taskId, error, agentName, {
  max_retries: 10,  // Override global setting
  backoff_strategy: 'exponential'
});
```

Or use task metadata to set per-task limits:

```json
{
  "task_id": "TASK-12345",
  "priority": "high",
  "recovery_config": {
    "max_retries": 10,
    "escalate_after_attempts": 10
  }
}
```

---

## 7. Retry Storms Under High Load

**Problem:**

Multiple tasks fail simultaneously and retry at the same time (thundering herd).

This can overwhelm downstream services and cause cascading failures.

**Symptoms:**
- Spikes in retry traffic
- Downstream service degrades further
- Recovery plans all have similar `next_retry_at` timestamps

**Mitigation:**

1. **Enable jitter** to spread retries:
   ```bash
   RECOVERY_JITTER_FACTOR="0.3"  # 30% randomization
   ```

2. **Stagger batch retries** manually:
   ```javascript
   for (const [index, plan] of recoveryPlans.entries()) {
     const staggerMs = index * 500;  // 500ms per task
     const totalBackoff = plan.recovery_strategy.backoff_ms + staggerMs;
     setTimeout(() => retryTask(plan.task_id), totalBackoff);
   }
   ```

3. **Use circuit breaker pattern** (separate skill):
   ```javascript
   if (circuitBreaker.isOpen('external-api')) {
     // Skip retries until circuit recovers
     return escalateTask(taskId);
   }
   ```

---

## 8. Permanent Errors Misclassified as Transient

**Problem:**

Some errors look transient but are actually permanent:

- `ENOTFOUND` (DNS resolution failure) - may be permanent if domain doesn't exist
- `500 Internal Server Error` - could be a bug (permanent) or load issue (transient)

**Symptoms:**
- Wasted retry attempts on unrecoverable errors
- Task eventually escalates after max retries

**Mitigation:**

Use confidence levels and retry counts:

```javascript
if (classification.error_type === 'transient' && classification.confidence === 'low') {
  // Conservative retry
  maxRetries = 2;  // Don't waste too many attempts
}
```

Or add heuristics for ambiguous cases:

```javascript
// If same error persists for 3+ attempts, reclassify as permanent
if (task.retry_metadata.attempts >= 3 && task.retry_metadata.last_error.code === errorCode) {
  classification.error_type = 'permanent';
  classification.reasoning = 'Error persisted across multiple retries, likely permanent';
}
```

---

## 9. Recovery Plans Accumulate Over Time

**Problem:**

Each error creates a recovery plan file in `Recovery_Plans/`.

Over time, this folder grows large (thousands of files).

**Symptoms:**
- Slow filesystem operations
- Disk space usage increases
- Audit queries become slow

**Mitigation:**

Implement cleanup job:

```bash
# Archive recovery plans older than 30 days
find "$VAULT_PATH/Recovery_Plans" -name '*.json' -mtime +30 -exec mv {} "$VAULT_PATH/Archive/Recovery_Plans/" \;
```

Or rotate logs in recovery planner:

```javascript
async function cleanupOldRecoveryPlans(daysToKeep = 30) {
  const cutoffDate = Date.now() - (daysToKeep * 24 * 60 * 60 * 1000);
  const plans = await fs.promises.readdir(`${VAULT_PATH}/Recovery_Plans`);

  let archived = 0;
  for (const file of plans) {
    const stats = await fs.promises.stat(`${VAULT_PATH}/Recovery_Plans/${file}`);
    if (stats.mtimeMs < cutoffDate) {
      await fs.promises.rename(
        `${VAULT_PATH}/Recovery_Plans/${file}`,
        `${VAULT_PATH}/Archive/Recovery_Plans/${file}`
      );
      archived++;
    }
  }

  console.log(`Archived ${archived} recovery plans older than ${daysToKeep} days`);
}
```

---

## 10. Backoff Strategies Can Be Confusing

**Problem:**

Three backoff strategies available: exponential, linear, fibonacci.

Choosing the wrong one can cause issues:
- **Exponential**: Grows too fast for long retry sequences
- **Linear**: May retry too aggressively under load
- **Fibonacci**: More balanced but less common (developers unfamiliar)

**Guidance:**

| Scenario | Recommended Strategy | Reasoning |
|----------|---------------------|-----------|
| **Network timeouts** | Exponential | Quick retries for transient blips, longer for sustained issues |
| **Rate limits** | Linear | Predictable spacing to avoid repeated limit hits |
| **File locks** | Linear (short) | High-frequency retries since locks are brief |
| **Service degradation** | Fibonacci | Balanced growth, good for load recovery |
| **Unknown errors** | Exponential | Safe default |

**Configuration:**

```bash
# Default strategy
RECOVERY_STRATEGY="exponential"

# Override per error type in code
if (error.status === 429) {
  plan.backoff_strategy = 'linear';
} else if (error.code === 'EBUSY') {
  plan.backoff_strategy = 'linear';
  plan.base_backoff_ms = 500;  // Short intervals
}
```

---

## 11. Escalation Can Create Approval Bottleneck

**Problem:**

Many tasks escalate to `Pending_Approval/` simultaneously.

Human becomes bottleneck (can't review 100 failed tasks quickly).

**Symptoms:**
- Tasks pile up in `Pending_Approval/`
- Recovery stalls waiting for human review
- Urgent tasks delayed behind low-priority failures

**Mitigation:**

1. **Prioritize escalations**:
   ```javascript
   // High-priority tasks escalate to separate folder
   if (task.priority === 'high') {
     await taskLifecycle.transitionTask(taskId, 'in_progress', 'urgent_approval', 'lex');
   } else {
     await taskLifecycle.transitionTask(taskId, 'in_progress', 'pending_approval', 'lex');
   }
   ```

2. **Batch similar failures**:
   ```javascript
   // If 10+ tasks fail with same error, create one escalation
   const similarFailures = await findSimilarFailures(error);
   if (similarFailures.length >= 10) {
     await createBatchEscalation(similarFailures);
   }
   ```

3. **Auto-approve safe retries** (Gold/Platinum tier):
   ```bash
   TASK_AUTO_APPROVE_SAFE_ACTIONS="true"
   ```

---

## 12. Concurrent Recovery Plans for Same Task

**Problem:**

Multiple agents try to create recovery plans for the same task simultaneously.

Results in duplicate recovery plans with conflicting strategies.

**Symptoms:**
- Multiple `REC-*` files for same `task_id`
- Recovery actions executed multiple times
- Wasted retries

**Mitigation:**

Use atomic operations with task lifecycle manager:

```javascript
async function planRecoveryAtomic(taskId, error, agentName) {
  // Check if recovery plan already exists
  const existingPlans = await findRecoveryPlans(taskId);

  if (existingPlans.length > 0) {
    const latestPlan = existingPlans[existingPlans.length - 1];
    console.log(`Recovery plan already exists: ${latestPlan.recovery_plan_id}`);
    return latestPlan;
  }

  // Create new plan (only if none exists)
  const plan = await createRecoveryPlan(taskId, error, agentName);
  return plan;
}
```

Or use file locking:

```javascript
const lockFile = `${VAULT_PATH}/Recovery_Plans/.lock-${taskId}`;

try {
  await fs.promises.writeFile(lockFile, agentName, { flag: 'wx' });  // Exclusive create
  const plan = await createRecoveryPlan(taskId, error, agentName);
  await fs.promises.unlink(lockFile);
  return plan;
} catch (err) {
  if (err.code === 'EEXIST') {
    console.log('Another agent is already planning recovery for this task');
    return null;
  }
  throw err;
}
```

---

## 13. Recovery Plans Don't Auto-Execute

**Problem:**

Recovery planner creates plans but doesn't execute them automatically.

Agents must read plans and implement recovery actions.

**Symptoms:**
- Recovery plans created but tasks still failed
- No retries happen even though plan says "retry"

**Mitigation:**

This is by design (separation of planning and execution).

Agents must integrate recovery planner with execution logic:

```javascript
async function executeWithRecovery(taskId, operation, agentName) {
  try {
    return await operation();
  } catch (error) {
    // Plan recovery
    const plan = await planRecovery(taskId, error, agentName);

    // Execute recovery strategy
    if (plan.recovery_strategy.action === 'retry') {
      await sleep(plan.recovery_strategy.backoff_ms);
      return executeWithRecovery(taskId, operation, agentName);  // Recursive
    } else if (plan.recovery_strategy.action === 'escalate') {
      await taskLifecycle.escalateTask(taskId, plan.escalation_policy.escalation_reason);
    }
  }
}
```

See `references/patterns.md` for complete integration examples.

---

## Summary

**Most Common Gotchas:**

1. Forgetting to set `RECOVERY_MAX_BACKOFF_MS` (backoff grows too large)
2. Not sanitizing sensitive data in error messages
3. Misclassifying permanent errors as transient (wasted retries)
4. Not handling missing `Retry-After` headers
5. Recovery plans accumulate without cleanup

**Best Practices:**

- Always configure `RECOVERY_MAX_BACKOFF_MS` and `RECOVERY_MAX_RETRIES`
- Enable jitter in production to prevent thundering herd
- Review recovery plans periodically (audit failures)
- Archive old recovery plans (keep disk usage low)
- Integrate recovery planner with task lifecycle manager (don't use standalone)
