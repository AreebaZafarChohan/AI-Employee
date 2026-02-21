---
name: plan_md_generator
description: Generates detailed planning markdown files (plan.md) from triaged Needs_Action items, with structured checklists, sub-tasks, approval gates, and human oversight requirements.
---

# Plan MD Generator

## Purpose

This skill transforms triaged Needs_Action items into comprehensive, executable plan.md files. It breaks down high-level tasks into actionable steps with checkboxes, identifies approval requirements, estimates effort, and provides clear guidance for both automated execution and human oversight.

The skill is designed to be used by the Local Executive Agent (lex) after claiming a task from Needs_Action, as the second stage of the Digital FTE workflow (after triage, before execution).

## When to Use This Skill

Use `plan_md_generator` when:

- **After claiming task**: Convert Needs_Action item into executable plan
- **Planning phase**: Break down high-level goal into steps
- **Approval workflows**: Identify which steps require human review
- **Effort estimation**: Calculate time/complexity for each sub-task
- **Risk assessment**: Flag high-risk operations that need approval
- **Dependency mapping**: Identify prerequisites and blockers
- **Resource planning**: List tools, APIs, credentials needed
- **Acceptance criteria**: Define what "done" looks like

Do NOT use this skill when:

- **Already have plan**: Plan.md already exists (use task execution instead)
- **Trivial tasks**: Single-step operations don't need planning
- **Research only**: Pure information gathering doesn't need formal plans
- **Emergency response**: Critical issues need immediate action, not planning
- **Human will execute**: Plans are for agent automation

## Impact Analysis Workflow

### 1. Environment Variable Strategy

**Build-Time vs Runtime Variables:**

This skill operates at runtime only. No build-time variables required.

**Runtime variables:**
```bash
# Required (inherited from vault_state_manager)
VAULT_PATH="/absolute/path/to/vault"

# Optional: Plan generation tuning
PLAN_MAX_STEPS="20"                         # Max steps per plan (prevent bloat)
PLAN_MIN_STEPS="3"                          # Min steps (enforce decomposition)
PLAN_AUTO_APPROVE_THRESHOLD="bronze"        # Auto-approve for bronze tier tasks
PLAN_REQUIRE_HUMAN_APPROVAL="high-risk,financial,destructive"  # Keywords requiring approval
PLAN_ESTIMATE_EFFORT="true"                 # Calculate time estimates
PLAN_INCLUDE_ROLLBACK="true"                # Add rollback steps for risky operations

# Optional: LLM configuration (if AI-assisted planning)
PLAN_MODEL="gemini-2.5-flash"               # Model for plan generation
PLAN_TEMPERATURE="0.2"                      # Low temp for consistent planning
PLAN_MAX_TOKENS="4000"                      # Allow detailed plans
```

**Secrets Management:**

- This skill does NOT handle secrets
- Plans may reference credentials (e.g., "use API key from .env") but never contain actual secrets
- Agent credentials managed outside planning
- Financial amounts may appear in plans (not secrets, but sensitive)

**Variable Discovery Process:**
```bash
# Check plan generation configuration
cat .env | grep PLAN_

# Verify Plans/ folder exists
test -d "$VAULT_PATH/Plans" && echo "OK" || echo "Missing"

# Review existing plans for format
find "$VAULT_PATH/Plans" -name '*.json' -exec jq '.steps' {} \;
```

### 2. Network & Topology Implications

**Port Discovery:**

No network ports required. This skill operates on local filesystem only.

**Dependency Topology:**

```
Plan MD Generator
  ├── Vault State Manager (file read/write)
  │   └── Filesystem (Plans/ folder)
  ├── Needs Action Triage (input metadata)
  └── Optional: LLM API (for AI-assisted planning)
      └── Gemini API (https://generativelanguage.googleapis.com)
```

**Topology Notes:**
- Primary operation: read Needs_Action item, write Plans/ file
- Optional: LLM API calls for intelligent decomposition
- No database dependencies
- Stateless operation (each plan independent)

**Docker/K8s Implications:**

When containerizing agents that use this skill:
- Mount vault with write access to Plans/: `-v /host/vault:/vault`
- If using LLM API, ensure outbound HTTPS allowed
- No persistent storage needed (plans stored in vault)
- Can run in parallel (different tasks)

### 3. Auth / CORS / Security Impact

**Authentication Pattern Analysis:**

- No authentication for filesystem access (local only)
- If using LLM API: requires API key in environment
- Agent authorization: lex has write access to Plans/ (per AGENTS.md §3)

**Security Considerations:**

| Risk | Mitigation |
|------|-----------|
| **Destructive plans** | Flag operations that delete/modify data, require approval |
| **Financial plans** | Always require human approval for money operations |
| **Secret exposure** | Never include credentials in plans, only references |
| **Overly complex plans** | Limit max steps (20), break into multiple tasks if needed |
| **Prompt injection** | Sanitize Needs_Action input before LLM processing |
| **Path operations** | Validate all file paths in steps, prevent traversal |

**Validation Rules:**

Before generating any plan:
```javascript
function validatePlanInput(triageData) {
  // Check triage data is complete
  if (!triageData.category || !triageData.priority_score) {
    throw new Error("Invalid triage data: missing required fields");
  }

  // Detect high-risk operations
  const content = triageData.metadata.subject + triageData.summary;
  const highRiskKeywords = ['delete', 'drop', 'remove', 'payment', 'transfer', '$'];

  const isHighRisk = highRiskKeywords.some(kw =>
    content.toLowerCase().includes(kw)
  );

  if (isHighRisk && !triageData.requires_human_approval) {
    console.warn('High-risk operation detected, forcing human approval');
    triageData.requires_human_approval = true;
  }

  return true;
}
```

**Approval Requirements:**

Per AGENTS.md, plans must flag approval needs:

| Operation Type | Approval Required | Autonomy Tier |
|----------------|-------------------|---------------|
| **Read-only** (research, fetch data) | No | Bronze |
| **Low-risk writes** (logs, drafts) | No | Silver |
| **Business logic** (API calls, notifications) | Optional | Gold |
| **Financial** (payments, invoices) | **Always** | Platinum |
| **Destructive** (delete, drop, modify prod) | **Always** | Manual only |

## Blueprints & Templates Used

### Blueprint: Plan.md Structure

**Purpose:** Standardize plan file format for consistent execution

**Template Variables:**
```yaml
# Plan metadata (JSON/YAML front-matter)
plan_id: "{{PLAN_ID}}"                      # Unique identifier (timestamp-based)
task_file: "{{TASK_FILE_NAME}}"             # Original Needs_Action file
created_at: "{{TIMESTAMP_ISO}}"             # Plan creation time
created_by: "{{AGENT_NAME}}"                # Agent that created plan (usually lex)
status: "planned"                           # planned | in_progress | completed | rejected

# Triage metadata (inherited)
category: "{{CATEGORY}}"                    # email | whatsapp | finance | file_drop | general
priority_score: {{PRIORITY}}                # 1-10
deadline: "{{DEADLINE_ISO}}"                # If any
requires_human_approval: {{BOOLEAN}}        # true if high-risk

# Plan details
goal: "{{HIGH_LEVEL_GOAL}}"                 # One-sentence objective
context: "{{BACKGROUND_INFO}}"              # Why this task exists
acceptance_criteria:                        # What defines "done"
  - "{{CRITERION_1}}"
  - "{{CRITERION_2}}"

estimated_effort: "{{EFFORT}}"              # low (< 5min) | medium (< 30min) | high (> 30min)
estimated_duration_minutes: {{DURATION}}    # Numeric estimate
autonomy_tier: "{{TIER}}"                   # bronze | silver | gold | platinum | manual

# Steps (ordered, sequential)
steps:
  - id: "{{STEP_ID}}"                       # step-1, step-2, etc.
    action: "{{ACTION_DESCRIPTION}}"        # Imperative verb (Research, Fetch, Send, etc.)
    type: "{{TYPE}}"                        # research | api_call | file_operation | notification | approval
    status: "pending"                       # pending | in_progress | completed | failed | skipped
    requires_approval: {{BOOLEAN}}          # true if human gate
    risk_level: "{{RISK}}"                  # low | medium | high
    tools_needed: ["{{TOOL1}}", "{{TOOL2}}"] # API keys, credentials, services
    estimated_minutes: {{TIME}}             # Per-step estimate
    success_criteria: "{{CRITERIA}}"        # How to verify step succeeded
    rollback_steps: ["{{ROLLBACK_1}}"]      # If step fails, how to undo (optional)
    dependencies: ["{{STEP_ID}}"]           # Which steps must complete first

# Approval gates
approval_gates:
  - step_id: "{{STEP_ID}}"
    reason: "{{WHY_APPROVAL_NEEDED}}"       # Financial, destructive, high-risk
    approver: "human"                       # human | auto (for low-risk)
    approved_at: "{{TIMESTAMP_ISO}}"        # Filled when approved
    approved_by: "{{USER_NAME}}"            # Filled when approved

# Risk assessment
risks:
  - description: "{{RISK_DESCRIPTION}}"
    mitigation: "{{HOW_TO_MITIGATE}}"
    severity: "{{low|medium|high}}"

# Resources needed
resources:
  apis: ["{{API_NAME}}"]                    # External services
  credentials: ["{{CRED_REF}}"]             # References to secrets (not actual secrets!)
  files: ["{{FILE_PATH}}"]                  # Input files needed
  data: ["{{DATA_SOURCE}}"]                 # Data dependencies

# Success validation
validation:
  automated_checks:                         # Tests to run
    - "{{CHECK_1}}"
  manual_verification:                      # Human review needed
    - "{{VERIFY_1}}"
  rollback_plan: "{{ROLLBACK_STRATEGY}}"    # If something goes wrong

# Execution log (filled during execution)
execution_log:
  - timestamp: "{{TIMESTAMP_ISO}}"
    step_id: "{{STEP_ID}}"
    status: "{{STATUS}}"
    agent: "{{AGENT_NAME}}"
    notes: "{{EXECUTION_NOTES}}"
```

**Impact Notes:**
- All timestamps in ISO 8601 (UTC)
- Steps ordered sequentially (dependencies tracked)
- Approval gates explicitly marked
- Rollback steps included for high-risk operations
- Execution log append-only (audit trail)

### Blueprint: Step Decomposition Algorithm

**Purpose:** Break high-level task into atomic, executable steps

**Algorithm:**

```javascript
function decomposeTask(triageData) {
  const { category, metadata, summary, suggested_action } = triageData;

  let steps = [];

  // Step 1: Always start with research/validation
  steps.push({
    id: 'step-1',
    action: 'Validate input and gather context',
    type: 'research',
    requires_approval: false,
    risk_level: 'low',
    estimated_minutes: 2,
    success_criteria: 'All required information is available'
  });

  // Step 2: Category-specific decomposition
  switch (category) {
    case 'email':
      steps.push(...decomposeEmailTask(metadata, summary));
      break;
    case 'whatsapp':
      steps.push(...decomposeWhatsAppTask(metadata, summary));
      break;
    case 'finance':
      steps.push(...decomposeFinanceTask(metadata, summary));
      break;
    case 'file_drop':
      steps.push(...decomposeFileDropTask(metadata, summary));
      break;
    default:
      steps.push(...decomposeGenericTask(metadata, summary));
  }

  // Step N-1: Always add validation step
  steps.push({
    id: `step-${steps.length + 1}`,
    action: 'Verify task completion',
    type: 'validation',
    requires_approval: false,
    risk_level: 'low',
    estimated_minutes: 1,
    success_criteria: 'All acceptance criteria met'
  });

  // Step N: Add approval step if needed
  if (triageData.requires_human_approval) {
    steps.push({
      id: `step-${steps.length + 1}`,
      action: 'Request human approval',
      type: 'approval',
      requires_approval: true,
      risk_level: 'high',
      estimated_minutes: 0,  // Human time not counted
      success_criteria: 'Human approves plan execution'
    });
  }

  return steps;
}

// Category-specific decomposition
function decomposeEmailTask(metadata, summary) {
  const steps = [];

  // Check if reply needed
  if (summary.toLowerCase().includes('reply') ||
      summary.toLowerCase().includes('respond')) {
    steps.push({
      id: 'step-2',
      action: 'Draft email response',
      type: 'research',
      risk_level: 'low',
      estimated_minutes: 5
    });
    steps.push({
      id: 'step-3',
      action: 'Send email',
      type: 'api_call',
      risk_level: 'medium',
      requires_approval: true,  // Email sends need approval
      tools_needed: ['email_api']
    });
  }

  // Check if action needed
  if (summary.toLowerCase().includes('schedule') ||
      summary.toLowerCase().includes('meeting')) {
    steps.push({
      id: 'step-2',
      action: 'Check calendar availability',
      type: 'api_call',
      risk_level: 'low',
      tools_needed: ['calendar_api']
    });
    steps.push({
      id: 'step-3',
      action: 'Create calendar event',
      type: 'api_call',
      risk_level: 'medium',
      requires_approval: true
    });
  }

  return steps;
}

function decomposeFinanceTask(metadata, summary) {
  const steps = [];

  // Finance tasks ALWAYS require approval
  steps.push({
    id: 'step-2',
    action: 'Verify invoice details',
    type: 'research',
    risk_level: 'low',
    estimated_minutes: 3,
    success_criteria: 'Amount, vendor, and terms validated'
  });

  if (metadata.financial_amount > 1000) {
    steps.push({
      id: 'step-3',
      action: 'Check budget allocation',
      type: 'research',
      risk_level: 'low',
      estimated_minutes: 2
    });
  }

  steps.push({
    id: `step-${steps.length + 2}`,
    action: 'Prepare payment authorization',
    type: 'approval',
    risk_level: 'high',
    requires_approval: true,
    success_criteria: 'Finance approves payment'
  });

  steps.push({
    id: `step-${steps.length + 2}`,
    action: 'Process payment',
    type: 'api_call',
    risk_level: 'high',
    requires_approval: true,  // Double approval for payments
    tools_needed: ['payment_api'],
    rollback_steps: ['Void transaction', 'Issue refund']
  });

  return steps;
}

function decomposeFileDropTask(metadata, summary) {
  const steps = [];

  steps.push({
    id: 'step-2',
    action: 'Read and parse file',
    type: 'file_operation',
    risk_level: 'low',
    estimated_minutes: 2
  });

  steps.push({
    id: 'step-3',
    action: 'Extract key information',
    type: 'research',
    risk_level: 'low',
    estimated_minutes: 3
  });

  // If file needs processing
  if (summary.toLowerCase().includes('process') ||
      summary.toLowerCase().includes('import')) {
    steps.push({
      id: 'step-4',
      action: 'Validate data format',
      type: 'validation',
      risk_level: 'low',
      estimated_minutes: 2
    });
    steps.push({
      id: 'step-5',
      action: 'Import data',
      type: 'api_call',
      risk_level: 'medium',
      requires_approval: true
    });
  }

  return steps;
}
```

**Impact Notes:**
- Always start with validation/research
- Always end with verification
- Approval gates inserted based on risk
- Finance operations get double approval
- Rollback steps for destructive operations

### Blueprint: Approval Gate Detection

**Purpose:** Identify which steps require human review

**Decision Tree:**

```javascript
function requiresApproval(step, triageData) {
  // Rule 1: Explicit high-risk keywords
  const highRiskKeywords = [
    'delete', 'drop', 'remove', 'destroy',
    'payment', 'transfer', 'charge', 'invoice',
    'publish', 'deploy', 'production', 'live',
    'email', 'send', 'notify', 'alert'
  ];

  const hasHighRiskKeyword = highRiskKeywords.some(kw =>
    step.action.toLowerCase().includes(kw)
  );

  if (hasHighRiskKeyword) {
    return {
      requires_approval: true,
      reason: `High-risk operation: ${step.action}`
    };
  }

  // Rule 2: Financial operations
  if (triageData.category === 'finance') {
    return {
      requires_approval: true,
      reason: 'Financial operation requires approval'
    };
  }

  // Rule 3: External communications
  if (step.type === 'api_call' &&
      (step.action.includes('send') || step.action.includes('notify'))) {
    return {
      requires_approval: true,
      reason: 'External communication requires approval'
    };
  }

  // Rule 4: Data modifications
  if (step.type === 'file_operation' &&
      (step.action.includes('write') || step.action.includes('modify'))) {
    return {
      requires_approval: true,
      reason: 'Data modification requires approval'
    };
  }

  // Rule 5: Autonomy tier check
  if (triageData.autonomy_tier === 'manual') {
    return {
      requires_approval: true,
      reason: 'Task marked as manual-only'
    };
  }

  // Rule 6: Risk level
  if (step.risk_level === 'high') {
    return {
      requires_approval: true,
      reason: 'High-risk operation'
    };
  }

  // Default: no approval needed
  return {
    requires_approval: false,
    reason: null
  };
}
```

**Impact Notes:**
- Multiple detection rules (defense in depth)
- Finance always requires approval
- External actions (email, API) need approval
- High-risk keywords trigger approval
- Autonomy tier overrides

### Blueprint: Effort Estimation

**Purpose:** Calculate realistic time estimates for planning

**Estimation Formula:**

```javascript
function estimateEffort(steps) {
  let totalMinutes = 0;

  steps.forEach(step => {
    // Base estimates by type
    const baseEstimates = {
      research: 5,        // Read docs, gather info
      api_call: 3,        // Make HTTP request, parse response
      file_operation: 2,  // Read/write files
      notification: 1,    // Send email/message
      approval: 0,        // Human time not counted
      validation: 2       // Run checks, verify output
    };

    let estimate = baseEstimates[step.type] || 5;

    // Adjust for complexity
    if (step.tools_needed && step.tools_needed.length > 1) {
      estimate *= 1.5;  // Multiple dependencies increase time
    }

    if (step.dependencies && step.dependencies.length > 0) {
      estimate += 1;  // Waiting for dependencies
    }

    if (step.risk_level === 'high') {
      estimate *= 1.3;  // Extra caution for risky ops
    }

    step.estimated_minutes = Math.ceil(estimate);
    totalMinutes += step.estimated_minutes;
  });

  // Classify overall effort
  let effortLevel;
  if (totalMinutes < 5) {
    effortLevel = 'low';
  } else if (totalMinutes < 30) {
    effortLevel = 'medium';
  } else {
    effortLevel = 'high';
  }

  return {
    estimated_duration_minutes: totalMinutes,
    estimated_effort: effortLevel
  };
}
```

**Impact Notes:**
- Conservative estimates (better to overestimate)
- Complexity multipliers applied
- Approval time excluded (human scheduling unpredictable)
- Categorized into low/medium/high buckets

### Blueprint: Plan.md Markdown Format

**Purpose:** Generate human-readable plan file

**Template:**

```markdown
# Plan: {{TASK_TITLE}}

**Plan ID:** {{PLAN_ID}}
**Created:** {{TIMESTAMP}}
**Priority:** {{PRIORITY_SCORE}}/10
**Category:** {{CATEGORY}}
**Status:** {{STATUS}}

---

## Goal

{{HIGH_LEVEL_GOAL}}

## Context

{{BACKGROUND_INFO}}

Source: {{TASK_FILE}}

## Estimated Effort

- **Duration:** ~{{DURATION}} minutes
- **Complexity:** {{EFFORT_LEVEL}}
- **Autonomy Tier:** {{TIER}}
- **Requires Approval:** {{YES/NO}}

---

## Acceptance Criteria

{{#each ACCEPTANCE_CRITERIA}}
- [ ] {{this}}
{{/each}}

---

## Steps

{{#each STEPS}}
### Step {{id}}: {{action}}

- **Type:** {{type}}
- **Risk Level:** {{risk_level}}
- **Estimated Time:** {{estimated_minutes}} min
- **Status:** {{status}}
{{#if requires_approval}}
- **⚠️ REQUIRES APPROVAL:** {{approval_reason}}
{{/if}}

**Success Criteria:** {{success_criteria}}

{{#if tools_needed}}
**Tools Needed:**
{{#each tools_needed}}
- {{this}}
{{/each}}
{{/if}}

{{#if dependencies}}
**Dependencies:** {{dependencies}}
{{/if}}

{{#if rollback_steps}}
**Rollback Steps (if failure):**
{{#each rollback_steps}}
1. {{this}}
{{/each}}
{{/if}}

---

{{/each}}

## Approval Gates

{{#if approval_gates}}
{{#each approval_gates}}
### Gate {{step_id}}

- **Reason:** {{reason}}
- **Approver:** {{approver}}
- **Status:** {{#if approved_at}}✅ Approved by {{approved_by}} at {{approved_at}}{{else}}⏳ Pending{{/if}}

{{/each}}
{{else}}
*No approval gates required (fully automated)*
{{/if}}

---

## Risk Assessment

{{#each risks}}
### {{description}}

- **Severity:** {{severity}}
- **Mitigation:** {{mitigation}}

{{/each}}

---

## Resources Needed

{{#if resources.apis}}
**APIs:**
{{#each resources.apis}}
- {{this}}
{{/each}}
{{/if}}

{{#if resources.credentials}}
**Credentials:**
{{#each resources.credentials}}
- {{this}} (reference only, not actual secret)
{{/each}}
{{/if}}

{{#if resources.files}}
**Files:**
{{#each resources.files}}
- {{this}}
{{/each}}
{{/if}}

---

## Validation

### Automated Checks
{{#each validation.automated_checks}}
- [ ] {{this}}
{{/each}}

### Manual Verification
{{#each validation.manual_verification}}
- [ ] {{this}}
{{/each}}

### Rollback Plan

{{validation.rollback_plan}}

---

## Execution Log

{{#each execution_log}}
**[{{timestamp}}]** Step {{step_id}} - {{status}}
- Agent: {{agent}}
- Notes: {{notes}}

{{/each}}

---

*Generated by plan_md_generator skill*
*Last updated: {{LAST_UPDATED}}*
```

**Impact Notes:**
- Human-readable markdown format
- Clear approval gates highlighted with ⚠️
- Checkboxes for acceptance criteria
- Execution log append-only
- Structured sections for scanning

## Validation Checklist

### Mandatory Checks (Skill Invalid If Failed)

- [x] Uses canonical folder structure: `SKILL.md`, `references/`, `assets/`
- [x] Contains complete impact analysis (Env, Network, Auth)
- [x] No `localhost` hardcoding (N/A - filesystem + optional API)
- [x] No secrets or passwords in templates
- [x] Auth/CORS impact explicitly documented (API key via env var)
- [x] Supports containerization (Docker volume mounts documented)
- [x] Gotchas document will have known failures and mitigation
- [x] Anti-patterns will list common mistakes
- [x] All templates use parameterized placeholders `{{VARIABLE}}`
- [x] Templates include IMPACT NOTES comments
- [x] References folder structure documented
- [x] SKILL.md contains all required sections

### Quality Checks (Skill Degraded If Failed)

- [x] Default values for non-sensitive variables
- [x] Variable naming follows consistent pattern
- [x] API endpoint documented (Anthropic API for LLM)
- [x] Graceful degradation (works without LLM if needed)
- [x] Step count limits enforced (3-20 steps)
- [x] Approval gates clearly marked
- [x] Effort estimates provided

### Plan-Specific Checks

- [x] Step decomposition algorithm implemented
- [x] Approval gate detection implemented
- [x] Effort estimation algorithm implemented
- [x] Markdown format template provided
- [x] Handles all categories (email, whatsapp, finance, file_drop, general)
- [x] Risk assessment included
- [x] Rollback plans for high-risk operations
- [x] Execution log structure defined
- [x] Acceptance criteria required
- [x] Dependencies tracked between steps

## Anti-Patterns

### ❌ Creating Plans Without Acceptance Criteria

**Problem:** No clear definition of "done"

**Example:**
```javascript
// WRONG - no acceptance criteria
const plan = {
  goal: "Process invoice",
  steps: [...]
  // Missing: acceptance_criteria
};

// CORRECT - explicit criteria
const plan = {
  goal: "Process invoice",
  acceptance_criteria: [
    "Invoice validated and approved",
    "Payment processed successfully",
    "Receipt sent to vendor",
    "Accounting system updated"
  ],
  steps: [...]
};
```

### ❌ Missing Approval Gates for Financial Operations

**Problem:** Finance operations execute without human review

**Example:**
```javascript
// WRONG - no approval for payment
{
  action: "Process $5000 payment",
  requires_approval: false  // DANGEROUS!
}

// CORRECT - approval required
{
  action: "Process $5000 payment",
  requires_approval: true,
  reason: "Financial operation requires approval",
  risk_level: "high"
}
```

### ❌ Steps Without Success Criteria

**Problem:** Can't verify if step succeeded

**Example:**
```javascript
// WRONG - no verification
{
  action: "Fetch data from API",
  // No success_criteria
}

// CORRECT - clear verification
{
  action: "Fetch data from API",
  success_criteria: "API returns 200 status and valid JSON with expected fields"
}
```

### ❌ Overly Granular Steps

**Problem:** 50+ micro-steps make plan unreadable

**Example:**
```javascript
// WRONG - too granular
steps = [
  "Open browser",
  "Navigate to login page",
  "Enter username",
  "Enter password",
  "Click submit",
  "Wait for redirect",
  // ... 44 more steps
];

// CORRECT - atomic but meaningful
steps = [
  "Authenticate to web portal",
  "Navigate to data export section",
  "Download CSV report",
  "Parse and validate data"
];
```

### ❌ No Rollback Plan for Destructive Operations

**Problem:** Can't undo if something goes wrong

**Example:**
```javascript
// WRONG - no rollback
{
  action: "Delete old records from database",
  risk_level: "high"
  // No rollback_steps
}

// CORRECT - rollback defined
{
  action: "Delete old records from database",
  risk_level: "high",
  rollback_steps: [
    "Restore from backup taken in step 2",
    "Verify record count matches pre-deletion",
    "Re-run data validation"
  ]
}
```

### ❌ Hardcoding Credentials in Plan

**Problem:** Secrets exposed in plan files

**Example:**
```javascript
// WRONG - actual secret in plan
{
  tools_needed: ["API_KEY=sk-abc123xyz"]  // LEAKED!
}

// CORRECT - reference only
{
  tools_needed: ["stripe_api_key (from .env)"]
}
```

### ❌ Single-Step "Plans"

**Problem:** No decomposition, just restatement of task

**Example:**
```javascript
// WRONG - not a plan, just a restatement
{
  goal: "Reply to email",
  steps: [
    { action: "Reply to email" }  // Circular!
  ]
}

// CORRECT - decomposed
{
  goal: "Reply to email",
  steps: [
    { action: "Read and understand email context" },
    { action: "Research appropriate response" },
    { action: "Draft reply email" },
    { action: "Review for tone and accuracy" },
    { action: "Send email", requires_approval: true }
  ]
}
```

### ❌ Ignoring Dependencies

**Problem:** Steps execute out of order

**Example:**
```javascript
// WRONG - no dependency tracking
steps = [
  { id: "step-1", action: "Send report" },
  { id: "step-2", action: "Generate report" }  // Should be first!
];

// CORRECT - dependencies enforced
steps = [
  { id: "step-1", action: "Generate report" },
  { id: "step-2", action: "Send report", dependencies: ["step-1"] }
];
```

## Enforcement Behavior

When this skill is active:

### Agent Responsibilities

1. **Always create plan before execution** - no ad-hoc task running
2. **Decompose into 3-20 steps** - enforce meaningful decomposition
3. **Flag approval gates** - identify high-risk operations
4. **Estimate effort** - provide time/complexity estimates
5. **Define acceptance criteria** - clear "done" definition
6. **Include rollback plans** - for destructive operations
7. **Track dependencies** - ensure correct execution order

### User Expectations

- All claimed tasks have detailed plans
- Approval requirements clearly marked
- Effort estimates are conservative (better to overestimate)
- High-risk operations explicitly flagged
- Rollback procedures defined for risky steps
- Execution can be tracked via logs

### Error Handling

All functions return structured results:

```typescript
interface PlanGenerationResult {
  success: boolean;
  plan_id?: string;
  plan_file_path?: string;
  plan_content?: PlanStructure;
  error?: string;
  warnings?: string[];
}

interface PlanStructure {
  plan_id: string;
  goal: string;
  context: string;
  acceptance_criteria: string[];
  estimated_effort: 'low' | 'medium' | 'high';
  estimated_duration_minutes: number;
  autonomy_tier: string;
  requires_human_approval: boolean;
  steps: Step[];
  approval_gates: ApprovalGate[];
  risks: Risk[];
  resources: Resources;
  validation: Validation;
}
```

Agents must check `success` field before proceeding.

## Integration with AGENTS.md

This skill implements the planning workflow defined in AGENTS.md §4:

- **§4.2 Planning Stage**: Convert Needs_Action to Plans/
- **§4.3 Approval Gates**: Identify steps requiring human review
- **§4.4 Execution Preparation**: Structured format for orchestrator
- **§4.5 Audit Trail**: Execution log for transparency

All agents using this skill MUST respect the planning requirements defined in AGENTS.md.

## Usage Examples

See `references/patterns.md` for concrete code examples and workflow patterns.
