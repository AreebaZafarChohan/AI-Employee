# Approval Request Creator - Impact Checklist

This checklist ensures comprehensive impact analysis when creating approval requests for sensitive actions.

---

## Pre-Request Setup

### Environment Configuration

- [ ] `VAULT_PATH` configured and points to valid vault directory
- [ ] `Pending_Approval/` folder exists and is writable by agent
- [ ] Approval timeout configured: `APPROVAL_DEFAULT_TIMEOUT_HOURS`
- [ ] Notification endpoints configured (optional):
  - [ ] Email: `APPROVAL_NOTIFY_EMAIL`
  - [ ] Slack: `APPROVAL_NOTIFY_SLACK_WEBHOOK`
- [ ] Escalation policy configured: `APPROVAL_AUTO_ESCALATE`
- [ ] Audit log path configured: `APPROVAL_AUDIT_LOG_PATH`
- [ ] Session ID available for audit trail: `APPROVAL_SESSION_ID`

### Approver Directory

- [ ] Approver email addresses validated against company directory
- [ ] Approval level mapping defined:
  - [ ] Manager → `manager@company.com`
  - [ ] Director → `director@company.com`
  - [ ] VP → `vp@company.com`
  - [ ] CFO → `cfo@company.com`
  - [ ] CTO → `cto@company.com`
  - [ ] CEO → `ceo@company.com`
- [ ] Out-of-office status checked for approvers
- [ ] Delegate assignments configured for unavailable approvers

---

## Action Classification

### Action Type Identification

- [ ] Action type identified and categorized:
  - [ ] Financial: `payment`, `refund`, `expense`
  - [ ] Communication: `email`, `slack_message`, `social_media_post`
  - [ ] Infrastructure: `deployment`, `database_migration`, `api_key_rotation`
  - [ ] Data: `data_deletion`, `data_modification`, `data_export`
  - [ ] Security: `access_grant`, `permission_change`, `credential_reset`
- [ ] Action priority determined: `low` | `medium` | `high` | `critical`
- [ ] Environment identified: `development` | `staging` | `production`
- [ ] Initiator agent recorded: `lex`, `planner`, `executor`, etc.

### Risk Assessment

- [ ] Business risk level assessed: `low` | `medium` | `high` | `critical`
- [ ] Customer impact evaluated
- [ ] Regulatory compliance checked (GDPR, SOC2, etc.)
- [ ] Brand reputation risk considered
- [ ] Financial exposure calculated
- [ ] Reversibility assessed (can action be undone?)

---

## Policy Violation Analysis

### Policy Identification

- [ ] Violated policy identified: `policy_key` (e.g., `financial.payment_limit`)
- [ ] Handbook section referenced: exact section path
- [ ] Violation severity assigned: `LOW` | `MEDIUM` | `HIGH` | `CRITICAL`
- [ ] Reasoning for violation clearly documented
- [ ] Impact assessment completed:
  - [ ] Business risk described
  - [ ] Affected stakeholders listed
  - [ ] Risk level quantified

### Threshold Checks

- [ ] Financial threshold checks (if applicable):
  - [ ] Amount: $______
  - [ ] Agent limit: $______
  - [ ] Approval required: YES / NO
  - [ ] Approval level: ______________
- [ ] Communication checks (if applicable):
  - [ ] Recipient count: ______
  - [ ] Public vs internal: ______________
  - [ ] Tone compliance: YES / NO
- [ ] Infrastructure checks (if applicable):
  - [ ] Environment: ______________
  - [ ] Downtime expected: ______________
  - [ ] Rollback plan available: YES / NO

---

## Justification Quality

### Business Reason

- [ ] Business reason clearly articulated
- [ ] Reason is specific (not vague or generic)
- [ ] Reason references contracts, SLAs, or policies
- [ ] Reason explains "why now" (urgency context)
- [ ] Reason is verifiable (can be fact-checked)

### Urgency Assessment

- [ ] Urgency level assigned: `low` | `medium` | `high` | `critical`
- [ ] Urgency justified with concrete deadline
- [ ] Customer impact documented (if applicable)
- [ ] Revenue impact quantified (if applicable)
- [ ] SLA implications stated (if applicable)

### Alternatives Evaluation

- [ ] Alternatives considered: YES / NO
- [ ] If YES: alternatives documented with rejection reasons
- [ ] If NO: reasoning for no alternatives provided
- [ ] Alternative pros/cons analyzed
- [ ] Lowest-risk alternative attempted first

---

## Approval Workflow Configuration

### Approver Selection

- [ ] Appropriate approver identified based on:
  - [ ] Action type
  - [ ] Risk level
  - [ ] Financial amount
  - [ ] Policy requirements
- [ ] Approver role validated: `manager` | `director` | `vp` | `cfo` | `cto` | `ceo`
- [ ] Approver email verified and active
- [ ] Approver availability checked (not on vacation/leave)
- [ ] Delegate identified if primary approver unavailable

### SLA Configuration

- [ ] SLA hours set appropriately:
  - [ ] Critical actions: 1-4 hours
  - [ ] High urgency: 4-12 hours
  - [ ] Medium urgency: 12-24 hours
  - [ ] Low urgency: 24-48 hours
  - [ ] C-level approvals: 24-48 hours (longer)
- [ ] Timeout action specified: `reject` | `escalate` | `allow_with_warning`
- [ ] Escalation path defined (if timeout action is `escalate`)
- [ ] Reminder schedule configured (e.g., 1 hour before expiry)

---

## Data Sanitization

### Sensitive Data Handling

- [ ] Action details sanitized before writing to file:
  - [ ] Passwords redacted: `[REDACTED]`
  - [ ] API keys redacted: `[REDACTED]`
  - [ ] Tokens redacted: `[REDACTED]`
  - [ ] Credit card numbers masked: `****-****-****-1234`
  - [ ] SSN/PII redacted: `[REDACTED]`
- [ ] Email content preview truncated (max 200 characters)
- [ ] SQL queries sanitized (parameters removed)
- [ ] Long text fields truncated (max 500 characters)

### Logging Safety

- [ ] No sensitive data logged to console
- [ ] No full action details logged
- [ ] No approval request IDs logged publicly
- [ ] Request ID logged only to secure audit trail
- [ ] Notification delivery status logged safely

---

## High-Risk Action Checks

### Rollback Plans (Required for High-Risk Actions)

- [ ] High-risk action identified (database, infrastructure, security)
- [ ] Rollback plan provided and non-empty
- [ ] Rollback plan tested in staging: YES / NO
- [ ] Rollback steps clearly documented
- [ ] Rollback time estimate provided
- [ ] Backup created before action (if applicable): YES / NO
- [ ] Backup verified and restorable: YES / NO

### Pre-Execution Validation

- [ ] Action tested in staging environment: YES / NO
- [ ] Peer review completed (if applicable): YES / NO
- [ ] Code review completed (if applicable): YES / NO
- [ ] Security scan completed (if applicable): YES / NO
- [ ] Load testing completed (if applicable): YES / NO
- [ ] Monitoring/alerts configured for action execution

---

## Notification Setup

### Email Notifications

- [ ] Email notification enabled: YES / NO
- [ ] SMTP configuration valid
- [ ] Approver email address verified
- [ ] Email template populated with all required fields
- [ ] Email subject clearly identifies action type and urgency
- [ ] Email body includes approval instructions
- [ ] Email includes direct link to approval file (if applicable)
- [ ] Retry logic configured (3 attempts with exponential backoff)

### Slack Notifications

- [ ] Slack notification enabled: YES / NO
- [ ] Slack webhook URL configured and valid
- [ ] Slack channel identified: ______________
- [ ] Slack message formatted with urgency indicators
- [ ] Slack message includes approval request ID
- [ ] Slack message includes approver mention (e.g., `@manager`)
- [ ] Retry logic configured (3 attempts with exponential backoff)

### Fallback Strategy

- [ ] Fallback notification method configured
- [ ] Dashboard alert configured (if all notifications fail)
- [ ] Manual notification plan documented
- [ ] Notification failure logged to audit trail

---

## File Creation Validation

### Filename Generation

- [ ] Filename follows convention: `YYYYMMDD-HHMMSS-<action-type>-<slug>.md`
- [ ] Unique suffix appended to prevent collisions
- [ ] Filename sanitized (no special characters, spaces replaced with hyphens)
- [ ] Filename length validated (max 255 characters)
- [ ] File extension is `.md`

### Frontmatter Validation

- [ ] All required frontmatter fields present:
  - [ ] `request_id`
  - [ ] `created_at`
  - [ ] `expires_at`
  - [ ] `timeout_action`
  - [ ] `status: pending`
  - [ ] `action_type`
  - [ ] `priority`
  - [ ] `approver`
  - [ ] `approval_level`
- [ ] ISO8601 timestamps used for all date fields
- [ ] Request ID is unique and follows convention
- [ ] Status is initially `pending`
- [ ] Optional fields set to `null` (not omitted)

### Markdown Body Validation

- [ ] Markdown structure follows template
- [ ] All sections present:
  - [ ] Action Details
  - [ ] Policy Violation
  - [ ] Justification
  - [ ] Approval Required
  - [ ] How to Approve or Reject
  - [ ] Approval Decision (empty, for approver notes)
  - [ ] Audit Trail
- [ ] Approval instructions clear and actionable
- [ ] Code examples provided for status updates
- [ ] Formatting correct (headings, lists, code blocks)

### File Write Validation

- [ ] File write successful (no permission errors)
- [ ] File exists at expected path
- [ ] File readable by approvers
- [ ] File permissions set correctly (rw-r--r--)
- [ ] File size reasonable (< 100KB)

---

## Audit Trail

### Audit Log Entry

- [ ] Audit log entry created for approval request
- [ ] Audit log includes:
  - [ ] Timestamp
  - [ ] Event type: `approval_request_created`
  - [ ] Request ID
  - [ ] Action type
  - [ ] Initiator agent
  - [ ] Approver
  - [ ] Session ID
  - [ ] IP address (if available)
  - [ ] User agent (if available)
- [ ] Audit log stored in secure location
- [ ] Audit log immutable (append-only)

### Traceability

- [ ] Request ID links to audit log entry
- [ ] Audit log links to approval file path
- [ ] Audit log links to action execution (if executed)
- [ ] Audit log retention policy applied
- [ ] Audit log indexed for search (optional)

---

## Post-Creation Checks

### Verification

- [ ] Approval file created successfully
- [ ] Request ID returned to caller
- [ ] Expiration timestamp calculated correctly
- [ ] Notifications sent successfully (or failures logged)
- [ ] Audit log entry created
- [ ] No errors or warnings during creation

### Monitoring Setup

- [ ] Approval request added to monitoring dashboard
- [ ] Expiration timer started
- [ ] Reminder notifications scheduled
- [ ] Escalation workflow triggered (if timeout occurs)
- [ ] Approval status polling configured

---

## Deduplication Checks

### Similar Approval Search

- [ ] Search for similar approvals in last 30 days
- [ ] Check both `Pending_Approval/` and `Approval_Archive/`
- [ ] Compare action type, amount, recipient, etc.
- [ ] If similar approval found:
  - [ ] Status: `approved` → Reuse existing approval
  - [ ] Status: `rejected` → Warn requester
  - [ ] Status: `pending` → Inform requester of duplicate
  - [ ] Status: `timeout` → Create new request
- [ ] Log duplicate detection to audit trail

---

## Testing Checklist (Before Production Use)

### Functional Tests

- [ ] Test approval request creation for each action type
- [ ] Test with minimal required fields
- [ ] Test with all optional fields populated
- [ ] Test with missing required fields (expect validation error)
- [ ] Test with invalid approver email (expect validation error)
- [ ] Test filename collision handling
- [ ] Test sensitive data sanitization
- [ ] Test timeout expiration and escalation
- [ ] Test approval status polling
- [ ] Test concurrent approval updates (race conditions)

### Notification Tests

- [ ] Test email notification success
- [ ] Test email notification failure + retry
- [ ] Test Slack notification success
- [ ] Test Slack notification failure + retry
- [ ] Test fallback notification strategy
- [ ] Test notification delivery confirmation

### Integration Tests

- [ ] Test integration with `company_handbook_enforcer`
- [ ] Test integration with `task_lifecycle_manager`
- [ ] Test integration with `vault_state_manager`
- [ ] Test integration with `dashboard_writer`
- [ ] Test audit log integration

### Edge Case Tests

- [ ] Test with very long action descriptions (> 1000 characters)
- [ ] Test with special characters in filenames
- [ ] Test with Unicode characters in content
- [ ] Test with concurrent approval requests (same second)
- [ ] Test with expired approval file (manual timestamp manipulation)
- [ ] Test with corrupted approval file (invalid YAML)
- [ ] Test with missing `Pending_Approval/` folder (auto-create)

---

## Production Readiness

### Configuration Review

- [ ] All environment variables reviewed and documented
- [ ] Approver directory up-to-date
- [ ] Notification endpoints tested and confirmed working
- [ ] Escalation policy reviewed with stakeholders
- [ ] SLA timeouts agreed upon by management
- [ ] Audit log retention policy defined

### Documentation

- [ ] Skill documentation complete and accurate
- [ ] Usage patterns documented with examples
- [ ] Gotchas and pitfalls documented
- [ ] Integration guide provided
- [ ] Troubleshooting guide available

### Monitoring & Alerting

- [ ] Dashboard displays pending approvals count
- [ ] Alerts configured for:
  - [ ] Expired approvals without escalation
  - [ ] Failed notification delivery
  - [ ] Duplicate approval requests
  - [ ] High volume of approval requests (potential abuse)
- [ ] Metrics tracked:
  - [ ] Average approval time by action type
  - [ ] Approval rejection rate
  - [ ] Timeout/escalation rate
  - [ ] Notification success rate

### Security Review

- [ ] Sensitive data sanitization validated
- [ ] Access controls reviewed (who can create/approve)
- [ ] Audit trail immutability confirmed
- [ ] Notification transport security confirmed (TLS)
- [ ] File permissions reviewed
- [ ] Path traversal vulnerabilities mitigated

---

## Cleanup & Maintenance

### Periodic Cleanup

- [ ] Cleanup schedule defined (daily/weekly)
- [ ] Archive policy defined:
  - [ ] Approved requests archived after ___ days
  - [ ] Rejected requests archived after ___ days
  - [ ] Expired requests archived after ___ days
- [ ] Archive location configured: `Approval_Archive/`
- [ ] Archive retention policy defined (e.g., 1 year)
- [ ] Cleanup job automated (cron, scheduled task)

### Health Checks

- [ ] Daily health check: `Pending_Approval/` folder accessible
- [ ] Daily health check: No permission errors in logs
- [ ] Weekly review: Expired approvals without escalation
- [ ] Weekly review: Average approval time by approver
- [ ] Monthly review: Approval policies and thresholds
- [ ] Quarterly review: Approver directory accuracy

---

## Example Validation Checklist for Payment Approval

**Action:** Process payment of $5,500 to Acme Vendors Inc.

### Pre-Checks
- [x] Action type: `payment`
- [x] Amount: $5,500
- [x] Agent limit: $1,000
- [x] Approval required: YES (exceeds limit)
- [x] Approval level: `manager` (< $10,000)
- [x] Environment: `production`

### Policy Violation
- [x] Policy: `financial.payment_limit_without_approval`
- [x] Severity: `MEDIUM` (< $10,000)
- [x] Impact: Business risk = "Unauthorized expense if not approved"

### Justification
- [x] Business reason: "Q1 2025 service contract payment per signed agreement"
- [x] Urgency: `medium` (not critical)
- [x] Customer impact: "None - internal vendor payment"
- [x] Alternatives considered: NO (contractual obligation)

### Approver
- [x] Approver: `manager@company.com`
- [x] Email verified: YES
- [x] Out-of-office: NO
- [x] SLA: 24 hours (medium urgency)

### Data Sanitization
- [x] No sensitive data in payment details
- [x] Vendor name safe to log
- [x] Invoice number safe to log

### High-Risk Checks
- [ ] N/A - payment action is not high-risk

### Notifications
- [x] Email notification enabled
- [x] Slack notification enabled
- [x] Retry logic configured

### Result
✅ Approval request created: `APR-20250204-143022-ABC123`
✅ File: `Pending_Approval/20250204-143022-payment-acme-vendors.md`
✅ Email sent to: `manager@company.com`
✅ Slack notification posted to: `#approvals`
✅ Audit log entry created
