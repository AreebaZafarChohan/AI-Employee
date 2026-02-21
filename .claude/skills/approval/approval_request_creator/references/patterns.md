# Approval Request Creator - Usage Patterns

This document provides concrete code examples and workflow patterns for the `approval_request_creator` skill.

---

## Pattern 1: Financial Payment Approval

**Use Case:** Process payment that exceeds agent's autonomy limit

**Code Example:**

```javascript
const { createApprovalRequest } = require('./approval_request_creator');
const crypto = require('crypto');

async function requestPaymentApproval(paymentDetails) {
  // Generate unique request ID
  const requestId = `APR-${new Date().toISOString().replace(/[:.]/g, '-')}-${crypto.randomBytes(4).toString('hex').toUpperCase()}`;

  const request = {
    request_id: requestId,
    action: {
      id: `payment-${Date.now()}`,
      type: "payment",
      description: `Process payment of $${paymentDetails.amount} to ${paymentDetails.recipient}`,
      initiator: "lex",
      environment: "production",
      priority: paymentDetails.amount > 5000 ? "high" : "medium",
      details: {
        amount: paymentDetails.amount,
        currency: paymentDetails.currency || "USD",
        recipient: paymentDetails.recipient,
        payment_method: paymentDetails.method,
        transaction_id: paymentDetails.transaction_id,
        invoice_number: paymentDetails.invoice_number,
        vendor: paymentDetails.vendor
      }
    },
    violation: {
      policy: "financial.payment_limit_without_approval",
      policy_section: "Financial Policies > Payment Authorization",
      severity: paymentDetails.amount > 5000 ? "HIGH" : "MEDIUM",
      reasoning: `Payment amount ($${paymentDetails.amount}) exceeds agent limit ($1,000)`,
      impact: {
        business_risk: "Unauthorized expense if not approved",
        affected_stakeholders: ["Finance Team", "Vendor"],
        risk_level: paymentDetails.amount > 5000 ? "high" : "medium"
      }
    },
    justification: {
      business_reason: paymentDetails.reason,
      urgency: paymentDetails.urgent ? "high" : "medium",
      customer_impact: paymentDetails.customer_impact || "None",
      alternative_considered: false,
      alternative_rejected_reason: "Payment is contractually obligated"
    },
    approval: {
      required_approver: paymentDetails.amount > 10000 ? "CFO" : "Manager",
      approver_email: paymentDetails.amount > 10000 ? "cfo@company.com" : "manager@company.com",
      approval_level: paymentDetails.amount > 10000 ? "cfo" : "manager",
      sla_hours: paymentDetails.urgent ? 2 : 24
    }
  };

  // Create approval request file
  const result = await createApprovalRequest(request);

  if (!result.success) {
    console.error('❌ Failed to create approval request:', result.error);
    return null;
  }

  console.log(`✅ Approval request created: ${result.file_path}`);
  console.log(`📋 Request ID: ${result.request_id}`);
  console.log(`⏰ Expires: ${result.expires_at}`);
  console.log(`📧 Notification sent to: ${request.approval.approver_email}`);

  return result;
}

// Usage
await requestPaymentApproval({
  amount: 5500.00,
  currency: "USD",
  recipient: "Acme Vendors Inc.",
  method: "wire_transfer",
  transaction_id: "txn_abc123",
  invoice_number: "INV-2025-001",
  vendor: "Acme Corp",
  reason: "Q1 2025 service contract payment per signed agreement",
  urgent: false,
  customer_impact: "None - internal vendor payment"
});
```

**Output:**
```
✅ Approval request created: Pending_Approval/20250204-143022-payment-acme-vendors.md
📋 Request ID: APR-20250204-143022-A1B2C3D4
⏰ Expires: 2025-02-05T14:30:22Z
📧 Notification sent to: manager@company.com
```

---

## Pattern 2: Bulk Email Approval with Template

**Use Case:** Send mass customer communication, requires compliance approval

**Code Example:**

```javascript
async function requestBulkEmailApproval(emailCampaign) {
  const requestId = `APR-${new Date().toISOString().replace(/[:.]/g, '-')}-${crypto.randomBytes(4).toString('hex').toUpperCase()}`;

  const request = {
    request_id: requestId,
    action: {
      id: `email-campaign-${Date.now()}`,
      type: "bulk_email",
      description: `Send ${emailCampaign.subject} to ${emailCampaign.recipient_count} customers`,
      initiator: "lex",
      environment: "production",
      priority: "high",
      details: {
        recipients: emailCampaign.recipient_list,
        recipient_count: emailCampaign.recipient_count,
        subject: emailCampaign.subject,
        body_preview: emailCampaign.body.substring(0, 200) + "...",
        send_time: emailCampaign.send_time,
        sender: emailCampaign.sender,
        reply_to: emailCampaign.reply_to,
        unsubscribe_link: emailCampaign.unsubscribe_link,
        template_id: emailCampaign.template_id
      }
    },
    violation: {
      policy: "communication.mass_customer_email_approval",
      policy_section: "Communication Guidelines > External Communications > Mass Emails",
      severity: "HIGH",
      reasoning: `Mass email to ${emailCampaign.recipient_count} customers requires compliance review`,
      impact: {
        business_risk: "Brand damage, unsubscribes, or regulatory violation if non-compliant",
        affected_stakeholders: ["All Customers", "Compliance Team", "Marketing"],
        risk_level: "high"
      }
    },
    justification: {
      business_reason: emailCampaign.business_reason,
      urgency: "medium",
      customer_impact: emailCampaign.customer_impact,
      alternative_considered: true,
      alternative_rejected_reason: "In-app notification insufficient - need email for inactive users"
    },
    approval: {
      required_approver: "Compliance Officer",
      approver_email: "compliance@company.com",
      approval_level: "director",
      sla_hours: 48
    }
  };

  const result = await createApprovalRequest(request);

  if (result.success) {
    console.log(`✅ Email campaign approval request created`);
    console.log(`📋 Request ID: ${result.request_id}`);
    console.log(`📧 Awaiting approval from: ${request.approval.approver_email}`);
    console.log(`📄 View request: ${result.file_path}`);
  }

  return result;
}

// Usage
await requestBulkEmailApproval({
  recipient_list: "all_customers@company.com",
  recipient_count: 5432,
  subject: "Important: Service Maintenance Scheduled",
  body: "Dear valued customer,\n\nWe will be performing critical system maintenance...",
  send_time: "2025-02-10T10:00:00Z",
  sender: "support@company.com",
  reply_to: "support@company.com",
  unsubscribe_link: "https://company.com/unsubscribe",
  template_id: "maintenance-notification-v1",
  business_reason: "Mandatory customer notification per SLA for scheduled maintenance",
  customer_impact: "Customers need advance notice to plan for 2-hour service disruption"
});
```

---

## Pattern 3: Social Media Post Approval

**Use Case:** Publish public social media content, requires marketing approval

**Code Example:**

```javascript
async function requestSocialMediaApproval(post) {
  const requestId = `APR-${new Date().toISOString().replace(/[:.]/g, '-')}-${crypto.randomBytes(4).toString('hex').toUpperCase()}`;

  const request = {
    request_id: requestId,
    action: {
      id: `social-${post.platform.toLowerCase()}-${Date.now()}`,
      type: "social_media_post",
      description: `Publish ${post.type} on ${post.platform}`,
      initiator: "lex",
      environment: "production",
      priority: "medium",
      details: {
        platform: post.platform,
        content: post.content,
        media_attachments: post.media || [],
        scheduled_time: post.scheduled_time,
        target_audience: post.target_audience || "public",
        hashtags: post.hashtags || [],
        mentions: post.mentions || [],
        post_type: post.type
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
      business_reason: post.business_reason,
      urgency: post.urgent ? "high" : "medium",
      customer_impact: post.customer_impact,
      alternative_considered: false,
      alternative_rejected_reason: "Social media is primary channel for this announcement"
    },
    approval: {
      required_approver: "Marketing Manager",
      approver_email: "marketing@company.com",
      approval_level: "manager",
      sla_hours: post.urgent ? 4 : 48
    }
  };

  const result = await createApprovalRequest(request);

  if (result.success) {
    console.log(`✅ Social media post approval request created`);
    console.log(`📋 Request ID: ${result.request_id}`);
    console.log(`🐦 Platform: ${post.platform}`);
    console.log(`📅 Scheduled: ${post.scheduled_time}`);
    console.log(`📧 Awaiting approval from: ${request.approval.approver_email}`);
  }

  return result;
}

// Usage
await requestSocialMediaApproval({
  platform: "Twitter",
  type: "product_announcement",
  content: "🚀 Introducing ProductX! The revolutionary AI-powered solution that saves you 10 hours per week. Join the waitlist: https://company.com/productx #AI #Productivity",
  media: ["product_screenshot.png", "demo_video.mp4"],
  scheduled_time: "2025-02-15T14:00:00Z",
  target_audience: "public",
  hashtags: ["AI", "Productivity", "ProductLaunch"],
  mentions: ["@TechInfluencer"],
  business_reason: "Product launch announcement per marketing roadmap Q1 2025",
  customer_impact: "Existing customers expecting public announcement of new product",
  urgent: false
});
```

---

## Pattern 4: Database Migration Approval

**Use Case:** Execute database schema change in production

**Code Example:**

```javascript
async function requestDatabaseMigrationApproval(migration) {
  const requestId = `APR-${new Date().toISOString().replace(/[:.]/g, '-')}-${crypto.randomBytes(4).toString('hex').toUpperCase()}`;

  const request = {
    request_id: requestId,
    action: {
      id: `db-migration-${Date.now()}`,
      type: "database_migration",
      description: `Execute ${migration.name} on production database`,
      initiator: "lex",
      environment: "production",
      priority: "critical",
      details: {
        migration_name: migration.name,
        database: migration.database,
        affected_tables: migration.affected_tables,
        estimated_duration: migration.estimated_duration,
        rollback_plan: migration.rollback_plan,
        backup_created: migration.backup_created,
        tested_in_staging: migration.tested_in_staging,
        sql_preview: migration.sql.substring(0, 500) + "..."
      }
    },
    violation: {
      policy: "operational.production_database_changes",
      policy_section: "Operational Constraints > Database Operations",
      severity: "CRITICAL",
      reasoning: "All production database schema changes require DBA and CTO approval",
      impact: {
        business_risk: "Data loss, service disruption, or performance degradation",
        affected_stakeholders: ["All Users", "Engineering", "Database Team"],
        risk_level: "critical"
      }
    },
    justification: {
      business_reason: migration.business_reason,
      urgency: "high",
      customer_impact: migration.customer_impact,
      alternative_considered: true,
      alternative_rejected_reason: "Schema change is blocking critical feature release"
    },
    approval: {
      required_approver: "CTO",
      approver_email: "cto@company.com",
      approval_level: "cto",
      sla_hours: 12
    }
  };

  const result = await createApprovalRequest(request);

  if (result.success) {
    console.log(`✅ Database migration approval request created`);
    console.log(`📋 Request ID: ${result.request_id}`);
    console.log(`🗄️ Database: ${migration.database}`);
    console.log(`📊 Affected Tables: ${migration.affected_tables.join(', ')}`);
    console.log(`⏱️ Estimated Duration: ${migration.estimated_duration}`);
    console.log(`📧 Awaiting CTO approval: ${request.approval.approver_email}`);
  }

  return result;
}

// Usage
await requestDatabaseMigrationApproval({
  name: "add-user-preferences-table",
  database: "production_db",
  affected_tables: ["users", "user_preferences"],
  estimated_duration: "5 minutes",
  rollback_plan: "DROP TABLE user_preferences; ALTER TABLE users DROP COLUMN preference_id;",
  backup_created: true,
  tested_in_staging: true,
  sql: "CREATE TABLE user_preferences (...); ALTER TABLE users ADD COLUMN preference_id INT;",
  business_reason: "User preferences feature is critical for Q1 product release",
  customer_impact: "Enables personalized user experience - high customer demand"
});
```

---

## Pattern 5: API Key Rotation Approval

**Use Case:** Rotate production API keys, requires security approval

**Code Example:**

```javascript
async function requestApiKeyRotationApproval(keyDetails) {
  const requestId = `APR-${new Date().toISOString().replace(/[:.]/g, '-')}-${crypto.randomBytes(4).toString('hex').toUpperCase()}`;

  const request = {
    request_id: requestId,
    action: {
      id: `api-key-rotation-${Date.now()}`,
      type: "api_key_rotation",
      description: `Rotate ${keyDetails.service} API keys in production`,
      initiator: "lex",
      environment: "production",
      priority: "critical",
      details: {
        service: keyDetails.service,
        affected_keys: keyDetails.affected_keys,
        rotation_reason: keyDetails.rotation_reason,
        downtime_expected: keyDetails.downtime_expected,
        rollback_plan: keyDetails.rollback_plan,
        communication_plan: keyDetails.communication_plan
      }
    },
    violation: {
      policy: "security.api_key_rotation_approval",
      policy_section: "Security Policies > Credential Management",
      severity: "CRITICAL",
      reasoning: "Production API key rotation requires security team approval to prevent service disruption",
      impact: {
        business_risk: "Service outage if keys not properly rotated, security breach if old keys remain active",
        affected_stakeholders: ["Security Team", "Engineering", "All API Consumers"],
        risk_level: "critical"
      }
    },
    justification: {
      business_reason: keyDetails.rotation_reason,
      urgency: keyDetails.urgent ? "critical" : "high",
      customer_impact: keyDetails.customer_impact,
      alternative_considered: false,
      alternative_rejected_reason: "Key rotation is mandatory per security policy"
    },
    approval: {
      required_approver: "CISO",
      approver_email: "ciso@company.com",
      approval_level: "ciso",
      sla_hours: keyDetails.urgent ? 2 : 24
    }
  };

  const result = await createApprovalRequest(request);

  if (result.success) {
    console.log(`✅ API key rotation approval request created`);
    console.log(`📋 Request ID: ${result.request_id}`);
    console.log(`🔐 Service: ${keyDetails.service}`);
    console.log(`⚠️ Urgency: ${keyDetails.urgent ? 'CRITICAL' : 'HIGH'}`);
    console.log(`📧 Awaiting CISO approval: ${request.approval.approver_email}`);
  }

  return result;
}

// Usage
await requestApiKeyRotationApproval({
  service: "Stripe Payment Gateway",
  affected_keys: ["stripe_live_pk_xxx", "stripe_live_sk_xxx"],
  rotation_reason: "Potential key exposure detected in logs - immediate rotation required",
  downtime_expected: "None - rolling rotation with zero downtime",
  rollback_plan: "Revert to old keys within 5 minutes if issues detected",
  communication_plan: "Engineering team notified, on-call ready",
  customer_impact: "None if rotation successful, payment disruption if failed",
  urgent: true
});
```

---

## Pattern 6: Polling for Approval Status

**Use Case:** Check if approval has been granted before executing action

**Code Example:**

```javascript
const fs = require('fs').promises;
const yaml = require('yaml');

async function checkApprovalStatus(requestId) {
  // Find approval file by request ID
  const pendingApprovalPath = process.env.VAULT_PATH + '/Pending_Approval';
  const files = await fs.readdir(pendingApprovalPath);

  for (const file of files) {
    if (!file.endsWith('.md')) continue;

    const filePath = `${pendingApprovalPath}/${file}`;
    const content = await fs.readFile(filePath, 'utf-8');

    // Extract YAML frontmatter
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

  return {
    found: false,
    error: `Approval request ${requestId} not found`
  };
}

async function waitForApproval(requestId, timeoutHours = 24, pollIntervalMinutes = 5) {
  const startTime = Date.now();
  const timeoutMs = timeoutHours * 60 * 60 * 1000;
  const pollIntervalMs = pollIntervalMinutes * 60 * 1000;

  console.log(`⏳ Waiting for approval: ${requestId}`);
  console.log(`⏰ Timeout: ${timeoutHours} hours`);
  console.log(`🔄 Poll interval: ${pollIntervalMinutes} minutes`);

  while (Date.now() - startTime < timeoutMs) {
    const status = await checkApprovalStatus(requestId);

    if (!status.found) {
      console.error(`❌ Approval request not found: ${requestId}`);
      return { approved: false, error: 'Request not found' };
    }

    if (status.approved) {
      console.log(`✅ Approval granted by ${status.approved_by} at ${status.approved_at}`);
      return { approved: true, ...status };
    }

    if (status.rejected) {
      console.log(`❌ Approval rejected by ${status.rejected_by} at ${status.rejected_at}`);
      console.log(`📝 Reason: ${status.rejection_reason}`);
      return { approved: false, rejected: true, ...status };
    }

    if (status.pending) {
      const elapsed = Math.round((Date.now() - startTime) / 1000 / 60);
      console.log(`⏳ Still pending... (${elapsed} minutes elapsed)`);
    }

    // Wait before next poll
    await new Promise(resolve => setTimeout(resolve, pollIntervalMs));
  }

  console.log(`⏰ Timeout reached after ${timeoutHours} hours`);
  return { approved: false, timeout: true };
}

// Usage
const approvalResult = await requestPaymentApproval({
  amount: 5500.00,
  recipient: "Vendor Inc.",
  reason: "Q1 contract payment"
});

if (approvalResult.success) {
  console.log(`📋 Approval requested: ${approvalResult.request_id}`);

  // Wait for approval (poll every 5 minutes, timeout after 24 hours)
  const result = await waitForApproval(approvalResult.request_id, 24, 5);

  if (result.approved) {
    console.log(`✅ Proceeding with payment...`);
    // Execute payment
  } else if (result.rejected) {
    console.log(`❌ Payment cancelled: ${result.rejection_reason}`);
  } else if (result.timeout) {
    console.log(`⏰ Approval timeout - escalating to supervisor`);
  }
}
```

---

## Best Practices

### 1. Always Include Business Justification
```javascript
// ❌ BAD - vague justification
justification: {
  business_reason: "Need to pay vendor",
  urgency: "high"
}

// ✅ GOOD - specific, actionable justification
justification: {
  business_reason: "Q1 2025 service contract payment per signed agreement dated 2024-12-15. Payment is 5 days overdue per NET-30 terms.",
  urgency: "high",
  customer_impact: "Vendor may suspend service if payment not received within 7 days",
  alternative_considered: true,
  alternative_rejected_reason: "Partial payment not accepted per contract terms"
}
```

### 2. Use Appropriate Approval Levels
```javascript
// Approval level based on amount/risk
function getApprovalLevel(amount) {
  if (amount > 50000) return { level: 'cfo', email: 'cfo@company.com' };
  if (amount > 10000) return { level: 'director', email: 'director@company.com' };
  if (amount > 5000) return { level: 'manager', email: 'manager@company.com' };
  return { level: 'manager', email: 'manager@company.com' };
}
```

### 3. Set Realistic SLA Hours
```javascript
// SLA based on urgency and approval level
function getSLA(urgency, approvalLevel) {
  if (urgency === 'critical') return 2;  // 2 hours for critical
  if (approvalLevel === 'ceo' || approvalLevel === 'cfo') return 48;  // 48 hours for C-level
  if (urgency === 'high') return 4;  // 4 hours for high urgency
  return 24;  // 24 hours default
}
```

### 4. Include Rollback Plans for High-Risk Actions
```javascript
// Always include rollback for infrastructure changes
action: {
  type: "database_migration",
  details: {
    migration_sql: "ALTER TABLE users ADD COLUMN...",
    rollback_plan: "ALTER TABLE users DROP COLUMN...",
    backup_created: true,
    tested_in_staging: true
  }
}
```

---

## Integration with Other Skills

### With company_handbook_enforcer:
```javascript
// company_handbook_enforcer detects violation
const violation = await checkPolicyCompliance(action);

if (violation.requires_approval) {
  // Automatically create approval request
  const approvalRequest = await createApprovalRequest({
    action: action,
    violation: violation,
    justification: extractJustification(action),
    approval: getApproverForPolicy(violation.policy)
  });

  console.log(`⚠️ Policy violation detected: ${violation.policy}`);
  console.log(`📋 Approval request created: ${approvalRequest.request_id}`);
}
```

### With task_lifecycle_manager:
```javascript
// task_lifecycle_manager blocks task execution
async function executeTask(task) {
  if (task.requires_approval) {
    const approvalRequest = await createApprovalRequest(task.approval_details);

    // Wait for approval
    const approval = await waitForApproval(approvalRequest.request_id);

    if (!approval.approved) {
      return { status: 'blocked', reason: 'Approval denied or timeout' };
    }
  }

  // Proceed with task execution
  return await executeTaskLogic(task);
}
```
