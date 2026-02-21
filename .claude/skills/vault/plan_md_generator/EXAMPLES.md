# Plan MD Generator - Complete Examples

This document provides end-to-end workflow examples showing how to use the `plan_md_generator` skill in real scenarios.

---

## Example 1: Complete Workflow (Triage → Plan → Execute)

**Scenario:** Email arrives requesting server maintenance. Full workflow from inbox to completion.

### Step 1: Triage Inbox

```javascript
const { triageNeedsAction } = require('./needs_action_triage');

const triage = await triageNeedsAction({ minPriorityScore: 5 });

console.log(`Found ${triage.items.length} medium+ priority items`);

// Select highest priority
const task = triage.items[0];
console.log(`\nTask: ${task.metadata.subject}`);
console.log(`Priority: ${task.priority_score}`);
console.log(`Category: ${task.category}`);
console.log(`Summary: ${task.summary}`);
```

**Output:**
```
Found 3 medium+ priority items

Task: Schedule server maintenance
Priority: 7
Category: email
Summary: Customer requesting maintenance window for database upgrade
```

### Step 2: Claim Task

```javascript
const { claimTask } = require('./task_lifecycle_manager');

const claim = await claimTask(task.file_name, 'lex');

if (claim.success) {
  console.log(`✅ Task claimed: ${claim.taskId}`);
} else {
  console.log(`❌ Already claimed`);
}
```

**Output:**
```
✅ Task claimed: task-1738587600-abc123
```

### Step 3: Generate Plan

```javascript
const { generatePlan } = require('./plan_md_generator');

console.log(`\n📝 Generating plan...`);

const planResult = await generatePlan({
  triageData: task,
  agentName: 'lex',
  includeRollback: true,
  estimateEffort: true
});

if (!planResult.success) {
  console.error(`❌ Plan generation failed: ${planResult.error}`);
  process.exit(1);
}

const plan = planResult.plan_content;

console.log(`\n✅ Plan generated successfully`);
console.log(`   Plan ID: ${plan.plan_id}`);
console.log(`   File: ${planResult.plan_file_path}`);
console.log(`   Goal: ${plan.goal}`);
console.log(`   Steps: ${plan.steps.length}`);
console.log(`   Duration: ~${plan.estimated_duration_minutes} minutes`);
console.log(`   Requires approval: ${plan.requires_human_approval ? 'YES' : 'NO'}`);

if (plan.approval_gates.length > 0) {
  console.log(`\n⚠️  Approval gates:`);
  plan.approval_gates.forEach(gate => {
    console.log(`   - Step ${gate.step_id}: ${gate.reason}`);
  });
}

console.log(`\n📋 Acceptance Criteria:`);
plan.acceptance_criteria.forEach((criteria, i) => {
  console.log(`   ${i + 1}. ${criteria}`);
});
```

**Output:**
```
📝 Generating plan...

✅ Plan generated successfully
   Plan ID: plan-1738587600-def456
   File: Plans/plan-1738587600-def456.md
   Goal: Schedule database maintenance window with customer
   Steps: 7
   Duration: ~15 minutes
   Requires approval: YES

⚠️  Approval gates:
   - Step 5: External communication (send calendar invite)
   - Step 6: Customer notification requires approval

📋 Acceptance Criteria:
   1. Maintenance window agreed upon
   2. Calendar invite sent
   3. Customer confirmed attendance
   4. Internal team notified
```

### Step 4: Review Plan (Human)

```markdown
# Plan: Schedule server maintenance

## Steps

### Step 1: Validate input and gather context
✅ Status: pending
- Review email thread
- Understand maintenance requirements

### Step 2: Check team calendar availability
✅ Status: pending
- Query calendar API for next 2 weeks
- Find 4-hour windows with all team members available

### Step 3: Propose maintenance windows to customer
✅ Status: pending
- Draft email with 3 suggested time slots
- Include timezone conversions

### Step 4: Wait for customer confirmation
✅ Status: pending
- Monitor inbox for response
- Timeout: 48 hours

### Step 5: Create calendar event
⚠️ REQUIRES APPROVAL: External communication
- Send calendar invite to customer and team
- Include maintenance details in description

### Step 6: Send confirmation notification
⚠️ REQUIRES APPROVAL: Customer notification
- Email customer with final confirmation
- Include preparation checklist

### Step 7: Verify task completion
✅ Status: pending
- All acceptance criteria met
```

### Step 5: Execute Plan (With Approvals)

```javascript
const { executePlan } = require('./plan_executor');

console.log(`\n⚙️  Executing plan: ${plan.plan_id}\n`);

for (const step of plan.steps) {
  console.log(`📍 Step ${step.id}: ${step.action}`);

  // Check if approval needed
  if (step.requires_approval) {
    console.log(`   ⏳ Requesting human approval...`);

    // Move plan to Pending_Approval/
    await moveFile('In_Progress', `${plan.plan_id}.json`, 'Pending_Approval', 'lex');

    // Wait for approval
    const approved = await waitForApproval(plan.plan_id, step.id);

    if (!approved) {
      console.log(`   ❌ Approval denied, halting execution`);
      break;
    }

    console.log(`   ✅ Approved by human`);

    // Move back to In_Progress/
    await moveFile('Approved', `${plan.plan_id}.json`, 'In_Progress', 'orch');
  }

  // Execute step
  try {
    const result = await executeStep(plan.plan_id, step);

    console.log(`   ✅ Completed`);
    console.log(`   Result: ${result.summary}\n`);

    // Update execution log
    await updatePlanExecution(plan.plan_id, {
      step_id: step.id,
      status: 'completed',
      timestamp: new Date().toISOString(),
      notes: result.summary
    });

  } catch (err) {
    console.error(`   ❌ Failed: ${err.message}\n`);

    // Update execution log
    await updatePlanExecution(plan.plan_id, {
      step_id: step.id,
      status: 'failed',
      timestamp: new Date().toISOString(),
      notes: err.message
    });

    // Execute rollback if available
    if (step.rollback_steps) {
      console.log(`   🔄 Executing rollback...`);
      for (const rollbackStep of step.rollback_steps) {
        console.log(`      - ${rollbackStep}`);
        await executeRollback(rollbackStep);
      }
    }

    throw err;
  }
}

console.log(`\n✅ Plan execution completed`);
```

**Output:**
```
⚙️  Executing plan: plan-1738587600-def456

📍 Step step-1: Validate input and gather context
   ✅ Completed
   Result: Email thread reviewed, maintenance requirements documented

📍 Step step-2: Check team calendar availability
   ✅ Completed
   Result: Found 3 available windows: Feb 10, Feb 12, Feb 15

📍 Step step-3: Propose maintenance windows to customer
   ✅ Completed
   Result: Draft email created with 3 time slot options

📍 Step step-4: Wait for customer confirmation
   ✅ Completed
   Result: Customer selected Feb 12, 2:00-6:00 PM EST

📍 Step step-5: Create calendar event
   ⏳ Requesting human approval...
   ✅ Approved by human
   ✅ Completed
   Result: Calendar invite sent to 5 attendees

📍 Step step-6: Send confirmation notification
   ⏳ Requesting human approval...
   ✅ Approved by human
   ✅ Completed
   Result: Confirmation email sent with preparation checklist

📍 Step step-7: Verify task completion
   ✅ Completed
   Result: All acceptance criteria verified

✅ Plan execution completed
```

### Step 6: Move to Done

```javascript
await taskLifecycle.transitionTask(
  plan.plan_id,
  'in_progress',
  'done',
  'orch'
);

console.log(`\n🎉 Task completed and moved to Done/`);
```

---

## Example 2: Finance Plan with Multiple Approval Gates

**Scenario:** Process overdue invoice payment (high-risk, requires multiple approvals)

### Input (Triage Data)

```json
{
  "category": "finance",
  "priority_score": 9,
  "metadata": {
    "subject": "Invoice #1234 payment overdue",
    "financial_amount": 5432.00,
    "deadline": "2025-01-31T23:59:59Z"
  },
  "requires_human_approval": true,
  "autonomy_tier": "platinum"
}
```

### Generated Plan

```javascript
const plan = await generatePlan({
  triageData: financeTask,
  agentName: 'lex',
  includeRollback: true
});

console.log(`\n💰 Finance Plan Generated`);
console.log(`   Approval gates: ${plan.plan_content.approval_gates.length}`);
console.log(`   Risk level: HIGH`);

plan.plan_content.approval_gates.forEach((gate, i) => {
  console.log(`   ${i + 1}. ${gate.step_id}: ${gate.reason}`);
});
```

**Output:**
```
💰 Finance Plan Generated
   Approval gates: 2
   Risk level: HIGH
   1. step-4: Financial operation requires approval
   2. step-5: Payment execution requires confirmation
```

### Plan Structure

```markdown
# Plan: Invoice #1234 payment overdue

**Autonomy Tier:** platinum (highest oversight)

## Steps

### Step 1: Validate invoice details
- Verify invoice number, amount, vendor
- Check against purchase order

### Step 2: Check budget allocation
- Query accounting system
- Verify sufficient funds

### Step 3: Verify vendor bank details
- Cross-check against vendor database
- Detect any changes since last payment

### Step 4: Prepare payment authorization
⚠️ REQUIRES APPROVAL: Financial operation requires approval
- Generate authorization form
- Submit to finance team

### Step 5: Process payment via payment gateway
⚠️ REQUIRES APPROVAL: Payment execution requires confirmation
- Execute payment transaction
- Obtain confirmation number

**Rollback Steps:**
1. Void transaction if partially processed
2. Issue refund if payment completed incorrectly
3. Contact payment gateway support

### Step 6: Update accounting system
- Mark invoice as paid
- Record transaction details

### Step 7: Verify completion
- Confirm all acceptance criteria met
```

### Execution with Double Approval

```javascript
// Execute steps 1-3 (automated)
for (let i = 0; i < 3; i++) {
  await executeStep(plan.plan_id, plan.steps[i]);
}

// Step 4: First approval (authorization)
console.log(`\n⏳ Requesting payment authorization...`);
await requestApproval(plan.plan_id, 'step-4');

const auth = await waitForApproval(plan.plan_id, 'step-4', timeout: 3600000);

if (!auth.approved) {
  console.log(`❌ Payment authorization denied: ${auth.reason}`);
  await moveFile('Pending_Approval', `${plan.plan_id}.json`, 'Rejected', 'human');
  process.exit(1);
}

console.log(`✅ Payment authorized by ${auth.approved_by}`);

// Step 5: Second approval (execution)
console.log(`\n⏳ Requesting payment execution confirmation...`);
await requestApproval(plan.plan_id, 'step-5');

const exec = await waitForApproval(plan.plan_id, 'step-5', timeout: 600000);

if (!exec.approved) {
  console.log(`❌ Payment execution denied: ${exec.reason}`);
  process.exit(1);
}

console.log(`✅ Payment execution confirmed by ${exec.approved_by}`);

// Execute payment
try {
  const payment = await executePayment({
    amount: 5432.00,
    vendor: 'Acme Corp',
    invoice: '#1234'
  });

  console.log(`✅ Payment processed: ${payment.confirmation}`);

} catch (err) {
  console.error(`❌ Payment failed: ${err.message}`);

  // Execute rollback
  console.log(`🔄 Executing rollback...`);
  await voidTransaction(payment.transaction_id);
  console.log(`✅ Transaction voided`);

  throw err;
}

// Continue with steps 6-7
```

**Output:**
```
⏳ Requesting payment authorization...
✅ Payment authorized by finance_manager

⏳ Requesting payment execution confirmation...
✅ Payment execution confirmed by cfo

✅ Payment processed: CONF-789012

✅ All steps completed successfully
```

---

## Example 3: Plan Execution with Rollback

**Scenario:** Database migration fails, rollback executed

### Plan (Abbreviated)

```markdown
### Step 5: Run database migration
⚠️ Risk Level: HIGH

**Rollback Steps:**
1. Restore database from backup (step-2)
2. Verify record counts match pre-migration
3. Re-enable application access
```

### Execution with Failure

```javascript
console.log(`📍 Step step-5: Run database migration`);

try {
  const result = await executeMigration({
    database: 'prod_db',
    script: 'migration_v2.sql'
  });

  console.log(`   ✅ Migration completed`);

} catch (err) {
  console.error(`   ❌ Migration failed: ${err.message}`);

  // Get rollback steps
  const step = plan.steps.find(s => s.id === 'step-5');

  if (step.rollback_steps) {
    console.log(`\n🔄 Executing rollback plan:\n`);

    for (const rollbackStep of step.rollback_steps) {
      console.log(`   📌 ${rollbackStep}`);

      try {
        await executeRollbackStep(rollbackStep);
        console.log(`      ✅ Completed\n`);

      } catch (rollbackErr) {
        console.error(`      ❌ Rollback failed: ${rollbackErr.message}\n`);
        console.error(`      🚨 CRITICAL: Manual intervention required!`);
        break;
      }
    }

    console.log(`✅ Rollback completed, system restored`);

  } else {
    console.error(`   🚨 No rollback plan available!`);
  }

  throw err;
}
```

**Output:**
```
📍 Step step-5: Run database migration
   ❌ Migration failed: Foreign key constraint violated

🔄 Executing rollback plan:

   📌 Restore database from backup (step-2)
      ✅ Completed

   📌 Verify record counts match pre-migration
      ✅ Completed

   📌 Re-enable application access
      ✅ Completed

✅ Rollback completed, system restored
```

---

## Example 4: Plan Validation Before Execution

**Scenario:** Validate plan structure before starting execution

### Validation Function

```javascript
function validatePlanBeforeExecution(plan) {
  console.log(`\n🔍 Validating plan: ${plan.plan_id}\n`);

  const errors = [];
  const warnings = [];

  // Check 1: Plan not stale
  const age = (Date.now() - new Date(plan.created_at)) / (1000 * 60 * 60 * 24);
  if (age > 2) {
    errors.push(`Plan is stale (${age.toFixed(1)} days old)`);
  }

  // Check 2: Required fields
  if (!plan.goal) errors.push('Missing goal');
  if (!plan.acceptance_criteria || plan.acceptance_criteria.length === 0) {
    errors.push('Missing acceptance criteria');
  }

  // Check 3: Steps
  if (plan.steps.length < 3) {
    errors.push('Plan has fewer than 3 steps');
  }
  if (plan.steps.length > 20) {
    errors.push('Plan has more than 20 steps');
  }

  // Check 4: Success criteria
  plan.steps.forEach((step, i) => {
    if (!step.success_criteria) {
      warnings.push(`Step ${i + 1} missing success criteria`);
    }
  });

  // Check 5: Approval gates
  const approvalSteps = plan.steps.filter(s => s.requires_approval);
  if (approvalSteps.length !== plan.approval_gates.length) {
    errors.push('Approval gates count mismatch');
  }

  // Check 6: Finance operations
  if (plan.category === 'finance' && !plan.requires_human_approval) {
    errors.push('Finance operations must require human approval');
  }

  // Check 7: Rollback plans
  const highRiskSteps = plan.steps.filter(s => s.risk_level === 'high');
  highRiskSteps.forEach(step => {
    if (!step.rollback_steps || step.rollback_steps.length === 0) {
      warnings.push(`High-risk step ${step.id} has no rollback plan`);
    }
  });

  // Check 8: Circular dependencies
  try {
    detectCircularDependencies(plan.steps);
  } catch (err) {
    errors.push(err.message);
  }

  // Check 9: Tools exist
  const unknownTools = [];
  plan.steps.forEach(step => {
    if (step.tools_needed) {
      step.tools_needed.forEach(tool => {
        const toolName = tool.split(' ')[0];
        if (!AVAILABLE_TOOLS.includes(toolName)) {
          unknownTools.push(toolName);
        }
      });
    }
  });
  if (unknownTools.length > 0) {
    errors.push(`Unknown tools: ${unknownTools.join(', ')}`);
  }

  // Report results
  if (errors.length > 0) {
    console.log(`❌ Validation failed:\n`);
    errors.forEach(err => console.log(`   - ${err}`));
    return { valid: false, errors, warnings };
  }

  if (warnings.length > 0) {
    console.log(`⚠️  Validation warnings:\n`);
    warnings.forEach(warn => console.log(`   - ${warn}`));
  }

  console.log(`✅ Plan validated successfully\n`);
  return { valid: true, errors: [], warnings };
}

// Use before execution
const validation = validatePlanBeforeExecution(plan);

if (!validation.valid) {
  console.error(`Cannot execute invalid plan`);
  process.exit(1);
}

// Proceed with execution
await executePlan(plan);
```

**Output (Success):**
```
🔍 Validating plan: plan-1738587600-abc123

✅ Plan validated successfully
```

**Output (Failure):**
```
🔍 Validating plan: plan-1738587700-def456

❌ Validation failed:

   - Plan is stale (3.2 days old)
   - Approval gates count mismatch
   - Unknown tools: widget_api, fake_service

Cannot execute invalid plan
```

---

## Example 5: Batch Plan Generation

**Scenario:** Generate plans for multiple triaged items

### Code

```javascript
async function batchGeneratePlans() {
  // Step 1: Triage all items
  const triage = await triageNeedsAction({ minPriorityScore: 5 });

  console.log(`\n📋 Generating plans for ${triage.items.length} items...\n`);

  const results = [];

  // Step 2: Generate plan for each
  for (const item of triage.items) {
    console.log(`📝 ${item.metadata.subject || item.file_name}`);

    try {
      const planResult = await generatePlan({
        triageData: item,
        agentName: 'lex',
        includeRollback: true
      });

      if (planResult.success) {
        console.log(`   ✅ ${planResult.plan_content.steps.length} steps, ~${planResult.plan_content.estimated_duration_minutes} min`);

        results.push({
          item: item.file_name,
          plan_id: planResult.plan_id,
          steps: planResult.plan_content.steps.length,
          duration: planResult.plan_content.estimated_duration_minutes,
          requires_approval: planResult.plan_content.requires_human_approval
        });

      } else {
        console.log(`   ❌ Failed: ${planResult.error}`);

        results.push({
          item: item.file_name,
          error: planResult.error
        });
      }

    } catch (err) {
      console.log(`   ❌ Error: ${err.message}`);
    }

    console.log();
  }

  // Step 3: Summary
  console.log(`\n📊 Batch Summary:\n`);
  console.log(`   Total items: ${triage.items.length}`);
  console.log(`   Plans generated: ${results.filter(r => r.plan_id).length}`);
  console.log(`   Failures: ${results.filter(r => r.error).length}`);

  const totalSteps = results.filter(r => r.steps).reduce((sum, r) => sum + r.steps, 0);
  const totalDuration = results.filter(r => r.duration).reduce((sum, r) => sum + r.duration, 0);

  console.log(`   Total steps: ${totalSteps}`);
  console.log(`   Total estimated time: ~${totalDuration} minutes`);

  const requireApproval = results.filter(r => r.requires_approval).length;
  console.log(`   Require approval: ${requireApproval}`);

  return results;
}

batchGeneratePlans();
```

**Output:**
```
📋 Generating plans for 5 items...

📝 Invoice #1234 payment overdue
   ✅ 7 steps, ~12 min

📝 URGENT: Production server down
   ✅ 6 steps, ~18 min

📝 Feature request: API rate limiting
   ✅ 7 steps, ~22 min

📝 Import contacts CSV
   ✅ 6 steps, ~14 min

📝 Weekly newsletter draft
   ✅ 5 steps, ~10 min

📊 Batch Summary:

   Total items: 5
   Plans generated: 5
   Failures: 0
   Total steps: 31
   Total estimated time: ~76 minutes
   Require approval: 4
```

---

## Best Practices

1. **Always validate plans before execution**
2. **Check approval gates before starting**
3. **Verify plan freshness (< 2 days old)**
4. **Update execution log after each step**
5. **Execute rollback on failures**
6. **Handle approvals asynchronously (don't block)**
7. **Log all state transitions for audit**
8. **Validate tools exist before execution**
9. **Monitor step duration vs estimate**
10. **Archive completed plans to Done/**

---

## Summary

These examples demonstrate:

1. **Complete workflow** - Triage → Claim → Plan → Execute
2. **Finance operations** - Multiple approval gates for high-risk
3. **Rollback execution** - Undo on failure
4. **Plan validation** - Structural checks before execution
5. **Batch generation** - Process multiple items efficiently

All patterns follow best practices for safety, auditability, and human oversight.
