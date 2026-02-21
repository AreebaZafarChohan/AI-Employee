# Plan MD Generator - Usage Patterns

This document provides concrete code examples and workflow patterns for the `plan_md_generator` skill.

---

## Pattern 1: Basic Plan Generation from Triage Data

**Use Case:** Generate plan for a triaged email task

### Input (Triage Data)

```json
{
  "file_name": "email-20250203-server-alert.md",
  "category": "email",
  "subcategory": "alert",
  "priority_score": 8,
  "confidence": 0.95,
  "metadata": {
    "source_type": "email",
    "sender": "ops-team@company.com",
    "subject": "URGENT: Production server down",
    "received_at": "2025-02-03T08:30:00Z",
    "deadline": "2025-02-03T10:30:00Z"
  },
  "suggested_action": "research",
  "estimated_effort": "medium",
  "requires_human_approval": false,
  "autonomy_tier": "silver",
  "summary": "Production API server unresponsive, all endpoints returning 503, high customer impact"
}
```

### Code Example

```javascript
const { generatePlan } = require('./plan_md_generator');

async function createPlanFromTriage(triageData) {
  console.log(`📝 Generating plan for: ${triageData.metadata.subject}\n`);

  // Generate plan
  const result = await generatePlan({
    triageData: triageData,
    agentName: 'lex',
    includeRollback: true,
    estimateEffort: true
  });

  if (!result.success) {
    console.error(`❌ Plan generation failed: ${result.error}`);
    return null;
  }

  console.log(`✅ Plan created successfully`);
  console.log(`   Plan ID: ${result.plan_id}`);
  console.log(`   File: ${result.plan_file_path}`);
  console.log(`   Steps: ${result.plan_content.steps.length}`);
  console.log(`   Estimated duration: ${result.plan_content.estimated_duration_minutes} min`);
  console.log(`   Requires approval: ${result.plan_content.requires_human_approval}`);

  return result;
}

// Execute
const triage = await triageNeedsAction({ filterFiles: ['email-20250203-server-alert.md'] });
const plan = await createPlanFromTriage(triage.items[0]);
```

### Output (Plan File: Plans/plan-1738587600-abc123.md)

```markdown
# Plan: URGENT: Production server down

**Plan ID:** plan-1738587600-abc123
**Created:** 2025-02-03T09:00:00Z
**Priority:** 8/10
**Category:** email
**Status:** planned

---

## Goal

Diagnose and resolve production API server outage to restore service availability

## Context

Production API server (api-prod-01) became unresponsive at 08:30 UTC. All endpoints are returning 503 errors, causing high customer impact. Issue reported by ops-team. Resolution required within 2 hours (deadline: 10:30 UTC).

Source: Needs_Action/email-20250203-server-alert.md

## Estimated Effort

- **Duration:** ~18 minutes
- **Complexity:** medium
- **Autonomy Tier:** silver
- **Requires Approval:** No (fully automated)

---

## Acceptance Criteria

- [ ] Root cause identified
- [ ] Service restored to healthy state
- [ ] All endpoints returning 200 status
- [ ] Customer impact mitigated
- [ ] Incident documented

---

## Steps

### Step 1: Validate input and gather context

- **Type:** research
- **Risk Level:** low
- **Estimated Time:** 2 min
- **Status:** pending

**Success Criteria:** All server details and symptoms documented

---

### Step 2: Check server health status

- **Type:** api_call
- **Risk Level:** low
- **Estimated Time:** 3 min
- **Status:** pending

**Success Criteria:** Health check API returns server status

**Tools Needed:**
- monitoring_api (from .env)

---

### Step 3: Review server logs

- **Type:** research
- **Risk Level:** low
- **Estimated Time:** 5 min
- **Status:** pending

**Success Criteria:** Logs retrieved and error patterns identified

**Tools Needed:**
- log_aggregation_api

---

### Step 4: Identify root cause

- **Type:** research
- **Risk Level:** low
- **Estimated Time:** 5 min
- **Status:** pending

**Success Criteria:** Specific issue identified (memory, disk, network, code)

**Dependencies:** step-2, step-3

---

### Step 5: Restart server

- **Type:** api_call
- **Risk Level:** medium
- **Estimated Time:** 2 min
- **Status:** pending

**⚠️ REQUIRES APPROVAL:** Restarting production service requires approval

**Success Criteria:** Server restart completes successfully

**Tools Needed:**
- infrastructure_api

**Rollback Steps (if failure):**
1. Failover to backup server
2. Rollback recent deployment if applicable

---

### Step 6: Verify service restoration

- **Type:** validation
- **Risk Level:** low
- **Estimated Time:** 2 min
- **Status:** pending

**Success Criteria:** All endpoints return 200, no customer errors

---

## Approval Gates

### Gate step-5

- **Reason:** Restarting production service requires approval
- **Approver:** human
- **Status:** ⏳ Pending

---

## Risk Assessment

### Service interruption during restart

- **Severity:** medium
- **Mitigation:** Use rolling restart or failover to backup server first

### Root cause not identified

- **Severity:** high
- **Mitigation:** If logs inconclusive, escalate to senior engineer

---

## Resources Needed

**APIs:**
- monitoring_api
- log_aggregation_api
- infrastructure_api

**Credentials:**
- monitoring_api_key (from .env)
- infra_admin_token (from .env)

---

## Validation

### Automated Checks
- [ ] Health check endpoint returns 200
- [ ] All API endpoints responding
- [ ] Error rate drops to 0%

### Manual Verification
- [ ] Customer support confirms no active complaints
- [ ] Monitoring dashboard shows green status

### Rollback Plan

If restart fails or causes additional issues, failover to backup server (api-prod-02) and investigate offline.

---

## Execution Log

*No executions yet*

---

*Generated by plan_md_generator skill*
*Last updated: 2025-02-03T09:00:00Z*
```

---

## Pattern 2: Finance Task Plan (High-Risk)

**Use Case:** Generate plan for invoice payment (requires approval)

### Input (Triage Data)

```json
{
  "file_name": "finance-20250203-invoice.md",
  "category": "finance",
  "subcategory": "invoice",
  "priority_score": 9,
  "metadata": {
    "sender": "Acme Corp <billing@acme.com>",
    "subject": "Invoice #1234 payment overdue",
    "financial_amount": 5432.00,
    "deadline": "2025-01-31T23:59:59Z"
  },
  "suggested_action": "approve",
  "requires_human_approval": true,
  "autonomy_tier": "platinum",
  "summary": "Overdue payment of $5,432.00 from Acme Corp"
}
```

### Code Example

```javascript
async function createFinancePlan(triageData) {
  console.log(`💰 Generating finance plan...\n`);

  const result = await generatePlan({
    triageData: triageData,
    agentName: 'lex',
    includeRollback: true,  // Critical for finance
    estimateEffort: true
  });

  // Finance plans always require approval
  if (!result.plan_content.requires_human_approval) {
    console.warn('⚠️ Finance plan missing approval requirement, forcing...');
    result.plan_content.requires_human_approval = true;
  }

  console.log(`✅ Finance plan created`);
  console.log(`   Approval gates: ${result.plan_content.approval_gates.length}`);
  console.log(`   Risk level: HIGH (financial operation)`);

  return result;
}
```

### Output (Plan File)

```markdown
# Plan: Invoice #1234 payment overdue

**Plan ID:** plan-1738587700-def456
**Created:** 2025-02-03T09:15:00Z
**Priority:** 9/10
**Category:** finance
**Status:** planned

---

## Goal

Process overdue payment of $5,432.00 to Acme Corp for Invoice #1234

## Context

Invoice #1234 from Acme Corp became overdue on January 31, 2025. Amount: $5,432.00. Late fees accruing at $50/day. Requires immediate payment to avoid service interruption and additional penalties.

Source: Needs_Action/finance-20250203-invoice.md

## Estimated Effort

- **Duration:** ~12 minutes
- **Complexity:** low
- **Autonomy Tier:** platinum (requires human approval)
- **Requires Approval:** **YES**

---

## Acceptance Criteria

- [ ] Invoice validated and approved
- [ ] Payment processed successfully
- [ ] Confirmation receipt received
- [ ] Accounting system updated
- [ ] Vendor notified of payment

---

## Steps

### Step 1: Validate invoice details

- **Type:** research
- **Risk Level:** low
- **Estimated Time:** 3 min
- **Status:** pending

**Success Criteria:** Invoice number, amount, vendor, and terms verified

---

### Step 2: Check budget allocation

- **Type:** research
- **Risk Level:** low
- **Estimated Time:** 2 min
- **Status:** pending

**Success Criteria:** Budget has sufficient funds for payment

**Tools Needed:**
- accounting_api

---

### Step 3: Verify vendor bank details

- **Type:** research
- **Risk Level:** medium
- **Estimated Time:** 2 min
- **Status:** pending

**Success Criteria:** Bank account matches vendor records

---

### Step 4: Prepare payment authorization

- **Type:** approval
- **Risk Level:** high
- **Estimated Time:** 0 min
- **Status:** pending

**⚠️ REQUIRES APPROVAL:** Financial operation requires approval

**Success Criteria:** Finance team approves payment

---

### Step 5: Process payment via payment gateway

- **Type:** api_call
- **Risk Level:** high
- **Estimated Time:** 3 min
- **Status:** pending

**⚠️ REQUIRES APPROVAL:** Payment execution requires confirmation

**Success Criteria:** Payment gateway returns success confirmation

**Tools Needed:**
- stripe_api (from .env)

**Dependencies:** step-4

**Rollback Steps (if failure):**
1. Void transaction if partially processed
2. Issue refund if payment completed incorrectly
3. Contact payment gateway support

---

### Step 6: Update accounting system

- **Type:** api_call
- **Risk Level:** medium
- **Estimated Time:** 2 min
- **Status:** pending

**Success Criteria:** Invoice marked as paid in accounting system

**Tools Needed:**
- quickbooks_api

**Dependencies:** step-5

---

### Step 7: Verify task completion

- **Type:** validation
- **Risk Level:** low
- **Estimated Time:** 1 min
- **Status:** pending

**Success Criteria:** All acceptance criteria met

---

## Approval Gates

### Gate step-4

- **Reason:** Financial operation requires approval
- **Approver:** human
- **Status:** ⏳ Pending

### Gate step-5

- **Reason:** Payment execution requires confirmation
- **Approver:** human
- **Status:** ⏳ Pending

---

## Risk Assessment

### Incorrect payment amount

- **Severity:** high
- **Mitigation:** Verify amount against invoice in step 1, require human approval before execution

### Payment to wrong vendor

- **Severity:** high
- **Mitigation:** Verify bank details in step 3, cross-check against vendor database

### Duplicate payment

- **Severity:** medium
- **Mitigation:** Check if invoice already paid before processing, use idempotency key

### Budget overrun

- **Severity:** medium
- **Mitigation:** Verify budget allocation in step 2 before requesting approval

---

## Resources Needed

**APIs:**
- accounting_api
- stripe_api (payment gateway)
- quickbooks_api

**Credentials:**
- stripe_api_key (from .env)
- quickbooks_oauth_token (from .env)

**Files:**
- Invoice #1234 PDF (for verification)

---

## Validation

### Automated Checks
- [ ] Payment gateway confirmation received
- [ ] Accounting system shows invoice as paid
- [ ] Bank account debited correct amount

### Manual Verification
- [ ] Finance team confirms payment authorized
- [ ] Vendor confirms payment received
- [ ] Invoice marked as closed

### Rollback Plan

If payment fails or processes incorrectly:
1. Immediately void/refund transaction
2. Contact payment gateway support
3. Notify finance team of failure
4. Retry after issue resolved, or process manually

---

## Execution Log

*No executions yet*

---

*Generated by plan_md_generator skill*
*Last updated: 2025-02-03T09:15:00Z*
```

**Key Differences for Finance:**
- Multiple approval gates (steps 4 and 5)
- Detailed rollback plan
- Risk assessment focused on financial risks
- Autonomy tier: platinum (highest oversight)

---

## Pattern 3: Multi-Step Email Response Plan

**Use Case:** Reply to complex email requiring research

### Input (Triage Data)

```json
{
  "file_name": "email-20250203-feature-request.md",
  "category": "email",
  "subcategory": "thread",
  "priority_score": 6,
  "metadata": {
    "sender": "customer@example.com",
    "subject": "Feature request: API rate limiting",
    "received_at": "2025-02-03T07:00:00Z"
  },
  "suggested_action": "research",
  "requires_human_approval": true,
  "autonomy_tier": "gold",
  "summary": "Customer requesting API rate limiting feature, needs technical response"
}
```

### Generated Plan (Abbreviated)

```markdown
# Plan: Feature request: API rate limiting

## Steps

### Step 1: Validate input and gather context
- Read full email thread
- Understand customer requirements

### Step 2: Research existing API features
- Check current API documentation
- Review existing rate limiting capabilities

### Step 3: Consult engineering team
- Query internal knowledge base
- Check if feature already planned

### Step 4: Draft response email
- Summarize findings
- Provide timeline if feature exists
- Explain alternatives if not available

### Step 5: Review draft for accuracy
- Verify technical details correct
- Check tone is professional

### Step 6: Send email response
- **⚠️ REQUIRES APPROVAL:** External communication requires approval
- Use email API to send

### Step 7: Verify task completion
- Confirm email sent successfully
- Mark ticket as responded

## Approval Gates

### Gate step-6
- **Reason:** External communication requires approval
- **Approver:** human
- **Status:** ⏳ Pending
```

---

## Pattern 4: File Processing Plan

**Use Case:** Process uploaded CSV file

### Input (Triage Data)

```json
{
  "file_name": "file-drop-20250203-contacts.md",
  "category": "file_drop",
  "subcategory": "import",
  "priority_score": 5,
  "metadata": {
    "source_type": "file",
    "subject": "Import contacts CSV"
  },
  "suggested_action": "research",
  "autonomy_tier": "silver"
}
```

### Generated Plan (Abbreviated)

```markdown
# Plan: Import contacts CSV

## Steps

### Step 1: Read and parse CSV file
- Load file from upload directory
- Validate CSV format

### Step 2: Extract and validate contact data
- Parse each row
- Check required fields present
- Validate email format

### Step 3: Check for duplicates
- Query existing contacts database
- Flag duplicates for review

### Step 4: Import new contacts
- **⚠️ REQUIRES APPROVAL:** Data modification requires approval
- Batch insert into database

### Step 5: Generate import report
- Count imported vs skipped
- List any errors

### Step 6: Send notification
- **⚠️ REQUIRES APPROVAL:** External notification requires approval
- Email user with import summary
```

---

## Pattern 5: Incremental Execution Tracking

**Use Case:** Track execution progress in plan file

### Code Example

```javascript
const { updatePlanExecution } = require('./plan_md_generator');

async function executeStepWithTracking(planId, stepId, agentName) {
  console.log(`⚙️  Executing ${planId} - ${stepId}...\n`);

  // Mark step as in-progress
  await updatePlanExecution(planId, {
    step_id: stepId,
    status: 'in_progress',
    agent: agentName,
    timestamp: new Date().toISOString()
  });

  try {
    // Execute step
    const result = await executeStep(stepId);

    // Mark as completed
    await updatePlanExecution(planId, {
      step_id: stepId,
      status: 'completed',
      agent: agentName,
      timestamp: new Date().toISOString(),
      notes: `Step completed successfully: ${result.summary}`
    });

    console.log(`✅ ${stepId} completed`);
    return result;

  } catch (err) {
    // Mark as failed
    await updatePlanExecution(planId, {
      step_id: stepId,
      status: 'failed',
      agent: agentName,
      timestamp: new Date().toISOString(),
      notes: `Step failed: ${err.message}`
    });

    console.error(`❌ ${stepId} failed: ${err.message}`);
    throw err;
  }
}

// Execute plan step-by-step
async function executePlan(planId) {
  const plan = await readPlan(planId);

  for (const step of plan.steps) {
    // Skip approval steps (handled separately)
    if (step.type === 'approval') {
      console.log(`⏳ ${step.id} requires approval, waiting...`);
      continue;
    }

    await executeStepWithTracking(planId, step.id, 'orch');
  }
}
```

### Updated Execution Log in Plan File

```markdown
## Execution Log

**[2025-02-03T09:30:00Z]** Step step-1 - in_progress
- Agent: orch
- Notes: Starting validation

**[2025-02-03T09:31:00Z]** Step step-1 - completed
- Agent: orch
- Notes: Step completed successfully: All required information validated

**[2025-02-03T09:31:30Z]** Step step-2 - in_progress
- Agent: orch
- Notes: Checking server health

**[2025-02-03T09:33:00Z]** Step step-2 - completed
- Agent: orch
- Notes: Step completed successfully: Server health retrieved

**[2025-02-03T09:33:30Z]** Step step-3 - failed
- Agent: orch
- Notes: Step failed: Log aggregation API timeout
```

---

## Pattern 6: Approval Workflow Integration

**Use Case:** Handle approval gates during execution

### Code Example

```javascript
async function handleApprovalGate(planId, stepId) {
  const plan = await readPlan(planId);
  const gate = plan.approval_gates.find(g => g.step_id === stepId);

  if (!gate) {
    console.log(`No approval gate for ${stepId}`);
    return { approved: true };
  }

  console.log(`⏳ Approval required for ${stepId}`);
  console.log(`   Reason: ${gate.reason}`);
  console.log(`   Approver: ${gate.approver}`);

  // Move plan to Pending_Approval/ folder
  await moveFile(
    'Plans',
    `${planId}.json`,
    'Pending_Approval',
    'orch'
  );

  console.log(`📋 Plan moved to Pending_Approval/`);
  console.log(`   Waiting for human approval...`);

  // Poll for approval (in real system, use webhook/notification)
  const approved = await waitForApproval(planId, stepId);

  if (approved) {
    // Update approval gate
    gate.approved_at = new Date().toISOString();
    gate.approved_by = 'human';
    await updatePlan(planId, { approval_gates: plan.approval_gates });

    // Move back to In_Progress/
    await moveFile(
      'Approved',
      `${planId}.json`,
      'In_Progress',
      'orch'
    );

    console.log(`✅ Approval granted, continuing execution`);
    return { approved: true };
  } else {
    // Rejected, move to Rejected/
    await moveFile(
      'Pending_Approval',
      `${planId}.json`,
      'Rejected',
      'human'
    );

    console.log(`❌ Approval denied, halting execution`);
    return { approved: false, reason: 'Human rejected approval' };
  }
}
```

---

## Pattern 7: Plan Validation Before Execution

**Use Case:** Validate plan structure before executing

### Code Example

```javascript
function validatePlan(plan) {
  const errors = [];
  const warnings = [];

  // Check required fields
  if (!plan.goal) {
    errors.push('Missing goal');
  }

  if (!plan.acceptance_criteria || plan.acceptance_criteria.length === 0) {
    errors.push('Missing acceptance criteria');
  }

  if (!plan.steps || plan.steps.length === 0) {
    errors.push('No steps defined');
  }

  // Check step count
  if (plan.steps && plan.steps.length < 3) {
    warnings.push('Plan has fewer than 3 steps, may be too simple');
  }

  if (plan.steps && plan.steps.length > 20) {
    errors.push('Plan has more than 20 steps, too complex');
  }

  // Check approval gates
  const approvalSteps = plan.steps.filter(s => s.requires_approval);
  if (approvalSteps.length !== plan.approval_gates.length) {
    errors.push('Approval gates count mismatch with approval steps');
  }

  // Check finance operations
  if (plan.category === 'finance' && !plan.requires_human_approval) {
    errors.push('Finance operations must require human approval');
  }

  // Check success criteria
  plan.steps.forEach((step, i) => {
    if (!step.success_criteria) {
      warnings.push(`Step ${i + 1} missing success criteria`);
    }

    if (step.risk_level === 'high' && !step.rollback_steps) {
      warnings.push(`Step ${i + 1} is high-risk but has no rollback plan`);
    }
  });

  return {
    valid: errors.length === 0,
    errors,
    warnings
  };
}

// Validate before execution
const validation = validatePlan(plan);

if (!validation.valid) {
  console.error('❌ Plan validation failed:');
  validation.errors.forEach(err => console.error(`   - ${err}`));
  throw new Error('Invalid plan');
}

if (validation.warnings.length > 0) {
  console.warn('⚠️  Plan warnings:');
  validation.warnings.forEach(warn => console.warn(`   - ${warn}`));
}

console.log('✅ Plan validated successfully');
```

---

## Best Practices

1. **Always define acceptance criteria** - clear "done" definition
2. **Decompose into 3-20 steps** - not too granular, not too high-level
3. **Flag approval gates explicitly** - mark high-risk operations
4. **Include rollback plans** - for destructive operations
5. **Estimate conservatively** - better to overestimate effort
6. **Track dependencies** - ensure correct execution order
7. **Validate before execution** - check plan structure
8. **Update execution log** - maintain audit trail
9. **Handle approvals gracefully** - move files between folders
10. **Never hardcode secrets** - reference only, not actual values

---

## Integration Points

- **Needs Action Triage:** Input metadata for plan generation
- **Task Lifecycle Manager:** Moves plan through stages (Plans → In_Progress → Approved → Done)
- **Orchestrator:** Executes plan step-by-step
- **Human Dashboard:** Review approval gates and execution logs
- **Vault State Manager:** File operations for plan storage
