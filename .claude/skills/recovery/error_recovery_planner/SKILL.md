---
name: error_recovery_planner
description: Plan retries and recovery strategies for transient or blocked tasks with intelligent backoff logic and actionable next steps.
---

# Error Recovery Planner

## Purpose

This skill provides intelligent error analysis and recovery planning for failed or blocked tasks in the Digital FTE workflow. It examines error context, determines whether failures are transient or permanent, and generates actionable recovery strategies with appropriate backoff logic.

Unlike reactive error handling, this skill proactively plans recovery paths based on error classification, task history, and system state.

## When to Use This Skill

Use `error_recovery_planner` when:

- **Task execution failed**: Agent encounters errors during task processing
- **Transient failures detected**: Network timeouts, rate limits, temporary unavailability
- **Resource conflicts**: File locks, concurrent access, race conditions
- **Dependency failures**: Upstream service failures, missing prerequisites
- **Quota exceeded**: API rate limits, resource limits, budget constraints
- **Blocked tasks**: Tasks stuck in intermediate states
- **Repeated failures**: Same task failing multiple times
- **Recovery decision needed**: Determining whether to retry, escalate, or abandon

Do NOT use this skill when:

- **Permanent failures**: Logic errors, invalid input, design flaws (use debugging instead)
- **Security violations**: Authentication failures, permission denials (requires human intervention)
- **Data corruption**: File corruption, database inconsistencies (requires manual recovery)
- **Successful executions**: No error occurred
- **Human decisions**: Strategic decisions requiring business judgment

## Impact Analysis Workflow

### 1. Environment Variable Strategy

**Build-Time vs Runtime Variables:**

This skill operates at runtime only. No build-time variables required.

**Runtime variables:**
```bash
# Required (inherited from task_lifecycle_manager)
VAULT_PATH="/absolute/path/to/vault"

# Optional: Recovery configuration
RECOVERY_MAX_RETRIES="3"                     # Max automatic retry attempts
RECOVERY_BASE_BACKOFF_MS="1000"              # Base backoff for exponential strategy
RECOVERY_MAX_BACKOFF_MS="300000"             # Max backoff (5 minutes)
RECOVERY_JITTER_FACTOR="0.2"                 # Randomization factor (0.0-1.0)
RECOVERY_STRATEGY="exponential"              # exponential | linear | fibonacci

# Optional: Error classification
RECOVERY_TRANSIENT_ERROR_PATTERNS="ETIMEDOUT,ECONNRESET,503,429,EAGAIN"
RECOVERY_PERMANENT_ERROR_PATTERNS="401,403,404,ENOENT,EINVAL"
RECOVERY_RETRY_HTTP_CODES="408,429,500,502,503,504"

# Optional: Escalation thresholds
RECOVERY_ESCALATE_AFTER_ATTEMPTS="3"         # Escalate to human after N failures
RECOVERY_ESCALATE_PERMANENT_ERRORS="true"    # Immediately escalate permanent errors
RECOVERY_AUTO_ABANDON_THRESHOLD="5"          # Abandon after N total retries

# Optional: Recovery plans storage
RECOVERY_PLANS_PATH="$VAULT_PATH/Recovery_Plans"
RECOVERY_AUDIT_LOG="$VAULT_PATH/Audit_Logs/recovery.log"
```

**Secrets Management:**

- This skill does NOT handle secrets
- May log sanitized error messages (no sensitive data)
- Recovery plans stored in plain text (no credentials)

**Variable Discovery Process:**
```bash
# Check recovery configuration
cat .env | grep RECOVERY_

# Count active recovery plans
find "$VAULT_PATH/Recovery_Plans" -name '*.json' -mtime -1 | wc -l

# Analyze error patterns
cat "$VAULT_PATH/Audit_Logs/recovery.log" | jq -r '.error_type' | sort | uniq -c
```

### 2. Network & Topology Implications

**Port Discovery:**

No network ports required. This skill operates on local filesystem only.

**Dependency Topology:**

```
Error Recovery Planner
  ├── Task Lifecycle Manager (task state queries)
  │   └── Vault State Manager (file operations)
  ├── Audit Logs (error history)
  └── Recovery Plans storage (Recovery_Plans/)
```

**Integration Points:**

This skill coordinates with:
- **Task Lifecycle Manager**: Queries task history and retry metadata
- **Local Executive Agent (lex)**: Consumes recovery plans
- **Orchestrator agent**: Executes recovery actions
- **Human**: Reviews escalated recovery plans

**Concurrency Considerations:**

- Multiple agents may request recovery plans concurrently
- Recovery plans are read-only once created
- Task state transitions still follow single-writer rules

### 3. Auth / CORS / Security Impact

**Authentication Pattern Analysis:**

- No authentication required (local filesystem)
- Agent authorization: all agents can read recovery plans
- Only task owner can execute recovery actions

**Security Considerations:**

| Risk | Mitigation |
|------|-----------|
| **Sensitive error data exposure** | Sanitize error messages before logging |
| **Infinite retry loops** | Hard cap on retry attempts (configurable) |
| **Resource exhaustion** | Exponential backoff prevents retry storms |
| **Recovery plan tampering** | Validate plans before execution |
| **Information leakage** | Never log credentials, API keys, or PII |

**Validation Rules:**

Before creating recovery plan:
```javascript
function validateRecoveryPlan(plan) {
  // Required fields
  if (!plan.task_id || !plan.error_context) {
    throw new Error("Task ID and error context are required");
  }

  // Retry limits
  if (plan.max_retries > parseInt(process.env.RECOVERY_AUTO_ABANDON_THRESHOLD || '5')) {
    throw new Error(`Max retries exceeds safety threshold (${process.env.RECOVERY_AUTO_ABANDON_THRESHOLD})`);
  }

  // Backoff strategy validation
  const validStrategies = ['exponential', 'linear', 'fibonacci', 'none'];
  if (!validStrategies.includes(plan.backoff_strategy)) {
    throw new Error(`Invalid backoff strategy: ${plan.backoff_strategy}`);
  }

  return true;
}
```

---

## Blueprints & Templates Used

### Blueprint: Error Classification Matrix

**Purpose:** Classify errors as transient, permanent, or ambiguous

**Classification Rules:**

| Error Type | Classification | Retry? | Backoff Strategy | Escalate? |
|------------|----------------|--------|------------------|-----------|
| **Network timeout** | Transient | Yes (3x) | Exponential | After 3 failures |
| **Connection refused** | Transient | Yes (3x) | Exponential | After 3 failures |
| **Rate limit (429)** | Transient | Yes (5x) | Linear with rate-limit headers | After 5 failures |
| **Service unavailable (503)** | Transient | Yes (3x) | Exponential | After 3 failures |
| **File locked** | Transient | Yes (5x) | Linear (short) | After 5 failures |
| **Auth failure (401)** | Permanent | No | None | Immediately |
| **Not found (404)** | Permanent | No | None | Immediately |
| **Invalid input** | Permanent | No | None | Immediately |
| **Logic error** | Permanent | No | None | Immediately |
| **Insufficient permissions** | Permanent | No | None | Immediately |
| **Quota exceeded** | Ambiguous | Maybe | None | Immediately |
| **Dependency missing** | Ambiguous | Yes (2x) | Linear | After 2 failures |

**Implementation:**

```javascript
function classifyError(error) {
  const errorMsg = error.message.toLowerCase();
  const errorCode = error.code;
  const httpStatus = error.status;

  // Transient error patterns
  const transientPatterns = [
    /timeout/i,
    /econnreset/i,
    /econnrefused/i,
    /eagain/i,
    /temporarily unavailable/i
  ];

  const transientHttpCodes = [408, 429, 500, 502, 503, 504];

  // Permanent error patterns
  const permanentPatterns = [
    /not found/i,
    /invalid/i,
    /forbidden/i,
    /unauthorized/i,
    /permission denied/i,
    /syntax error/i
  ];

  const permanentHttpCodes = [400, 401, 403, 404, 405, 410];

  // Check transient patterns
  if (transientHttpCodes.includes(httpStatus)) {
    return { classification: 'transient', confidence: 'high' };
  }

  for (const pattern of transientPatterns) {
    if (pattern.test(errorMsg) || pattern.test(errorCode)) {
      return { classification: 'transient', confidence: 'high' };
    }
  }

  // Check permanent patterns
  if (permanentHttpCodes.includes(httpStatus)) {
    return { classification: 'permanent', confidence: 'high' };
  }

  for (const pattern of permanentPatterns) {
    if (pattern.test(errorMsg)) {
      return { classification: 'permanent', confidence: 'high' };
    }
  }

  // Default to ambiguous
  return { classification: 'ambiguous', confidence: 'low' };
}
```

### Blueprint: Backoff Strategy Generator

**Purpose:** Generate retry schedules based on error type and history

**Supported Strategies:**

1. **Exponential Backoff** (default for transient errors)
   ```javascript
   function exponentialBackoff(attemptNumber, baseMs = 1000, maxMs = 300000, jitter = 0.2) {
     const delay = Math.min(baseMs * Math.pow(2, attemptNumber - 1), maxMs);
     const jitterRange = delay * jitter;
     const jitterOffset = Math.random() * jitterRange - (jitterRange / 2);
     return Math.round(delay + jitterOffset);
   }

   // Example: attempt 1 → ~1s, attempt 2 → ~2s, attempt 3 → ~4s, attempt 4 → ~8s
   ```

2. **Linear Backoff** (for rate limits with known recovery time)
   ```javascript
   function linearBackoff(attemptNumber, intervalMs = 5000) {
     return intervalMs * attemptNumber;
   }

   // Example: attempt 1 → 5s, attempt 2 → 10s, attempt 3 → 15s
   ```

3. **Fibonacci Backoff** (balanced growth)
   ```javascript
   function fibonacciBackoff(attemptNumber, baseMs = 1000) {
     const fib = [0, 1];
     for (let i = 2; i <= attemptNumber; i++) {
       fib[i] = fib[i-1] + fib[i-2];
     }
     return fib[attemptNumber] * baseMs;
   }

   // Example: attempt 1 → 1s, attempt 2 → 1s, attempt 3 → 2s, attempt 4 → 3s, attempt 5 → 5s
   ```

4. **Rate-Limit Aware Backoff** (uses Retry-After header)
   ```javascript
   function rateLimitBackoff(error, baseMs = 1000) {
     if (error.headers && error.headers['retry-after']) {
       const retryAfter = parseInt(error.headers['retry-after']);
       return retryAfter * 1000; // Convert seconds to ms
     }

     if (error.headers && error.headers['x-ratelimit-reset']) {
       const resetTime = parseInt(error.headers['x-ratelimit-reset']);
       const now = Math.floor(Date.now() / 1000);
       return Math.max((resetTime - now) * 1000, baseMs);
     }

     // Fallback to exponential
     return exponentialBackoff(1, baseMs);
   }
   ```

### Blueprint: Recovery Plan Template

**Purpose:** Structured recovery plan with actionable steps

**Template Structure:**

```json
{
  "recovery_plan_id": "REC-20250204-143022-ABC123",
  "task_id": "TASK-12345",
  "created_at": "2025-02-04T14:30:22Z",
  "created_by": "lex",
  "status": "active",

  "error_context": {
    "error_message": "ETIMEDOUT: Connection timeout after 30s",
    "error_code": "ETIMEDOUT",
    "error_stack": "Error: ETIMEDOUT...",
    "occurred_at": "2025-02-04T14:25:15Z",
    "task_state": "in_progress",
    "attempt_number": 2
  },

  "classification": {
    "error_type": "transient",
    "category": "network_timeout",
    "confidence": "high",
    "reasoning": "Network timeout errors are typically transient and resolve on retry"
  },

  "recovery_strategy": {
    "action": "retry",
    "max_retries": 3,
    "current_attempt": 2,
    "backoff_strategy": "exponential",
    "next_retry_at": "2025-02-04T14:34:22Z",
    "backoff_schedule": [
      { "attempt": 1, "delay_ms": 1000, "retry_at": "2025-02-04T14:30:23Z" },
      { "attempt": 2, "delay_ms": 2000, "retry_at": "2025-02-04T14:32:25Z" },
      { "attempt": 3, "delay_ms": 4000, "retry_at": "2025-02-04T14:34:29Z" }
    ]
  },

  "recommended_actions": [
    {
      "priority": 1,
      "action": "retry_with_backoff",
      "description": "Retry task execution with 4-second exponential backoff",
      "automated": true,
      "requires_approval": false
    },
    {
      "priority": 2,
      "action": "check_network_health",
      "description": "Verify network connectivity to external service",
      "automated": false,
      "requires_approval": false
    },
    {
      "priority": 3,
      "action": "escalate_to_human",
      "description": "Escalate to human if retry fails again",
      "automated": true,
      "requires_approval": false,
      "trigger_condition": "attempt >= 3"
    }
  ],

  "escalation_policy": {
    "escalate_after_attempts": 3,
    "escalate_if_permanent": true,
    "escalation_reason": "Max retries exceeded without success",
    "escalation_target": "human_operator"
  },

  "metadata": {
    "related_tasks": [],
    "similar_failures_count": 0,
    "last_successful_execution": "2025-02-03T10:15:00Z",
    "environment": "production"
  }
}
```

### Blueprint: Recovery Decision Tree

**Purpose:** Deterministic decision-making for recovery actions

**Decision Flow:**

```
┌─────────────────┐
│ Error Occurred  │
└────────┬────────┘
         │
         v
┌─────────────────────┐
│ Classify Error Type │
└────────┬────────────┘
         │
    ┌────┴────┐
    │         │
    v         v
┌──────────┐ ┌───────────┐
│Transient │ │ Permanent │
└────┬─────┘ └─────┬─────┘
     │             │
     v             v
┌──────────────┐ ┌─────────────────┐
│Check Retry   │ │ Escalate        │
│  Count       │ │ Immediately     │
└──────┬───────┘ └─────────────────┘
       │
  ┌────┴────┐
  │         │
  v         v
< Max?    >= Max?
  │         │
  v         v
┌──────────────┐ ┌─────────────────┐
│ Retry with   │ │ Escalate or     │
│ Backoff      │ │ Abandon         │
└──────────────┘ └─────────────────┘
```

**Implementation:**

```javascript
async function planRecovery(taskId, error, agentName) {
  // Step 1: Load task history
  const task = await taskLifecycle.getTask(taskId);

  // Step 2: Classify error
  const classification = classifyError(error);

  // Step 3: Make decision based on classification
  let recoveryPlan;

  if (classification.classification === 'permanent') {
    // Permanent error: escalate immediately
    recoveryPlan = {
      action: 'escalate',
      reason: 'Permanent error detected',
      recommended_actions: [
        { action: 'escalate_to_human', description: 'Manual intervention required' }
      ]
    };
  } else if (classification.classification === 'transient') {
    // Transient error: check retry count
    const attemptNumber = (task.retry_metadata?.attempts || 0) + 1;
    const maxRetries = parseInt(process.env.RECOVERY_MAX_RETRIES || '3');

    if (attemptNumber <= maxRetries) {
      // Retry with backoff
      const backoffMs = exponentialBackoff(attemptNumber);
      const nextRetryAt = new Date(Date.now() + backoffMs);

      recoveryPlan = {
        action: 'retry',
        max_retries: maxRetries,
        current_attempt: attemptNumber,
        backoff_strategy: 'exponential',
        next_retry_at: nextRetryAt.toISOString(),
        backoff_ms: backoffMs,
        recommended_actions: [
          {
            action: 'retry_with_backoff',
            description: `Retry after ${Math.round(backoffMs/1000)}s delay`,
            automated: true
          }
        ]
      };
    } else {
      // Max retries exceeded: escalate
      recoveryPlan = {
        action: 'escalate',
        reason: `Max retries (${maxRetries}) exceeded`,
        total_attempts: attemptNumber,
        recommended_actions: [
          { action: 'escalate_to_human', description: 'Persistent transient failure' }
        ]
      };
    }
  } else {
    // Ambiguous error: conservative retry
    recoveryPlan = {
      action: 'retry_conservative',
      max_retries: 2,
      current_attempt: (task.retry_metadata?.attempts || 0) + 1,
      backoff_strategy: 'linear',
      recommended_actions: [
        { action: 'retry_with_backoff', description: 'Limited retry with manual review' },
        { action: 'escalate_if_fails', description: 'Escalate if second retry fails' }
      ]
    };
  }

  // Step 4: Generate full recovery plan
  const fullPlan = {
    recovery_plan_id: generateRecoveryId(),
    task_id: taskId,
    created_at: new Date().toISOString(),
    created_by: agentName,
    status: 'active',
    error_context: sanitizeError(error),
    classification: classification,
    recovery_strategy: recoveryPlan,
    escalation_policy: generateEscalationPolicy(classification, recoveryPlan)
  };

  // Step 5: Persist recovery plan
  await saveRecoveryPlan(fullPlan);

  return fullPlan;
}
```

### Blueprint: Sanitization for Error Logging

**Purpose:** Remove sensitive data from error messages before logging

**Implementation:**

```javascript
function sanitizeError(error) {
  const sanitized = {
    message: error.message,
    code: error.code,
    status: error.status,
    occurred_at: new Date().toISOString()
  };

  // Patterns to redact
  const sensitivePatterns = [
    { pattern: /Bearer [A-Za-z0-9\-._~+\/]+=*/g, replacement: 'Bearer [REDACTED]' },
    { pattern: /api[_-]?key[=:]\s*['"]?[A-Za-z0-9]+['"]?/gi, replacement: 'api_key=[REDACTED]' },
    { pattern: /password[=:]\s*['"]?[^\s'"]+['"]?/gi, replacement: 'password=[REDACTED]' },
    { pattern: /token[=:]\s*['"]?[A-Za-z0-9\-._~+\/]+=*['"]?/gi, replacement: 'token=[REDACTED]' },
    { pattern: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g, replacement: '[EMAIL_REDACTED]' }
  ];

  // Apply redactions
  for (const { pattern, replacement } of sensitivePatterns) {
    if (sanitized.message) {
      sanitized.message = sanitized.message.replace(pattern, replacement);
    }
  }

  // Truncate long messages
  if (sanitized.message && sanitized.message.length > 500) {
    sanitized.message = sanitized.message.substring(0, 497) + '...';
  }

  return sanitized;
}
```

---

## Validation Checklist

### Mandatory Checks (Skill Invalid If Failed)

- [x] Uses canonical folder structure: `SKILL.md`, `references/`, `assets/`
- [x] Contains complete impact analysis (Env, Network, Auth)
- [x] No `localhost` hardcoding (N/A - filesystem only)
- [x] No secrets or passwords in templates
- [x] Auth/CORS impact explicitly documented
- [x] Supports containerization (Docker volume mounts)
- [x] Gotchas document has known failures and mitigation
- [x] Anti-patterns list common mistakes
- [x] All templates use parameterized placeholders
- [x] Templates include IMPACT NOTES comments
- [x] References folder has all three files
- [x] SKILL.md contains all 9 required sections

### Recovery-Specific Checks

- [x] Error classification logic clearly defined
- [x] Backoff strategies implemented (exponential, linear, fibonacci)
- [x] Hard caps on retry attempts (prevents infinite loops)
- [x] Sensitive data sanitization before logging
- [x] Escalation policies for permanent errors
- [x] Recovery plans stored persistently
- [x] Decision tree for retry/escalate/abandon
- [x] Support for rate-limit aware backoff
- [x] Audit trail for all recovery decisions
- [x] Integration with task lifecycle manager

---

## Anti-Patterns

### ❌ Retrying Permanent Errors

**Problem:** Continuously retrying errors that will never succeed

**Example:**
```javascript
// WRONG - retrying 404 (permanent error)
for (let i = 0; i < 10; i++) {
  try {
    await fetchResource('/nonexistent');
    break;
  } catch (err) {
    if (err.status === 404) {
      await sleep(1000);  // Useless retry
    }
  }
}

// CORRECT - detect permanent error and escalate
const plan = await errorRecoveryPlanner.planRecovery(taskId, error, 'lex');
if (plan.action === 'escalate') {
  await taskLifecycle.escalateTask(taskId, plan.escalation_policy.escalation_reason);
}
```

### ❌ No Backoff Strategy

**Problem:** Retrying immediately without delay (retry storm)

**Example:**
```javascript
// WRONG - no backoff
while (attempts < 10) {
  try {
    await executeTask();
    break;
  } catch (err) {
    attempts++;
  }
}

// CORRECT - use recovery planner with backoff
const plan = await errorRecoveryPlanner.planRecovery(taskId, error, 'lex');
await sleep(plan.recovery_strategy.backoff_ms);
await executeTask();
```

### ❌ Logging Sensitive Error Data

**Problem:** Leaking credentials, tokens, or PII in error logs

**Example:**
```javascript
// WRONG - logs entire error (may contain secrets)
console.error('Task failed:', error);

// CORRECT - sanitize before logging
const plan = await errorRecoveryPlanner.planRecovery(taskId, error, 'lex');
console.error('Task failed:', plan.error_context);  // Sanitized
```

### ❌ Ignoring Retry-After Headers

**Problem:** Not respecting rate limit signals from APIs

**Example:**
```javascript
// WRONG - ignores Retry-After header
if (error.status === 429) {
  await sleep(1000);  // Fixed delay
  await retry();
}

// CORRECT - use rate-limit aware backoff
const plan = await errorRecoveryPlanner.planRecovery(taskId, error, 'lex');
const backoffMs = plan.recovery_strategy.backoff_ms;  // Computed from headers
await sleep(backoffMs);
```

### ❌ No Escalation Path

**Problem:** Tasks fail indefinitely without human intervention

**Example:**
```javascript
// WRONG - infinite retry loop
while (true) {
  try {
    await executeTask();
    break;
  } catch (err) {
    console.log('Retrying...');
  }
}

// CORRECT - escalate after max retries
const plan = await errorRecoveryPlanner.planRecovery(taskId, error, 'lex');
if (plan.action === 'escalate') {
  await taskLifecycle.transitionTask(taskId, 'in_progress', 'pending_approval', 'lex',
    plan.escalation_policy.escalation_reason);
}
```

### ❌ Not Tracking Retry History

**Problem:** No visibility into failure patterns

**Example:**
```javascript
// WRONG - no history tracking
try {
  await executeTask();
} catch (err) {
  await retry();  // No record of failure
}

// CORRECT - recovery planner tracks history
const plan = await errorRecoveryPlanner.planRecovery(taskId, error, 'lex');
// Plan includes attempt_number, classification, backoff_schedule
```

---

## Enforcement Behavior

When this skill is active:

### Agent Responsibilities

1. **Always classify errors** before deciding recovery action
2. **Use recovery planner** instead of ad-hoc retry logic
3. **Respect backoff schedules** (don't retry prematurely)
4. **Sanitize error data** before logging
5. **Escalate permanent errors** immediately
6. **Track retry history** in task metadata
7. **Honor max retry limits** (don't exceed safety threshold)

### User Expectations

- Transient errors retry automatically with intelligent backoff
- Permanent errors escalate immediately (no wasted retries)
- All recovery decisions logged for audit
- Recovery plans available for review
- Tasks don't fail silently (always escalate after max retries)
- No retry storms (backoff prevents excessive load)

### Error Handling

All recovery planning functions return structured results:

```typescript
interface RecoveryPlan {
  recovery_plan_id: string;
  task_id: string;
  created_at: string;
  status: 'active' | 'completed' | 'abandoned';

  error_context: {
    error_message: string;
    error_code: string;
    occurred_at: string;
    attempt_number: number;
  };

  classification: {
    error_type: 'transient' | 'permanent' | 'ambiguous';
    category: string;
    confidence: 'high' | 'medium' | 'low';
  };

  recovery_strategy: {
    action: 'retry' | 'escalate' | 'abandon';
    max_retries?: number;
    current_attempt?: number;
    backoff_strategy?: string;
    next_retry_at?: string;
    backoff_ms?: number;
  };

  recommended_actions: Array<{
    priority: number;
    action: string;
    description: string;
    automated: boolean;
  }>;
}
```

---

## Integration with Task Lifecycle

This skill extends `task_lifecycle_manager` with intelligent recovery:

- **§4.6 Error Recovery**: Implements structured recovery planning
- **§4.7 Retry Logic**: Provides backoff strategies and retry schedules
- **§4.8 Escalation Policies**: Defines when and how to escalate failures

All recovery plans are stored in `Recovery_Plans/` and linked to task metadata.

---

## Usage Examples

See `references/patterns.md` for concrete code examples and workflow patterns.
