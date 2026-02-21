# Company Handbook Template

This template provides a structured format for creating a machine-readable company handbook that can be enforced by the Company Handbook Enforcer skill.

---

## YAML Front Matter (Machine-Readable Policies)

```yaml
---
handbook_version: "1.0.0"
last_updated: "2024-01-15"
enforcement_level: "STRICT"  # STRICT | WARN | SUGGEST

# Communication Guidelines
communication:
  tone: "professional, empathetic, clear"
  prohibited_phrases:
    - "URGENT"
    - "ASAP"
    - "IMMEDIATELY"
    - "CRITICAL"
    - "FIX THIS NOW"
  required_elements:
    - greeting
    - clear_explanation
    - next_steps
    - contact_info
  customer_facing:
    response_time: "4 hours"
    tone: "empathetic and helpful"
    language: "plain English, no jargon"
  internal:
    response_time: "24 hours"
    tone: "professional and direct"
    language: "technical terms acceptable"

# Financial Policies
financial:
  payment_limit_without_approval:
    amount: 1000
    currency: "USD"
  approval_required_at_or_above:
    amount: 1000
    currency: "USD"
    approver: "finance-manager"
    sla_hours: 4
  critical_approval_above:
    amount: 10000
    currency: "USD"
    approver: "cfo"
    sla_hours: 24
  prohibited_transactions:
    - "cryptocurrency payments"
    - "unverified vendors"
    - "personal expenses"
  expense_categories:
    software: 5000
    hardware: 2000
    travel: 3000
    marketing: 10000

# Privacy & Security
privacy:
  pii_types:
    - "SSN"
    - "credit_card"
    - "email"
    - "phone_number"
    - "physical_address"
    - "medical_records"
    - "financial_data"
  encryption:
    at_rest: "required"
    in_transit: "required (TLS 1.2+)"
  prohibited_storage:
    - "SSN in plain text"
    - "passwords without hashing"
    - "credit card numbers (full)"
    - "unencrypted PII"
  data_retention:
    logs: "30 days"
    customer_data: "7 years"
    financial_records: "7 years"
    employee_data: "7 years post-termination"
  access_control:
    authentication: "required for all sensitive data"
    authorization: "role-based (RBAC)"
    audit_logging: "required"

# Operational Constraints
operational:
  deployment_windows:
    allowed:
      - day: "Tuesday"
        start: "10:00:00Z"
        end: "16:00:00Z"
      - day: "Wednesday"
        start: "10:00:00Z"
        end: "16:00:00Z"
      - day: "Thursday"
        start: "10:00:00Z"
        end: "16:00:00Z"
  change_freeze_periods:
    - name: "Holiday Freeze"
      start: "2024-12-15"
      end: "2025-01-05"
    - name: "Q4 Close"
      start: "2024-12-28"
      end: "2025-01-03"
  sla_response_times:
    critical: "1 hour"
    high: "4 hours"
    medium: "24 hours"
    low: "5 business days"
  customer_notification:
    service_outage: "requires manager approval"
    planned_maintenance: "48 hours advance notice"
    security_incident: "requires legal and PR approval"

# Ethical Guidelines
ethical:
  ai_usage:
    transparency: "required for customer-facing AI decisions"
    human_in_loop: "required for critical decisions"
    bias_detection: "quarterly audits"
    explainability: "required for automated decisions"
  automated_decisions:
    financial:
      requires_human_review: true
      appeal_process: true
    hiring:
      requires_human_review: true
      bias_audit: "required"
    customer_service:
      escalation_path: "human agent within 2 interactions"
  data_usage:
    customer_consent: "required for non-essential use"
    anonymization: "required for analytics"
    third_party_sharing: "requires explicit consent"
---
```

---

## Human-Readable Documentation

### 1. Communication Guidelines

#### Tone and Language

All company communications, whether internal or customer-facing, must maintain a professional, empathetic, and clear tone.

**Prohibited Phrases:**

The following phrases create unnecessary pressure and should be avoided:
- **URGENT** - Use "Important" or "High Priority" instead
- **ASAP** / **IMMEDIATELY** - Provide specific deadlines (e.g., "by 5:00 PM today")
- **CRITICAL** / **FIX THIS NOW** - Use "High Priority" and explain impact

**Required Elements for Customer-Facing Communications:**

Every customer communication must include:
1. **Greeting** - Personalized when possible (e.g., "Dear [Customer Name]")
2. **Clear Explanation** - What happened, why it matters, what we're doing
3. **Next Steps** - Specific actions required by customer or expected timeline
4. **Contact Info** - How to reach us for questions or support

**Example - Non-Compliant:**
```
URGENT: Your order failed. Fix your payment ASAP!
```

**Example - Compliant:**
```
Important: Action Required by End of Day

Dear [Customer Name],

We were unable to process your order #12345 due to a payment authorization issue.

What this means for you:
- Your order is on hold
- No charges have been made to your account
- You can resolve this by updating your payment method

Next steps:
1. Visit your account settings: [link]
2. Update your payment information
3. Resubmit your order

If you need assistance, please contact us at support@company.com or call 1-800-555-0100.

Best regards,
[Company Name] Team
```

#### Internal Communications

Internal communications can use technical terminology and be more direct, but must still maintain professionalism.

**Response Time Expectations:**
- Customer-facing: 4 hours during business hours
- Internal: 24 hours (1 business day)

---

### 2. Financial Policies

#### Payment Authorization Limits

**Without Approval:**
- Up to $999.99 USD: Can be processed immediately by authorized personnel

**Requires Finance Manager Approval:**
- $1,000 - $9,999.99 USD
- SLA: 4 hours for approval response
- Approval request must include: amount, reason, customer/vendor, business justification

**Requires CFO Approval:**
- $10,000+ USD
- SLA: 24 hours for approval response
- Requires detailed business case and ROI justification

#### Prohibited Transactions

The following transaction types are prohibited without executive approval:
- Cryptocurrency payments (volatility and regulatory risk)
- Unverified vendors (due diligence required first)
- Personal expenses (must be through expense reimbursement system)

#### Expense Categories and Limits

Each department has budget authority within these limits per quarter:
- **Software/SaaS**: $5,000 per approval
- **Hardware**: $2,000 per purchase
- **Travel**: $3,000 per trip
- **Marketing**: $10,000 per campaign

**Example - Compliant Workflow:**
```
1. Employee requests $1,500 software subscription
2. Request routed to Finance Manager
3. Manager reviews justification and budget
4. Approval granted within 4 hours
5. Payment processed with approval reference
6. Transaction logged in financial system
```

---

### 3. Privacy & Security

#### Personally Identifiable Information (PII)

The following data types are classified as PII and must be protected:
- Social Security Numbers (SSN)
- Credit card numbers
- Email addresses (when linked to identity)
- Phone numbers
- Physical addresses
- Medical records
- Financial data (account numbers, balances, transactions)

#### Encryption Requirements

**At Rest:**
- All PII must be encrypted when stored in databases
- Encryption standard: AES-256 or equivalent
- Encryption keys must be stored in secure key management system (e.g., AWS KMS, HashiCorp Vault)

**In Transit:**
- All data transmission must use TLS 1.2 or higher
- No plain text transmission of PII over any network
- Internal service-to-service communication must use mutual TLS

#### Prohibited Storage Practices

The following practices are prohibited:
- Storing SSN in plain text (always encrypt)
- Storing passwords without hashing (use bcrypt, scrypt, or Argon2)
- Storing full credit card numbers (use tokenization, store last 4 digits only)
- Logging PII in application logs (sanitize before logging)

#### Data Retention

- **Application Logs**: 30 days, then delete
- **Customer Data**: 7 years (regulatory requirement)
- **Financial Records**: 7 years (tax and audit requirements)
- **Employee Data**: 7 years post-termination (legal requirement)

#### Access Control

- **Authentication**: Required for all access to systems containing sensitive data
- **Authorization**: Role-Based Access Control (RBAC) enforced
- **Audit Logging**: All access to PII must be logged (who, what, when)

**Example - Compliant PII Handling:**
```javascript
// CORRECT: Encrypt before storing
const encryptedSSN = await encrypt(ssn, encryptionKey);
await db.customers.update({
  id: customerId,
  ssn_encrypted: encryptedSSN
});

// CORRECT: Never log PII
logger.info('Customer updated', {
  customer_id: customerId,
  fields_updated: ['ssn']  // Don't log actual SSN
});
```

---

### 4. Operational Constraints

#### Deployment Windows

To minimize risk and ensure support coverage, production deployments are only allowed during these windows:

**Allowed:**
- Tuesday: 10:00 AM - 4:00 PM UTC
- Wednesday: 10:00 AM - 4:00 PM UTC
- Thursday: 10:00 AM - 4:00 PM UTC

**Prohibited:**
- Monday (highest traffic day, recent code changes risky)
- Friday (support availability lower over weekend)
- Saturday/Sunday (limited support staff)
- Outside 10:00-16:00 UTC (to ensure overlap with all timezones)

**Exceptions:**
- Critical security hotfixes (requires CTO approval)
- Emergency production fixes (requires incident commander approval)

#### Change Freeze Periods

No deployments or infrastructure changes during these periods:

**Holiday Freeze:**
- December 15 - January 5 (annually)
- Reason: Reduced staff, high customer usage

**Quarter-End Freeze:**
- Last 3 business days of each quarter
- Reason: Financial close processes, reporting

#### SLA Response Times

**Critical Issues** (production down, security breach, data loss):
- Response: 1 hour
- Resolution target: 4 hours
- Escalation: Immediate to engineering lead and CTO

**High Priority** (major feature broken, performance degraded):
- Response: 4 hours
- Resolution target: 24 hours
- Escalation: After 8 hours to engineering manager

**Medium Priority** (minor bug, non-critical feature issue):
- Response: 24 hours
- Resolution target: 5 business days

**Low Priority** (enhancement request, minor UI issue):
- Response: 5 business days
- Resolution target: Next sprint planning

#### Customer Notifications

**Service Outage:**
- Requires: Manager approval
- Timeline: Notify within 1 hour of detection
- Template: Use approved incident communication template

**Planned Maintenance:**
- Requires: 48 hours advance notice to customers
- Schedule: During lowest traffic window (identify via analytics)
- Template: Include start time, duration, expected impact, alternative options

**Security Incident:**
- Requires: Legal and PR approval
- Timeline: Determined by legal counsel (varies by incident severity)
- Template: Legal to review all communications

---

### 5. Ethical Guidelines

#### AI Usage Boundaries

Our company uses AI to enhance productivity and decision-making, but with ethical guardrails:

**Transparency:**
- Customers must be informed when interacting with AI systems
- AI-generated content must be labeled as such
- Decision logic must be explainable to affected parties

**Human-in-the-Loop:**
- Critical decisions (financial, hiring, termination, legal) require human review
- AI can provide recommendations, but human makes final decision
- Override mechanism available for all automated decisions

**Bias Detection:**
- Quarterly audits of AI systems for demographic bias
- Training data reviewed for representativeness
- Outcomes monitored for disparate impact

#### Automated Decision Making

**Financial Decisions:**
- Loan approvals, credit limits, pricing → Requires human review
- Fraud detection → AI can flag, human decides on account suspension
- Payment processing → AI can authorize up to policy limits, escalate above

**Hiring Decisions:**
- Resume screening → AI can shortlist, human makes interview decisions
- Interview scoring → AI can provide insights, human makes hire/no-hire decision
- Salary offers → AI can suggest range, human negotiates and finalizes

**Customer Service:**
- AI can handle routine inquiries (FAQs, order status, account info)
- Escalation required within 2 interactions if AI cannot resolve
- Human agent can take over any conversation at customer request

#### Data Usage Ethics

**Customer Consent:**
- Essential use (service delivery) → Implied consent acceptable
- Non-essential use (analytics, marketing, research) → Explicit consent required
- Third-party sharing → Always requires explicit consent

**Anonymization:**
- Analytics and reporting → Data must be anonymized or aggregated
- No individual customer identifiable in reports
- Exception: Customer support cases (with customer permission)

**Third-Party Sharing:**
- Never share PII without explicit customer consent
- Data sharing agreements must be reviewed by legal
- Customers must be able to opt-out of third-party sharing

---

## Policy Enforcement

This handbook is enforced through:
1. **Automated validation** - Company Handbook Enforcer skill validates all agent actions
2. **Code reviews** - Engineers review code for policy compliance
3. **Quarterly audits** - Compliance team audits adherence to policies
4. **Training** - All employees complete handbook training annually

**Violations:**
- Documented in compliance system
- Escalated to manager and compliance team
- Remediation plan required
- Repeated violations may result in disciplinary action

**Policy Updates:**
- Proposed by any employee via handbook update request
- Reviewed by legal, compliance, and affected departments
- Approved by executive team
- Communicated to all employees 30 days before enforcement

---

## Handbook Revision History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0.0 | 2024-01-15 | Initial handbook creation | Legal & Compliance Team |

---

## Questions or Clarifications

For questions about this handbook or to request policy clarifications:
- Email: compliance@company.com
- Slack: #company-policies
- Internal wiki: https://wiki.company.com/handbook

---
