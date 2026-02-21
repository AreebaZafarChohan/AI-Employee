# Design Patterns for Ralph Wiggum Loop Controller

## Pattern: Stop-Hook Priority Hierarchy

**Problem:** Multiple hooks may trigger simultaneously, need clear resolution order.

**Solution:** Evaluate hooks in fixed priority order: timeout → resource → failure → success → retry.

**Implementation:**
```javascript
const HOOK_PRIORITY = {
  'timeout': 1,
  'resource': 2,
  'failure': 3,
  'success': 4,
  'retry': 5
};

function evaluateHooks(hooks, loopContext) {
  const sortedHooks = hooks.sort((a, b) =>
    HOOK_PRIORITY[a.type] - HOOK_PRIORITY[b.type]
  );

  for (const hook of sortedHooks) {
    const result = evaluateSingleHook(hook, loopContext);
    if (result.triggered) {
      return { triggered: true, hook, action: getActionForHook(hook) };
    }
  }

  return { triggered: false };
}
```

**When to Use:** Always use prioritized evaluation to prevent ambiguous outcomes.

**Trade-offs:**
- ✅ Deterministic behavior
- ✅ Timeout protection always wins
- ❌ Requires careful hook priority design

---

## Pattern: Exponential Backoff with Jitter

**Problem:** Retry storms when multiple loops retry simultaneously.

**Solution:** Add random jitter to backoff delays.

**Implementation:**
```javascript
function calculateBackoffWithJitter(attempt, baseDelays, jitterPercent = 0.2) {
  const baseDelay = baseDelays[Math.min(attempt, baseDelays.length - 1)];
  const jitter = baseDelay * jitterPercent * Math.random();
  return baseDelay + jitter;
}

// Example: attempt 2 with base delay 4000ms
const delay = calculateBackoffWithJitter(2, [1000, 2000, 4000, 8000]);
// Returns: 4000-4800ms (random within 20% jitter)
```

**When to Use:** Any retry hook where multiple agents may fail simultaneously.

**Trade-offs:**
- ✅ Prevents retry thundering herd
- ✅ Smooths out retry spikes
- ❌ Adds complexity to backoff calculation

---

## Pattern: Checkpoint Recovery

**Problem:** Long-running loops lose progress on crash or restart.

**Solution:** Periodically save checkpoints with full loop state.

**Implementation:**
```javascript
async function createCheckpoint(loopId, iteration) {
  const loopTask = await readLoopTask(loopId);

  const checkpoint = {
    loop_id: loopId,
    iteration,
    state: loopTask.state,
    created_at: new Date().toISOString(),
    execution: loopTask.execution,
    metrics: loopTask.metrics,
    variables: loopTask.prompt.variables
  };

  const checkpointPath = `Loops/Checkpoints/${loopId}-checkpoint-${iteration}.json`;
  await fs.writeFile(checkpointPath, JSON.stringify(checkpoint, null, 2));

  // Keep only last 3 checkpoints
  await pruneOldCheckpoints(loopId, 3);
}

async function recoverFromCheckpoint(loopId) {
  const checkpoints = await listCheckpoints(loopId);
  if (checkpoints.length === 0) return null;

  const latestCheckpoint = checkpoints[checkpoints.length - 1];
  const checkpoint = await readCheckpoint(latestCheckpoint);

  // Restore loop state from checkpoint
  await updateLoopTask(loopId, {
    state: checkpoint.state,
    execution: checkpoint.execution,
    metrics: checkpoint.metrics,
    prompt: { ...loopTask.prompt, variables: checkpoint.variables }
  });

  return checkpoint;
}
```

**When to Use:** Loops with `max_duration_ms > 300000` (5+ minutes).

**Trade-offs:**
- ✅ No lost work on crash
- ✅ Fast recovery
- ❌ Extra disk I/O
- ❌ Checkpoint storage overhead

---

## Pattern: Circuit Breaker for Failing Loops

**Problem:** A broken task causes infinite retry loops, wasting resources.

**Solution:** Track failure rate and open circuit breaker after threshold.

**Implementation:**
```javascript
class LoopCircuitBreaker {
  constructor(failureThreshold = 5, resetTimeout = 60000) {
    this.failureThreshold = failureThreshold;
    this.resetTimeout = resetTimeout;
    this.failures = {};
  }

  recordFailure(loopId) {
    if (!this.failures[loopId]) {
      this.failures[loopId] = { count: 0, firstFailureAt: Date.now() };
    }

    this.failures[loopId].count++;

    if (this.failures[loopId].count >= this.failureThreshold) {
      this.openCircuit(loopId);
    }
  }

  openCircuit(loopId) {
    console.log(`Circuit breaker OPEN for loop ${loopId}`);
    this.failures[loopId].circuitOpen = true;
    this.failures[loopId].openedAt = Date.now();

    // Auto-reset after timeout
    setTimeout(() => this.resetCircuit(loopId), this.resetTimeout);
  }

  resetCircuit(loopId) {
    console.log(`Circuit breaker RESET for loop ${loopId}`);
    delete this.failures[loopId];
  }

  isCircuitOpen(loopId) {
    return this.failures[loopId]?.circuitOpen || false;
  }
}

// Usage
const circuitBreaker = new LoopCircuitBreaker(5, 60000);

async function checkStopHooks({ loop_id }) {
  if (circuitBreaker.isCircuitOpen(loop_id)) {
    return {
      should_continue: false,
      final_state: 'FAILED',
      reason: 'Circuit breaker open due to repeated failures'
    };
  }

  const result = await evaluateHooks(loopTask.mission.stop_hooks, loopTask);

  if (result.triggered && result.hook.type === 'failure') {
    circuitBreaker.recordFailure(loop_id);
  }

  return result;
}
```

**When to Use:** Production loops with retry hooks to prevent runaway failures.

**Trade-offs:**
- ✅ Protects system resources
- ✅ Prevents infinite failure loops
- ❌ May stop prematurely for flaky tasks
- ❌ Requires tuning thresholds

---

## Pattern: Prompt Variable Evolution

**Problem:** Loop needs to update prompt variables between iterations (e.g., increment counter, update cursor).

**Solution:** Support variable update callbacks in loop configuration.

**Implementation:**
```javascript
const loopConfig = {
  task_id: 'paginated-fetch',
  prompt_template: 'Fetch page {{page_number}} from API',
  prompt_variables: {
    page_number: 1
  },
  variable_updater: {
    after_iteration: async (variables, iteration) => {
      return {
        ...variables,
        page_number: variables.page_number + 1
      };
    }
  },
  stop_hooks: [
    {
      type: 'success',
      condition: 'custom',
      script: {
        path: '/vault/scripts/check_no_more_pages.sh',
        success_exit_code: 0
      }
    }
  ]
};

// Controller updates variables after each iteration
async function injectPrompt({ loop_id }) {
  const loopTask = await readLoopTask(loop_id);

  // Update variables if updater provided
  if (loopTask.variable_updater?.after_iteration) {
    const updatedVariables = await loopTask.variable_updater.after_iteration(
      loopTask.prompt.variables,
      loopTask.metrics.loop_iterations
    );

    loopTask.prompt.variables = updatedVariables;
    await saveLoopTask(loopTask);
  }

  const renderedPrompt = renderTemplate(
    loopTask.prompt.template,
    loopTask.prompt.variables
  );

  await writeSignalFile(/* ... */);
}
```

**When to Use:** Loops processing paginated data, batch jobs, or iterative refinement.

**Trade-offs:**
- ✅ Flexible variable updates
- ✅ No manual state management
- ❌ Adds complexity to loop config
- ❌ Variable updater must be serializable

---

## Pattern: Multi-Agent Loop Coordination

**Problem:** Multiple agents want to run loops, need to prevent conflicts.

**Solution:** Integrate with agent_claim_coordinator to claim loop execution.

**Implementation:**
```javascript
const { claimTask } = require('./agent_claim_coordinator');
const { startLoop } = require('./ralph_wiggum_loop_controller');

async function startLoopWithClaim(loopConfig, agentId) {
  // First, claim the loop as a task
  const claimed = await claimTask({
    task_id: loopConfig.task_id,
    agent_id: agentId
  });

  if (!claimed) {
    throw new Error(`Failed to claim loop for task ${loopConfig.task_id}`);
  }

  try {
    const { loop_id } = await startLoop(loopConfig);

    // Update loop metadata with claim info
    await updateLoopTask(loop_id, {
      metadata: {
        claimed_by: agentId,
        claimed_at: new Date().toISOString()
      }
    });

    return { loop_id, claimed: true };
  } catch (error) {
    // Release claim on failure
    await releaseTask({ task_id: loopConfig.task_id, agent_id: agentId });
    throw error;
  }
}
```

**When to Use:** Multi-agent systems where loops may be triggered concurrently.

**Trade-offs:**
- ✅ Prevents duplicate loops
- ✅ Integrates with existing claim system
- ❌ Adds dependency on claim coordinator
- ❌ Requires claim release on completion

---

## Pattern: Nested Loop Hierarchy

**Problem:** Complex tasks require nested loops (outer loop delegates to inner loops).

**Solution:** Track parent-child loop relationships and propagate stop signals.

**Implementation:**
```javascript
async function startChildLoop(parentLoopId, childConfig) {
  const childLoopId = await startLoop({
    ...childConfig,
    metadata: {
      parent_loop_id: parentLoopId
    }
  });

  // Update parent with child reference
  await updateLoopTask(parentLoopId, {
    metadata: {
      child_loops: [childLoopId]
    }
  });

  return childLoopId;
}

async function stopLoop({ loop_id, reason }) {
  const loopTask = await readLoopTask(loop_id);

  // Stop all child loops first
  if (loopTask.metadata?.child_loops) {
    for (const childLoopId of loopTask.metadata.child_loops) {
      await stopLoop({ loop_id: childLoopId, reason: 'Parent loop stopped' });
    }
  }

  // Then stop parent
  await updateLoopTask(loop_id, {
    state: 'STOPPED',
    stopped_at: new Date().toISOString(),
    stop_reason: reason
  });
}
```

**When to Use:** Complex workflows with subtasks (e.g., process emails → delegate each email to child loop).

**Trade-offs:**
- ✅ Clean hierarchical structure
- ✅ Propagates stop signals
- ❌ Complex state management
- ❌ Risk of orphaned child loops

---

## Pattern: Rate-Limited Prompt Injection

**Problem:** Rapid prompt injection overwhelms target agent.

**Solution:** Add rate limiting to prompt injection.

**Implementation:**
```javascript
class PromptInjectionRateLimiter {
  constructor(maxPerMinute = 10) {
    this.maxPerMinute = maxPerMinute;
    this.recentInjections = [];
  }

  canInject() {
    const oneMinuteAgo = Date.now() - 60000;
    this.recentInjections = this.recentInjections.filter(t => t > oneMinuteAgo);
    return this.recentInjections.length < this.maxPerMinute;
  }

  recordInjection() {
    this.recentInjections.push(Date.now());
  }

  async waitForSlot() {
    while (!this.canInject()) {
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }
}

const rateLimiter = new PromptInjectionRateLimiter(10);

async function injectPrompt({ loop_id }) {
  await rateLimiter.waitForSlot();

  // Proceed with injection
  const signalFile = await writeSignalFile(/* ... */);

  rateLimiter.recordInjection();

  return { injected: true };
}
```

**When to Use:** Environments with multiple concurrent loops.

**Trade-offs:**
- ✅ Prevents agent overload
- ✅ Fair scheduling across loops
- ❌ May delay urgent prompts
- ❌ Global state management needed

---

## Summary Table

| Pattern | Use Case | Complexity | Performance Impact |
|---------|----------|------------|-------------------|
| Stop-Hook Priority | All loops | Low | None |
| Exponential Backoff with Jitter | Retry hooks | Low | Minimal |
| Checkpoint Recovery | Long-running loops | Medium | Moderate (disk I/O) |
| Circuit Breaker | Production loops | Medium | Minimal |
| Variable Evolution | Paginated/batch tasks | Low | None |
| Multi-Agent Coordination | Multi-agent systems | Medium | Low (claim overhead) |
| Nested Loop Hierarchy | Complex workflows | High | Moderate (state management) |
| Rate-Limited Injection | High-concurrency systems | Low | Low (delays only) |

Choose patterns based on your specific requirements and system constraints. Combine patterns for comprehensive loop management.
