# Approval Request Creator Skill

**Version:** 1.0.0
**Last Updated:** 2025-02-04

## Overview

The `approval_request_creator` skill generates formal, structured approval request files for any agent action that requires human authorization before execution. It creates markdown files in the `Pending_Approval/` folder with comprehensive metadata, reasoning, alternatives, and clear approval workflows.

---

## Quick Start

### Basic Usage

Create a payment approval request:

```javascript
const { createApprovalRequest } = require('./approval_request_creator');

const result = await createApprovalRequest({
  action: {
    type: "payment",
    description: "Process refund to customer John Doe",
    details: {
      amount: 1500.00,
      currency: "USD",
      recipient: "John Doe <john@example.com>",
      reason: "Product defect - customer complaint #12345"
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

console.log(`Approval request created: ${result.file_path}`);
console.log(`Request ID: ${result.request_id}`);
```

### Configuration

Add to `.env`:

```bash
# Required
VAULT_PATH="/absolute/path/to/vault"

# Optional
APPROVAL_DEFAULT_TIMEOUT_HOURS="4"
APPROVAL_NOTIFY_EMAIL="manager@company.com"
APPROVAL_AUTO_ESCALATE="true"
```

---

## Key Features

- **Structured Format**: Consistent markdown with YAML frontmatter
- **Unique IDs**: Cryptographically secure request IDs
- **Audit Trail**: Full audit log of requests, approvals, rejections
- **Clear Instructions**: Approvers know exactly how to approve/reject
- **Expiration Handling**: Automatic timeout and escalation
- **Notification Support**: Email and Slack notifications
- **Checksum Integrity**: Detect file tampering
- **Policy Linkage**: Reference to violated policy and handbook section

---

## Action Types Supported

| Action Type | Description | Example Use Case |
|------------|-------------|------------------|
| `payment` | Financial transactions | Process vendor payment |
| `refund` | Customer refunds | Issue refund for defective product |
| `bulk_email` | Mass customer emails | Send service outage notification |
| `social_media_post` | Public social posts | Publish product launch announcement |
| `database_migration` | Production schema changes | Add new database table |
| `api_key_rotation` | Credential rotation | Rotate Stripe API keys |
| `deployment` | Production deployments | Deploy v2.0 to production |
| `data_deletion` | Delete production data | Purge inactive user accounts |
| `access_grant` | Permission changes | Grant admin access to new employee |

---

## Approval Levels

| Level | Description | Typical Actions |
|-------|-------------|-----------------|
| `manager` | Team manager approval | Payments < $10K, non-critical deployments |
| `director` | Department director | Payments $10K-$50K, customer-facing comms |
| `vp` | VP-level approval | Payments $50K-$100K, major features |
| `cfo` | Chief Financial Officer | Payments > $100K, budget changes |
| `cto` | Chief Technology Officer | Infrastructure changes, security policies |
| `ceo` | Chief Executive Officer | Strategic decisions, partnerships |
| `ciso` | Chief Information Security Officer | Security policies, credential management |

---

## Output Format

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
action_type: "payment | email | deployment | etc"
priority: "low | medium | high | critical"
approver: "approver@company.com"
approval_level: "manager | director | vp | cfo | cto | ceo"
```

---

## Integration Points

**Upstream Skills:**
- `company_handbook_enforcer` → Detects violations → Triggers approval request
- `task_lifecycle_manager` → Task blocked → Triggers approval request

**Downstream Skills:**
- `vault_state_manager` → Reads approval status → Unblocks execution
- `needs_action_triage` → Scans Pending_Approval/ for expired requests

**Related Skills:**
- `dashboard_writer` → Displays pending approvals in dashboard

---

## Common Workflows

### 1. Payment Approval

```javascript
// Agent attempts payment
const paymentResult = await processPayment(5500.00, "Vendor Inc.");

// Payment blocked by policy enforcer
if (paymentResult.requires_approval) {
  const approval = await createApprovalRequest(paymentResult.approval_details);

  // Wait for approval
  const approved = await waitForApproval(approval.request_id);

  if (approved) {
    // Retry payment
    await processPayment(5500.00, "Vendor Inc.");
  }
}
```

### 2. Email Campaign Approval

```javascript
// Agent wants to send bulk email
const emailCampaign = {
  recipients: "all_customers@company.com",
  subject: "Important Service Update",
  body: "..."
};

// Request approval
const approval = await createApprovalRequest({
  action: { type: "bulk_email", details: emailCampaign },
  violation: { policy: "communication.mass_email_approval", ... },
  ...
});

console.log(`Email campaign pending approval: ${approval.request_id}`);
```

### 3. Polling for Approval

```javascript
async function waitForApproval(requestId, timeoutHours = 24) {
  const pollInterval = 5 * 60 * 1000;  // 5 minutes
  const startTime = Date.now();

  while (Date.now() - startTime < timeoutHours * 3600 * 1000) {
    const status = await checkApprovalStatus(requestId);

    if (status.approved) {
      return true;
    }

    if (status.rejected || status.timeout) {
      return false;
    }

    await sleep(pollInterval);
  }

  return false;  // Timeout
}
```

---

## Configuration Examples

### Minimal (filesystem only):
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

### Production Setup:
```bash
VAULT_PATH="/path/to/vault"
APPROVAL_DEFAULT_TIMEOUT_HOURS="4"
APPROVAL_AUTO_ESCALATE="true"
APPROVAL_ESCALATION_EMAIL="ceo@company.com"
APPROVAL_AUDIT_LOG_PATH="$VAULT_PATH/Audit_Logs"
APPROVAL_NOTIFY_EMAIL="approver@company.com"
APPROVAL_NOTIFY_SLACK_WEBHOOK="https://hooks.slack.com/..."
```

---

## Error Handling

**Common Errors:**

| Error | Cause | Solution |
|-------|-------|----------|
| `Missing required field 'action.type'` | Incomplete request | Validate all required fields |
| `Approver not found` | Invalid email | Check approver directory |
| `Permission denied` | No write access | Verify agent permissions |
| `Email notification failed` | SMTP error | Check SMTP configuration |
| `File already exists` | Naming collision | Append unique suffix |

---

## Testing Checklist

Before deploying:

- [ ] Verify `Pending_Approval/` folder writable
- [ ] Test approval file creation
- [ ] Test approval workflow (manual edit)
- [ ] Test rejection workflow
- [ ] Test timeout expiration
- [ ] Test email notifications
- [ ] Test Slack notifications
- [ ] Test audit log creation
- [ ] Test deduplication
- [ ] Test with invalid inputs

---

## Documentation

- **SKILL.md**: Complete skill specification and impact analysis
- **patterns.md**: Code examples and usage patterns
- **gotchas.md**: Common pitfalls and edge cases
- **impact-checklist.md**: Comprehensive checklist for production use

---

## Version History

- **v1.0.0** (2025-02-04): Initial release
  - Core approval request generation
  - YAML frontmatter structure
  - Markdown body templates
  - Notification support (email, Slack)
  - Audit trail integration

---

## Support

For issues or questions:
- Check the `gotchas.md` file for common problems
- Review `patterns.md` for usage examples
- Consult `impact-checklist.md` for production readiness
- File bug reports in project issue tracker
