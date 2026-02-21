# Approval Request Creator - Examples

This document provides complete, copy-paste examples for common approval request scenarios.

---

## Example 1: Payment Approval ($5,500)

**Scenario:** Agent needs to process a $5,500 payment to a vendor, which exceeds the $1,000 agent limit.

### Input Code:

```javascript
const { createApprovalRequest } = require('./approval_request_creator');
const crypto = require('crypto');

async function requestPaymentApproval() {
  const requestId = `APR-${new Date().toISOString().replace(/[:.]/g, '-')}-${crypto.randomBytes(4).toString('hex').toUpperCase()}`;

  const request = {
    request_id: requestId,
    action: {
      id: `payment-${Date.now()}`,
      type: "payment",
      description: "Process payment of $5,500 to Acme Vendors Inc.",
      initiator: "lex",
      environment: "production",
      priority: "medium",
      details: {
        amount: 5500.00,
        currency: "USD",
        recipient: "Acme Vendors Inc.",
        payment_method: "wire_transfer",
        transaction_id: "txn_abc123",
        invoice_number: "INV-2025-001",
        vendor: "Acme Corp",
        account_number: "****-****-1234"
      }
    },
    violation: {
      policy: "financial.payment_limit_without_approval",
      policy_section: "Financial Policies > Payment Authorization",
      severity: "MEDIUM",
      reasoning: "Payment amount ($5,500) exceeds agent limit ($1,000)",
      impact: {
        business_risk: "Unauthorized expense if not approved",
        affected_stakeholders: ["Finance Team", "Vendor"],
        risk_level: "medium"
      }
    },
    justification: {
      business_reason: "Q1 2025 service contract payment per signed agreement dated 2024-12-15. Payment is 5 days overdue per NET-30 terms.",
      urgency: "medium",
      customer_impact: "None - internal vendor payment",
      alternative_considered: false,
      alternative_rejected_reason: "Payment is contractually obligated per signed agreement"
    },
    approval: {
      required_approver: "Manager",
      approver_email: "manager@company.com",
      approval_level: "manager",
      sla_hours: 24
    }
  };

  const result = await createApprovalRequest(request);

  if (result.success) {
    console.log(`✅ Approval request created: ${result.file_path}`);
    console.log(`📋 Request ID: ${result.request_id}`);
    console.log(`📧 Notification sent to: ${request.approval.approver_email}`);
  } else {
    console.error(`❌ Failed to create approval request: ${result.error}`);
  }

  return result;
}

// Execute
requestPaymentApproval();
```

### Generated File: `Pending_Approval/20250204-143022-payment-acme-vendors.md`

```markdown
---
request_id: APR-20250204-143022-A1B2C3D4
created_at: 2025-02-04T14:30:22Z
expires_at: 2025-02-05T14:30:22Z
timeout_action: escalate
status: pending
action_type: payment
priority: medium
approver: manager@company.com
approval_level: manager
approved_by: null
approved_at: null
rejected_by: null
rejected_at: null
rejection_reason: null
---

# Approval Request: Payment - Process payment of $5,500 to Acme Vendors Inc.

**Request ID:** APR-20250204-143022-A1B2C3D4
**Created:** 2025-02-04 14:30:22 UTC
**Expires:** 2025-02-05 14:30:22 UTC (24 hours)
**Status:** 🟡 Pending Approval

---

## Action Details

**Type:** Payment
**Description:** Process payment of $5,500 to Acme Vendors Inc.
**Environment:** Production
**Initiator:** lex (Local Executive Agent)
**Priority:** 🟡 Medium

**Transaction Details:**
- **Amount:** $5,500.00 USD
- **Recipient:** Acme Vendors Inc.
- **Payment Method:** wire_transfer
- **Transaction ID:** txn_abc123
- **Invoice Number:** INV-2025-001
- **Vendor:** Acme Corp
- **Account Number:** ****-****-1234

---

## Policy Violation

**Policy:** financial.payment_limit_without_approval
**Section:** Financial Policies > Payment Authorization
**Severity:** 🟡 MEDIUM

**Reasoning:**
Payment amount ($5,500) exceeds agent limit ($1,000)

**Impact Assessment:**
- **Business Risk:** Unauthorized expense if not approved
- **Affected Stakeholders:** Finance Team, Vendor
- **Risk Level:** medium

---

## Justification

**Business Reason:**
Q1 2025 service contract payment per signed agreement dated 2024-12-15. Payment is 5 days overdue per NET-30 terms.

**Urgency:** 🟡 Medium
**Customer Impact:** None - internal vendor payment

**Alternatives Considered:** No
**Reason:** Payment is contractually obligated per signed agreement

---

## Approval Required

**Required Approver:** Manager
**Approver Contact:** manager@company.com
**Approval Level:** Manager
**SLA:** 24 hours

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

## Example 2: Bulk Email Campaign Approval

**Scenario:** Agent wants to send a service outage notification to 5,432 customers.

### Input Code:

```javascript
async function requestBulkEmailApproval() {
  const requestId = `APR-${new Date().toISOString().replace(/[:.]/g, '-')}-${crypto.randomBytes(4).toString('hex').toUpperCase()}`;

  const request = {
    request_id: requestId,
    action: {
      id: `email-campaign-${Date.now()}`,
      type: "bulk_email",
      description: "Send service outage notification to all customers",
      initiator: "lex",
      environment: "production",
      priority: "high",
      details: {
        recipients: "all_customers@company.com (mailing list)",
        recipient_count: 5432,
        subject: "Important: Service Disruption Scheduled for Feb 5",
        body_preview: "Dear valued customer,\n\nWe will be performing critical maintenance on February 5, 2025, from 2:00 AM to 4:00 AM UTC...",
        send_time: "2025-02-05T02:00:00Z",
        sender: "support@company.com",
        reply_to: "support@company.com",
        unsubscribe_link: "https://company.com/unsubscribe",
        template_id: "maintenance-notification-v1"
      }
    },
    violation: {
      policy: "communication.mass_customer_email_approval",
      policy_section: "Communication Guidelines > External Communications > Mass Emails",
      severity: "HIGH",
      reasoning: "Mass email to 5,432 customers requires compliance review",
      impact: {
        business_risk: "Brand damage, unsubscribes, or regulatory violation if non-compliant",
        affected_stakeholders: ["All Customers", "Compliance Team", "Marketing"],
        risk_level: "high"
      }
    },
    justification: {
      business_reason: "Critical maintenance window requires customer notification per SLA",
      urgency: "medium",
      customer_impact: "Customers need advance notice to plan around 2-hour outage",
      alternative_considered: true,
      alternative_rejected_reason: "In-app notification insufficient for users not logged in"
    },
    approval: {
      required_approver: "Compliance Officer",
      approver_email: "compliance@company.com",
      approval_level: "director",
      sla_hours: 48
    }
  };

  return await createApprovalRequest(request);
}
```

---

## Example 3: Social Media Post Approval

**Scenario:** Agent wants to publish a product launch announcement on Twitter.

### Input Code:

```javascript
async function requestSocialMediaApproval() {
  const requestId = `APR-${new Date().toISOString().replace(/[:.]/g, '-')}-${crypto.randomBytes(4).toString('hex').toUpperCase()}`;

  const request = {
    request_id: requestId,
    action: {
      id: `social-twitter-${Date.now()}`,
      type: "social_media_post",
      description: "Publish product launch announcement on Twitter",
      initiator: "lex",
      environment: "production",
      priority: "medium",
      details: {
        platform: "Twitter",
        content: "🚀 Introducing ProductX! The revolutionary AI-powered solution that saves you 10 hours per week. Join the waitlist: https://company.com/productx #AI #Productivity #ProductLaunch",
        media_attachments: ["product_screenshot.png", "demo_video.mp4"],
        scheduled_time: "2025-02-10T14:00:00Z",
        target_audience: "public",
        hashtags: ["AI", "Productivity", "ProductLaunch"],
        mentions: ["@TechInfluencer"],
        post_type: "product_announcement"
      }
    },
    violation: {
      policy: "communication.social_media_approval",
      policy_section: "Communication Guidelines > Social Media > Public Posts",
      severity: "HIGH",
      reasoning: "All public social media posts require marketing approval for brand consistency",
      impact: {
        business_risk: "Public messaging that contradicts brand voice or ongoing campaigns",
        affected_stakeholders: ["Marketing", "Brand Team", "Public Audience"],
        risk_level: "high"
      }
    },
    justification: {
      business_reason: "Product launch scheduled for Feb 10 per marketing roadmap Q1 2025",
      urgency: "medium",
      customer_impact: "Existing customers expecting public announcement of new product",
      alternative_considered: false,
      alternative_rejected_reason: "Social media is primary channel for this announcement"
    },
    approval: {
      required_approver: "Marketing Manager",
      approver_email: "marketing@company.com",
      approval_level: "manager",
      sla_hours: 48
    }
  };

  return await createApprovalRequest(request);
}
```

---

## Example 4: Database Migration Approval

**Scenario:** Agent needs to execute a production database schema change.

### Input Code:

```javascript
async function requestDatabaseMigrationApproval() {
  const requestId = `APR-${new Date().toISOString().replace(/[:.]/g, '-')}-${crypto.randomBytes(4).toString('hex').toUpperCase()}`;

  const request = {
    request_id: requestId,
    action: {
      id: `db-migration-${Date.now()}`,
      type: "database_migration",
      description: "Execute add-user-preferences-table migration on production database",
      initiator: "lex",
      environment: "production",
      priority: "critical",
      details: {
        migration_name: "add-user-preferences-table",
        database: "production_db",
        affected_tables: ["users", "user_preferences"],
        estimated_duration: "5 minutes",
        downtime_expected: "None - online schema change",
        rollback_plan: "DROP TABLE user_preferences; ALTER TABLE users DROP COLUMN preference_id;",
        backup_created: true,
        backup_verified: true,
        tested_in_staging: true,
        staging_test_date: "2025-02-03",
        sql_preview: "CREATE TABLE user_preferences (id SERIAL PRIMARY KEY, user_id INT REFERENCES users(id), theme VARCHAR(20), language VARCHAR(10), created_at TIMESTAMP DEFAULT NOW());\nALTER TABLE users ADD COLUMN preference_id INT REFERENCES user_preferences(id);"
      }
    },
    violation: {
      policy: "operational.production_database_changes",
      policy_section: "Operational Constraints > Database Operations",
      severity: "CRITICAL",
      reasoning: "All production database schema changes require DBA and CTO approval",
      impact: {
        business_risk: "Data loss, service disruption, or performance degradation if migration fails",
        affected_stakeholders: ["All Users", "Engineering", "Database Team"],
        risk_level: "critical"
      }
    },
    justification: {
      business_reason: "User preferences feature is critical for Q1 product release per product roadmap",
      urgency: "high",
      customer_impact: "Enables personalized user experience - high customer demand (152 feature requests)",
      alternative_considered: true,
      alternative_rejected_reason: "Schema change is required - no-SQL alternatives evaluated but rejected due to consistency requirements"
    },
    approval: {
      required_approver: "CTO",
      approver_email: "cto@company.com",
      approval_level: "cto",
      sla_hours: 12
    }
  };

  return await createApprovalRequest(request);
}
```

---

## Example 5: API Key Rotation Approval (Emergency)

**Scenario:** Potential API key exposure detected in logs - immediate rotation required.

### Input Code:

```javascript
async function requestEmergencyApiKeyRotation() {
  const requestId = `APR-${new Date().toISOString().replace(/[:.]/g, '-')}-${crypto.randomBytes(4).toString('hex').toUpperCase()}`;

  const request = {
    request_id: requestId,
    action: {
      id: `api-key-rotation-${Date.now()}`,
      type: "api_key_rotation",
      description: "EMERGENCY: Rotate Stripe API keys in production",
      initiator: "lex",
      environment: "production",
      priority: "critical",
      details: {
        service: "Stripe Payment Gateway",
        affected_keys: ["stripe_live_pk_xxx", "stripe_live_sk_xxx"],
        rotation_reason: "Potential key exposure detected in application logs - immediate rotation required",
        downtime_expected: "None - rolling rotation with zero downtime",
        rollback_plan: "Revert to old keys within 5 minutes if payment failures detected",
        communication_plan: "Engineering team notified, on-call engineer standing by",
        monitoring_plan: "Payment success rate monitoring active, alerts configured for <95% success rate",
        tested_in_staging: true
      }
    },
    violation: {
      policy: "security.api_key_rotation_approval",
      policy_section: "Security Policies > Credential Management",
      severity: "CRITICAL",
      reasoning: "Production API key rotation requires CISO approval to prevent service disruption",
      impact: {
        business_risk: "Service outage if keys not properly rotated, security breach if old keys remain active",
        affected_stakeholders: ["Security Team", "Engineering", "All Customers"],
        risk_level: "critical"
      }
    },
    justification: {
      business_reason: "Potential key exposure detected in logs during security audit - immediate action required per incident response policy",
      urgency: "critical",
      customer_impact: "Potential payment disruption if rotation fails, data breach if key compromised",
      alternative_considered: false,
      alternative_rejected_reason: "Key rotation is mandatory per security policy - no alternative exists"
    },
    approval: {
      required_approver: "CISO",
      approver_email: "ciso@company.com",
      approval_level: "ciso",
      sla_hours: 2  // Emergency SLA
    }
  };

  return await createApprovalRequest(request);
}
```

---

## Example 6: Customer Data Deletion Approval

**Scenario:** Customer requests GDPR data deletion.

### Input Code:

```javascript
async function requestDataDeletionApproval() {
  const requestId = `APR-${new Date().toISOString().replace(/[:.]/g, '-')}-${crypto.randomBytes(4).toString('hex').toUpperCase()}`;

  const request = {
    request_id: requestId,
    action: {
      id: `data-deletion-${Date.now()}`,
      type: "data_deletion",
      description: "Delete all personal data for customer John Doe per GDPR request",
      initiator: "lex",
      environment: "production",
      priority: "high",
      details: {
        customer_id: "cust_12345",
        customer_name: "John Doe",
        customer_email: "john@example.com",
        request_date: "2025-01-28",
        request_method: "Email to privacy@company.com",
        gdpr_deadline: "2025-02-27",
        data_scope: ["user profile", "order history", "payment methods", "support tickets"],
        retention_exceptions: ["financial records (7 years per law)", "fraud prevention logs (2 years)"],
        backup_retention: "Backups containing customer data will be retained for 30 days then purged"
      }
    },
    violation: {
      policy: "privacy.customer_data_deletion",
      policy_section: "Privacy & Security > GDPR Compliance",
      severity: "HIGH",
      reasoning: "All customer data deletion requests require privacy officer review to ensure GDPR compliance",
      impact: {
        business_risk: "GDPR violation if deletion incomplete, data loss if deletion too broad",
        affected_stakeholders: ["Customer", "Privacy Team", "Legal"],
        risk_level: "high"
      }
    },
    justification: {
      business_reason: "Customer submitted GDPR data deletion request per Article 17 (Right to Erasure) on 2025-01-28",
      urgency: "high",
      customer_impact: "Customer exercising legal right to data deletion - 30-day compliance window",
      alternative_considered: false,
      alternative_rejected_reason: "GDPR mandates deletion - no alternative exists under law"
    },
    approval: {
      required_approver: "Privacy Officer",
      approver_email: "privacy@company.com",
      approval_level: "director",
      sla_hours: 48
    }
  };

  return await createApprovalRequest(request);
}
```

---

## Example 7: Checking Approval Status

**Scenario:** Poll approval file to check if approval has been granted.

### Code:

```javascript
const fs = require('fs').promises;
const yaml = require('yaml');

async function checkApprovalStatus(requestId) {
  const pendingApprovalPath = process.env.VAULT_PATH + '/Pending_Approval';
  const files = await fs.readdir(pendingApprovalPath);

  for (const file of files) {
    if (!file.endsWith('.md')) continue;

    const filePath = `${pendingApprovalPath}/${file}`;
    const content = await fs.readFile(filePath, 'utf-8');

    const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---/);
    if (!frontmatterMatch) continue;

    const frontmatter = yaml.parse(frontmatterMatch[1]);

    if (frontmatter.request_id === requestId) {
      return {
        found: true,
        status: frontmatter.status,
        approved: frontmatter.status === 'approved',
        rejected: frontmatter.status === 'rejected',
        pending: frontmatter.status === 'pending',
        approved_by: frontmatter.approved_by,
        approved_at: frontmatter.approved_at,
        rejected_by: frontmatter.rejected_by,
        rejected_at: frontmatter.rejected_at,
        rejection_reason: frontmatter.rejection_reason,
        file_path: filePath
      };
    }
  }

  return { found: false, error: `Approval request ${requestId} not found` };
}

// Usage
const status = await checkApprovalStatus('APR-20250204-143022-ABC123');

if (status.approved) {
  console.log(`✅ Approved by ${status.approved_by} at ${status.approved_at}`);
} else if (status.rejected) {
  console.log(`❌ Rejected by ${status.rejected_by}: ${status.rejection_reason}`);
} else if (status.pending) {
  console.log(`⏳ Still pending approval`);
}
```

---

## Example 8: Complete Workflow (Request → Poll → Execute)

**Scenario:** Request payment approval, wait for approval, then execute payment.

### Code:

```javascript
async function completePaymentWorkflow(paymentDetails) {
  console.log(`💳 Initiating payment: $${paymentDetails.amount} to ${paymentDetails.recipient}`);

  // Step 1: Request approval
  const approvalRequest = await requestPaymentApproval(paymentDetails);

  if (!approvalRequest.success) {
    console.error(`❌ Failed to create approval request`);
    return { success: false, error: 'Approval request creation failed' };
  }

  console.log(`✅ Approval request created: ${approvalRequest.request_id}`);
  console.log(`⏳ Waiting for approval (timeout: 24 hours)...`);

  // Step 2: Poll for approval
  const approved = await waitForApproval(approvalRequest.request_id, 24, 5);

  if (!approved) {
    console.log(`❌ Approval not granted (rejected or timeout)`);
    return { success: false, error: 'Approval denied' };
  }

  console.log(`✅ Approval granted! Proceeding with payment...`);

  // Step 3: Execute payment
  const paymentResult = await executePayment(paymentDetails);

  if (paymentResult.success) {
    console.log(`✅ Payment successful: ${paymentResult.transaction_id}`);
  } else {
    console.error(`❌ Payment failed: ${paymentResult.error}`);
  }

  return paymentResult;
}

// Execute workflow
await completePaymentWorkflow({
  amount: 5500.00,
  recipient: "Acme Vendors Inc.",
  invoice_number: "INV-2025-001",
  reason: "Q1 2025 service contract payment"
});
```

---

## Templates for Quick Copy-Paste

### Payment Approval Template:

```javascript
const paymentApproval = {
  action: {
    type: "payment",
    description: "TODO: Describe payment",
    details: { amount: 0, currency: "USD", recipient: "TODO" }
  },
  violation: {
    policy: "financial.payment_limit_without_approval",
    severity: "MEDIUM",
    reasoning: "TODO: Why this violates policy"
  },
  justification: {
    business_reason: "TODO: Why this payment is needed",
    urgency: "medium",
    customer_impact: "TODO: How this affects customers"
  },
  approval: {
    approver_email: "manager@company.com",
    approval_level: "manager",
    sla_hours: 24
  }
};
```

### Email Approval Template:

```javascript
const emailApproval = {
  action: {
    type: "bulk_email",
    description: "TODO: Describe email campaign",
    details: { recipients: "TODO", subject: "TODO", recipient_count: 0 }
  },
  violation: {
    policy: "communication.mass_email_approval",
    severity: "HIGH",
    reasoning: "TODO: Why this requires approval"
  },
  justification: {
    business_reason: "TODO: Why this email is needed",
    urgency: "medium",
    customer_impact: "TODO: How this affects customers"
  },
  approval: {
    approver_email: "compliance@company.com",
    approval_level: "director",
    sla_hours: 48
  }
};
```
