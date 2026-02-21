---
name: approval_request_creator
description: Generate formal human approval request markdown files for sensitive actions (payments, emails, social posts) requiring human authorization. Creates structured requests in Pending_Approval folder with clear approve/reject instructions.
---

# Approval Request Creator

## Purpose

This skill generates formal, structured approval request files for any agent action that requires human authorization before execution. It creates markdown files in the `Pending_Approval/` folder with comprehensive metadata, reasoning, alternatives, and clear approval workflows.

The skill is designed to be used by any agent (lex, planner, executor) when they encounter actions that exceed their autonomy tier or violate company policies requiring escalation.

## When to Use This Skill

Use `approval_request_creator` when:

- **Payment processing**: Any financial transaction requiring approval
- **External communications**: Sending emails, Slack messages, social media posts to external parties
- **Publishing actions**: Deploying code, publishing content, making public announcements
- **Data modifications**: Deleting production data, modifying critical records
- **Policy violations**: Actions flagged by `company_handbook_enforcer` as requiring approval
- **High-risk operations**: Database migrations, infrastructure changes, API key rotations
- **Customer-facing actions**: Refunds, account modifications, service cancellations
- **Contract actions**: Agreement signing, vendor onboarding, partnership decisions

Do NOT use this skill when:

- **Pre-approved actions**: Routine operations within agent autonomy tier
- **Already approved**: Action was previously approved (check for existing approval file)
- **Emergency bypass**: Critical production incidents with executive override
- **Internal testing**: Actions in development/staging environments
- **Read-only operations**: Gathering information, generating reports, research tasks

## Impact Analysis Workflow

### 1. Environment Variable Strategy

**Build-Time vs Runtime Variables:**

This skill operates at runtime only. No build-time variables required.

**Runtime variables:**
```bash
# Required
VAULT_PATH="/absolute/path/to/vault"
PENDING_APPROVAL_PATH="$VAULT_PATH/Pending_Approval"  # Auto-created if missing

# Optional: Approval configuration
APPROVAL_DEFAULT_TIMEOUT_HOURS="4"           # Default time before escalation
APPROVAL_REQUIRE_REASON="true"               # Mandate justification field
APPROVAL_NOTIFY_EMAIL="approver@company.com" # Email for notifications
APPROVAL_NOTIFY_SLACK_WEBHOOK="https://..."  # Slack webhook for notifications
APPROVAL_AUTO_ESCALATE="true"                # Escalate if timeout expires
APPROVAL_ESCALATION_EMAIL="ceo@company.com"  # Escalation contact

# Optional: Risk thresholds
APPROVAL_FINANCIAL_THRESHOLD="1000"          # $ amount requiring approval
APPROVAL_CRITICAL_THRESHOLD="10000"          # $ amount requiring C-level approval
APPROVAL_VIP_CUSTOMERS="customer1,customer2" # Comma-separated VIP list

# Optional: Audit trail
APPROVAL_AUDIT_LOG_PATH="$VAULT_PATH/Audit_Logs"
APPROVAL_SESSION_ID=""                       # Current agent session ID
```

**Secrets Management:**

- This skill does NOT handle secrets directly
- May reference email addresses, customer names (not sensitive)
- API keys for notifications (Slack, email) managed via separate env vars
- Never log approval request IDs or sensitive action details

**Variable Discovery Process:**
```bash
# Check approval configuration
cat .env | grep APPROVAL_

# Verify Pending_Approval folder exists
test -d "$VAULT_PATH/Pending_Approval" && echo "OK" || mkdir -p "$VAULT_PATH/Pending_Approval"

# Count pending approvals
find "$VAULT_PATH/Pending_Approval" -name '*.md' -exec grep -l 'status: pending' {} \; | wc -l
```

### 2. Network & Topology Implications

**Port Discovery:**

No network ports required. This skill operates on local filesystem only, unless notifications are enabled.

**Dependency Topology:**

```
Approval Request Creator
  ├── Vault State Manager (file writes to Pending_Approval/)
  │   └── Filesystem (Pending_Approval/ folder)
  ├── Optional: Email Service (SMTP for notifications)
  │   └── SMTP server (port 587 or 465)
  └── Optional: Slack Webhook (for notifications)
      └── Slack API (https://hooks.slack.com)
```

**Topology Notes:**
- Primary operation: local file writes (no external dependencies)
- Optional: notification services (email, Slack) for real-time approver alerts
- No database dependencies
- Stateless operation (each approval request is independent)

**Docker/K8s Implications:**

When containerizing agents that use this skill:
- Mount vault as read-write volume: `-v /host/vault:/vault:rw`
- Ensure `Pending_Approval/` folder is writable
- If using email notifications, allow outbound SMTP (port 587/465)
- If using Slack notifications, allow outbound HTTPS
- No persistent storage needed beyond vault mount

### 3. Auth / CORS / Security Impact

**Authentication Pattern Analysis:**

- No authentication for filesystem access (local only)
- If using email service: requires SMTP credentials in environment
- If using Slack webhook: requires webhook URL secret
- Agent authorization: all agents have write access to Pending_Approval/ (per AGENTS.md §4)

**Security Considerations:**

| Risk | Mitigation |
|------|-----------|
| **Sensitive data exposure** | Sanitize logs; never log full action details or approval IDs |
| **Approval forgery** | Generate cryptographic hash for request integrity |
| **Path traversal** | Validate all paths via vault_state_manager |
| **Unauthorized approval** | Require approver signature/token (future enhancement) |
| **Notification interception** | Use TLS for email/Slack notifications |
| **Request tampering** | Include checksum/hash in approval file |

**Validation Rules:**

Before creating any approval request:
```javascript
function validateApprovalRequest(request) {
  // Required fields check
  if (!request.action || !request.action.type || !request.action.description) {
    throw new Error("Missing required action fields");
  }

  // Justification check
  if (!request.justification || !request.justification.business_reason) {
    throw new Error("Approval request must include business justification");
  }

  // Approver check
  if (!request.approval.required_approver) {
    throw new Error("Approver must be specified");
  }

  // Timeout validation
  if (request.approval.sla_hours < 1 || request.approval.sla_hours > 72) {
    throw new Error("SLA must be between 1 and 72 hours");
  }

  return true;
}
```

---

## Usage Patterns

### Pattern 1: Financial Transaction Approval

**Use Case:** Payment exceeds autonomy tier limit, requires manager approval

**Input:**
```javascript
const { createApprovalRequest } = require('./approval_request_creator');

const approvalRequest = await createApprovalRequest({
  action: {
    type: "payment",
    description: "Process refund to customer John Doe",
    details: {
      amount: 1500.00,
      currency: "USD",
      recipient: "John Doe <john@example.com>",
      reason: "Product defect - customer complaint #12345",
      payment_method: "original_payment_method",
      transaction_id: "txn_abc123"
    },
    environment: "production"
  },
  violation: {
    policy: "financial.payment_limit_without_approval",
    policy_section: "Financial Policies > Payment Authorization",
    severity: "MEDIUM",
    reasoning: "Refund amount ($1,500) exceeds agent limit ($1,000)",
    impact: {
      business_risk: "Unauthorized refund if not approved",
      affected_stakeholders: ["Finance Team", "Customer"],
      risk_level: "medium"
    }
  },
  justification: {
    business_reason: "Customer received defective product, requesting full refund per warranty policy",
    urgency: "high",
    customer_impact: "Customer is currently blocked, expecting resolution today",
    alternative_considered: false,
    alternative_rejected_reason: "No viable alternative - customer insists on refund"
  },
  approval: {
    required_approver: "Manager",
    approver_email: "manager@company.com",
    approval_level: "manager",
    sla_hours: 4
  }
});

console.log(`Approval request created: ${approvalRequest.file_path}`);
console.log(`Request ID: ${approvalRequest.request_id}`);
```

**Output File:** `Pending_Approval/20250204-143022-payment-refund-john-doe.md`

**File Content:**
```markdown
---
request_id: APR-20250204-143022-ABC123
created_at: 2025-02-04T14:30:22Z
expires_at: 2025-02-04T18:30:22Z
timeout_action: escalate
status: pending
action_type: payment
priority: high
approver: manager@company.com
approval_level: manager
---

# Approval Request: Payment - Process refund to customer John Doe

**Request ID:** APR-20250204-143022-ABC123
**Created:** 2025-02-04 14:30:22 UTC
**Expires:** 2025-02-04 18:30:22 UTC (4 hours)
**Status:** 🟡 Pending Approval

---

## Action Details

**Type:** Payment
**Description:** Process refund to customer John Doe
**Environment:** Production
**Initiator:** lex (Local Executive Agent)

**Transaction Details:**
- **Amount:** $1,500.00 USD
- **Recipient:** John Doe <john@example.com>
- **Reason:** Product defect - customer complaint #12345
- **Payment Method:** original_payment_method
- **Transaction ID:** txn_abc123

---

## Policy Violation

**Policy:** financial.payment_limit_without_approval
**Section:** Financial Policies > Payment Authorization
**Severity:** 🟡 MEDIUM

**Reasoning:**
Refund amount ($1,500) exceeds agent limit ($1,000)

**Impact Assessment:**
- **Business Risk:** Unauthorized refund if not approved
- **Affected Stakeholders:** Finance Team, Customer
- **Risk Level:** medium

---

## Justification

**Business Reason:**
Customer received defective product, requesting full refund per warranty policy

**Urgency:** 🔴 High
**Customer Impact:** Customer is currently blocked, expecting resolution today

**Alternatives Considered:** No
**Why Not:** No viable alternative - customer insists on refund

---

## Approval Required

**Required Approver:** Manager
**Approver Contact:** manager@company.com
**Approval Level:** Manager
**SLA:** 4 hours

---

## How to Approve or Reject

### ✅ To Approve:

1. Add the following to the YAML frontmatter:
   ```yaml
   status: approved
   approved_by: "Your Name <your.email@company.com>"
   approved_at: "2025-02-04T15:00:00Z"
   ```

2. (Optional) Add approval notes in the `## Approval Decision` section below

3. Save the file

4. The agent will automatically detect approval and execute the action

### ❌ To Reject:

1. Add the following to the YAML frontmatter:
   ```yaml
   status: rejected
   rejected_by: "Your Name <your.email@company.com>"
   rejected_at: "2025-02-04T15:00:00Z"
   rejection_reason: "Your reason here"
   ```

2. (Optional) Provide detailed rejection reasoning in the `## Approval Decision` section below

3. Save the file

4. The agent will abort the action and log the rejection

---

## Approval Decision

<!-- Approver: Add your decision notes here -->


---

## Audit Trail

- **Session ID:** session_abc123
- **Audit Log ID:** audit_20250204_143022
- **Handbook Version:** v2.1.0
- **Enforcer Version:** approval_request_creator v1.0.0

---

**🔔 Notifications Sent:**
- ✅ Email sent to manager@company.com at 2025-02-04T14:30:25Z
- ✅ Slack notification posted to #approvals at 2025-02-04T14:30:26Z
```

---

### Pattern 2: External Email Approval

**Use Case:** Agent wants to send customer-facing email, requires compliance review

**Input:**
```javascript
const approvalRequest = await createApprovalRequest({
  action: {
    type: "email",
    description: "Send service outage notification to all customers",
    details: {
      recipients: "all_customers@company.com (mailing list: 5,432 recipients)",
      subject: "Important: Service Disruption Scheduled for Feb 5",
      body_preview: "We will be performing critical maintenance...",
      send_time: "2025-02-05T02:00:00Z",
      sender: "support@company.com"
    },
    environment: "production"
  },
  violation: {
    policy: "communication.customer_facing_approval",
    policy_section: "Communication Guidelines > External Communications",
    severity: "HIGH",
    reasoning: "Mass customer communication requires compliance review",
    impact: {
      business_risk: "Brand damage if messaging is non-compliant",
      affected_stakeholders: ["All Customers", "Support Team", "Marketing"],
      risk_level: "high"
    }
  },
  justification: {
    business_reason: "Critical maintenance window requires customer notification per SLA",
    urgency: "medium",
    customer_impact: "Customers need advance notice to plan around outage",
    alternative_considered: true,
    alternative_rejected_reason: "In-app notification insufficient for users not logged in"
  },
  approval: {
    required_approver: "Compliance Officer",
    approver_email: "compliance@company.com",
    approval_level: "director",
    sla_hours: 24
  }
});
```

---

### Pattern 3: Social Media Post Approval

**Use Case:** Agent wants to publish social media post, requires marketing approval

**Input:**
```javascript
const approvalRequest = await createApprovalRequest({
  action: {
    type: "social_media_post",
    description: "Publish product launch announcement on Twitter",
    details: {
      platform: "Twitter",
      content: "🚀 Introducing ProductX! Revolutionary AI-powered...",
      media_attachments: ["product_screenshot.png", "demo_video.mp4"],
      scheduled_time: "2025-02-10T14:00:00Z",
      target_audience: "public"
    },
    environment: "production"
  },
  violation: {
    policy: "communication.social_media_approval",
    policy_section: "Communication Guidelines > Social Media",
    severity: "HIGH",
    reasoning: "All public social media posts require marketing approval",
    impact: {
      business_risk: "Public messaging that doesn't align with brand voice",
      affected_stakeholders: ["Marketing", "Brand Team", "Public Audience"],
      risk_level: "high"
    }
  },
  justification: {
    business_reason: "Product launch scheduled for Feb 10, need to announce on social media",
    urgency: "medium",
    customer_impact: "Customers expecting announcement per launch roadmap",
    alternative_considered: true,
    alternative_rejected_reason: "Blog post alone won't reach target audience"
  },
  approval: {
    required_approver: "Marketing Manager",
    approver_email: "marketing@company.com",
    approval_level: "manager",
    sla_hours: 48
  }
});
```

---

## Key Guarantees

1. **Structured Format**: All approval requests use consistent markdown format with YAML frontmatter
2. **Unique IDs**: Each request gets cryptographically secure unique ID
3. **Audit Trail**: Full audit log of who requested, when, and why
4. **Clear Instructions**: Approver knows exactly how to approve/reject
5. **Expiration Handling**: Requests expire after SLA timeout (default escalation)
6. **Notification Support**: Optional email/Slack notifications to approvers
7. **Checksum Integrity**: Request includes hash to detect tampering
8. **Policy Linkage**: Clear reference to violated policy and handbook section

---

## Output Schema

**Approval Request File:**
- **Location:** `Pending_Approval/`
- **Naming:** `YYYYMMDD-HHMMSS-<action-type>-<brief-slug>.md`
- **Format:** Markdown with YAML frontmatter

**Frontmatter Fields:**
```yaml
request_id: "APR-YYYYMMDD-HHMMSS-HASH"
created_at: "ISO8601 timestamp"
expires_at: "ISO8601 timestamp"
timeout_action: "reject | escalate | allow_with_warning"
status: "pending | approved | rejected | timeout | escalated"
action_type: "payment | email | social_media_post | deployment | data_modification | etc"
priority: "low | medium | high | critical"
approver: "approver@company.com"
approval_level: "manager | director | vp | cfo | cto | ceo"
approved_by: null  # Filled when approved
approved_at: null
rejected_by: null
rejected_at: null
rejection_reason: null
```

---

## Integration Points

**Upstream Skills:**
- `company_handbook_enforcer` → Detects policy violations → Triggers approval request creation
- `task_lifecycle_manager` → Task execution blocked → Triggers approval request creation

**Downstream Skills:**
- `vault_state_manager` → Reads approval status → Unblocks execution if approved
- `needs_action_triage` → May scan Pending_Approval/ for expired requests

**Related Skills:**
- `dashboard_writer` → Displays pending approvals count in dashboard

---

## Error Handling

**Common Errors:**

1. **Missing Required Fields:**
   ```
   Error: Approval request missing required field 'action.type'
   Solution: Ensure all required fields populated before calling skill
   ```

2. **Invalid Approver:**
   ```
   Error: Approver 'unknown@company.com' not found in directory
   Solution: Validate approver email against company directory
   ```

3. **File Write Failure:**
   ```
   Error: Permission denied writing to Pending_Approval/
   Solution: Ensure agent has write access to vault directory
   ```

4. **Notification Failure:**
   ```
   Warning: Email notification failed, approval request still created
   Solution: Approver must manually check Pending_Approval/ folder
   ```

---

## Configuration Examples

### Minimal Configuration (filesystem only):
```bash
VAULT_PATH="/path/to/vault"
```

### With Email Notifications:
```bash
VAULT_PATH="/path/to/vault"
APPROVAL_NOTIFY_EMAIL="manager@company.com"
SMTP_HOST="smtp.company.com"
SMTP_PORT="587"
SMTP_USER="agent@company.com"
SMTP_PASS="<secret>"
```

### With Slack Notifications:
```bash
VAULT_PATH="/path/to/vault"
APPROVAL_NOTIFY_SLACK_WEBHOOK="https://hooks.slack.com/services/XXX/YYY/ZZZ"
```

### Production Setup (full audit trail):
```bash
VAULT_PATH="/path/to/vault"
APPROVAL_DEFAULT_TIMEOUT_HOURS="4"
APPROVAL_AUTO_ESCALATE="true"
APPROVAL_ESCALATION_EMAIL="ceo@company.com"
APPROVAL_AUDIT_LOG_PATH="$VAULT_PATH/Audit_Logs"
APPROVAL_NOTIFY_EMAIL="approver@company.com"
APPROVAL_NOTIFY_SLACK_WEBHOOK="https://hooks.slack.com/services/XXX/YYY/ZZZ"
```

---

## Testing Checklist

Before deploying this skill:

- [ ] Verify `Pending_Approval/` folder exists and is writable
- [ ] Test approval file creation with all action types
- [ ] Verify unique ID generation (no collisions)
- [ ] Test approval workflow (manual edit of status field)
- [ ] Test rejection workflow (manual edit of status field)
- [ ] Test timeout expiration (mock timestamp)
- [ ] Verify email notifications sent (if configured)
- [ ] Verify Slack notifications sent (if configured)
- [ ] Test audit log entries created
- [ ] Verify checksum integrity detection
- [ ] Test with missing required fields (expect validation error)
- [ ] Test with invalid approver (expect validation error)

---

## Version History

- **v1.0.0** (2025-02-04): Initial release
  - Core approval request generation
  - YAML frontmatter structure
  - Markdown body templates
  - Notification support (email, Slack)
  - Audit trail integration
