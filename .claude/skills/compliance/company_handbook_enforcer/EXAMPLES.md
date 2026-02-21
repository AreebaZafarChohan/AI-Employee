# Company Handbook Enforcer - Examples

Real-world examples demonstrating the Company Handbook Enforcer skill in action.

---

## Example 1: Customer Email Validation

### Scenario
Agent attempts to send an urgent customer notification about a service issue.

### Original Action
```javascript
{
  type: "email",
  to: "customer@example.com",
  subject: "URGENT: Service Issue",
  body: "Your service is down! Fix your payment ASAP or we'll suspend your account immediately!"
}
```

### Validation Result
```json
{
  "compliant": false,
  "severity": "HIGH",
  "violations": [
    {
      "policy": "communication.prohibited_phrases",
      "description": "Email contains prohibited phrases",
      "prohibited_found": ["URGENT", "ASAP", "immediately"],
      "reasoning": "These phrases create unnecessary pressure and violate communication guidelines"
    },
    {
      "policy": "communication.required_elements",
      "description": "Missing required elements",
      "missing": ["greeting", "clear_explanation", "next_steps", "contact_info"],
      "reasoning": "Customer communications must include all required elements"
    },
    {
      "policy": "communication.tone",
      "description": "Tone is threatening rather than empathetic",
      "reasoning": "Threatens suspension without offering help"
    }
  ]
}
```

### Suggested Alternative
```
Subject: Important: Payment Update Required by 5:00 PM Today

Dear [Customer Name],

We noticed an issue with processing your payment for [Service Name], which is affecting your service access.

What this means for you:
- Your current payment method was declined
- Service access may be limited until resolved
- No action has been taken yet on your account

Next steps to resolve:
1. Update your payment method at: [secure link]
2. Verify billing information is current
3. If resolved by 5:00 PM today, no service interruption

We're here to help:
- Email: support@company.com
- Phone: 1-800-555-0100 (Mon-Fri 9am-5pm)
- Live chat: [link] (available 24/7)

We value your business and want to ensure uninterrupted service.

Best regards,
[Company Name] Customer Success Team
```

### Outcome
```
✅ COMPLIANCE ACHIEVED

Changes made:
- Removed "URGENT" → Used "Important"
- Removed "ASAP" → Specific deadline "5:00 PM today"
- Removed "immediately" → Clear timeline provided
- Added greeting: "Dear [Customer Name]"
- Added clear explanation of issue
- Added specific next steps (numbered list)
- Added multiple contact options
- Changed tone from threatening to helpful
```

---

## Example 2: Payment Authorization

### Scenario
Agent attempts to process a customer refund exceeding authorization limit.

### Original Action
```javascript
{
  type: "payment",
  action: "refund",
  amount: 5000,
  currency: "USD",
  customer_id: "CUST-12345",
  reason: "Service outage compensation"
}
```

### Validation Result
```json
{
  "compliant": false,
  "severity": "HIGH",
  "violations": [
    {
      "policy": "financial.payment_limit_without_approval",
      "description": "Payment exceeds authorization limit",
      "current_value": 5000,
      "required_value": 1000,
      "excess_amount": 4000,
      "reasoning": "Payments above $1,000 require Finance Manager approval"
    }
  ],
  "approval": {
    "required": true,
    "approver": "finance-manager",
    "sla_hours": 4,
    "request_id": "APR-78901"
  }
}
```

### Approval Request Generated
```json
{
  "request_id": "APR-78901",
  "created_at": "2024-01-15T10:30:00Z",
  "expires_at": "2024-01-15T14:30:00Z",
  "action": {
    "type": "payment",
    "amount": 5000,
    "currency": "USD",
    "description": "Customer refund for service outage"
  },
  "justification": {
    "business_reason": "Major service outage affected customer's business operations",
    "urgency": "high",
    "customer_impact": "Customer lost revenue due to 6-hour service outage",
    "alternative_considered": false,
    "alternative_rejected_reason": "No lower compensation amount is appropriate for this level of outage"
  },
  "violation": {
    "policy": "financial.payment_limit_without_approval",
    "severity": "HIGH",
    "reasoning": "Amount ($5,000) exceeds authorization limit ($1,000) by $4,000"
  },
  "approval": {
    "required_approver": "finance-manager@company.com",
    "approval_level": "manager",
    "sla_hours": 4,
    "status": "pending"
  }
}
```

### Approval Flow
```
1. 10:30 AM: Approval request created
2. 10:31 AM: Email sent to finance-manager@company.com
3. 10:31 AM: Slack notification sent to #finance-approvals
4. 11:45 AM: Finance manager views request
5. 12:00 PM: Finance manager approves with justification:
   "Approved. Customer is enterprise tier, outage was our fault,
    compensation is appropriate per SLA."
6. 12:01 PM: Agent notified of approval
7. 12:02 PM: Payment processed with approval reference: APR-78901
8. 12:02 PM: Audit log updated with complete trail
```

### Outcome
```
✅ COMPLIANCE ACHIEVED WITH APPROVAL

Timeline:
- Request submitted: 10:30 AM
- Approval received: 12:00 PM
- Payment processed: 12:02 PM
- Total time: 1 hour 32 minutes (within 4-hour SLA)

Audit trail:
- Request ID: APR-78901
- Approver: finance-manager@company.com
- Approval reason: Per enterprise SLA
- Payment reference: PAY-45678-APR-78901
```

---

## Example 3: PII Storage Violation

### Scenario
Agent attempts to store customer Social Security Number without encryption.

### Original Action
```javascript
await db.customers.update({
  id: 'CUST-12345',
  ssn: '123-45-6789',  // Plain text storage
  email: 'customer@example.com',
  phone: '555-1234'
});

logger.info('Customer updated', {
  customer_id: 'CUST-12345',
  ssn: '123-45-6789',  // PII in logs
  changes: ['ssn', 'email', 'phone']
});
```

### Validation Result
```json
{
  "compliant": false,
  "severity": "CRITICAL",
  "violations": [
    {
      "policy": "privacy.prohibited_storage",
      "description": "PII stored in plain text",
      "pii_type": "SSN",
      "reasoning": "SSN must be encrypted before storage per privacy policy",
      "impact": {
        "business_risk": "GDPR/CCPA violation, potential data breach liability",
        "affected_stakeholders": ["customer", "legal", "compliance"],
        "remediation_required": true
      }
    },
    {
      "policy": "privacy.pii_handling",
      "description": "PII logged in plain text",
      "pii_types": ["SSN"],
      "reasoning": "PII must never appear in application logs",
      "impact": {
        "business_risk": "PII exposure in log aggregation systems",
        "affected_stakeholders": ["customer", "security"],
        "remediation_required": true
      }
    }
  ]
}
```

### Suggested Alternative
```javascript
// ✅ COMPLIANT: Encrypt before storage
const encryptedSSN = await encrypt(
  '123-45-6789',
  process.env.ENCRYPTION_KEY
);

await db.customers.update({
  id: 'CUST-12345',
  ssn_encrypted: encryptedSSN,  // Encrypted storage
  email: 'customer@example.com',
  phone: '555-1234'
});

// ✅ COMPLIANT: Never log PII
logger.info('Customer PII updated', {
  customer_id: 'CUST-12345',
  fields_updated: ['ssn', 'email', 'phone'],
  // PII values NOT logged
});

// ✅ COMPLIANT: Audit log for PII access
await auditLog.record({
  event: 'pii_update',
  customer_id: 'CUST-12345',
  fields: ['ssn'],
  user: currentUser.id,
  timestamp: new Date().toISOString()
});
```

### Implementation Steps
```
Step 1: Set up encryption key
- Store in environment variable or secrets manager
- Never hardcode in source code
- Rotate periodically per security policy

Step 2: Encrypt PII before storage
- Use AES-256 or equivalent
- Store in dedicated encrypted field (ssn_encrypted)
- Never store plain text alongside encrypted

Step 3: Remove PII from logs
- Sanitize log messages
- Use customer_id instead of PII values
- Review all logging statements

Step 4: Add audit logging
- Track all PII access (read/write)
- Include user, timestamp, operation
- Store in tamper-evident log
```

### Outcome
```
✅ COMPLIANCE ACHIEVED

Security improvements:
- SSN encrypted with AES-256
- Encryption key in AWS KMS
- No PII in application logs
- Audit logging enabled for all PII access
- Access controls updated (RBAC)

Compliance verification:
- Privacy policy requirement: MET
- Encryption at rest: MET
- PII logging prohibition: MET
- Audit trail requirement: MET
```

---

## Example 4: Deployment Window Violation

### Scenario
Agent attempts to deploy to production on Friday evening.

### Original Action
```javascript
{
  type: "deployment",
  environment: "production",
  scheduled_time: "2024-01-19T18:00:00Z",  // Friday 6:00 PM UTC
  changes: ["feature-x", "bug-fix-y"],
  rollback_plan: "automated"
}
```

### Validation Result
```json
{
  "compliant": false,
  "severity": "HIGH",
  "violations": [
    {
      "policy": "operational.deployment_windows",
      "description": "Deployment outside allowed window",
      "scheduled": "Friday 18:00 UTC",
      "allowed_windows": [
        "Tuesday 10:00-16:00 UTC",
        "Wednesday 10:00-16:00 UTC",
        "Thursday 10:00-16:00 UTC"
      ],
      "reasoning": "Friday deployments prohibited to ensure support coverage over weekend"
    }
  ],
  "alternative": {
    "available": true,
    "next_allowed_time": "2024-01-23T10:00:00Z",  // Following Tuesday
    "description": "Schedule for next available deployment window"
  }
}
```

### Agent Response
```
❌ DEPLOYMENT BLOCKED: Outside allowed window

Your requested deployment:
- Scheduled: Friday, Jan 19, 2024 at 6:00 PM UTC
- Environment: Production

Policy violation:
- Allowed windows: Tuesday-Thursday, 10:00 AM - 4:00 PM UTC
- Reason: Friday deployments risk weekend incidents with limited support

Next available window:
- Tuesday, Jan 23, 2024 at 10:00 AM UTC (4 days from now)

Is this a critical hotfix that requires immediate deployment?
Options:
1. Reschedule to Tuesday 10:00 AM UTC (recommended)
2. Request emergency deployment approval (CTO authorization required)
3. Deploy to staging for validation, schedule production for Tuesday
```

### User Selection: Critical Hotfix
```
User: "This is a critical security hotfix that must be deployed immediately."

Agent: "Creating emergency deployment approval request..."
```

### Emergency Approval Request
```json
{
  "request_id": "EMERG-99123",
  "created_at": "2024-01-19T17:00:00Z",
  "priority": "critical",
  "action": {
    "type": "deployment",
    "environment": "production",
    "scheduled_time": "2024-01-19T18:00:00Z"
  },
  "justification": {
    "business_reason": "Critical security vulnerability fix (CVE-2024-XXXXX)",
    "urgency": "critical",
    "customer_impact": "All customers at risk of data breach if not patched immediately",
    "alternative_considered": true,
    "alternative_rejected_reason": "Waiting until Tuesday leaves 4-day exposure window"
  },
  "violation": {
    "policy": "operational.deployment_windows",
    "severity": "HIGH",
    "override_required": true
  },
  "approval": {
    "required_approver": "cto@company.com",
    "approval_level": "cto",
    "sla_hours": 1,
    "status": "pending"
  }
}
```

### Outcome (Approved)
```
✅ EMERGENCY DEPLOYMENT APPROVED

Approval details:
- Request ID: EMERG-99123
- Approver: CTO
- Approved at: 5:15 PM UTC (15 minutes)
- Justification: "Approved. Security vulnerability requires immediate patch.
                 Ensure on-call team is standing by."

Deployment proceed:
- Scheduled: Friday 6:00 PM UTC (as requested)
- Approval reference: EMERG-99123
- On-call team: Notified and standing by
- Rollback plan: Automated (tested in staging)

Audit trail: Complete
```

---

## Example 5: Multi-Policy Violation

### Scenario
Agent attempts to send marketing email to customer list without proper consent checks.

### Original Action
```javascript
{
  type: "marketing_email",
  to: ["all_customers"],  // ~10,000 recipients
  subject: "URGENT: Limited Time Offer - Act Now!",
  body: "Don't miss out! Buy now or regret it forever!",
  consent_verified: false,
  unsubscribe_link: false
}
```

### Validation Result
```json
{
  "compliant": false,
  "severity": "CRITICAL",
  "violations": [
    {
      "policy": "communication.prohibited_phrases",
      "description": "Marketing content uses prohibited phrases",
      "prohibited_found": ["URGENT", "Act Now", "Don't miss out"],
      "reasoning": "Creates false urgency, violates communication guidelines"
    },
    {
      "policy": "ethical.data_usage",
      "description": "Customer consent not verified",
      "reasoning": "Marketing emails require explicit customer consent per GDPR/CCPA",
      "impact": {
        "business_risk": "Regulatory violation, potential fines up to $43M (GDPR)",
        "affected_stakeholders": ["all_customers", "legal", "marketing"],
        "remediation_required": true
      }
    },
    {
      "policy": "legal.marketing_compliance",
      "description": "Missing required unsubscribe link",
      "reasoning": "CAN-SPAM Act requires unsubscribe link in all marketing emails",
      "impact": {
        "business_risk": "Federal law violation, up to $46,517 per email",
        "affected_stakeholders": ["legal", "compliance"],
        "remediation_required": true
      }
    },
    {
      "policy": "operational.customer_notification",
      "description": "Mass communication requires approval",
      "reasoning": "Emails to >1,000 recipients require marketing manager approval",
      "approval_required": true
    }
  ]
}
```

### Suggested Alternative
```javascript
{
  type: "marketing_email",

  // ✅ Filter to only opted-in customers
  to: await db.customers.find({
    marketing_consent: true,
    consent_date: { $gte: new Date('2024-01-01') },
    unsubscribed: false
  }),  // ~3,500 recipients (verified consent)

  subject: "Exclusive Offer for Our Valued Customers",

  body: `
    Dear [Customer Name],

    As a valued customer, you're invited to take advantage of our new product offering.

    What's included:
    - [Feature 1]
    - [Feature 2]
    - [Feature 3]

    Special pricing available until January 31, 2024.

    Learn more: [link]

    Questions? Reply to this email or contact us at sales@company.com.

    ---
    You're receiving this because you opted in to marketing communications.
    Unsubscribe: [unsubscribe_link]
    Update preferences: [preferences_link]

    Best regards,
    [Company] Team
  `,

  // ✅ Required compliance fields
  consent_verified: true,
  unsubscribe_link: true,
  sender_address: "123 Main St, City, ST 12345",  // Required by CAN-SPAM
  marketing_manager_approval: "pending"
}
```

### Compliance Checklist
```
Before sending:
- [ ] Recipients filtered to opted-in only (3,500 from 10,000)
- [ ] Consent timestamp within last 2 years (verified)
- [ ] Unsubscribe link present and functional
- [ ] Physical mailing address included (CAN-SPAM requirement)
- [ ] Subject line not deceptive
- [ ] "Marketing" label clear (not disguised as transactional)
- [ ] Prohibited phrases removed
- [ ] Marketing manager approval obtained
- [ ] Scheduled for appropriate time (business hours in recipient timezone)

Approval workflow:
1. Submit for marketing manager review
2. Legal review (for new campaigns)
3. Final approval
4. Send to opted-in list only
```

### Outcome
```
✅ COMPLIANCE ACHIEVED WITH REVISIONS

Changes made:
1. Recipient list filtered: 10,000 → 3,500 (consent verified)
2. Subject changed: Removed "URGENT"
3. Body rewritten: Removed pressure tactics
4. Added unsubscribe link (required)
5. Added physical address (CAN-SPAM)
6. Submitted for marketing manager approval

Risk mitigation:
- GDPR/CCPA violation risk: ELIMINATED (consent verified)
- CAN-SPAM violation risk: ELIMINATED (all requirements met)
- Regulatory fine risk: ELIMINATED
- Reputational damage risk: MINIMIZED (professional tone)

Approval status: PENDING
- Approver: marketing-manager@company.com
- SLA: 4 hours
- Can send once approved
```

---

## Example 6: Context-Aware Validation (Multi-Environment)

### Scenario
Same deployment action validated in different environments.

### Action (Identical)
```javascript
{
  type: "deployment",
  code_version: "v2.5.0",
  changes: ["new-feature-x", "performance-improvements"],
  tests_passed: true
}
```

### Development Environment
```json
{
  "environment": "development",
  "enforcement_level": "SUGGEST",
  "validation_result": {
    "compliant": true,
    "severity": "PASS",
    "suggestions": [
      "Consider adding integration tests for new-feature-x",
      "Performance benchmarks recommended before production"
    ],
    "action": "ALLOWED"
  }
}
```

### Staging Environment
```json
{
  "environment": "staging",
  "enforcement_level": "WARN",
  "validation_result": {
    "compliant": false,
    "severity": "MEDIUM",
    "violations": [
      {
        "policy": "operational.pre_production_validation",
        "description": "No performance benchmarks recorded",
        "reasoning": "Performance improvements should be quantified before production",
        "action": "WARN"
      }
    ],
    "warnings": [
      "Deployment allowed but performance benchmarks recommended"
    ],
    "action": "ALLOWED_WITH_WARNING"
  }
}
```

### Production Environment
```json
{
  "environment": "production",
  "enforcement_level": "STRICT",
  "validation_result": {
    "compliant": false,
    "severity": "HIGH",
    "violations": [
      {
        "policy": "operational.deployment_windows",
        "description": "Deployment attempted at 9:00 AM UTC (Monday)",
        "reasoning": "Monday deployments prohibited (high traffic, recent code risky)"
      },
      {
        "policy": "operational.pre_production_validation",
        "description": "No performance benchmarks recorded",
        "reasoning": "Performance improvements must be quantified and validated in staging",
        "remediation_required": true
      }
    ],
    "action": "BLOCKED",
    "alternative": {
      "available": true,
      "description": "1. Run performance benchmarks in staging\n2. Document improvements\n3. Schedule deployment for Tuesday 10:00 AM UTC"
    }
  }
}
```

### Key Insight
Same action, different enforcement based on environment:
- **Development**: Allowed with suggestions
- **Staging**: Allowed with warnings
- **Production**: Blocked until compliance achieved

---

## Summary

These examples demonstrate:

1. **Communication Validation**: Prohibited phrases, tone, required elements
2. **Financial Authorization**: Payment limits, approval workflows, audit trails
3. **Privacy Protection**: PII encryption, logging restrictions, access controls
4. **Operational Constraints**: Deployment windows, freeze periods, SLA compliance
5. **Multi-Policy Violations**: Complex scenarios with multiple policy categories
6. **Environment-Aware Enforcement**: Different rules for dev/staging/production

All examples show:
- Clear violation identification
- Detailed reasoning
- Actionable alternatives
- Approval workflows (when applicable)
- Complete audit trails
- Compliance verification

---
