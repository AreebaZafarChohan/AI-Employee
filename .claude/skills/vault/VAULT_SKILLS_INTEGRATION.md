# Vault Skills Integration Guide

This document explains how the four vault skills work together to implement the complete Digital FTE workflow.

---

## Overview

The Digital FTE workflow is powered by four complementary skills:

1. **vault_state_manager** - Low-level file operations (read, write, move)
2. **task_lifecycle_manager** - Task state transitions and claim-by-move protocol
3. **needs_action_triage** - Intelligent classification and prioritization
4. **plan_md_generator** - Planning and decomposition into executable steps

---

## Skill Responsibilities

### 1. vault_state_manager (Foundation Layer)

**Purpose:** Safe, atomic file operations on the Obsidian vault

**Responsibilities:**
- Read files from vault folders
- Write files atomically (temp file → rename)
- Move files between folders (claim-by-move)
- List folder contents
- Validate paths (prevent traversal)
- Enforce agent permissions

**Example:**
```javascript
// Read file
const { content } = await vaultManager.readVaultFile('Needs_Action/email-123.md', 'lex');

// Move file (atomic)
await vaultManager.moveFile('Needs_Action', 'email-123.md', 'Plans', 'lex');

// List pending work
const files = await vaultManager.listFolderFiles('Needs_Action');
```

**Used By:** All other vault skills

---

### 2. task_lifecycle_manager (Workflow Layer)

**Purpose:** Manage task state transitions and enforce workflow rules

**Responsibilities:**
- Claim tasks (Needs_Action → Plans)
- Start work (Plans → In_Progress)
- Request approval (In_Progress → Pending_Approval)
- Complete tasks (Approved → Done)
- Handle conflicts (already claimed, stale tasks)
- Retry failed tasks (exponential backoff)

**Example:**
```javascript
// Claim task
const claim = await taskLifecycle.claimTask('email-123.md', 'lex');
// Moves file: Needs_Action/email-123.md → Plans/email-123.md

// Start work
await taskLifecycle.startWork(claim.taskId, 'lex');
// Moves file: Plans/email-123.md → In_Progress/email-123.md

// Request approval
await taskLifecycle.requestApproval(claim.taskId, 'lex');
// Moves file: In_Progress/email-123.md → Pending_Approval/email-123.md
```

**Depends On:** vault_state_manager

**Used By:** Agents (lex, orch) for workflow orchestration

---

### 3. needs_action_triage (Intelligence Layer)

**Purpose:** Analyze and prioritize incoming work

**Responsibilities:**
- Classify by category (email, whatsapp, finance, file_drop, general)
- Assign priority scores (1-10)
- Extract metadata (sender, subject, deadline, amounts)
- Detect approval requirements
- Generate next-step recommendations
- Produce summary reports

**Example:**
```javascript
// Scan inbox
const triage = await triageNeedsAction({ minPriorityScore: 5 });

// Results sorted by priority
triage.items[0];
// {
//   file_name: 'finance-invoice.md',
//   category: 'finance',
//   priority_score: 9,
//   metadata: { financial_amount: 5432.00, deadline: '...' },
//   suggested_action: 'approve',
//   requires_human_approval: true
// }
```

**Depends On:** vault_state_manager (read Needs_Action/)

**Used By:** Agents (lex) for prioritizing work

---

### 4. plan_md_generator (Planning Layer)

**Purpose:** Transform high-level tasks into executable plans

**Responsibilities:**
- Decompose tasks into 3-20 steps
- Identify approval gates (finance, destructive, high-risk)
- Estimate effort and duration
- Generate rollback plans for risky operations
- Track dependencies between steps
- Provide acceptance criteria

**Example:**
```javascript
// Generate plan from triage data
const plan = await generatePlan({
  triageData: triage.items[0],
  agentName: 'lex',
  includeRollback: true
});

// Plan structure
plan.plan_content;
// {
//   goal: 'Process overdue invoice payment',
//   steps: [
//     { id: 'step-1', action: 'Validate invoice details', ... },
//     { id: 'step-4', action: 'Authorize payment', requires_approval: true },
//     { id: 'step-5', action: 'Process payment', requires_approval: true }
//   ],
//   approval_gates: [ { step_id: 'step-4', reason: 'Financial operation' } ]
// }
```

**Depends On:** vault_state_manager (write Plans/), needs_action_triage (input metadata)

**Used By:** Agents (lex) for creating execution plans

---

## Complete Workflow

### Phase 1: Inbox Processing

```
Watcher Agent → Needs_Action/
                      ↓
          ┌───────────────────────┐
          │ needs_action_triage   │
          └───────────────────────┘
                      ↓
          Prioritized task list
          (sorted by priority_score)
```

**Code:**
```javascript
// Scan inbox
const triage = await triageNeedsAction({
  minPriorityScore: 5,
  autoClassify: true
});

console.log(`Found ${triage.items.length} medium+ priority items`);
console.log(`Top priority: ${triage.items[0].metadata.subject} (${triage.items[0].priority_score}/10)`);
```

---

### Phase 2: Task Claiming

```
Needs_Action/ → task_lifecycle_manager.claimTask()
                      ↓
                vault_state_manager.moveFile()
                      ↓
                  Plans/
```

**Code:**
```javascript
// Claim highest-priority task
const topItem = triage.items[0];

const claim = await taskLifecycle.claimTask(topItem.file_name, 'lex');

if (claim.success) {
  console.log(`Claimed: ${claim.taskId}`);
} else {
  console.log(`Already claimed by another agent`);
}
```

**State Change:**
- File moved: `Needs_Action/email-123.md` → `Plans/email-123.md`
- Metadata updated: `status: 'needs_action'` → `status: 'planned'`
- Ownership set: `claimed_by: 'lex'`, `claimed_at: '...'`

---

### Phase 3: Plan Generation

```
Triage metadata → plan_md_generator.generatePlan()
                      ↓
                Category-specific decomposition
                      ↓
                Approval gate detection
                      ↓
                vault_state_manager.writeVaultFile()
                      ↓
                  Plans/plan-*.md
```

**Code:**
```javascript
// Generate plan
const planResult = await generatePlan({
  triageData: topItem,
  agentName: 'lex',
  includeRollback: true,
  estimateEffort: true
});

const plan = planResult.plan_content;

console.log(`Plan created: ${plan.plan_id}`);
console.log(`  Steps: ${plan.steps.length}`);
console.log(`  Duration: ~${plan.estimated_duration_minutes} min`);
console.log(`  Requires approval: ${plan.requires_human_approval ? 'YES' : 'NO'}`);

if (plan.approval_gates.length > 0) {
  console.log(`  Approval gates:`);
  plan.approval_gates.forEach(gate => {
    console.log(`    - Step ${gate.step_id}: ${gate.reason}`);
  });
}
```

**Output:**
- Plan file created: `Plans/plan-1738587600-abc123.md`
- Structured plan with steps, approval gates, rollback procedures

---

### Phase 4: Plan Execution

```
Plans/ → task_lifecycle_manager.startWork()
              ↓
         In_Progress/
              ↓
    Execute steps sequentially
              ↓
    Approval gate? → Pending_Approval/ → Human review → Approved/
              ↓
    Continue execution
              ↓
         Done/
```

**Code:**
```javascript
// Start work
await taskLifecycle.startWork(claim.taskId, 'lex');

// Execute each step
for (const step of plan.steps) {
  console.log(`Executing: ${step.action}`);

  // Check approval requirement
  if (step.requires_approval) {
    // Request approval
    await taskLifecycle.requestApproval(claim.taskId, 'lex');
    console.log(`⏳ Awaiting approval for ${step.id}...`);

    // Wait for human
    const approved = await waitForApproval(claim.taskId, step.id);

    if (!approved) {
      console.log(`❌ Approval denied, halting`);
      break;
    }

    console.log(`✅ Approved, continuing`);
  }

  // Execute step
  try {
    const result = await executeStep(step);
    console.log(`✅ ${step.id} completed`);

    // Update execution log
    await updatePlanExecution(plan.plan_id, {
      step_id: step.id,
      status: 'completed',
      timestamp: new Date().toISOString(),
      notes: result.summary
    });

  } catch (err) {
    console.error(`❌ ${step.id} failed: ${err.message}`);

    // Execute rollback if available
    if (step.rollback_steps) {
      console.log(`🔄 Executing rollback...`);
      for (const rollbackStep of step.rollback_steps) {
        await executeRollback(rollbackStep);
      }
    }

    throw err;
  }
}

// Mark as completed
await taskLifecycle.completeTask(claim.taskId, 'orch');
console.log(`🎉 Task completed`);
```

**State Transitions:**
1. `Plans/` → `In_Progress/` (start work)
2. `In_Progress/` → `Pending_Approval/` (request approval)
3. `Pending_Approval/` → `Approved/` (human approves)
4. `Approved/` → `In_Progress/` (resume execution)
5. `In_Progress/` → `Done/` (task complete)

---

## Skill Interactions

### Interaction 1: Triage → Claim → Plan

```javascript
async function processNextTask(agentName) {
  // 1. Triage inbox (needs_action_triage)
  const triage = await triageNeedsAction({ minPriorityScore: 5 });

  if (triage.items.length === 0) {
    console.log('No work available');
    return null;
  }

  // 2. Claim highest-priority task (task_lifecycle_manager)
  const topItem = triage.items[0];
  const claim = await taskLifecycle.claimTask(topItem.file_name, agentName);

  if (!claim.success) {
    console.log('Task already claimed, trying next...');
    return processNextTask(agentName);  // Recursive retry
  }

  // 3. Generate plan (plan_md_generator)
  const planResult = await generatePlan({
    triageData: topItem,
    agentName: agentName,
    includeRollback: true
  });

  return {
    taskId: claim.taskId,
    triageData: topItem,
    plan: planResult.plan_content
  };
}

// Agent workflow
const work = await processNextTask('lex');
console.log(`Ready to execute: ${work.plan.goal}`);
```

---

### Interaction 2: Plan → Execute → Lifecycle

```javascript
async function executePlanWithLifecycle(work) {
  const { taskId, plan } = work;

  // 1. Start work (task_lifecycle_manager)
  await taskLifecycle.startWork(taskId, 'lex');

  // 2. Execute steps (plan_md_generator execution tracking)
  for (const step of plan.steps) {
    if (step.requires_approval) {
      // Request approval (task_lifecycle_manager)
      await taskLifecycle.requestApproval(taskId, 'lex');

      // Wait for human
      const approved = await waitForApproval(taskId, step.id);

      if (!approved) {
        // Move to Rejected (task_lifecycle_manager)
        await taskLifecycle.rejectTask(taskId, 'human', 'Approval denied');
        return { success: false, reason: 'rejected' };
      }
    }

    // Execute step
    await executeStep(step);

    // Update execution log (vault_state_manager)
    await vaultManager.writeVaultFile(
      `In_Progress/${taskId}.json`,
      JSON.stringify(plan),
      'orch'
    );
  }

  // 3. Mark completed (task_lifecycle_manager)
  await taskLifecycle.completeTask(taskId, 'orch');

  return { success: true };
}
```

---

### Interaction 3: Failure → Retry → Rollback

```javascript
async function executeWithRetry(work) {
  const { taskId, plan } = work;
  let attempts = 0;
  const maxRetries = 3;

  while (attempts < maxRetries) {
    try {
      // Execute plan
      await executePlanWithLifecycle(work);

      console.log('✅ Task completed successfully');
      return { success: true };

    } catch (err) {
      attempts++;
      console.error(`❌ Attempt ${attempts} failed: ${err.message}`);

      // Execute rollback (plan_md_generator)
      if (plan.rollback_plan) {
        console.log('🔄 Executing rollback...');
        await executeRollback(plan.rollback_plan);
      }

      if (attempts >= maxRetries) {
        // Max retries exceeded (task_lifecycle_manager)
        await taskLifecycle.handleTaskFailure(taskId, err, 'orch');

        console.log('❌ Max retries exceeded, moving to Rejected/');
        return { success: false, reason: 'max_retries' };
      }

      // Retry with exponential backoff
      const backoffMs = Math.pow(2, attempts) * 1000;
      console.log(`⏳ Retrying in ${backoffMs}ms...`);
      await sleep(backoffMs);

      // Move back to Needs_Action (task_lifecycle_manager)
      await taskLifecycle.retryTask(taskId, 'orch');
    }
  }
}
```

---

## Agent Responsibilities

### Local Executive Agent (lex)

**Responsibilities:**
- Scan inbox (needs_action_triage)
- Claim tasks (task_lifecycle_manager)
- Generate plans (plan_md_generator)
- Request approvals (task_lifecycle_manager)

**Permissions:**
- Read: `Needs_Action/`, `Plans/`, `In_Progress/`, `Pending_Approval/`
- Write: `Plans/`, `In_Progress/`, `Pending_Approval/`, `Logs/`

**Example Flow:**
```javascript
// Lex's main loop
async function lexMainLoop() {
  while (true) {
    // 1. Triage inbox
    const triage = await triageNeedsAction({ minPriorityScore: 5 });

    if (triage.items.length === 0) {
      await sleep(60000);  // Wait 1 minute
      continue;
    }

    // 2. Claim and plan
    const work = await processNextTask('lex');

    if (!work) {
      continue;  // All tasks claimed
    }

    // 3. Start execution (hand off to orchestrator)
    await taskLifecycle.startWork(work.taskId, 'lex');

    console.log(`✅ Task ${work.taskId} ready for orchestrator`);
  }
}
```

---

### Orchestrator Agent (orch)

**Responsibilities:**
- Execute approved plans
- Handle step failures
- Execute rollbacks
- Mark tasks completed

**Permissions:**
- Read: `Approved/`, `In_Progress/`
- Write: `In_Progress/`, `Done/`, `Rejected/`, `Logs/`
- Move: `Approved/` → `In_Progress/` → `Done/`

**Example Flow:**
```javascript
// Orchestrator's main loop
async function orchMainLoop() {
  while (true) {
    // 1. Check for approved work
    const approvedFiles = await vaultManager.listFolderFiles('Approved');

    if (approvedFiles.length === 0) {
      await sleep(10000);  // Wait 10 seconds
      continue;
    }

    // 2. Claim approved task
    const file = approvedFiles[0];
    await taskLifecycle.claimApprovedTask(file.name, 'orch');

    // 3. Read plan
    const { content } = await vaultManager.readVaultFile(`In_Progress/${file.name}`, 'orch');
    const plan = JSON.parse(content);

    // 4. Execute with retry
    const result = await executeWithRetry({ taskId: plan.plan_id, plan });

    if (result.success) {
      console.log(`✅ Task ${plan.plan_id} completed`);
    } else {
      console.error(`❌ Task ${plan.plan_id} failed: ${result.reason}`);
    }
  }
}
```

---

### Human User

**Responsibilities:**
- Review and approve high-risk operations
- Reject inappropriate tasks
- Monitor dashboard
- Handle exceptions

**Permissions:**
- Read: ALL folders
- Write: `Needs_Action/`, `Approved/`, `Rejected/`
- Move: `Pending_Approval/` → `Approved/` OR `Rejected/`

**Approval Workflow:**
```
1. Agent requests approval → Pending_Approval/
2. Human reviews task in Obsidian
3. Decision:
   - Approve: Move to Approved/
   - Reject: Move to Rejected/ with reason
4. Agent resumes execution (if approved)
```

---

## Dashboard Integration

### Daily Summary Report

```javascript
async function generateDailySummary() {
  // 1. Triage inbox
  const triage = await triageNeedsAction({ autoClassify: true });

  // 2. Count tasks in each stage
  const planFiles = await vaultManager.listFolderFiles('Plans');
  const inProgressFiles = await vaultManager.listFolderFiles('In_Progress');
  const pendingFiles = await vaultManager.listFolderFiles('Pending_Approval');
  const doneFiles = await vaultManager.listFolderFiles('Done');

  // 3. Generate report
  const summary = `
# Daily Digital FTE Summary

**Date:** ${new Date().toLocaleDateString()}

## Inbox
- **Total items:** ${triage.summary.total}
- **High priority:** ${triage.summary.high_priority}
- **Requires approval:** ${triage.items.filter(i => i.requires_human_approval).length}

## Work in Progress
- **Planned:** ${planFiles.length}
- **In Progress:** ${inProgressFiles.length}
- **Pending Approval:** ${pendingFiles.length}
- **Completed Today:** ${doneFiles.filter(f => isToday(f.modified)).length}

## Top Priority Items
${triage.items.slice(0, 5).map((item, i) => `
${i + 1}. **[${item.priority_score}/10]** ${item.metadata.subject || item.file_name}
   - Category: ${item.category}
   - Action: ${item.suggested_action}
   - ${item.summary}
`).join('\n')}

## Approval Queue
${pendingFiles.length > 0 ?
  pendingFiles.map(f => `- ${f.name}`).join('\n') :
  '*No items awaiting approval*'
}
`;

  // 4. Save to Updates/
  await vaultManager.writeVaultFile(
    `Updates/daily-summary-${new Date().toISOString().split('T')[0]}.md`,
    summary,
    'system'
  );

  return summary;
}

// Run daily at 9:00 AM
generateDailySummary();
```

---

## Best Practices

### 1. Always Triage Before Claiming

```javascript
// GOOD
const triage = await triageNeedsAction({ minPriorityScore: 5 });
const topItem = triage.items[0];
await taskLifecycle.claimTask(topItem.file_name, 'lex');

// BAD - skips prioritization
const files = await vaultManager.listFolderFiles('Needs_Action');
await taskLifecycle.claimTask(files[0].name, 'lex');  // May claim low-priority item!
```

### 2. Always Generate Plan Before Execution

```javascript
// GOOD
const work = await processNextTask('lex');  // Includes plan generation
await executePlanWithLifecycle(work);

// BAD - executes without plan
await taskLifecycle.startWork(taskId, 'lex');
await executeTaskDirectly(taskId);  // No approval gates, no rollback!
```

### 3. Always Check Approval Requirements

```javascript
// GOOD
if (step.requires_approval) {
  await taskLifecycle.requestApproval(taskId, 'lex');
  const approved = await waitForApproval(taskId, step.id);
  if (!approved) return;
}

// BAD - bypasses approval
await executeStep(step);  // Executes even if requires_approval=true!
```

### 4. Always Update Execution Log

```javascript
// GOOD
await executeStep(step);
await updatePlanExecution(plan.plan_id, {
  step_id: step.id,
  status: 'completed',
  timestamp: new Date().toISOString()
});

// BAD - no audit trail
await executeStep(step);
```

### 5. Always Handle Failures with Rollback

```javascript
// GOOD
try {
  await executeStep(step);
} catch (err) {
  if (step.rollback_steps) {
    await executeRollback(step.rollback_steps);
  }
  throw err;
}

// BAD - leaves partial state
try {
  await executeStep(step);
} catch (err) {
  throw err;  // No cleanup!
}
```

---

## Summary

The four vault skills work together to provide:

1. **Safe file operations** (vault_state_manager)
2. **Workflow orchestration** (task_lifecycle_manager)
3. **Intelligent prioritization** (needs_action_triage)
4. **Structured planning** (plan_md_generator)

Together they enable:
- **Automated inbox processing**
- **Priority-based task execution**
- **Human-in-the-loop approvals**
- **Audit trails for all actions**
- **Graceful failure handling with rollback**

All skills follow the same patterns:
- Atomic operations (claim-by-move, temp file → rename)
- Structured errors (no generic exceptions)
- Agent permissions enforced
- Full audit logs
- Idempotent operations (safe to retry)

The result is a production-ready Digital FTE workflow system.
