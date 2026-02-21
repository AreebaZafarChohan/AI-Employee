# Vault State Manager Patterns

This document provides concrete code examples and workflow patterns for using the Vault State Manager skill.

## Table of Contents

1. [Basic Operations](#basic-operations)
2. [Lifecycle Workflows](#lifecycle-workflows)
3. [Multi-Agent Coordination](#multi-agent-coordination)
4. [Error Handling Patterns](#error-handling-patterns)
5. [Common Scenarios](#common-scenarios)

---

## Basic Operations

### Pattern 1: List Files in Folder

**Use Case:** Agent needs to see all pending work in `Needs_Action/`

```javascript
const vaultManager = require('./vault-state-manager');

async function checkPendingWork() {
  try {
    // List all files in Needs_Action folder
    const files = await vaultManager.listFolderFiles('Needs_Action');

    console.log(`Found ${files.length} items needing action:`);
    files.forEach(file => {
      console.log(`- ${file.name} (created: ${file.created})`);
    });

    // Filter for emails only
    const emails = await vaultManager.listFolderFiles('Needs_Action/emails', {
      extension: '.json'
    });

    return files;
  } catch (err) {
    console.error('Failed to list files:', err.message);
    throw err;
  }
}
```

**Expected Output:**
```
Found 3 items needing action:
- 2024-01-15T10:30:00Z-email-001.json (created: 2024-01-15T10:30:00.000Z)
- 2024-01-15T11:00:00Z-msg-whatsapp-001.json (created: 2024-01-15T11:00:00.000Z)
- 2024-01-15T11:15:00Z-file-invoice.json (created: 2024-01-15T11:15:00.000Z)
```

---

### Pattern 2: Read File with Metadata

**Use Case:** Agent needs to read file contents and metadata

```javascript
async function readTaskDetails(filename) {
  try {
    const { content, metadata } = await vaultManager.readVaultFile(
      `Needs_Action/${filename}`,
      'lex'  // Agent identity
    );

    // Parse JSON content
    const task = JSON.parse(content);

    console.log('Task Details:');
    console.log(`  Title: ${task.title}`);
    console.log(`  Priority: ${task.priority}`);
    console.log(`  Source: ${task.source}`);
    console.log('Metadata:');
    console.log(`  Size: ${metadata.size} bytes`);
    console.log(`  Modified: ${metadata.modified}`);

    return { task, metadata };
  } catch (err) {
    if (err instanceof vaultManager.FileNotFoundError) {
      console.log(`File not found: ${filename}`);
      return null;
    }
    throw err;
  }
}
```

---

### Pattern 3: Write File Atomically

**Use Case:** Agent creates a new plan file

```javascript
async function createPlan(planData, agentName) {
  const planId = `plan-${Date.now()}`;
  const filename = `${planId}.json`;
  const relativePath = `Plans/${filename}`;

  // Check for collisions first
  try {
    await vaultManager.readVaultFile(relativePath, agentName);
    // File exists! Try a different ID
    return createPlan(planData, agentName);  // Retry with new timestamp
  } catch (err) {
    if (!(err instanceof vaultManager.FileNotFoundError)) {
      throw err;  // Unexpected error
    }
    // File doesn't exist, safe to create
  }

  const plan = {
    plan_id: planId,
    created_at: new Date().toISOString(),
    created_by: agentName,
    status: 'planned',
    ...planData
  };

  const content = JSON.stringify(plan, null, 2);

  try {
    const result = await vaultManager.writeVaultFile(
      relativePath,
      content,
      agentName
    );

    console.log(`Plan created: ${result.path}`);
    return planId;
  } catch (err) {
    if (err instanceof vaultManager.PermissionError) {
      console.error(`${agentName} cannot write to Plans/`);
    }
    throw err;
  }
}
```

---

### Pattern 4: Move File (Claim Work)

**Use Case:** Agent claims a file from Needs_Action and moves to Plans

```javascript
async function claimWorkItem(filename, agentName) {
  try {
    const result = await vaultManager.moveFile(
      'Needs_Action',
      filename,
      'Plans',
      agentName
    );

    console.log(`Claimed ${filename} → ${result.newPath}`);
    return result.newPath;
  } catch (err) {
    if (err instanceof vaultManager.FileNotFoundError) {
      console.log(`File already claimed by another agent: ${filename}`);
      return null;
    }
    if (err instanceof vaultManager.ConflictError) {
      console.log(`Conflict: file already exists in Plans/`);
      return null;
    }
    if (err instanceof vaultManager.PermissionError) {
      console.error(`${agentName} cannot move from Needs_Action to Plans`);
    }
    throw err;
  }
}
```

---

## Lifecycle Workflows

### Workflow 1: Lex Processes Email → Plan → Execution

```javascript
async function processNewEmail(emailFilename) {
  const agentName = 'lex';

  // Step 1: Read email from Needs_Action
  const { content } = await vaultManager.readVaultFile(
    `Needs_Action/emails/${emailFilename}`,
    agentName
  );

  const email = JSON.parse(content);
  console.log(`Processing email: ${email.subject}`);

  // Step 2: Create plan
  const planData = {
    title: `Respond to: ${email.subject}`,
    goal: `Draft reply to email from ${email.from}`,
    priority: email.urgent ? 'high' : 'medium',
    source: 'email',
    autonomy_required: 'silver',  // Requires approval
    steps: [
      { action: 'Analyze email intent', status: 'pending' },
      { action: 'Draft response', status: 'pending' },
      { action: 'Send via MCP email agent', status: 'pending' }
    ]
  };

  const planId = await createPlan(planData, agentName);

  // Step 3: Move email to Plans (mark as claimed)
  await vaultManager.moveFile(
    'Needs_Action/emails',
    emailFilename,
    'Plans',
    agentName
  );

  // Step 4: Move plan to In_Progress
  await vaultManager.moveFile(
    'Plans',
    `${planId}.json`,
    'In_Progress',
    agentName
  );

  // Step 5: Execute plan (simulate work)
  await executeSteps(planId, agentName);

  // Step 6: Move to Pending_Approval
  await vaultManager.moveFile(
    'In_Progress',
    `${planId}.json`,
    'Pending_Approval',
    agentName
  );

  console.log(`Plan ${planId} awaiting human approval`);
}

async function executeSteps(planId, agentName) {
  const planPath = `In_Progress/${planId}.json`;
  const { content } = await vaultManager.readVaultFile(planPath, agentName);
  const plan = JSON.parse(content);

  for (let i = 0; i < plan.steps.length; i++) {
    plan.steps[i].status = 'in_progress';
    await vaultManager.writeVaultFile(
      planPath,
      JSON.stringify(plan, null, 2),
      agentName
    );

    // Simulate work
    await new Promise(resolve => setTimeout(resolve, 1000));

    plan.steps[i].status = 'completed';
    await vaultManager.writeVaultFile(
      planPath,
      JSON.stringify(plan, null, 2),
      agentName
    );
  }

  plan.status = 'pending_approval';
  await vaultManager.writeVaultFile(
    planPath,
    JSON.stringify(plan, null, 2),
    agentName
  );
}
```

---

### Workflow 2: Human Approval Process

```bash
# Human reviews file in Pending_Approval/
cat vault/Pending_Approval/plan-1705320000000.json

# Human approves by moving to Approved/
mv vault/Pending_Approval/plan-1705320000000.json vault/Approved/

# Or rejects by moving to Rejected/
mv vault/Pending_Approval/plan-1705320000000.json vault/Rejected/

# Optional: Add rejection reason
cat > vault/Rejected/plan-1705320000000.rejection.md <<EOF
## Rejection Reason

The proposed email response is too informal for a client communication.
Please revise with more professional tone.

- Human reviewer
EOF
```

---

### Workflow 3: Orchestrator Executes Approved Action

```javascript
async function orchestratorLoop() {
  const agentName = 'orch';

  while (true) {
    // Step 1: Check for approved actions
    const approvedFiles = await vaultManager.listFolderFiles('Approved');

    if (approvedFiles.length === 0) {
      await new Promise(resolve => setTimeout(resolve, 5000));  // Wait 5s
      continue;
    }

    const file = approvedFiles[0];  // Process oldest first

    // Step 2: Claim file by moving to In_Progress
    try {
      await vaultManager.moveFile(
        'Approved',
        file.name,
        'In_Progress',
        agentName
      );
    } catch (err) {
      if (err instanceof vaultManager.FileNotFoundError) {
        console.log(`File already claimed: ${file.name}`);
        continue;  // Another orchestrator claimed it
      }
      throw err;
    }

    // Step 3: Read plan and execute
    const { content } = await vaultManager.readVaultFile(
      `In_Progress/${file.name}`,
      agentName
    );

    const plan = JSON.parse(content);

    let outcome = 'success';
    try {
      await executePlanViaMCP(plan);
    } catch (err) {
      console.error(`Execution failed: ${err.message}`);
      outcome = 'failure';
    }

    // Step 4: Update plan with outcome
    plan.completed_at = new Date().toISOString();
    plan.completed_by = agentName;
    plan.outcome = outcome;
    plan.status = 'done';

    await vaultManager.writeVaultFile(
      `In_Progress/${file.name}`,
      JSON.stringify(plan, null, 2),
      agentName
    );

    // Step 5: Move to Done
    await vaultManager.moveFile(
      'In_Progress',
      file.name,
      'Done',
      agentName
    );

    console.log(`Completed: ${file.name} (outcome: ${outcome})`);
  }
}

async function executePlanViaMCP(plan) {
  // Call MCP Action Agents based on plan.steps
  console.log(`Executing plan: ${plan.title}`);
  // ... MCP integration code ...
}
```

---

## Multi-Agent Coordination

### Pattern 5: Preventing Concurrent Claims

**Use Case:** Multiple lex instances must not claim same file

```javascript
async function safeClaim(filename) {
  const agentName = 'lex';

  try {
    const result = await vaultManager.moveFile(
      'Needs_Action',
      filename,
      'Plans',
      agentName
    );

    console.log(`Successfully claimed: ${filename}`);
    return result;
  } catch (err) {
    if (err instanceof vaultManager.FileNotFoundError) {
      console.log(`File already claimed by another agent`);
      return null;  // Not an error, just concurrent access
    }

    if (err instanceof vaultManager.ConflictError) {
      console.log(`Plan ID collision detected, retrying with new ID`);
      // Regenerate plan with new timestamp
      return null;
    }

    throw err;  // Unexpected error, propagate
  }
}
```

---

### Pattern 6: Watcher Agent Writes

**Use Case:** Gmail watcher writes new email to vault

```python
import json
import os
from datetime import datetime
from vault_state_manager import VaultManager

def write_email_to_vault(email_data):
    vault = VaultManager(os.environ['VAULT_PATH'])
    agent_name = 'watcher-gmail'

    # Generate unique filename
    timestamp = datetime.utcnow().isoformat()
    email_id = email_data['id']
    filename = f"{timestamp}-{email_id}.json"
    relative_path = f"Needs_Action/emails/{filename}"

    # Format email data
    vault_entry = {
        'created_at': timestamp,
        'created_by': agent_name,
        'status': 'needs_action',
        'priority': 'medium',
        'source': 'email',
        'data': email_data
    }

    try:
        vault.write_file(relative_path, json.dumps(vault_entry, indent=2), agent_name)
        print(f"Email written to vault: {relative_path}")

        # Log to watcher log
        log_entry = {
            'timestamp': timestamp,
            'event': 'email_received',
            'email_id': email_id,
            'file': relative_path
        }
        vault.append_log('watcher-gmail.json', json.dumps(log_entry))

    except Exception as e:
        print(f"Failed to write email: {e}")
        raise
```

---

## Error Handling Patterns

### Pattern 7: Graceful Degradation

**Use Case:** Handle missing files without crashing

```javascript
async function processAllPending(agentName) {
  let processed = 0;
  let failed = 0;

  try {
    const files = await vaultManager.listFolderFiles('Needs_Action');

    for (const file of files) {
      try {
        await processFile(file.name, agentName);
        processed++;
      } catch (err) {
        if (err instanceof vaultManager.FileNotFoundError) {
          console.log(`File disappeared (claimed by another agent): ${file.name}`);
          // Not a failure, just concurrent access
        } else if (err instanceof vaultManager.PermissionError) {
          console.error(`Permission denied: ${file.name}`);
          failed++;
        } else {
          console.error(`Unexpected error processing ${file.name}:`, err);
          failed++;
        }
      }
    }

    console.log(`Processed: ${processed}, Failed: ${failed}`);
  } catch (err) {
    console.error('Failed to list files:', err);
    throw err;
  }
}
```

---

### Pattern 8: Retry with Exponential Backoff

**Use Case:** Handle transient filesystem errors

```javascript
async function retryOperation(fn, maxRetries = 3) {
  let retries = 0;

  while (retries < maxRetries) {
    try {
      return await fn();
    } catch (err) {
      retries++;

      if (err instanceof vaultManager.PermissionError) {
        throw err;  // Don't retry permission errors
      }

      if (err instanceof vaultManager.FileNotFoundError) {
        throw err;  // Don't retry missing files
      }

      if (retries >= maxRetries) {
        throw err;  // Max retries exceeded
      }

      const delay = Math.pow(2, retries) * 1000;  // Exponential backoff
      console.log(`Retry ${retries}/${maxRetries} after ${delay}ms`);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
}

// Usage
await retryOperation(async () => {
  return await vaultManager.moveFile('Plans', 'file.json', 'In_Progress', 'lex');
});
```

---

## Common Scenarios

### Scenario 1: Check for Existing Plans Before Creating

```javascript
async function ensureUniquePlanId(baseId, agentName) {
  let planId = baseId;
  let attempt = 0;

  while (attempt < 10) {  // Max 10 attempts
    const filename = `${planId}.json`;
    const relativePath = `Plans/${filename}`;

    try {
      // Try to read file
      await vaultManager.readVaultFile(relativePath, agentName);
      // File exists, increment ID
      attempt++;
      planId = `${baseId}-${attempt}`;
    } catch (err) {
      if (err instanceof vaultManager.FileNotFoundError) {
        // File doesn't exist, safe to use this ID
        return planId;
      }
      throw err;  // Unexpected error
    }
  }

  throw new Error(`Failed to generate unique plan ID after 10 attempts`);
}

// Usage
const baseId = `plan-${Date.now()}`;
const uniqueId = await ensureUniquePlanId(baseId, 'lex');
```

---

### Scenario 2: Read All Logs for Audit

```javascript
async function auditRecentActions(hours = 24) {
  const cutoff = Date.now() - (hours * 60 * 60 * 1000);

  const logFiles = [
    'watcher-gmail.json',
    'watcher-whats.json',
    'watcher-finance.json',
    'orchestrator-actions.json',
    'lex-decisions.json'
  ];

  const events = [];

  for (const logFile of logFiles) {
    try {
      const { content } = await vaultManager.readVaultFile(`Logs/${logFile}`, 'human');
      const lines = content.split('\n').filter(line => line.trim());

      for (const line of lines) {
        const event = JSON.parse(line);
        if (new Date(event.timestamp).getTime() > cutoff) {
          events.push(event);
        }
      }
    } catch (err) {
      if (err instanceof vaultManager.FileNotFoundError) {
        console.log(`Log file not found: ${logFile}`);
      } else {
        console.error(`Failed to read log: ${logFile}`, err);
      }
    }
  }

  // Sort by timestamp
  events.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

  console.log(`Found ${events.length} events in last ${hours} hours`);
  return events;
}
```

---

### Scenario 3: Clean Up Old Completed Plans

```javascript
async function archiveOldPlans(daysOld = 30) {
  const cutoff = Date.now() - (daysOld * 24 * 60 * 60 * 1000);

  const doneFiles = await vaultManager.listFolderFiles('Done');

  let archived = 0;

  for (const file of doneFiles) {
    if (file.created.getTime() < cutoff) {
      try {
        await vaultManager.moveFile('Done', file.name, 'Archive', 'human');
        archived++;
        console.log(`Archived: ${file.name}`);
      } catch (err) {
        console.error(`Failed to archive ${file.name}:`, err);
      }
    }
  }

  console.log(`Archived ${archived} old plans`);
}
```

---

## Best Practices Summary

1. **Always validate paths** before operations
2. **Check permissions** before writes/moves
3. **Use atomic operations** (write to temp, then rename)
4. **Handle conflicts gracefully** (file already claimed)
5. **Log all state changes** for audit trail
6. **Return structured errors** (not generic exceptions)
7. **Clean up temp files** on failure
8. **Retry transient errors** with backoff
9. **Never skip lifecycle stages** (enforce state machine)
10. **Use relative paths** in all APIs (not absolute)
