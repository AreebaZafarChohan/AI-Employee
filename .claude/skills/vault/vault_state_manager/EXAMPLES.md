# Vault State Manager - Concrete Examples

This document provides real-world examples using actual files from a Digital FTE vault.

---

## Example 1: Processing an Email from Gmail Watcher

### Scenario

Gmail watcher detects a new email with `#ai-action` label and writes it to the vault.

### Step 1: Watcher Writes Email to Vault

**File:** `vault/Needs_Action/emails/2024-01-15T10:30:00Z-abc123.json`

```json
{
  "created_at": "2024-01-15T10:30:00Z",
  "created_by": "watcher-gmail",
  "status": "needs_action",
  "priority": "high",
  "source": "email",
  "data": {
    "id": "abc123",
    "from": "client@example.com",
    "to": "you@example.com",
    "subject": "Urgent: Invoice for January",
    "body": "Hi, can you send me the invoice for January? Thanks!",
    "labels": ["#ai-action"],
    "received_at": "2024-01-15T10:25:00Z"
  }
}
```

### Step 2: Lex Lists Pending Work

```javascript
const files = await vaultManager.listFolderFiles('Needs_Action/emails');
console.log('Pending emails:', files.length);
// Output: Pending emails: 1

// files[0]:
// {
//   name: '2024-01-15T10:30:00Z-abc123.json',
//   path: 'Needs_Action/emails/2024-01-15T10:30:00Z-abc123.json',
//   size: 458,
//   modified: 2024-01-15T10:30:00.000Z,
//   created: 2024-01-15T10:30:00.000Z
// }
```

### Step 3: Lex Reads Email

```javascript
const { content, metadata } = await vaultManager.readVaultFile(
  'Needs_Action/emails/2024-01-15T10:30:00Z-abc123.json',
  'lex'
);

const email = JSON.parse(content);
console.log('Email subject:', email.data.subject);
// Output: Email subject: Urgent: Invoice for January
```

### Step 4: Lex Creates Plan

```javascript
const planData = {
  title: 'Send January invoice to client@example.com',
  goal: 'Retrieve January invoice from accounting system and email to client',
  priority: 'high',
  source: 'email',
  autonomy_required: 'silver',  // Requires approval
  steps: [
    { action: 'Query accounting system for January invoice', status: 'pending' },
    { action: 'Generate PDF invoice', status: 'pending' },
    { action: 'Draft email response', status: 'pending' },
    { action: 'Send email via MCP email agent', status: 'pending' }
  ],
  metadata: {
    source_file: 'Needs_Action/emails/2024-01-15T10:30:00Z-abc123.json',
    estimated_duration_minutes: 5,
    requires_human_review: true,
    dependencies: []
  }
};

const planId = `plan-${Date.now()}`;  // e.g., plan-1705320000000
const planPath = `Plans/${planId}.json`;

const plan = {
  plan_id: planId,
  created_at: new Date().toISOString(),
  created_by: 'lex',
  status: 'planned',
  ...planData
};

await vaultManager.writeVaultFile(
  planPath,
  JSON.stringify(plan, null, 2),
  'lex'
);

console.log('Plan created:', planPath);
// Output: Plan created: Plans/plan-1705320000000.json
```

### Step 5: Lex Moves Email to Plans (Mark as Claimed)

```javascript
await vaultManager.moveFile(
  'Needs_Action/emails',
  '2024-01-15T10:30:00Z-abc123.json',
  'Plans',
  'lex'
);

// Email now at: Plans/2024-01-15T10:30:00Z-abc123.json
```

### Step 6: Lex Moves Plan to In_Progress

```javascript
await vaultManager.moveFile(
  'Plans',
  `${planId}.json`,
  'In_Progress',
  'lex'
);

// Plan now at: In_Progress/plan-1705320000000.json
```

### Step 7: Lex Executes Steps

```javascript
const planPath = `In_Progress/${planId}.json`;
const { content } = await vaultManager.readVaultFile(planPath, 'lex');
const plan = JSON.parse(content);

for (let i = 0; i < plan.steps.length; i++) {
  // Mark step as in_progress
  plan.steps[i].status = 'in_progress';
  await vaultManager.writeVaultFile(
    planPath,
    JSON.stringify(plan, null, 2),
    'lex'
  );

  // Execute step (simulate work)
  console.log(`Executing: ${plan.steps[i].action}`);
  await simulateWork();  // Placeholder

  // Mark step as completed
  plan.steps[i].status = 'completed';
  plan.steps[i].completed_at = new Date().toISOString();
  await vaultManager.writeVaultFile(
    planPath,
    JSON.stringify(plan, null, 2),
    'lex'
  );
}

// Update plan status
plan.status = 'pending_approval';
await vaultManager.writeVaultFile(
  planPath,
  JSON.stringify(plan, null, 2),
  'lex'
);
```

### Step 8: Lex Moves to Pending_Approval

```javascript
await vaultManager.moveFile(
  'In_Progress',
  `${planId}.json`,
  'Pending_Approval',
  'lex'
);

console.log('Plan awaiting human approval');
// Output: Plan awaiting human approval
```

### Step 9: Human Reviews and Approves

**File:** `vault/Pending_Approval/plan-1705320000000.json`

Human reads the plan:

```bash
cat vault/Pending_Approval/plan-1705320000000.json
```

Human decides to approve:

```bash
mv vault/Pending_Approval/plan-1705320000000.json vault/Approved/
```

### Step 10: Orchestrator Claims and Executes

```javascript
// Orchestrator polls Approved/
const approvedFiles = await vaultManager.listFolderFiles('Approved');

if (approvedFiles.length > 0) {
  const file = approvedFiles[0];  // Process oldest first

  // Claim file by moving to In_Progress
  await vaultManager.moveFile(
    'Approved',
    file.name,
    'In_Progress',
    'orch'
  );

  // Read plan
  const { content } = await vaultManager.readVaultFile(
    `In_Progress/${file.name}`,
    'orch'
  );

  const plan = JSON.parse(content);

  // Execute via MCP
  let outcome = 'success';
  try {
    await executePlanViaMCP(plan);  // Send email via MCP email agent
  } catch (err) {
    outcome = 'failure';
  }

  // Update plan with completion data
  plan.completed_at = new Date().toISOString();
  plan.completed_by = 'orch';
  plan.outcome = outcome;
  plan.status = 'done';

  await vaultManager.writeVaultFile(
    `In_Progress/${file.name}`,
    JSON.stringify(plan, null, 2),
    'orch'
  );

  // Move to Done
  await vaultManager.moveFile(
    'In_Progress',
    file.name,
    'Done',
    'orch'
  );

  console.log(`Completed: ${file.name} (outcome: ${outcome})`);
}
```

---

## Example 2: Human Rejects a Plan

### Scenario

Human reviews plan and decides it's too risky.

### Step 1: Human Reviews Plan

```bash
cat vault/Pending_Approval/plan-1705320000001.json
```

**Content:**
```json
{
  "plan_id": "plan-1705320000001",
  "title": "Delete all spam emails older than 30 days",
  "goal": "Clean up inbox by deleting old spam",
  "priority": "low",
  "steps": [
    { "action": "Query Gmail for spam older than 30 days", "status": "completed" },
    { "action": "Delete all matching emails (approx 500)", "status": "pending" }
  ]
}
```

### Step 2: Human Rejects

```bash
# Move to Rejected
mv vault/Pending_Approval/plan-1705320000001.json vault/Rejected/

# Add rejection reason
cat > vault/Rejected/plan-1705320000001.rejection.md <<EOF
## Rejection Reason

Deleting 500 emails is too aggressive. Some spam folder emails may be legitimate (false positives).

**Recommendation:** Modify plan to:
1. Review top 10 emails first
2. Only delete if confidence > 95%
3. Move to archive instead of delete

- Human reviewer, 2024-01-15
EOF
```

### Step 3: Lex Reads Rejection

```javascript
const rejectedFiles = await vaultManager.listFolderFiles('Rejected');

for (const file of rejectedFiles) {
  if (file.name.endsWith('.json')) {
    const rejectionFile = file.name.replace('.json', '.rejection.md');
    const rejectionPath = `Rejected/${rejectionFile}`;

    try {
      const { content } = await vaultManager.readVaultFile(rejectionPath, 'lex');
      console.log(`Rejection reason for ${file.name}:`);
      console.log(content);

      // Lex can learn from rejection and create revised plan
    } catch (err) {
      if (err instanceof vaultManager.FileNotFoundError) {
        console.log(`No rejection reason provided for ${file.name}`);
      }
    }
  }
}
```

---

## Example 3: Handling Concurrent Claims

### Scenario

Two lex instances try to claim same file.

### Setup

```bash
# File exists
ls vault/Needs_Action/emails/2024-01-15T11:00:00Z-xyz789.json
# Output: vault/Needs_Action/emails/2024-01-15T11:00:00Z-xyz789.json
```

### Lex Instance 1

```javascript
const filename = '2024-01-15T11:00:00Z-xyz789.json';

try {
  await vaultManager.moveFile(
    'Needs_Action/emails',
    filename,
    'Plans',
    'lex-1'
  );

  console.log('Lex-1: Successfully claimed', filename);
} catch (err) {
  if (err instanceof vaultManager.FileNotFoundError) {
    console.log('Lex-1: Already claimed by another agent');
  }
}
```

### Lex Instance 2 (runs concurrently)

```javascript
const filename = '2024-01-15T11:00:00Z-xyz789.json';

try {
  await vaultManager.moveFile(
    'Needs_Action/emails',
    filename,
    'Plans',
    'lex-2'
  );

  console.log('Lex-2: Successfully claimed', filename);
} catch (err) {
  if (err instanceof vaultManager.FileNotFoundError) {
    console.log('Lex-2: Already claimed by another agent');
  }
}
```

### Output

```
Lex-1: Successfully claimed 2024-01-15T11:00:00Z-xyz789.json
Lex-2: Already claimed by another agent
```

**What Happened:**
- Lex-1's `moveFile` executed first (atomic operation)
- Lex-2's `moveFile` failed because source file no longer exists
- FileNotFoundError is NOT an error; it means another agent claimed the file
- Both agents continue processing other files

---

## Example 4: Reading Logs for Audit

### Scenario

Human wants to audit recent agent actions.

### Log File: `vault/Logs/lex-decisions.json`

```json
{"timestamp":"2024-01-15T10:30:00Z","event":"plan_created","plan_id":"plan-1705320000000","source":"email"}
{"timestamp":"2024-01-15T10:30:05Z","event":"file_moved","src":"Needs_Action/emails/2024-01-15T10:30:00Z-abc123.json","dst":"Plans/2024-01-15T10:30:00Z-abc123.json","agent":"lex"}
{"timestamp":"2024-01-15T10:30:10Z","event":"file_moved","src":"Plans/plan-1705320000000.json","dst":"In_Progress/plan-1705320000000.json","agent":"lex"}
{"timestamp":"2024-01-15T10:35:00Z","event":"plan_completed","plan_id":"plan-1705320000000","status":"pending_approval"}
{"timestamp":"2024-01-15T10:35:05Z","event":"file_moved","src":"In_Progress/plan-1705320000000.json","dst":"Pending_Approval/plan-1705320000000.json","agent":"lex"}
```

### Reading Logs

```javascript
async function auditRecentActions(hours = 24) {
  const cutoff = Date.now() - (hours * 60 * 60 * 1000);

  const { content } = await vaultManager.readVaultFile(
    'Logs/lex-decisions.json',
    'human'
  );

  const events = content
    .split('\n')
    .filter(line => line.trim())
    .map(line => JSON.parse(line))
    .filter(event => new Date(event.timestamp).getTime() > cutoff);

  console.log(`Found ${events.length} events in last ${hours} hours:`);

  events.forEach(event => {
    console.log(`[${event.timestamp}] ${event.event}: ${JSON.stringify(event)}`);
  });

  return events;
}

// Usage
await auditRecentActions(24);
```

**Output:**
```
Found 5 events in last 24 hours:
[2024-01-15T10:30:00Z] plan_created: {"timestamp":"2024-01-15T10:30:00Z","event":"plan_created","plan_id":"plan-1705320000000","source":"email"}
[2024-01-15T10:30:05Z] file_moved: {"timestamp":"2024-01-15T10:30:05Z","event":"file_moved","src":"Needs_Action/emails/2024-01-15T10:30:00Z-abc123.json","dst":"Plans/2024-01-15T10:30:00Z-abc123.json","agent":"lex"}
...
```

---

## Example 5: Archiving Old Plans

### Scenario

Human wants to clean up vault by archiving old completed plans.

### Script

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
        console.error(`Failed to archive ${file.name}:`, err.message);
      }
    }
  }

  console.log(`Archived ${archived} old plans`);
}

// Usage
await archiveOldPlans(30);
```

**Output:**
```
Archived: plan-1704326400000.json
Archived: plan-1704412800000.json
Archived: plan-1704499200000.json
Archived 3 old plans
```

---

## Example 6: Monitoring Dashboard

### File: `vault/Dashboard.md`

```markdown
# Digital FTE Dashboard

**Last Updated:** 2024-01-15T12:00:00Z

---

## Status Overview

| Folder | Count | Action Required |
|--------|-------|-----------------|
| Needs_Action | 2 | None |
| Plans | 1 | None |
| In_Progress | 0 | Monitor |
| Pending_Approval | 3 | **Review & Approve** |
| Approved | 0 | Orchestrator Processing |
| Done | 15 | None |
| Rejected | 1 | None |

---

## Recent Activity

- **2024-01-15 10:30** - Created plan to send January invoice
- **2024-01-15 10:35** - Plan moved to Pending_Approval
- **2024-01-15 11:00** - Human approved plan
- **2024-01-15 11:05** - Orchestrator completed plan (sent invoice)

---

## Autonomy Tier

**Current Tier:** Bronze

All actions require approval before execution.

---

## Alerts

⚠️ 3 plans awaiting approval in Pending_Approval/

---

## Notes

- Need to review spam deletion plan (currently rejected)
- Consider increasing autonomy tier to Silver after testing
```

### Updating Dashboard

```javascript
async function updateDashboard() {
  const counts = {};

  for (const folder of ['Needs_Action', 'Plans', 'In_Progress', 'Pending_Approval', 'Approved', 'Done', 'Rejected']) {
    const files = await vaultManager.listFolderFiles(folder);
    counts[folder] = files.length;
  }

  const dashboard = `
# Digital FTE Dashboard

**Last Updated:** ${new Date().toISOString()}

---

## Status Overview

| Folder | Count | Action Required |
|--------|-------|-----------------|
| Needs_Action | ${counts.Needs_Action} | None |
| Plans | ${counts.Plans} | None |
| In_Progress | ${counts.In_Progress} | Monitor |
| Pending_Approval | ${counts.Pending_Approval} | **Review & Approve** |
| Approved | ${counts.Approved} | Orchestrator Processing |
| Done | ${counts.Done} | None |
| Rejected | ${counts.Rejected} | None |

---

[Rest of dashboard content...]
  `.trim();

  // Dashboard is human-maintained; agents should not overwrite
  // Instead, generate a report file
  await vaultManager.writeVaultFile(
    'Updates/dashboard-report.md',
    dashboard,
    'lex'
  );

  console.log('Dashboard report generated: Updates/dashboard-report.md');
}
```

---

## Summary

These examples demonstrate:

✅ **Complete workflow** from email ingestion to execution
✅ **Multi-agent coordination** (concurrent claims handled safely)
✅ **Human-in-the-loop** approval process
✅ **Error handling** (rejections, conflicts)
✅ **Audit logging** for compliance
✅ **Maintenance tasks** (archiving, monitoring)

All operations follow the claim-by-move protocol and enforce agent permissions per AGENTS.md §3.
