# Plan MD Generator - Gotchas & Pitfalls

This document lists common issues, edge cases, and failure modes when using the `plan_md_generator` skill.

---

## Gotcha 1: Over-Granular Decomposition

**Problem:**

Plan contains 50+ micro-steps that make it unreadable and unmanageable.

**Symptom:**
```
Generated plan has 73 steps:
Step 1: Open browser
Step 2: Navigate to URL
Step 3: Wait for page load
Step 4: Click login button
... (69 more steps)
```

**Root Cause:**

- Decomposition too fine-grained
- Treating clicks/keystrokes as separate steps
- No grouping of related actions

**Mitigation:**

```javascript
// WRONG - too granular
steps = [
  "Open email client",
  "Navigate to inbox",
  "Find email",
  "Click reply button",
  "Type response",
  "Click send"
];

// CORRECT - atomic but meaningful
steps = [
  "Read and understand email context",
  "Draft appropriate response",
  "Send reply email"
];
```

**Prevention:**

- Enforce max 20 steps per plan
- Group UI interactions into logical actions
- Focus on "what" not "how"
- Each step should have clear business value

---

## Gotcha 2: Missing Approval Gates for Finance

**Problem:**

Financial operations generated without human approval requirement.

**Symptom:**
```
Plan: Process $10,000 payment
requires_human_approval: false  // DANGEROUS!
```

**Root Cause:**

- Category detection failed (classified as 'general' instead of 'finance')
- Approval gate logic doesn't check financial amounts
- Override flag set incorrectly

**Mitigation:**

```javascript
// Add safety check before generating plan
function enforceFinanceApproval(triageData, plan) {
  // Rule 1: Category check
  if (triageData.category === 'finance') {
    plan.requires_human_approval = true;
  }

  // Rule 2: Amount check
  if (triageData.metadata.financial_amount > 100) {
    plan.requires_human_approval = true;
  }

  // Rule 3: Keyword check
  const financialKeywords = ['payment', 'invoice', 'transfer', 'charge', '$'];
  const content = plan.goal + plan.context;
  if (financialKeywords.some(kw => content.toLowerCase().includes(kw))) {
    plan.requires_human_approval = true;
  }

  return plan;
}
```

**Prevention:**

- Always check category === 'finance'
- Check for financial amounts in metadata
- Scan goal/context for money keywords ($, payment, invoice)
- Default to requiring approval if uncertain

---

## Gotcha 3: Steps Without Success Criteria

**Problem:**

Steps lack clear verification criteria, making execution ambiguous.

**Symptom:**
```
Step 5: Fetch data from API
// No success_criteria field - how do we know it worked?
```

**Root Cause:**

- Generator skips success criteria for "obvious" steps
- Template doesn't enforce required field
- No validation before saving plan

**Mitigation:**

```javascript
// Validate each step has success criteria
function validateStepCompleteness(step) {
  if (!step.success_criteria) {
    // Auto-generate based on type
    switch (step.type) {
      case 'api_call':
        step.success_criteria = 'API returns 200 status and valid response';
        break;
      case 'file_operation':
        step.success_criteria = 'File operation completes without errors';
        break;
      case 'research':
        step.success_criteria = 'Required information gathered and documented';
        break;
      default:
        step.success_criteria = 'Step completes successfully';
    }
  }
  return step;
}
```

**Prevention:**

- Make success_criteria a required field
- Auto-generate defaults based on step type
- Validate plan before saving
- Reject plans with missing criteria

---

## Gotcha 4: Circular Dependencies

**Problem:**

Step A depends on Step B, which depends on Step A.

**Symptom:**
```
Step 3: dependencies: ["step-5"]
Step 5: dependencies: ["step-3"]
// Deadlock! Cannot execute either step
```

**Root Cause:**

- Dependency graph not validated
- Manual edits created cycle
- LLM hallucinated invalid dependencies

**Mitigation:**

```javascript
function detectCircularDependencies(steps) {
  const visited = new Set();
  const recursionStack = new Set();

  function hasCycle(stepId) {
    if (recursionStack.has(stepId)) {
      return true;  // Cycle detected
    }

    if (visited.has(stepId)) {
      return false;  // Already checked
    }

    visited.add(stepId);
    recursionStack.add(stepId);

    const step = steps.find(s => s.id === stepId);
    if (step && step.dependencies) {
      for (const depId of step.dependencies) {
        if (hasCycle(depId)) {
          return true;
        }
      }
    }

    recursionStack.delete(stepId);
    return false;
  }

  for (const step of steps) {
    if (hasCycle(step.id)) {
      throw new Error(`Circular dependency detected involving ${step.id}`);
    }
  }

  return false;  // No cycles
}
```

**Prevention:**

- Validate dependency graph before saving
- Detect cycles using DFS
- Only allow forward dependencies (step N depends on step < N)
- Reject plans with circular deps

---

## Gotcha 5: No Rollback Plan for Destructive Operations

**Problem:**

High-risk operations lack rollback instructions.

**Symptom:**
```
Step 7: Delete old database records
risk_level: high
// No rollback_steps - can't undo!
```

**Root Cause:**

- Generator doesn't create rollback steps automatically
- Template makes rollback_steps optional
- Risk assessment incomplete

**Mitigation:**

```javascript
function enforceRollbackPlans(step) {
  const destructiveKeywords = ['delete', 'drop', 'remove', 'destroy'];
  const isDestructive = destructiveKeywords.some(kw =>
    step.action.toLowerCase().includes(kw)
  );

  if (isDestructive || step.risk_level === 'high') {
    if (!step.rollback_steps || step.rollback_steps.length === 0) {
      // Auto-generate basic rollback
      step.rollback_steps = [
        'Restore from backup taken before operation',
        'Verify data integrity after restoration',
        'Document incident in error log'
      ];
      console.warn(`Auto-generated rollback for high-risk step: ${step.id}`);
    }
  }

  return step;
}
```

**Prevention:**

- Make rollback_steps required for high-risk operations
- Auto-generate generic rollback if missing
- Validate rollback feasibility (e.g., backup exists)
- Flag plans without rollback for review

---

## Gotcha 6: Hardcoded Secrets in Plan

**Problem:**

Actual API keys or passwords appear in plan files.

**Symptom:**
```
tools_needed: ["stripe_api_key=sk_live_abc123xyz"]  // LEAKED!
```

**Root Cause:**

- LLM included example secrets
- Copy-pasted from Needs_Action item containing secret
- Template doesn't sanitize input

**Mitigation:**

```javascript
function sanitizeSecrets(plan) {
  const secretPatterns = [
    /sk_live_[a-zA-Z0-9]+/g,        // Stripe keys
    /[a-zA-Z0-9]{32,}/g,             // Long hex strings
    /AIza[a-zA-Z0-9-_]{35}/g,        // Google API keys
    /[A-Z0-9]{20}/g,                 // AWS access keys
    /password\s*[:=]\s*\S+/gi        // Password fields
  ];

  const planStr = JSON.stringify(plan);

  secretPatterns.forEach(pattern => {
    if (pattern.test(planStr)) {
      throw new Error('Secret detected in plan! Remove before saving.');
    }
  });

  return plan;
}
```

**Prevention:**

- Scan plan content for secret patterns
- Never include actual credentials, only references
- Format: "stripe_api_key (from .env)" not "stripe_api_key=sk_live_..."
- Validate before writing to Plans/ folder

---

## Gotcha 7: Approval Gate Missing from approval_gates Array

**Problem:**

Step marked `requires_approval: true` but no corresponding entry in `approval_gates` array.

**Symptom:**
```
steps: [
  { id: "step-5", requires_approval: true }
]
approval_gates: []  // Missing!
```

**Root Cause:**

- Generator creates steps but forgets approval_gates
- Manual edit removed gate but left step flag
- Inconsistent state

**Mitigation:**

```javascript
function syncApprovalGates(plan) {
  const approvalSteps = plan.steps.filter(s => s.requires_approval);

  // Rebuild approval_gates from scratch
  plan.approval_gates = approvalSteps.map(step => ({
    step_id: step.id,
    reason: step.action.includes('payment') ? 'Financial operation' :
            step.action.includes('send') ? 'External communication' :
            'High-risk operation',
    approver: 'human',
    approved_at: null,
    approved_by: null
  }));

  return plan;
}
```

**Prevention:**

- Auto-generate approval_gates from steps
- Validate count matches (approval steps === approval gates)
- Reject plans with mismatched counts
- Re-sync on every plan update

---

## Gotcha 8: Unrealistic Effort Estimates

**Problem:**

Estimate is way off (claims 2 minutes but actually takes 30).

**Symptom:**
```
estimated_duration_minutes: 2
// Actually took 28 minutes to complete
```

**Root Cause:**

- Formula too optimistic
- Doesn't account for API latency
- Human review time not included
- Dependencies underestimated

**Mitigation:**

```javascript
function estimateConservatively(step) {
  // Base estimates (conservative)
  const baseEstimates = {
    research: 8,        // Not 5
    api_call: 5,        // Not 3
    file_operation: 3,  // Not 2
    notification: 2,    // Not 1
    validation: 3       // Not 2
  };

  let estimate = baseEstimates[step.type] || 8;

  // Complexity multipliers
  if (step.tools_needed && step.tools_needed.length > 1) {
    estimate *= 1.8;  // More aggressive than 1.5
  }

  if (step.dependencies && step.dependencies.length > 0) {
    estimate += step.dependencies.length * 2;  // Wait time
  }

  if (step.risk_level === 'high') {
    estimate *= 1.5;  // Extra caution
  }

  // Round up to nearest 5
  return Math.ceil(estimate / 5) * 5;
}
```

**Prevention:**

- Use conservative base estimates
- Add buffer for complexity
- Round up, not down
- Track actual vs estimated (learn over time)

---

## Gotcha 9: Single-Step "Plans"

**Problem:**

Plan has only one step, defeating the purpose of planning.

**Symptom:**
```
steps: [
  { action: "Reply to email" }
]
// Not decomposed at all!
```

**Root Cause:**

- Generator failed to decompose
- Input too simple (trivial task)
- Min steps check not enforced

**Mitigation:**

```javascript
function enforceMinimumDecomposition(plan) {
  if (plan.steps.length < 3) {
    throw new Error(
      `Plan must have at least 3 steps (has ${plan.steps.length}). ` +
      `Task may be too simple for planning.`
    );
  }

  // Auto-expand if possible
  if (plan.steps.length === 1) {
    const originalStep = plan.steps[0];

    plan.steps = [
      {
        id: 'step-1',
        action: 'Validate input and gather context',
        type: 'research'
      },
      {
        id: 'step-2',
        action: originalStep.action,
        type: originalStep.type
      },
      {
        id: 'step-3',
        action: 'Verify task completion',
        type: 'validation'
      }
    ];
  }

  return plan;
}
```

**Prevention:**

- Enforce minimum 3 steps
- Always include: validation → action → verification
- Reject plans with single step
- Consider if task needs planning at all

---

## Gotcha 10: LLM Hallucinated Steps

**Problem:**

LLM generates steps that reference non-existent APIs or tools.

**Symptom:**
```
Step 4: Call the WidgetMaker API
tools_needed: ["widget_api"]
// WidgetMaker API doesn't exist!
```

**Root Cause:**

- LLM invented plausible-sounding API
- No validation against available tools
- Context didn't include tool inventory

**Mitigation:**

```javascript
const AVAILABLE_TOOLS = [
  'email_api',
  'calendar_api',
  'stripe_api',
  'quickbooks_api',
  'slack_api',
  'monitoring_api'
];

function validateToolsExist(plan) {
  const unknownTools = new Set();

  plan.steps.forEach(step => {
    if (step.tools_needed) {
      step.tools_needed.forEach(tool => {
        // Extract tool name (before " (from .env)")
        const toolName = tool.split(' ')[0];

        if (!AVAILABLE_TOOLS.includes(toolName)) {
          unknownTools.add(toolName);
        }
      });
    }
  });

  if (unknownTools.size > 0) {
    throw new Error(
      `Plan references unknown tools: ${Array.from(unknownTools).join(', ')}`
    );
  }

  return plan;
}
```

**Prevention:**

- Maintain tool inventory
- Validate tools_needed against inventory
- Provide tool list in LLM context
- Reject plans with unknown tools

---

## Gotcha 11: Approval Gate Never Checked

**Problem:**

Plan moved to execution without waiting for approval.

**Symptom:**
```
Step 5: Process payment (requires_approval: true)
// Executed without human review!
```

**Root Cause:**

- Executor skipped approval check
- Plan moved from Pending_Approval to In_Progress prematurely
- Approval gate status not validated

**Mitigation:**

```javascript
async function executeStepSafely(plan, step) {
  // Check if step requires approval
  if (step.requires_approval) {
    const gate = plan.approval_gates.find(g => g.step_id === step.id);

    if (!gate) {
      throw new Error(`Step ${step.id} requires approval but no gate defined`);
    }

    if (!gate.approved_at) {
      throw new Error(
        `Cannot execute ${step.id}: approval pending. ` +
        `Plan must be in Approved/ folder first.`
      );
    }

    console.log(`✅ Step ${step.id} approved by ${gate.approved_by} at ${gate.approved_at}`);
  }

  // Proceed with execution
  return await executeStep(step);
}
```

**Prevention:**

- Always check approval status before execution
- Validate plan is in Approved/ folder (not Pending_Approval/)
- Reject execution if approval missing
- Log approval checks for audit

---

## Gotcha 12: Stale Plan Executed

**Problem:**

Plan generated days ago executed without review, context may have changed.

**Symptom:**
```
Plan created: 2025-01-28
Executed: 2025-02-03  (6 days later)
// Situation may have changed!
```

**Root Cause:**

- No staleness check
- Plan sat in Plans/ folder for days
- Context changed but plan not updated

**Mitigation:**

```javascript
function checkPlanStaleness(plan, maxAgeDays = 2) {
  const createdAt = new Date(plan.created_at);
  const now = new Date();
  const ageHours = (now - createdAt) / (1000 * 60 * 60);
  const ageDays = ageHours / 24;

  if (ageDays > maxAgeDays) {
    throw new Error(
      `Plan is stale (${ageDays.toFixed(1)} days old). ` +
      `Review and regenerate before executing.`
    );
  }

  return plan;
}
```

**Prevention:**

- Check plan age before execution
- Reject plans older than 2 days
- Prompt human to review/regenerate stale plans
- Add "expires_at" field to plans

---

## Common Error Codes

| Code | Meaning | Recovery |
|------|---------|----------|
| `TOO_MANY_STEPS` | Plan exceeds 20 steps | Break into multiple tasks |
| `TOO_FEW_STEPS` | Plan has <3 steps | Add validation/verification steps or skip planning |
| `MISSING_APPROVAL_GATE` | Finance/high-risk without approval | Force requires_human_approval = true |
| `CIRCULAR_DEPENDENCY` | Step dependencies form cycle | Reorder steps, break cycle |
| `NO_ROLLBACK_PLAN` | High-risk step without rollback | Add generic rollback or reject |
| `SECRET_DETECTED` | Actual credentials in plan | Sanitize, replace with references |
| `UNKNOWN_TOOL` | References non-existent API/tool | Remove or replace with valid tool |
| `STALE_PLAN` | Plan older than 2 days | Regenerate plan |
| `APPROVAL_NOT_GRANTED` | Executing step without approval | Wait for approval, halt execution |

---

## Debugging Tips

1. **Validate plan structure:** Run validation before saving
2. **Check approval gates:** Ensure count matches approval steps
3. **Verify dependencies:** No cycles, all referenced steps exist
4. **Test effort estimates:** Compare actual vs estimated
5. **Scan for secrets:** Grep for API keys, passwords
6. **Check step count:** 3-20 steps (reject outliers)
7. **Review success criteria:** Every step should have clear criteria
8. **Verify tools exist:** Cross-check against tool inventory
9. **Check staleness:** Plans >2 days old need review
10. **Audit approval flow:** Track all approval gates through execution

---

## Performance Issues

### Issue: Plan generation takes >30 seconds

**Causes:**
- LLM API slow or rate-limited
- Complex task requires extensive decomposition
- Too many steps generated (>50)

**Solutions:**
- Use faster model (Haiku instead of Sonnet)
- Reduce max_tokens limit
- Simplify task before planning
- Cache common plan templates

### Issue: Plans stored as large files (>1MB)

**Causes:**
- Execution log too verbose
- Steps have long descriptions
- LLM included unnecessary detail

**Solutions:**
- Truncate execution log (keep last 50 entries)
- Limit step descriptions to 200 chars
- Remove verbose LLM output before saving

---

## Security Issues

### Issue: Plan exposes sensitive information

**Mitigation:**
- Never log financial amounts in public logs
- Redact sender emails in summaries
- Replace actual secrets with references
- Sanitize plan content before archiving

### Issue: Malicious plan injected

**Mitigation:**
- Validate all step actions against whitelist
- Reject plans with shell commands
- Scan for code injection patterns
- Require approval for all file operations
