---
name: company-handbook-enforcer
description: Apply the rules from Company_Handbook.md in planning and actions. Reject or escalate actions that violate policy. Ensures all agent actions comply with organizational tone, payment limits, privacy rules, and operational constraints.
---

# Company Handbook Enforcer

## Purpose

This skill enforces organizational policies defined in `Company_Handbook.md` across all agent planning and execution workflows.

It prevents:
- Policy violations in automated actions
- Non-compliant communication with customers/stakeholders
- Unauthorized financial transactions beyond approval limits
- Privacy and data handling breaches
- Actions that contradict company operational guidelines

---

## When to Use This Skill

This skill MUST be invoked when:

- **Planning any feature or implementation** - validate against handbook policies before execution
- **Generating customer-facing content** - ensure tone and language compliance
- **Financial transactions or payment processing** - verify against payment authorization limits
- **Data handling operations** - validate privacy and security compliance
- **External integrations** - check third-party service policies
- **Deployment or infrastructure changes** - verify operational guidelines

If this skill is NOT applied → actions may violate company policy and require rollback.

---

## Overview

### Core Responsibilities

1. **Policy Validation**: Check all planned actions against Company_Handbook.md rules
2. **Violation Detection**: Identify conflicts between agent actions and policies
3. **Reasoning & Explanation**: Provide clear reasoning for compliance or violation
4. **Alternative Suggestions**: Propose policy-compliant alternatives when violations detected
5. **Escalation Triggers**: Flag actions requiring human approval

### Handbook Structure

The Company_Handbook.md typically includes:
- **Communication Guidelines**: Tone, language, customer interaction rules
- **Financial Policies**: Payment limits, approval workflows, expense rules
- **Privacy & Security**: Data handling, PII protection, access controls
- **Operational Constraints**: Work hours, SLA requirements, deployment windows
- **Ethical Guidelines**: AI usage boundaries, bias prevention, fairness standards

---

## Impact Analysis Workflow

### 1. Policy Discovery & Parsing

Before any action validation, the skill MUST:

**Locate Handbook:**
```bash
# Search for Company_Handbook.md in standard locations
find . -name "Company_Handbook.md" -o -name "company_handbook.md"
# Common locations:
# - ./Company_Handbook.md
# - ./docs/Company_Handbook.md
# - ./.specify/memory/Company_Handbook.md
```

**Parse Policy Categories:**
- Extract sections: Communication, Financial, Privacy, Operational, Ethical
- Identify hard rules (MUST/MUST NOT) vs soft guidelines (SHOULD/RECOMMEND)
- Map policies to enforcement levels:
  - BLOCK: Hard stop, reject action immediately
  - WARN: Flag for review, allow with justification
  - SUGGEST: Provide alternative, allow action

**Build Policy Index:**
```yaml
policies:
  communication:
    tone: "professional, empathetic, no jargon"
    prohibited_phrases: ["ASAP", "urgent", "immediately"]
    required_elements: ["greeting", "clear explanation", "next steps"]
  financial:
    payment_limit_without_approval: 1000
    approval_required_above: 1000
    prohibited_transactions: ["cryptocurrency", "unverified vendors"]
  privacy:
    pii_handling: "encrypt at rest, TLS in transit"
    data_retention: "30 days max for logs"
    prohibited_storage: ["SSN in plain text", "passwords without hashing"]
  operational:
    deployment_windows: ["Tue-Thu 10:00-16:00 UTC"]
    change_freeze_periods: ["Dec 15 - Jan 5"]
    sla_response_time: "4 hours for critical bugs"
```

### 2. Action Classification & Mapping

**Identify Action Type:**
- Code generation (feature implementation, bug fix)
- Communication (email, Slack message, documentation)
- Financial operation (payment processing, expense recording)
- Data handling (database query, API call, file storage)
- Infrastructure change (deployment, config update)

**Map Action to Policy Categories:**
```yaml
action: "Send customer notification email"
mapped_policies:
  - communication.tone
  - communication.prohibited_phrases
  - privacy.pii_handling (if includes customer data)

action: "Process refund of $1500"
mapped_policies:
  - financial.payment_limit_without_approval
  - financial.approval_required_above
```

### 3. Compliance Validation

**For each mapped policy, check:**

1. **Exact Match Violation**
   ```yaml
   action: "Send email with 'URGENT ACTION REQUIRED'"
   policy: communication.prohibited_phrases: ["URGENT"]
   result: VIOLATION - contains prohibited phrase
   ```

2. **Threshold Violation**
   ```yaml
   action: "Process payment of $1500"
   policy: financial.payment_limit_without_approval: 1000
   result: VIOLATION - exceeds limit, requires approval
   ```

3. **Pattern Violation**
   ```yaml
   action: "Store user SSN in database field 'ssn_plain'"
   policy: privacy.prohibited_storage: ["SSN in plain text"]
   result: VIOLATION - PII storage without encryption
   ```

4. **Time Window Violation**
   ```yaml
   action: "Deploy to production on Dec 20"
   policy: operational.change_freeze_periods: ["Dec 15 - Jan 5"]
   result: VIOLATION - deployment during freeze period
   ```

### 4. Reasoning Generation

For each validation result, generate:

**Compliance Reasoning:**
```markdown
✅ COMPLIANT: Send customer notification email

Reasoning:
- Tone: Professional and empathetic language used
- Prohibited phrases: None detected
- Required elements: Includes greeting, explanation, next steps
- Privacy: No PII included in plain text

Policy references:
- communication.tone: PASS
- communication.required_elements: PASS
```

**Violation Reasoning:**
```markdown
❌ VIOLATION: Process payment of $1500

Reasoning:
- Payment amount: $1500
- Policy limit: $1000 (without approval)
- Approval required: YES
- Current authorization level: None provided

Policy references:
- financial.payment_limit_without_approval: FAIL (exceeds by $500)
- financial.approval_required_above: REQUIRES HUMAN APPROVAL

Impact: Financial transaction blocked until manager approval obtained.
```

### 5. Alternative Suggestion

When violation detected, suggest compliant alternative:

**Example 1: Communication Violation**
```markdown
Original action: "Send email: 'URGENT: Fix this ASAP!'"

Violation: Contains prohibited phrases ["URGENT", "ASAP"]

Alternative:
"Send email: 'Important: Action Required by End of Day
Dear [Customer],

We've identified an issue that needs your attention by 5:00 PM today.
Here's what you need to do: [clear steps]

If you have questions, reply to this email or call us at [phone].

Best regards,
[Team]'"

Changes:
- Removed "URGENT" → Used "Important: Action Required"
- Removed "ASAP" → Specific deadline "by 5:00 PM today"
- Added clear steps and contact information
```

**Example 2: Financial Violation**
```markdown
Original action: "Process refund of $1500 immediately"

Violation: Exceeds payment limit ($1000) without approval

Alternative:
1. Create approval request:
   - Amount: $1500
   - Reason: Customer refund for order #12345
   - Approver: Finance Manager
2. Wait for approval (SLA: 4 hours)
3. Once approved, process payment with approval reference

Compliance path:
- Splits action into approval request + conditional execution
- Follows financial.approval_required_above policy
- Maintains audit trail
```

**Example 3: Privacy Violation**
```markdown
Original action: "Store user SSN in database field 'customer.ssn'"

Violation: Plain text storage of PII

Alternative:
1. Encrypt SSN before storage:
   ```javascript
   const encryptedSSN = await encrypt(ssn, process.env.ENCRYPTION_KEY);
   await db.customers.update({ id }, { ssn_encrypted: encryptedSSN });
   ```
2. Use separate encrypted field: 'ssn_encrypted'
3. Never log or display SSN in plain text
4. Implement access controls (only authorized roles)

Compliance changes:
- Uses encryption at rest (privacy.pii_handling)
- Prevents plain text storage (privacy.prohibited_storage)
- Follows data protection best practices
```

---

## Environment Variable Strategy

This skill requires configuration to locate and parse the handbook:

**Runtime Variables:**
```yaml
HANDBOOK_PATH: "{{HANDBOOK_FILE_PATH}}"                    # Path to Company_Handbook.md
HANDBOOK_ENFORCEMENT_LEVEL: "{{ENFORCEMENT_LEVEL}}"       # STRICT | WARN | SUGGEST
HANDBOOK_CACHE_TTL: "{{CACHE_TTL_SECONDS}}"              # Cache parsed policies
HANDBOOK_ESCALATION_WEBHOOK: "{{ESCALATION_URL}}"        # Notify on violations
HANDBOOK_APPROVAL_TIMEOUT: "{{APPROVAL_TIMEOUT_SEC}}"    # Max wait for human approval
```

**Default Values:**
```yaml
HANDBOOK_PATH: "./Company_Handbook.md"
HANDBOOK_ENFORCEMENT_LEVEL: "STRICT"  # Block on violations
HANDBOOK_CACHE_TTL: "300"             # 5 minutes
HANDBOOK_APPROVAL_TIMEOUT: "14400"    # 4 hours
```

**Impact Notes:**
- `STRICT` mode blocks all violations (recommended for production)
- `WARN` mode flags violations but allows action (dev/testing only)
- `SUGGEST` mode provides alternatives without blocking (advisory)
- Cache TTL balances performance vs policy update freshness
- Escalation webhook enables real-time violation monitoring

---

## Network & Topology Implications

**Internal Dependencies:**
- **Handbook Repository**: Must be accessible (local file or remote endpoint)
- **Approval Service**: API endpoint for escalation workflows
- **Audit Log**: Violation tracking and compliance reporting
- **Notification Service**: Alerts for policy violations

**External Dependencies:**
- **Third-party Policy APIs**: Legal compliance services, payment gateways
- **Approval Workflow Tools**: Jira, ServiceNow, custom systems

**Network Considerations:**
- If handbook is remote (Git repo, S3), network latency impacts validation speed
- Approval webhooks require outbound HTTPS access
- Audit logging may require database or external log service
- Consider caching handbook locally to reduce network calls

---

## Auth / CORS / Security Impact

**Authentication Considerations:**
- Handbook access may require credentials (private repos, internal wikis)
- Approval workflows need secure authentication (OAuth, API keys)
- Audit logs must be tamper-proof (append-only, signed entries)

**Authorization Levels:**
```yaml
roles:
  agent:
    - validate_action
    - request_approval
    - log_violation
  manager:
    - approve_action
    - override_policy (with justification)
  admin:
    - update_handbook
    - change_enforcement_level
```

**Security Requirements:**
- Handbook itself should be version-controlled and protected
- Approval requests must be authenticated and logged
- Policy overrides require audit trail and justification
- Sensitive policies (financial limits) should not be in public repos

---

## Blueprints & Templates Used

### Blueprint: Policy Validation Template

**Purpose:** Standard structure for policy compliance checks

**Template Variables:**
```yaml
ACTION_DESCRIPTION: "{{ACTION_TO_VALIDATE}}"
POLICY_CATEGORIES: ["communication", "financial", "privacy", "operational"]
ENFORCEMENT_LEVEL: "{{STRICT|WARN|SUGGEST}}"

# Validation result
COMPLIANCE_STATUS: "{{COMPLIANT|VIOLATION|NEEDS_APPROVAL}}"
VIOLATED_POLICIES: ["policy.key.1", "policy.key.2"]
REASONING: "{{DETAILED_EXPLANATION}}"
ALTERNATIVES: ["{{ALTERNATIVE_1}}", "{{ALTERNATIVE_2}}"]
ESCALATION_REQUIRED: "{{YES|NO}}"
```

### Blueprint: Violation Report Template

**Purpose:** Generate compliance violation reports

**Template Variables:**
```yaml
timestamp: "{{ISO_TIMESTAMP}}"
action_id: "{{UNIQUE_ACTION_ID}}"
agent: "{{AGENT_IDENTIFIER}}"
action_type: "{{CODE|COMMUNICATION|FINANCIAL|DATA|INFRASTRUCTURE}}"
description: "{{ACTION_DESCRIPTION}}"

violation:
  policy_section: "{{HANDBOOK_SECTION}}"
  policy_rule: "{{SPECIFIC_RULE}}"
  severity: "{{CRITICAL|HIGH|MEDIUM|LOW}}"
  reasoning: "{{WHY_IT_VIOLATES}}"

impact:
  business_risk: "{{RISK_DESCRIPTION}}"
  affected_stakeholders: ["{{STAKEHOLDER_1}}", "{{STAKEHOLDER_2}}"]
  remediation_required: "{{YES|NO}}"

alternative:
  compliant_approach: "{{SUGGESTED_ALTERNATIVE}}"
  changes_needed: ["{{CHANGE_1}}", "{{CHANGE_2}}"]
  approval_path: "{{ESCALATION_WORKFLOW}}"
```

### Blueprint: Company Handbook Template

**Purpose:** Standard structure for organizational policy documents

**Sections:**
1. **Communication Guidelines**
   - Tone and language standards
   - Prohibited phrases and jargon
   - Customer interaction protocols

2. **Financial Policies**
   - Payment authorization limits
   - Approval workflows
   - Expense and refund rules

3. **Privacy & Security**
   - PII handling requirements
   - Data retention policies
   - Access control rules

4. **Operational Constraints**
   - Deployment windows
   - Change freeze periods
   - SLA and response time requirements

5. **Ethical Guidelines**
   - AI usage boundaries
   - Bias prevention measures
   - Fairness and transparency standards

---

## Validation Checklist

### Mandatory Checks (Skill Invalid If Failed)

- [ ] Company_Handbook.md file exists and is readable
- [ ] All policy categories parsed correctly (Communication, Financial, Privacy, Operational, Ethical)
- [ ] Hard rules (MUST/MUST NOT) clearly identified
- [ ] Enforcement level configured (STRICT/WARN/SUGGEST)
- [ ] Violation detection logic covers all policy types
- [ ] Reasoning generation includes policy references
- [ ] Alternative suggestions provided for common violations
- [ ] Escalation workflow defined for approval-required actions
- [ ] Audit logging enabled for all policy checks

### Quality Checks (Skill Degraded If Failed)

- [ ] Handbook cached for performance (TTL configured)
- [ ] Violation reports include business impact assessment
- [ ] Alternatives are actionable and specific
- [ ] Policy references link to handbook sections
- [ ] Escalation webhooks tested and functional
- [ ] Approval timeout configured and enforced
- [ ] Compliance dashboard available for monitoring

### Policy Coverage Checks

- [ ] Communication tone validation works
- [ ] Financial limit checks enforce thresholds
- [ ] Privacy PII detection functions correctly
- [ ] Operational time window checks accurate
- [ ] Ethical guideline violations detected

---

## Anti-Patterns

### ❌ Hardcoding Policy Rules

**Problem:** Handbook changes don't propagate to skill

**Example:**
```javascript
// WRONG
const PAYMENT_LIMIT = 1000;  // Hardcoded

// CORRECT
const PAYMENT_LIMIT = handbook.financial.payment_limit_without_approval;
```

### ❌ Ignoring Enforcement Level

**Problem:** Violations block in dev/test environments

**Example:**
```javascript
// WRONG
if (violation) {
  throw new Error('Policy violation');  // Always blocks
}

// CORRECT
if (violation) {
  if (enforcementLevel === 'STRICT') {
    throw new Error('Policy violation');
  } else if (enforcementLevel === 'WARN') {
    console.warn('Policy violation detected', violation);
  } else {
    console.info('Policy suggestion', violation.alternative);
  }
}
```

### ❌ Vague Violation Reasoning

**Problem:** Users don't understand why action rejected

**Example:**
```javascript
// WRONG
return { compliant: false, reason: 'Policy violation' };

// CORRECT
return {
  compliant: false,
  reason: 'Payment amount ($1500) exceeds approval limit ($1000)',
  policy: 'financial.payment_limit_without_approval',
  alternative: 'Request manager approval before processing'
};
```

### ❌ No Alternative Suggestions

**Problem:** Action blocked with no path forward

**Example:**
```javascript
// WRONG
if (containsProhibitedPhrase(email)) {
  return { error: 'Prohibited phrase detected' };
}

// CORRECT
if (containsProhibitedPhrase(email)) {
  return {
    error: 'Prohibited phrase detected',
    violated_phrases: ['URGENT', 'ASAP'],
    alternative: 'Use "Important: Action Required by [specific time]"',
    example: getCompliantEmailExample(email)
  };
}
```

### ❌ Missing Escalation Path

**Problem:** Actions requiring approval have no workflow

**Example:**
```javascript
// WRONG
if (amount > LIMIT) {
  throw new Error('Exceeds payment limit');
}

// CORRECT
if (amount > LIMIT) {
  const approvalRequest = await createApprovalRequest({
    action: 'payment',
    amount,
    reason,
    approver: 'finance-manager'
  });
  return { status: 'pending_approval', request_id: approvalRequest.id };
}
```

### ❌ No Audit Trail

**Problem:** Cannot track compliance violations over time

**Example:**
```javascript
// WRONG
if (violation) {
  console.log('Violation detected');  // Lost after container restart
}

// CORRECT
if (violation) {
  await auditLog.record({
    timestamp: new Date().toISOString(),
    action,
    violation,
    agent: process.env.AGENT_ID,
    severity: violation.severity
  });
}
```

---

## Enforcement Behavior

When this skill is active:

### Agent Responsibilities

1. **Pre-Action Validation**
   - Before executing any action, validate against handbook policies
   - For multi-step plans, validate each step independently
   - Cache validation results to avoid redundant checks

2. **Violation Handling**
   - STRICT mode: Block action, return violation reasoning and alternative
   - WARN mode: Log violation, allow action with warning
   - SUGGEST mode: Provide alternative, allow original action

3. **Approval Escalation**
   - If action requires approval, create escalation request
   - Wait for approval (up to timeout)
   - On timeout, block action and notify user
   - On approval, execute with approval reference in logs

4. **Reasoning Transparency**
   - Always explain WHY action violates policy
   - Reference specific handbook sections
   - Show exact values that triggered violation (amounts, phrases, dates)

### User Expectations

- All actions automatically validated against company policies
- Clear explanations for rejections with policy references
- Actionable alternatives suggested for violations
- Approval workflows triggered automatically when needed
- Compliance audit trail maintained for all actions

---

## Final Rule (Hard Stop)

If a user requests an action that violates policy without approval:

```
User: "Process a $5000 refund immediately"

Agent: "This action violates company policy and cannot be executed.

Violation:
- Policy: financial.payment_limit_without_approval
- Limit: $1000
- Requested: $5000
- Exceeds by: $4000

Required action: Manager approval needed

Compliant alternative:
1. Create approval request for Finance Manager
2. Wait for approval (SLA: 4 hours max)
3. Once approved, process payment with approval reference

Would you like me to create the approval request?"
```

Then wait for user consent before creating approval request.

If user insists on bypassing policy, escalate to human manager:

```
Agent: "I cannot bypass company policy without proper authorization.

This request has been escalated to your manager for review.

Escalation ticket: #12345
Estimated response: Within 4 hours per SLA

You can track the status at: [escalation_url]"
```

---

## Integration with Other Skills

### Planning Skills (sp.plan, sp.tasks)
- Run handbook enforcer during plan generation
- Validate all planned actions before task creation
- Flag policy-sensitive tasks for human review

### Implementation Skills (sp.implement)
- Check each task against policies before execution
- Block implementation if task violates policy
- Suggest policy-compliant task modifications

### Git Workflow Skills (sp.git.commit_pr)
- Validate commit messages against communication guidelines
- Check PR descriptions for policy compliance
- Ensure code changes don't introduce policy violations

---

## Example: End-to-End Policy Enforcement

**Scenario:** Agent asked to implement customer notification feature

**Step 1: Action Analysis**
```yaml
requested_action:
  type: "feature_implementation"
  description: "Send urgent email to customers about service outage"
  components:
    - email_template: "URGENT: Service Down - Fix ASAP"
    - send_time: "immediately"
    - recipients: "all_active_customers"
```

**Step 2: Policy Mapping**
```yaml
applicable_policies:
  - communication.tone
  - communication.prohibited_phrases
  - operational.customer_notification_protocol
  - privacy.pii_handling (if email includes customer data)
```

**Step 3: Violation Detection**
```yaml
violations:
  - policy: "communication.prohibited_phrases"
    violated_rules: ["URGENT", "ASAP"]
    severity: "HIGH"
  - policy: "operational.customer_notification_protocol"
    violated_rules: ["requires_manager_approval_for_service_outage"]
    severity: "CRITICAL"
```

**Step 4: Reasoning Generation**
```markdown
❌ VIOLATIONS DETECTED (2)

1. Communication Policy Violation
   Policy: communication.prohibited_phrases
   Issue: Email contains prohibited phrases
   - "URGENT" (use "Important" instead)
   - "ASAP" (provide specific timeline)
   Severity: HIGH
   Impact: Non-compliant customer communication

2. Operational Policy Violation
   Policy: operational.customer_notification_protocol
   Issue: Service outage notifications require manager approval
   Severity: CRITICAL
   Impact: Unauthorized mass customer communication
```

**Step 5: Alternative Suggestion**
```markdown
✅ COMPLIANT ALTERNATIVE

1. Update email template:
   Subject: "Important: Service Update - [Specific Time]"
   Body:
   "Dear Valued Customer,

   We're currently experiencing a service issue affecting [specific feature].

   What this means for you:
   - [Clear impact description]
   - Estimated resolution: [Specific time]
   - Workaround available: [If applicable]

   We apologize for the inconvenience and are working to resolve this quickly.

   For questions, contact us at: [support info]

   Best regards,
   [Company Name] Team"

2. Request manager approval:
   - Reason: Service outage notification (critical impact)
   - Approver: Customer Success Manager
   - SLA: 1 hour for critical notifications

3. Once approved, schedule send with approval reference

Compliance changes:
- Removed prohibited phrases ✓
- Added specific timeline ✓
- Clear impact explanation ✓
- Manager approval workflow ✓
```

**Step 6: Execution with Approval**
```yaml
action_plan:
  - step: "Create approval request"
    status: "pending"
    approval_id: "APR-001"
  - step: "Wait for approval (timeout: 1 hour)"
    status: "waiting"
    depends_on: "APR-001"
  - step: "Send compliant email"
    status: "blocked"
    depends_on: "APR-001.approved"
    template: "compliant_service_outage_notification"
```

---
