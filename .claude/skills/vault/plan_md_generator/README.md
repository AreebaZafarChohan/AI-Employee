# Plan MD Generator Skill

**Version:** 1.0.0
**Last Updated:** 2025-02-03

## Overview

The `plan_md_generator` skill transforms triaged Needs_Action items into comprehensive, executable plan.md files. It decomposes high-level tasks into 3-20 actionable steps with checkboxes, identifies approval requirements, estimates effort, and provides structured guidance for both automated execution and human oversight.

## Quick Start

### Basic Usage

```javascript
const { generatePlan } = require('./plan_md_generator');

// Input: triaged item
const triageData = {
  category: 'email',
  priority_score: 8,
  metadata: {
    subject: 'URGENT: Production server down',
    deadline: '2025-02-03T10:30:00Z'
  },
  summary: 'Production API server unresponsive',
  requires_human_approval: false
};

// Generate plan
const result = await generatePlan({
  triageData: triageData,
  agentName: 'lex',
  includeRollback: true,
  estimateEffort: true
});

console.log(`Plan created: ${result.plan_file_path}`);
console.log(`Steps: ${result.plan_content.steps.length}`);
console.log(`Duration: ${result.plan_content.estimated_duration_minutes} min`);
```

### Configuration

Add to `.env`:

```bash
# Required
VAULT_PATH="/absolute/path/to/vault"

# Optional
PLAN_MAX_STEPS="20"                        # Max steps per plan
PLAN_MIN_STEPS="3"                         # Min steps (enforce decomposition)
PLAN_AUTO_APPROVE_THRESHOLD="bronze"       # Auto-approve tier
PLAN_REQUIRE_HUMAN_APPROVAL="payment,delete,drop"  # High-risk keywords
PLAN_ESTIMATE_EFFORT="true"                # Calculate time estimates
PLAN_INCLUDE_ROLLBACK="true"               # Add rollback for risky ops
```

## Key Features

- **Intelligent Decomposition**: Breaks tasks into 3-20 atomic steps
- **Approval Gate Detection**: Identifies high-risk operations requiring human review
- **Effort Estimation**: Conservative time estimates (low/medium/high)
- **Risk Assessment**: Evaluates severity and provides mitigation strategies
- **Rollback Plans**: Undo procedures for destructive operations
- **Category-Specific**: Custom decomposition for email, finance, file_drop, etc.
- **Dependency Tracking**: Ensures correct execution order
- **Execution Logging**: Append-only audit trail

## Plan Structure

```json
{
  "plan_id": "plan-1738587600-abc123",
  "goal": "Resolve production server outage",
  "context": "Server unresponsive since 08:30 UTC...",
  "acceptance_criteria": [
    "Service restored",
    "Root cause identified",
    "Incident documented"
  ],
  "estimated_effort": "medium",
  "estimated_duration_minutes": 18,
  "autonomy_tier": "silver",
  "requires_human_approval": false,
  "steps": [
    {
      "id": "step-1",
      "action": "Validate input and gather context",
      "type": "research",
      "status": "pending",
      "requires_approval": false,
      "risk_level": "low",
      "estimated_minutes": 2,
      "success_criteria": "All server details documented"
    },
    {
      "id": "step-2",
      "action": "Check server health status",
      "type": "api_call",
      "risk_level": "low",
      "tools_needed": ["monitoring_api (from .env)"],
      "success_criteria": "Health check returns status"
    }
  ],
  "approval_gates": [
    {
      "step_id": "step-5",
      "reason": "Restarting production service",
      "approver": "human",
      "approved_at": null
    }
  ],
  "risks": [
    {
      "description": "Service interruption during restart",
      "severity": "medium",
      "mitigation": "Use rolling restart or failover"
    }
  ]
}
```

## Step Types

| Type | Description | Typical Duration | Requires Approval |
|------|-------------|------------------|-------------------|
| **research** | Gather information, read docs | 5-8 min | No |
| **api_call** | External API request | 3-5 min | Depends |
| **file_operation** | Read/write files | 2-3 min | If write |
| **notification** | Send email/message | 1-2 min | Yes |
| **approval** | Human review gate | 0 min | Always |
| **validation** | Verify success | 2-3 min | No |

## Approval Requirements

Plans automatically require approval for:

- **Finance operations** (payments, invoices, transfers)
- **Destructive operations** (delete, drop, remove)
- **External communications** (email, notifications)
- **Data modifications** (write, update, import)
- **High-risk operations** (production changes)

## Category-Specific Decomposition

### Email Tasks
```
1. Validate input and gather context
2. Research appropriate response
3. Draft reply email
4. Review for accuracy
5. Send email (requires approval)
6. Verify sent successfully
```

### Finance Tasks
```
1. Validate invoice details
2. Check budget allocation
3. Verify vendor bank details
4. Prepare payment authorization (requires approval)
5. Process payment (requires approval)
6. Update accounting system
7. Verify completion
```

### File Drop Tasks
```
1. Read and parse file
2. Extract key information
3. Validate data format
4. Import data (requires approval)
5. Verify import success
```

## Markdown Output

Plans are saved as human-readable markdown files in `Plans/` folder:

```markdown
# Plan: URGENT: Production server down

**Plan ID:** plan-1738587600-abc123
**Priority:** 8/10
**Estimated Duration:** ~18 minutes
**Requires Approval:** No

## Goal
Diagnose and resolve production API server outage

## Acceptance Criteria
- [ ] Root cause identified
- [ ] Service restored
- [ ] Incident documented

## Steps

### Step 1: Validate input and gather context
- **Type:** research
- **Risk Level:** low
- **Success Criteria:** All server details documented

### Step 5: Restart server
- **Type:** api_call
- **Risk Level:** medium
- **⚠️ REQUIRES APPROVAL:** Restarting production service

**Rollback Steps:**
1. Failover to backup server
2. Rollback recent deployment
```

## Integration

### With Needs Action Triage

```javascript
// Step 1: Triage inbox
const triage = await triageNeedsAction({ minPriorityScore: 5 });

// Step 2: Claim highest-priority task
const item = triage.items[0];
await claimTask(item.file_name, 'lex');

// Step 3: Generate plan
const plan = await generatePlan({
  triageData: item,
  agentName: 'lex'
});

console.log(`Plan ready for execution: ${plan.plan_id}`);
```

### With Task Lifecycle

```javascript
// After plan generation, move to In_Progress
await taskLifecycle.transitionTask(
  plan.plan_id,
  'planned',
  'in_progress',
  'lex'
);

// Execute steps
for (const step of plan.steps) {
  if (step.requires_approval) {
    await requestApproval(plan.plan_id, step.id);
  } else {
    await executeStep(plan.plan_id, step.id);
  }
}
```

## Validation

All plans are validated before saving:

```javascript
const validation = validatePlan(plan);

// Checks:
// - Goal defined
// - Acceptance criteria present
// - 3-20 steps
// - Success criteria for each step
// - Approval gates match approval steps
// - No circular dependencies
// - Finance requires approval
// - High-risk has rollback plans
// - No secrets in content

if (!validation.valid) {
  console.error('Plan validation failed:', validation.errors);
}
```

## Error Handling

```typescript
interface PlanGenerationResult {
  success: boolean;
  plan_id?: string;
  plan_file_path?: string;
  plan_content?: PlanStructure;
  error?: string;
  warnings?: string[];
}
```

**Common Errors:**
- `TOO_MANY_STEPS`: Plan exceeds 20 steps (break into multiple tasks)
- `TOO_FEW_STEPS`: Plan has <3 steps (add validation steps or skip planning)
- `MISSING_APPROVAL_GATE`: Finance/high-risk without approval
- `CIRCULAR_DEPENDENCY`: Steps form cycle
- `NO_ROLLBACK_PLAN`: High-risk without undo procedure
- `SECRET_DETECTED`: Actual credentials in plan

## Performance

**Benchmarks:**
- Simple plan (3-5 steps): <5 seconds
- Complex plan (15-20 steps): <15 seconds
- Finance plan (with approval): <10 seconds

**Optimization:**
- Use rule-based decomposition (fast, no LLM needed)
- Optional LLM for complex tasks
- Template-based generation for common categories

## Security

**Secret Protection:**
- Never includes actual API keys or passwords
- Only references: "stripe_api_key (from .env)"
- Regex-based secret detection
- Validation before saving

**Approval Enforcement:**
- Finance operations always require approval
- Destructive operations flagged automatically
- High-risk keywords trigger approval gates
- Multiple approval levels for critical operations

## Documentation

- **SKILL.md**: Complete skill specification
- **patterns.md**: Code examples and usage patterns
- **gotchas.md**: Common issues and edge cases
- **impact-checklist.md**: Deployment and validation checklist
- **EXAMPLES.md**: End-to-end workflow examples

## Support

For issues or questions:
1. Check `gotchas.md` for known issues
2. Review `patterns.md` for examples
3. Consult `impact-checklist.md` for troubleshooting
4. Contact: Digital FTE team

## License

Part of the Digital FTE Agent System.
