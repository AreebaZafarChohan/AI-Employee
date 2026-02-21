# Agent Delegation Manager - Usage Examples

This document provides practical examples for using the agent_delegation_manager skill in various scenarios.

## Example 1: Basic Task Delegation

**Scenario**: lex receives a new task and delegates planning to cex

```javascript
// Step 1: lex receives task in Needs_Action/
const taskId = "task-20250115-103000";
const task = await readTaskFile(`Needs_Action/${taskId}.json`);

// Step 2: Check if task can be delegated
if (task.sync_policy === "local_only") {
  console.log("Cannot delegate local-only task; handling locally");
  await handleTaskLocally(taskId);
  return;
}

// Step 3: Create delegation request signal
const delegationSignal = {
  signal_type: "delegation_request",
  task_id: taskId,
  from_agent: "lex",
  to_agent: "cex",
  created_at: new Date().toISOString(),
  timeout_at: new Date(Date.now() + 30000).toISOString(), // 30 seconds
  request: {
    action: "plan_task",
    task_path: `Needs_Action/${taskId}.json`,
    sync_policy: "sync",
    context: {
      user_request: task.description,
      constraints: task.constraints || []
    },
    task_summary: {
      title: task.title,
      description: task.description,
      priority: task.priority
    }
  },
  metadata: {
    priority: task.priority,
    autonomy_tier: task.autonomy_tier || "silver",
    delegation_depth: 1,
    delegation_chain: [{ agent: "lex", timestamp: new Date().toISOString() }]
  }
};

// Step 4: Write signal to SIGNALS_DIR_LOCAL
await writeFile(
  `${process.env.SIGNALS_DIR_LOCAL}/${taskId}.delegate.json`,
  JSON.stringify(delegationSignal, null, 2)
);

console.log(`Delegation request created for ${taskId}`);

// Step 5: Wait for response (with timeout)
const response = await waitForDelegationResponse(taskId, 30000);

if (response.status === "completed") {
  console.log(`Plan ready: ${response.plan_path}`);
  // Move task to In_Progress
  await moveFile(`Needs_Action/${taskId}.json`, `In_Progress/${taskId}.json`);
} else if (response.status === "failed") {
  console.error(`Delegation failed: ${response.errors.join(", ")}`);
  // Fallback to local planning
  await handleTaskLocally(taskId);
}
```

---

## Example 2: Cloud Agent Processing Delegation

**Scenario**: cex polls for delegation requests and creates plan

```javascript
// Step 1: cex polls SIGNALS_DIR_CLOUD
const signals = await fs.readdir(process.env.SIGNALS_DIR_CLOUD);
const delegationRequests = signals.filter(f => f.endsWith(".delegate.json"));

for (const signalFile of delegationRequests) {
  const signalPath = `${process.env.SIGNALS_DIR_CLOUD}/${signalFile}`;

  // Step 2: Attempt to claim signal (atomic)
  try {
    const claimPath = signalPath.replace(".delegate.json", ".claimed.json");
    await fs.rename(signalPath, claimPath);

    console.log(`Claimed signal: ${signalFile}`);

    // Step 3: Read and process delegation request
    const signal = JSON.parse(await fs.readFile(claimPath, "utf-8"));

    // Step 4: Read task file (retry if not synced yet)
    let task;
    for (let i = 0; i < 3; i++) {
      try {
        const taskPath = `${process.env.VAULT_PATH_CLOUD}/${signal.request.task_path}`;
        task = JSON.parse(await fs.readFile(taskPath, "utf-8"));
        break;
      } catch (err) {
        if (err.code === "ENOENT" && i < 2) {
          console.warn(`Task file not synced yet; retrying in ${2 ** i} seconds`);
          await sleep(2 ** i * 1000);
        } else {
          throw err;
        }
      }
    }

    // Step 5: Create plan using AI
    const plan = await createTaskPlan(task);

    // Step 6: Write plan to Plans/
    const planPath = `${process.env.VAULT_PATH_CLOUD}/Plans/${signal.task_id}.json`;
    await fs.writeFile(planPath, JSON.stringify(plan, null, 2));

    // Step 7: Create delegation response signal
    const responseSignal = {
      signal_type: "delegation_response",
      task_id: signal.task_id,
      from_agent: "cex",
      to_agent: "lex",
      created_at: new Date().toISOString(),
      in_response_to: signalPath,
      response: {
        status: "completed",
        plan_path: `Plans/${signal.task_id}.json`,
        sync_policy: "sync",
        outcome: "Plan created successfully",
        next_action: "Review plan and move to In_Progress"
      },
      errors: []
    };

    await fs.writeFile(
      `${process.env.SIGNALS_DIR_CLOUD}/${signal.task_id}.response.json`,
      JSON.stringify(responseSignal, null, 2)
    );

    // Step 8: Cleanup claimed signal
    await fs.unlink(claimPath);

    console.log(`Delegation completed for ${signal.task_id}`);

  } catch (err) {
    if (err.code === "ENOENT") {
      // Another cex instance claimed it first; skip
      continue;
    }
    // Unexpected error; log and continue
    console.error(`Error processing delegation: ${err.message}`);
  }
}
```

---

## Example 3: Approval Sync from Cloud

**Scenario**: Human approves task in cloud vault; lex syncs approval to local vault

```javascript
// Step 1: Human approves task in cloud vault
// (Manual: move file from Pending_Approval/ to Approved/ in cloud vault)

// Step 2: Cloud watcher creates approval sync signal
const taskId = "task-20250115-103000";
const approvalSignal = {
  signal_type: "approval_sync",
  task_id: taskId,
  from_agent: "human",
  to_agent: "lex",
  created_at: new Date().toISOString(),
  approval: {
    decision: "approved",
    reason: "Looks good; proceed with execution",
    approved_by: "alice",
    approved_at: new Date().toISOString(),
    task_path: `Approved/${taskId}.json`,
    sync_policy: "sync"
  },
  signature: {
    user: "alice",
    timestamp: new Date().toISOString(),
    hmac: computeHMAC(taskId + "approved" + "alice") // If HMAC enabled
  }
};

await fs.writeFile(
  `${process.env.SIGNALS_DIR_CLOUD}/${taskId}.approval.json`,
  JSON.stringify(approvalSignal, null, 2)
);

// Step 3: lex polls for approval signals (synced to local via Dropbox)
const approvalSignals = await fs.readdir(process.env.SIGNALS_DIR_LOCAL);
const approvals = approvalSignals.filter(f => f.endsWith(".approval.json"));

for (const approvalFile of approvals) {
  const signalPath = `${process.env.SIGNALS_DIR_LOCAL}/${approvalFile}`;
  const signal = JSON.parse(await fs.readFile(signalPath, "utf-8"));

  // Step 4: Validate approval signature
  if (process.env.ENABLE_APPROVAL_HMAC === "true") {
    const expectedHMAC = computeHMAC(
      signal.task_id + signal.approval.decision + signal.signature.user
    );
    if (signal.signature.hmac !== expectedHMAC) {
      console.error(`Invalid approval signature for ${signal.task_id}`);
      await fs.unlink(signalPath); // Delete invalid signal
      continue;
    }
  }

  // Step 5: Validate timestamp (not expired)
  const signatureAge = Date.now() - new Date(signal.signature.timestamp).getTime();
  const maxAge = parseInt(process.env.APPROVAL_MAX_AGE_MS || "3600000");
  if (signatureAge > maxAge) {
    console.error(`Approval signature expired for ${signal.task_id}`);
    await fs.unlink(signalPath);
    continue;
  }

  // Step 6: Apply approval to local vault
  const targetFolder = signal.approval.decision === "approved" ? "Approved" : "Rejected";
  const localTaskPath = `${process.env.VAULT_PATH_LOCAL}/Pending_Approval/${signal.task_id}.json`;
  const targetPath = `${process.env.VAULT_PATH_LOCAL}/${targetFolder}/${signal.task_id}.json`;

  try {
    // Read task and update metadata
    const task = JSON.parse(await fs.readFile(localTaskPath, "utf-8"));
    task.approval = signal.approval;
    task.status = signal.approval.decision === "approved" ? "approved" : "rejected";

    // Write updated task to target folder
    await fs.writeFile(targetPath, JSON.stringify(task, null, 2));

    // Delete from Pending_Approval
    await fs.unlink(localTaskPath);

    // Log approval event
    await appendToLog("approvals.log", {
      task_id: signal.task_id,
      decision: signal.approval.decision,
      approved_by: signal.signature.user,
      synced_at: new Date().toISOString()
    });

    console.log(`Approval synced: ${signal.task_id} → ${targetFolder}`);

  } catch (err) {
    console.error(`Error syncing approval for ${signal.task_id}: ${err.message}`);
  }

  // Step 7: Cleanup approval signal
  await fs.unlink(signalPath);
}
```

---

## Example 4: Info Request (Secret Reference)

**Scenario**: cex needs to reference a secret during planning; requests reference from lex

```javascript
// Step 1: cex needs secret reference
const taskId = "task-20250115-103000";
const infoRequest = {
  signal_type: "info_request",
  task_id: taskId,
  from_agent: "cex",
  to_agent: "lex",
  created_at: new Date().toISOString(),
  timeout_at: new Date(Date.now() + 10000).toISOString(), // 10 seconds
  request: {
    info_type: "secret_reference",
    query: "sendgrid_api_key",
    required_for: "Planning email notification service"
  }
};

await fs.writeFile(
  `${process.env.SIGNALS_DIR_CLOUD}/${taskId}.info_request.json`,
  JSON.stringify(infoRequest, null, 2)
);

// Step 2: lex receives info request (synced to local)
const infoRequests = await fs.readdir(process.env.SIGNALS_DIR_LOCAL);
const requests = infoRequests.filter(f => f.endsWith(".info_request.json"));

for (const requestFile of requests) {
  const signalPath = `${process.env.SIGNALS_DIR_LOCAL}/${requestFile}`;
  const signal = JSON.parse(await fs.readFile(signalPath, "utf-8"));

  let response;

  if (signal.request.info_type === "secret_reference") {
    // Step 3: lex provides reference (NOT the actual secret)
    const SECRET_MAP = {
      "sendgrid_api_key": "USE_SENDGRID_API_KEY_FROM_LOCAL_ENV",
      "database_password": "USE_DB_PASSWORD_FROM_LOCAL_ENV"
    };

    response = {
      status: "success",
      info_type: "secret_reference",
      data: {
        secret_name: signal.request.query,
        reference: SECRET_MAP[signal.request.query] || "SECRET_NOT_FOUND",
        instruction: "Reference this in your plan; lex will substitute at runtime"
      },
      sanitized: true,
      redacted_fields: ["secret_value"]
    };
  } else if (signal.request.info_type === "env_var") {
    // Step 4: lex provides safe environment variables
    const SAFE_VARS = ["NODE_ENV", "API_URL", "LOG_LEVEL"];

    if (SAFE_VARS.includes(signal.request.query)) {
      response = {
        status: "success",
        info_type: "env_var",
        data: {
          var_name: signal.request.query,
          var_value: process.env[signal.request.query] || null
        },
        sanitized: false
      };
    } else {
      response = {
        status: "error",
        info_type: "env_var",
        data: {},
        errors: ["Variable not in safe list"],
        sanitized: true
      };
    }
  }

  // Step 5: lex writes info response signal
  const responseSignal = {
    signal_type: "info_response",
    task_id: signal.task_id,
    from_agent: "lex",
    to_agent: "cex",
    created_at: new Date().toISOString(),
    in_response_to: signalPath,
    response: response,
    errors: []
  };

  await fs.writeFile(
    `${process.env.SIGNALS_DIR_LOCAL}/${signal.task_id}.info_response.json`,
    JSON.stringify(responseSignal, null, 2)
  );

  // Step 6: Cleanup info request
  await fs.unlink(signalPath);

  console.log(`Info response created for ${signal.task_id}`);
}

// Step 7: cex receives info response (synced from local)
const infoResponse = await waitForInfoResponse(taskId, 10000);

if (infoResponse.response.status === "success") {
  const secretRef = infoResponse.response.data.reference;
  console.log(`Use secret reference in plan: ${secretRef}`);

  // Include in plan
  const plan = {
    task_id: taskId,
    steps: [
      {
        action: "Configure SendGrid",
        command: `export SENDGRID_API_KEY="${secretRef}"`
      }
    ]
  };
}
```

---

## Example 5: Handling Delegation Timeout

**Scenario**: cex doesn't respond within timeout; lex handles locally

```javascript
// Step 1: lex creates delegation request with timeout
const taskId = "task-20250115-103000";
const delegationSignal = {
  signal_type: "delegation_request",
  task_id: taskId,
  created_at: new Date().toISOString(),
  timeout_at: new Date(Date.now() + 30000).toISOString(), // 30 seconds
  // ... rest of signal
};

await fs.writeFile(
  `${process.env.SIGNALS_DIR_LOCAL}/${taskId}.delegate.json`,
  JSON.stringify(delegationSignal, null, 2)
);

// Step 2: lex waits for response
try {
  const response = await waitForDelegationResponse(taskId, 30000);

  if (response.status === "completed") {
    console.log(`Plan ready: ${response.plan_path}`);
  }

} catch (err) {
  if (err.code === "TIMEOUT") {
    // Step 3: Timeout occurred; delete delegation signal
    await fs.unlink(`${process.env.SIGNALS_DIR_LOCAL}/${taskId}.delegate.json`);

    // Step 4: Log timeout event
    await appendToLog("delegation_timeouts.log", {
      task_id: taskId,
      expired_at: new Date().toISOString(),
      reason: "cex did not respond within 30 seconds"
    });

    // Step 5: Fallback to local planning
    console.warn(`Delegation timeout for ${taskId}; handling locally`);
    const plan = await createPlanLocally(taskId);

    await fs.writeFile(
      `${process.env.VAULT_PATH_LOCAL}/Plans/${taskId}.json`,
      JSON.stringify(plan, null, 2)
    );

    console.log(`Local plan created: Plans/${taskId}.json`);
  }
}
```

---

## Example 6: Detecting and Marking Secrets

**Scenario**: lex detects secrets in task content and marks as local_only

```javascript
// Step 1: Task arrives in Needs_Action/
const taskId = "task-20250115-103000";
const task = await readTaskFile(`Needs_Action/${taskId}.json`);

// Step 2: Detect secrets in content
function detectSecrets(content) {
  const contentStr = JSON.stringify(content);

  const SECRET_PATTERNS = [
    /API[_-]?KEY/i,
    /SECRET[_-]?TOKEN/i,
    /PASSWORD/i,
    /CREDENTIALS/i,
    /\b[A-Za-z0-9]{32,}\b/ // Long random strings
  ];

  for (const pattern of SECRET_PATTERNS) {
    if (pattern.test(contentStr)) {
      return {
        hasSecrets: true,
        matchedPattern: pattern.toString()
      };
    }
  }

  return { hasSecrets: false };
}

const detection = detectSecrets(task);

// Step 3: Mark as local_only if secrets detected
if (detection.hasSecrets) {
  task.sync_policy = "local_only";
  task.secret_detection = {
    detected: true,
    pattern: detection.matchedPattern,
    marked_at: new Date().toISOString()
  };

  await writeTaskFile(`Needs_Action/${taskId}.json`, task);

  console.log(`Task ${taskId} marked as local_only due to secret detection`);

  // Step 4: Handle locally (cannot delegate)
  await handleTaskLocally(taskId);

} else {
  // Step 5: Safe to delegate to cloud
  await delegateTaskToCloud(taskId);
}
```

---

## Example 7: Cleanup Job (Reclaim Orphaned Signals)

**Scenario**: Periodic cleanup job reclaims stale signals

```javascript
// Run this as a cron job or setInterval

async function cleanupOrphanedSignals() {
  const signalDir = process.env.SIGNALS_DIR_LOCAL;
  const claimedSignals = (await fs.readdir(signalDir)).filter(f => f.endsWith(".claimed.json"));

  for (const signalFile of claimedSignals) {
    const signalPath = `${signalDir}/${signalFile}`;
    const signal = JSON.parse(await fs.readFile(signalPath, "utf-8"));

    // Check heartbeat
    const lastHeartbeat = signal.last_heartbeat || signal.claimed_at;
    const staleness = Date.now() - lastHeartbeat;
    const threshold = parseInt(process.env.SIGNAL_STALE_THRESHOLD_MS || "300000"); // 5 minutes

    if (staleness > threshold) {
      console.warn(`Reclaiming stale signal: ${signal.task_id} (staleness: ${staleness}ms)`);

      // Release claim by renaming back to unclaimed
      const unclaimedPath = signalPath.replace(".claimed.json", ".json");
      await fs.rename(signalPath, unclaimedPath);

      // Log orphan event
      await appendToLog("orphaned_signals.log", {
        task_id: signal.task_id,
        reclaimed_at: new Date().toISOString(),
        staleness_ms: staleness
      });
    }
  }

  // Also cleanup expired signals
  const allSignals = (await fs.readdir(signalDir)).filter(f => f.endsWith(".json"));

  for (const signalFile of allSignals) {
    const signalPath = `${signalDir}/${signalFile}`;
    const signal = JSON.parse(await fs.readFile(signalPath, "utf-8"));

    if (signal.timeout_at) {
      const timeoutAt = new Date(signal.timeout_at);
      const now = new Date();

      if (now > timeoutAt) {
        console.warn(`Deleting expired signal: ${signal.task_id}`);
        await fs.unlink(signalPath);

        await appendToLog("delegation_timeouts.log", {
          task_id: signal.task_id,
          expired_at: now.toISOString(),
          reason: "timeout"
        });
      }
    }
  }
}

// Run every 60 seconds
setInterval(cleanupOrphanedSignals, 60000);
```

---

## Example 8: Sync Conflict Resolution

**Scenario**: Task modified in both local and cloud vaults; resolve conflict

```javascript
// Step 1: Detect sync conflict (version mismatch)
const taskId = "task-20250115-103000";
const localTask = await readTaskFile(`${process.env.VAULT_PATH_LOCAL}/In_Progress/${taskId}.json`);
const cloudTask = await readTaskFile(`${process.env.VAULT_PATH_CLOUD}/In_Progress/${taskId}.json`);

function detectSyncConflict(localTask, cloudTask) {
  if (!localTask || !cloudTask) return { conflict: false };

  const localVersion = localTask.version?.local || 0;
  const cloudVersion = cloudTask.version?.cloud || 0;
  const localCloudVersion = localTask.version?.cloud || 0;
  const cloudLocalVersion = cloudTask.version?.local || 0;

  if (localVersion > cloudLocalVersion && cloudVersion > localCloudVersion) {
    return {
      conflict: true,
      reason: "Both sides modified since last sync"
    };
  }

  return { conflict: false };
}

const conflict = detectSyncConflict(localTask, cloudTask);

// Step 2: Resolve conflict based on policy
if (conflict.conflict) {
  const policy = process.env.SYNC_CONFLICT_POLICY || "human_resolve";

  switch (policy) {
    case "local_wins":
      await fs.writeFile(
        `${process.env.VAULT_PATH_CLOUD}/In_Progress/${taskId}.json`,
        JSON.stringify(localTask, null, 2)
      );
      console.log(`Conflict resolved: local wins (${taskId})`);
      break;

    case "cloud_wins":
      await fs.writeFile(
        `${process.env.VAULT_PATH_LOCAL}/In_Progress/${taskId}.json`,
        JSON.stringify(cloudTask, null, 2)
      );
      console.log(`Conflict resolved: cloud wins (${taskId})`);
      break;

    case "last_write_wins":
      const localModified = new Date(localTask.modified_at);
      const cloudModified = new Date(cloudTask.modified_at);

      if (localModified > cloudModified) {
        await fs.writeFile(
          `${process.env.VAULT_PATH_CLOUD}/In_Progress/${taskId}.json`,
          JSON.stringify(localTask, null, 2)
        );
        console.log(`Conflict resolved: local (last write wins)`);
      } else {
        await fs.writeFile(
          `${process.env.VAULT_PATH_LOCAL}/In_Progress/${taskId}.json`,
          JSON.stringify(cloudTask, null, 2)
        );
        console.log(`Conflict resolved: cloud (last write wins)`);
      }
      break;

    case "human_resolve":
      // Create conflict marker files
      await fs.writeFile(
        `${process.env.VAULT_PATH_LOCAL}/In_Progress/${taskId}.conflict-local.json`,
        JSON.stringify(localTask, null, 2)
      );
      await fs.writeFile(
        `${process.env.VAULT_PATH_LOCAL}/In_Progress/${taskId}.conflict-cloud.json`,
        JSON.stringify(cloudTask, null, 2)
      );

      console.warn(`Conflict detected for ${taskId}; human resolution required`);
      await notifyHuman(`Sync conflict: ${taskId}. Please review and resolve manually.`);
      break;
  }

  // Log conflict event
  await appendToLog("sync_conflicts.log", {
    task_id: taskId,
    resolved_at: new Date().toISOString(),
    policy: policy,
    local_version: localTask.version,
    cloud_version: cloudTask.version
  });
}
```

---

## Helper Functions

### waitForDelegationResponse

```javascript
async function waitForDelegationResponse(taskId, timeoutMs) {
  const startTime = Date.now();
  const responsePath = `${process.env.SIGNALS_DIR_LOCAL}/${taskId}.response.json`;

  while (Date.now() - startTime < timeoutMs) {
    try {
      const response = JSON.parse(await fs.readFile(responsePath, "utf-8"));
      await fs.unlink(responsePath); // Cleanup
      return response;
    } catch (err) {
      if (err.code === "ENOENT") {
        // Not found yet; wait and retry
        await sleep(1000);
      } else {
        throw err;
      }
    }
  }

  throw { code: "TIMEOUT", message: `No response received for ${taskId} within ${timeoutMs}ms` };
}
```

### computeHMAC

```javascript
const crypto = require("crypto");

function computeHMAC(data) {
  const secret = process.env.APPROVAL_HMAC_SECRET || "default-secret";
  return crypto.createHmac("sha256", secret).update(data).digest("hex");
}
```

### appendToLog

```javascript
async function appendToLog(logFile, entry) {
  const logPath = `${process.env.VAULT_PATH_LOCAL}/Logs/${logFile}`;
  const logLine = JSON.stringify(entry) + "\n";
  await fs.appendFile(logPath, logLine);
}
```

---

These examples demonstrate the core workflows and patterns for using the agent_delegation_manager skill. Adapt them to your specific use case and integration requirements.
