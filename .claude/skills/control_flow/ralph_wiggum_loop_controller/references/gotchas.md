# Gotchas and Edge Cases for Ralph Wiggum Loop Controller

## 1. Hook Evaluation Race Condition

**Problem:**
File-based hooks checked at same time as file is being written, causing false negatives.

```javascript
// Agent writes completion file
fs.writeFile('Completed/task-123.json', data);

// Loop checks immediately (before write completes!)
const exists = fs.existsSync('Completed/task-123.json'); // false!
```

**Mitigation:**
Add small delay after detecting file write events, or use atomic file operations:

```javascript
async function evaluateFileExistsHook(hook) {
  const exists = fs.existsSync(hook.value);

  if (!exists) return { triggered: false };

  // Wait 100ms and check again to ensure write completed
  await new Promise(resolve => setTimeout(resolve, 100));

  const stillExists = fs.existsSync(hook.value);
  return { triggered: stillExists };
}
```

---

## 2. Signal File Expiry

**Problem:**
Injected prompt signal expires before agent processes it.

```javascript
{
  "signal_type": "prompt_injection",
  "created_at": "2025-01-15T10:00:00.000Z",
  "expires_at": "2025-01-15T10:05:00.000Z"  // 5 minute expiry
}

// Agent checks at 10:05:01 → signal expired!
```

**Mitigation:**
Configure longer expiry times for slow agents, or re-inject on expiry:

```javascript
async function injectPromptWithExpiry({ loop_id, expiry_ms = 300000 }) {
  const signal = {
    signal_type: 'prompt_injection',
    created_at: new Date().toISOString(),
    expires_at: new Date(Date.now() + expiry_ms).toISOString(),
    prompt: renderedPrompt
  };

  await writeSignalFile(signal);

  // Schedule expiry check
  setTimeout(async () => {
    const processed = await checkSignalProcessed(signal);
    if (!processed) {
      console.log('Signal expired, re-injecting');
      await injectPromptWithExpiry({ loop_id, expiry_ms });
    }
  }, expiry_ms);
}
```

---

## 3. Custom Script Hook Timeout

**Problem:**
Custom script hangs, blocking hook evaluation indefinitely.

```javascript
{
  "type": "success",
  "condition": "custom",
  "script": {
    "path": "/vault/scripts/check_completion.sh",
    "timeout_ms": 5000  // But script takes 10+ seconds!
  }
}
```

**Mitigation:**
Always enforce strict timeouts with kill signals:

```javascript
async function executeCustomScriptHook(hook) {
  const { path, args, timeout_ms } = hook.script;

  return new Promise((resolve, reject) => {
    const child = spawn(path, args);

    let stdout = '';
    let stderr = '';

    child.stdout.on('data', data => { stdout += data; });
    child.stderr.on('data', data => { stderr += data; });

    const timeout = setTimeout(() => {
      child.kill('SIGKILL');
      reject(new Error(`Script timeout after ${timeout_ms}ms`));
    }, timeout_ms);

    child.on('exit', code => {
      clearTimeout(timeout);
      resolve({ exit_code: code, stdout, stderr });
    });
  });
}
```

---

## 4. Variable Injection Attacks

**Problem:**
Malicious variable values can inject commands into prompts.

```javascript
{
  "prompt_template": "Process file {{file_path}}",
  "prompt_variables": {
    "file_path": "'; rm -rf /; echo '"  // Command injection!
  }
}

// Rendered: "Process file '; rm -rf /; echo '"
```

**Mitigation:**
Sanitize all variables before rendering:

```javascript
function sanitizeVariable(value) {
  if (typeof value !== 'string') return value;

  // Escape shell metacharacters
  return value.replace(/[;&|`$()<>]/g, '\\$&');
}

function renderTemplate(template, variables) {
  const sanitized = Object.entries(variables).reduce((acc, [key, value]) => {
    acc[key] = sanitizeVariable(value);
    return acc;
  }, {});

  return template.replace(/\{\{(\w+)\}\}/g, (_, key) => sanitized[key] || '');
}
```

---

## 5. Loop State Corruption on Crash

**Problem:**
Process crash during loop state update leaves loop in inconsistent state.

```javascript
// Update started
await updateLoopTask(loop_id, { state: 'RUNNING' });

// CRASH HERE!

// Execution tracking never updated
await updateLoopTask(loop_id, { execution: { ... } });
```

**Mitigation:**
Use atomic write operations with temp files:

```javascript
async function updateLoopTask(loopId, updates) {
  const loopPath = `Loops/Active/${loopId}.json`;
  const tempPath = `${loopPath}.tmp`;

  const currentTask = await fs.readFile(loopPath, 'utf8').then(JSON.parse);
  const updatedTask = { ...currentTask, ...updates };

  // Write to temp file first
  await fs.writeFile(tempPath, JSON.stringify(updatedTask, null, 2));

  // Atomic rename
  await fs.rename(tempPath, loopPath);
}
```

---

## 6. Infinite Loop on Broken Hook

**Problem:**
Hook condition never evaluates to true, loop runs forever.

```javascript
{
  "type": "success",
  "condition": "file_exists",
  "value": "Completed/typo-task-123.json"  // Typo! Agent writes "task-123.json"
}

// Loop checks forever, file never matches
```

**Mitigation:**
Always include timeout hook as safety net:

```javascript
const loopConfig = {
  stop_hooks: [
    {
      type: 'success',
      condition: 'file_exists',
      value: 'Completed/task-123.json'
    },
    // ALWAYS include timeout!
    {
      type: 'timeout',
      condition: 'elapsed_time_ms',
      value: 600000,  // 10 minutes max
      operator: 'gte',
      description: 'Safety timeout to prevent infinite loop'
    }
  ]
};
```

---

## 7. Prompt Variable Staleness

**Problem:**
Loop uses stale variable values when conditions change.

```javascript
// Start loop with inbox path
const loopConfig = {
  prompt_variables: {
    inbox_path: '/vault/Needs_Action'
  }
};

// User moves inbox to new location
// Loop still uses old path!
```

**Mitigation:**
Support dynamic variable resolution:

```javascript
{
  "prompt_variables": {
    "inbox_path": {
      "type": "dynamic",
      "resolver": "read_config",
      "config_key": "inbox.path"
    }
  }
}

async function renderTemplate(template, variables) {
  const resolved = {};

  for (const [key, value] of Object.entries(variables)) {
    if (value?.type === 'dynamic') {
      resolved[key] = await resolveDynamicVariable(value);
    } else {
      resolved[key] = value;
    }
  }

  return template.replace(/\{\{(\w+)\}\}/g, (_, key) => resolved[key] || '');
}
```

---

## 8. Backoff Overflow

**Problem:**
Exponential backoff grows unbounded, causing extremely long delays.

```javascript
const backoff_ms = [1000, 2000, 4000, 8000, 16000, 32000, 64000, 128000];
// After 8 failures: 128 seconds = 2+ minutes!
```

**Mitigation:**
Cap maximum backoff delay:

```javascript
function calculateBackoff(attempt, backoffStrategy, maxDelay = 60000) {
  const baseDelay = backoffStrategy[Math.min(attempt, backoffStrategy.length - 1)];

  // Cap at maxDelay (default 60 seconds)
  return Math.min(baseDelay, maxDelay);
}
```

---

## 9. Zombie Loops After Agent Crash

**Problem:**
Agent crashes, loop continues running indefinitely.

```javascript
// Agent crashes
// Loop still in 'RUNNING' state, never cleaned up
```

**Mitigation:**
Implement heartbeat monitoring:

```javascript
async function checkZombieLoops() {
  const activeLoops = await listActiveLoops();

  for (const loopTask of activeLoops) {
    const lastHeartbeat = loopTask.execution.last_heartbeat_at;
    const staleThreshold = Date.now() - 60000; // 1 minute

    if (lastHeartbeat < staleThreshold) {
      console.log(`Detected zombie loop: ${loopTask.loop_id}`);

      await stopLoop({
        loop_id: loopTask.loop_id,
        reason: 'Agent heartbeat stopped, assuming crash',
        final_state: 'FAILED'
      });
    }
  }
}

// Run zombie checker every minute
setInterval(checkZombieLoops, 60000);
```

---

## 10. Resource Leak on Loop Spam

**Problem:**
Many failed loops create signal files that are never cleaned up.

```bash
$ ls Signals/Pending/lex/ | wc -l
5432  # Thousands of orphaned signals!
```

**Mitigation:**
Implement signal file garbage collection:

```javascript
async function cleanupOrphanedSignals() {
  const signalDir = 'Signals/Pending/lex/';
  const signals = await fs.readdir(signalDir);

  for (const signalFile of signals) {
    const signal = await fs.readFile(`${signalDir}/${signalFile}`, 'utf8').then(JSON.parse);

    // Delete expired signals
    if (new Date(signal.expires_at) < new Date()) {
      console.log(`Deleting expired signal: ${signalFile}`);
      await fs.unlink(`${signalDir}/${signalFile}`);
    }
  }
}

// Run cleanup hourly
setInterval(cleanupOrphanedSignals, 3600000);
```

---

## Summary Table

| Gotcha | Severity | Detection | Mitigation Complexity |
|--------|----------|-----------|----------------------|
| Hook Evaluation Race | Medium | Hard | Low |
| Signal Expiry | Medium | Easy | Medium |
| Script Timeout | High | Easy | Low |
| Variable Injection | Critical | Hard | Medium |
| State Corruption | High | Easy | Medium |
| Infinite Loop | Critical | Hard | Low (timeout) |
| Variable Staleness | Low | Medium | Medium |
| Backoff Overflow | Low | Easy | Low |
| Zombie Loops | High | Easy | Medium |
| Resource Leak | Medium | Easy | Low |

Always implement timeout hooks, atomic state updates, and garbage collection to avoid the most critical issues.
