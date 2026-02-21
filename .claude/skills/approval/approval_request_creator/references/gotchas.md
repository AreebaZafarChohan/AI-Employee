# Approval Request Creator - Gotchas & Pitfalls

This document lists common issues, edge cases, and failure modes when using the `approval_request_creator` skill.

---

## Gotcha 1: Approval File Naming Collisions

**Problem:**

Multiple approval requests created within the same second result in filename collisions, overwriting previous requests.

**Symptom:**
```
Creating approval request: Pending_Approval/20250204-143022-payment-vendor.md
Error: File already exists, previous approval request overwritten
```

**Root Cause:**

- Filename based on timestamp with 1-second granularity
- Multiple agents or rapid requests within same second
- No unique suffix to prevent collisions

**Mitigation:**

```javascript
// WRONG - timestamp only (collision risk)
const filename = `${timestamp}-${actionType}-${slug}.md`;

// CORRECT - timestamp + random suffix
const crypto = require('crypto');
const uniqueSuffix = crypto.randomBytes(4).toString('hex');
const filename = `${timestamp}-${actionType}-${slug}-${uniqueSuffix}.md`;
```

**Prevention:**

- Always append random suffix (4-8 hex characters)
- Check for file existence before writing
- Use `fs.writeFile` with `wx` flag (exclusive write, fails if exists)
- Log collision warnings

---

## Gotcha 2: Approver Email Not Validated

**Problem:**

Approval request created with invalid or non-existent approver email, notification never delivered.

**Symptom:**
```
✅ Approval request created
📧 Notification sent to: manager@company.com
[ERROR] Email delivery failed: User not found
```

**Root Cause:**

- Approver email not validated against company directory
- Typos in email address
- Approver has left company
- Email service silently fails

**Mitigation:**

```javascript
// Validate approver before creating request
const { validateApprover } = require('./directory_service');

async function createApprovalRequest(request) {
  const approver = await validateApprover(request.approval.approver_email);

  if (!approver.valid) {
    throw new Error(`Invalid approver: ${request.approval.approver_email}. Suggestion: ${approver.suggestion}`);
  }

  if (approver.out_of_office) {
    console.warn(`⚠️ Approver is out of office until ${approver.return_date}`);
    console.warn(`📧 Delegate: ${approver.delegate_email}`);
  }

  // Proceed with approval request creation
  // ...
}
```

**Prevention:**

- Maintain approver directory (mapping roles to emails)
- Validate email against directory before request creation
- Check for out-of-office status
- Suggest delegate if approver unavailable
- Log notification delivery status

---

## Gotcha 3: Sensitive Data Logged in Approval Files

**Problem:**

Full action details logged in approval file, exposing sensitive data (passwords, API keys, PII).

**Symptom:**
```markdown
**Transaction Details:**
- Customer Email: john@example.com
- Credit Card: 4532-****-****-1234
- CVV: 123  <!-- SENSITIVE! -->
- API Key: sk_live_abc123xyz  <!-- SENSITIVE! -->
```

**Root Cause:**

- Action details not sanitized before writing to file
- Developer copies all fields from action object
- Approval file stored in vault (potentially synced to cloud)

**Mitigation:**

```javascript
// Define sensitive field patterns
const SENSITIVE_PATTERNS = [
  /password/i,
  /api[_-]?key/i,
  /secret/i,
  /token/i,
  /cvv/i,
  /ssn/i,
  /credit[_-]?card/i
];

function sanitizeActionDetails(details) {
  const sanitized = {};

  for (const [key, value] of Object.entries(details)) {
    // Check if field name matches sensitive pattern
    const isSensitive = SENSITIVE_PATTERNS.some(pattern => pattern.test(key));

    if (isSensitive) {
      sanitized[key] = '[REDACTED]';
    } else if (typeof value === 'string' && value.length > 500) {
      // Truncate long strings
      sanitized[key] = value.substring(0, 500) + '... [TRUNCATED]';
    } else {
      sanitized[key] = value;
    }
  }

  return sanitized;
}

// Usage
const sanitizedDetails = sanitizeActionDetails(action.details);
```

**Prevention:**

- Whitelist safe fields for approval files
- Blacklist sensitive fields (passwords, tokens, keys)
- Redact credit card numbers (show last 4 digits only)
- Truncate long text fields
- Never log full API responses or request bodies

---

## Gotcha 4: Approval Timeout Not Enforced

**Problem:**

Approval request expires per SLA, but agent never checks expiration and continues waiting indefinitely.

**Symptom:**
```
⏳ Waiting for approval: APR-20250204-143022-ABC123
[24 hours later]
⏳ Still waiting for approval... (approval expired 20 hours ago)
```

**Root Cause:**

- No timeout enforcement in polling logic
- Agent doesn't check `expires_at` timestamp
- No automatic escalation when timeout occurs

**Mitigation:**

```javascript
async function checkApprovalStatus(requestId) {
  const status = await readApprovalFile(requestId);

  if (!status.found) {
    return { found: false, error: 'Request not found' };
  }

  // Check if expired
  const now = new Date();
  const expiresAt = new Date(status.expires_at);

  if (now > expiresAt && status.status === 'pending') {
    console.warn(`⏰ Approval request expired at ${expiresAt}`);

    // Update status to 'timeout'
    await updateApprovalStatus(requestId, {
      status: 'timeout',
      timeout_at: now.toISOString()
    });

    // Trigger escalation
    if (process.env.APPROVAL_AUTO_ESCALATE === 'true') {
      await escalateApproval(requestId);
    }

    return {
      ...status,
      status: 'timeout',
      expired: true
    };
  }

  return status;
}
```

**Prevention:**

- Always check `expires_at` when polling
- Update status to `timeout` if expired
- Trigger escalation workflow automatically
- Notify requester of timeout
- Log timeout event to audit trail

---

## Gotcha 5: Concurrent Approval Status Updates (Race Condition)

**Problem:**

Two agents or processes simultaneously update approval status, causing data corruption or lost updates.

**Symptom:**
```
[Agent 1] Approving request...
[Agent 2] Approving request...
[Agent 1] Status updated: approved
[Agent 2] Status updated: approved (overwrites Agent 1's update)
Result: Missing approved_by and approved_at from Agent 1
```

**Root Cause:**

- No file locking mechanism
- Read-modify-write cycle without atomicity
- Multiple approvers or agents accessing same file

**Mitigation:**

```javascript
const lockfile = require('proper-lockfile');

async function updateApprovalStatus(requestId, updates) {
  const filePath = getApprovalFilePath(requestId);

  // Acquire lock before updating
  const release = await lockfile.lock(filePath, {
    retries: 5,
    minTimeout: 100,
    maxTimeout: 1000
  });

  try {
    // Read current content
    const content = await fs.readFile(filePath, 'utf-8');
    const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);

    if (!frontmatterMatch) {
      throw new Error('Invalid approval file format');
    }

    const frontmatter = yaml.parse(frontmatterMatch[1]);
    const body = frontmatterMatch[2];

    // Update frontmatter
    Object.assign(frontmatter, updates);

    // Write updated content
    const updatedContent = `---\n${yaml.stringify(frontmatter)}---\n${body}`;
    await fs.writeFile(filePath, updatedContent, 'utf-8');

    console.log(`✅ Approval status updated: ${requestId} → ${updates.status}`);
  } finally {
    // Always release lock
    await release();
  }
}
```

**Prevention:**

- Use file locking library (e.g., `proper-lockfile`)
- Implement retry logic for lock acquisition
- Log concurrent update attempts
- Consider using database instead of files for high-concurrency scenarios

---

## Gotcha 6: Notification Failure Silently Ignored

**Problem:**

Email or Slack notification fails to send, but approval request creation reports success. Approver never notified.

**Symptom:**
```
✅ Approval request created
📧 Notification sent to: manager@company.com
[Internally: SMTP connection timeout - notification not sent]
```

**Root Cause:**

- Notification treated as non-critical
- Errors swallowed in notification logic
- No retry mechanism for failed notifications
- No fallback notification method

**Mitigation:**

```javascript
async function createApprovalRequest(request) {
  // Create approval file first
  const filePath = await writeApprovalFile(request);

  // Attempt notifications with retry
  const notificationResults = {
    email: { sent: false, error: null },
    slack: { sent: false, error: null }
  };

  // Try email notification (3 retries)
  for (let i = 0; i < 3; i++) {
    try {
      await sendEmailNotification(request);
      notificationResults.email.sent = true;
      break;
    } catch (error) {
      notificationResults.email.error = error.message;
      console.warn(`⚠️ Email notification attempt ${i + 1}/3 failed: ${error.message}`);
      await sleep(1000 * (i + 1));  // Exponential backoff
    }
  }

  // Try Slack notification (3 retries)
  for (let i = 0; i < 3; i++) {
    try {
      await sendSlackNotification(request);
      notificationResults.slack.sent = true;
      break;
    } catch (error) {
      notificationResults.slack.error = error.message;
      console.warn(`⚠️ Slack notification attempt ${i + 1}/3 failed: ${error.message}`);
      await sleep(1000 * (i + 1));
    }
  }

  // Check if ALL notifications failed
  if (!notificationResults.email.sent && !notificationResults.slack.sent) {
    console.error(`❌ CRITICAL: All notification methods failed for ${request.request_id}`);
    console.error(`📧 Email error: ${notificationResults.email.error}`);
    console.error(`💬 Slack error: ${notificationResults.slack.error}`);

    // Fallback: Write notification failure to dashboard
    await writeToDashboard(`⚠️ Approval request ${request.request_id} created but notifications FAILED. Manual notification required.`);
  }

  return {
    success: true,
    file_path: filePath,
    request_id: request.request_id,
    notifications: notificationResults
  };
}
```

**Prevention:**

- Implement retry logic (3 attempts with exponential backoff)
- Log notification failures prominently
- Fallback to alternative notification method
- Write to dashboard if all methods fail
- Return notification status in response

---

## Gotcha 7: Approval Request Without Audit Trail

**Problem:**

Approval granted/rejected, but no audit log entry created. Cannot trace who approved, when, or why.

**Symptom:**
```
Action executed: Payment of $5000 to Vendor Inc.
[Later] Auditor: Who approved this payment?
[No audit trail found]
```

**Root Cause:**

- Audit logging not implemented
- Approval status updated but audit trail missing
- No link between approval request and audit log

**Mitigation:**

```javascript
async function updateApprovalStatus(requestId, updates) {
  // Update approval file
  await updateApprovalFile(requestId, updates);

  // Create audit log entry
  const auditEntry = {
    timestamp: new Date().toISOString(),
    event_type: updates.status === 'approved' ? 'approval_granted' : 'approval_rejected',
    request_id: requestId,
    approver: updates.approved_by || updates.rejected_by,
    action_taken: updates.status,
    rejection_reason: updates.rejection_reason || null,
    ip_address: updates.ip_address || null,
    user_agent: updates.user_agent || null,
    session_id: process.env.APPROVAL_SESSION_ID || null
  };

  await writeAuditLog(auditEntry);

  console.log(`✅ Audit log entry created: ${auditEntry.event_type} by ${auditEntry.approver}`);
}

async function writeAuditLog(entry) {
  const auditLogPath = process.env.APPROVAL_AUDIT_LOG_PATH || `${process.env.VAULT_PATH}/Audit_Logs`;
  const filename = `${entry.timestamp.replace(/[:.]/g, '-')}-${entry.event_type}.json`;
  const filePath = `${auditLogPath}/${filename}`;

  await fs.mkdir(auditLogPath, { recursive: true });
  await fs.writeFile(filePath, JSON.stringify(entry, null, 2), 'utf-8');
}
```

**Prevention:**

- Always create audit log entry for status changes
- Include approver identity, timestamp, IP address
- Link audit log to approval request ID
- Store audit logs in tamper-proof location
- Implement audit log retention policy

---

## Gotcha 8: Missing Rollback Plan for High-Risk Actions

**Problem:**

High-risk action (database migration, API key rotation) approved without rollback plan. Action fails, no way to undo.

**Symptom:**
```
Executing database migration...
[ERROR] Migration failed: Syntax error in SQL
[ERROR] Cannot rollback - no rollback plan provided
[CRITICAL] Database in inconsistent state
```

**Root Cause:**

- Approval request doesn't mandate rollback plan
- Validation doesn't check for rollback plan
- Approver assumes rollback is handled automatically

**Mitigation:**

```javascript
// Define high-risk action types that require rollback plans
const HIGH_RISK_ACTIONS = [
  'database_migration',
  'api_key_rotation',
  'deployment',
  'infrastructure_change',
  'data_deletion'
];

function validateApprovalRequest(request) {
  // Check if action is high-risk
  if (HIGH_RISK_ACTIONS.includes(request.action.type)) {
    // Require rollback plan
    if (!request.action.details.rollback_plan) {
      throw new Error(`High-risk action '${request.action.type}' requires a rollback plan`);
    }

    // Require backup confirmation
    if (request.action.type === 'database_migration' && !request.action.details.backup_created) {
      throw new Error('Database migration requires backup confirmation');
    }

    // Require staging test confirmation
    if (!request.action.details.tested_in_staging) {
      console.warn(`⚠️ Action '${request.action.type}' has not been tested in staging`);
    }
  }

  return true;
}
```

**Prevention:**

- Mandate rollback plans for high-risk actions
- Validate rollback plan is not empty or placeholder
- Require staging test confirmation
- Include rollback instructions in approval file
- Test rollback plan before approval

---

## Gotcha 9: Stale Approval Requests Never Cleaned Up

**Problem:**

Old, expired approval requests accumulate in `Pending_Approval/` folder, cluttering workspace.

**Symptom:**
```
Pending_Approval/
  ├── 20250101-100000-payment-vendor.md (expired 34 days ago)
  ├── 20250115-120000-email-customer.md (expired 20 days ago)
  ├── 20250201-143022-payment-acme.md (expired 3 days ago)
  └── 20250204-143022-payment-current.md (pending)
```

**Root Cause:**

- No cleanup process for expired requests
- Agents don't archive or delete old requests
- Manual cleanup required

**Mitigation:**

```javascript
async function cleanupExpiredApprovals() {
  const pendingApprovalPath = process.env.VAULT_PATH + '/Pending_Approval';
  const archivePath = process.env.VAULT_PATH + '/Approval_Archive';

  await fs.mkdir(archivePath, { recursive: true });

  const files = await fs.readdir(pendingApprovalPath);
  let archivedCount = 0;

  for (const file of files) {
    if (!file.endsWith('.md')) continue;

    const filePath = `${pendingApprovalPath}/${file}`;
    const content = await fs.readFile(filePath, 'utf-8');

    const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---/);
    if (!frontmatterMatch) continue;

    const frontmatter = yaml.parse(frontmatterMatch[1]);

    // Check if request is expired or completed
    const expiresAt = new Date(frontmatter.expires_at);
    const now = new Date();
    const daysSinceExpiry = (now - expiresAt) / (1000 * 60 * 60 * 24);

    const shouldArchive =
      frontmatter.status === 'approved' ||
      frontmatter.status === 'rejected' ||
      (frontmatter.status === 'pending' && daysSinceExpiry > 7);

    if (shouldArchive) {
      // Move to archive
      const archiveFilePath = `${archivePath}/${file}`;
      await fs.rename(filePath, archiveFilePath);
      archivedCount++;
      console.log(`📁 Archived: ${file}`);
    }
  }

  console.log(`✅ Cleanup complete: ${archivedCount} requests archived`);
}

// Run cleanup daily
setInterval(cleanupExpiredApprovals, 24 * 60 * 60 * 1000);
```

**Prevention:**

- Run periodic cleanup (daily or weekly)
- Archive approved/rejected requests after 7 days
- Archive expired pending requests after 7 days
- Move to `Approval_Archive/` instead of deleting
- Log cleanup actions to audit trail

---

## Gotcha 10: Approval Request Created for Already-Approved Action

**Problem:**

Agent creates duplicate approval request for action that was already approved previously.

**Symptom:**
```
Creating approval request for: Payment of $5000 to Vendor Inc.
✅ Approval request created: APR-20250204-143022-ABC123

[Later discovered] Same payment was approved last week: APR-20250128-100000-XYZ789
[Result] Duplicate approvals, confusion, wasted approver time
```

**Root Cause:**

- No deduplication check before creating request
- Agent doesn't search for existing approvals
- Similar actions not detected

**Mitigation:**

```javascript
async function findSimilarApprovals(action, lookbackDays = 30) {
  const pendingApprovalPath = process.env.VAULT_PATH + '/Pending_Approval';
  const archivePath = process.env.VAULT_PATH + '/Approval_Archive';

  const allPaths = [pendingApprovalPath, archivePath];
  const cutoffDate = new Date();
  cutoffDate.setDate(cutoffDate.getDate() - lookbackDays);

  const similarApprovals = [];

  for (const basePath of allPaths) {
    const files = await fs.readdir(basePath);

    for (const file of files) {
      if (!file.endsWith('.md')) continue;

      const filePath = `${basePath}/${file}`;
      const content = await fs.readFile(filePath, 'utf-8');

      const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---/);
      if (!frontmatterMatch) continue;

      const frontmatter = yaml.parse(frontmatterMatch[1]);

      // Check if created after cutoff date
      const createdAt = new Date(frontmatter.created_at);
      if (createdAt < cutoffDate) continue;

      // Check for similarity
      if (isSimilarAction(action, frontmatter.action)) {
        similarApprovals.push({
          request_id: frontmatter.request_id,
          status: frontmatter.status,
          created_at: frontmatter.created_at,
          file_path: filePath
        });
      }
    }
  }

  return similarApprovals;
}

function isSimilarAction(action1, action2) {
  // Check if same action type
  if (action1.type !== action2.type) return false;

  // Type-specific similarity checks
  if (action1.type === 'payment') {
    return (
      action1.details.recipient === action2.details.recipient &&
      action1.details.amount === action2.details.amount &&
      Math.abs(action1.details.invoice_number - action2.details.invoice_number) < 5
    );
  }

  // Generic similarity check
  return action1.description === action2.description;
}

// Usage
async function createApprovalRequest(request) {
  // Check for similar approvals
  const similar = await findSimilarApprovals(request.action, 30);

  if (similar.length > 0) {
    console.warn(`⚠️ Found ${similar.length} similar approval request(s) in last 30 days:`);
    similar.forEach(s => {
      console.warn(`   - ${s.request_id} (${s.status}) created ${s.created_at}`);
    });

    const approved = similar.find(s => s.status === 'approved');
    if (approved) {
      console.log(`✅ Previous approval found: ${approved.request_id}`);
      console.log(`   Reusing existing approval instead of creating duplicate`);
      return { success: true, reused: true, request_id: approved.request_id };
    }
  }

  // Proceed with creating new request
  // ...
}
```

**Prevention:**

- Search for similar approvals before creating new request
- Check both `Pending_Approval/` and `Approval_Archive/`
- Reuse existing approval if action is identical
- Warn approver if similar request exists
- Implement action fingerprinting for deduplication
