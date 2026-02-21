# Company Handbook Enforcer

A Claude Code Agent Skill for enforcing organizational policies defined in `Company_Handbook.md` across all agent planning and execution workflows.

## Overview

This skill validates all agent actions against company policies to prevent:
- Non-compliant communication with customers
- Unauthorized financial transactions
- Privacy and data handling breaches
- Actions that violate operational guidelines

## Quick Start

### 1. Create Your Company Handbook

Copy the template and customize for your organization:

```bash
cp assets/Company_Handbook.template.md ./Company_Handbook.md
# Edit Company_Handbook.md with your policies
```

### 2. Configure Environment

```bash
cp assets/.env.example .env
# Edit .env with your configuration
```

Key settings:
- `HANDBOOK_PATH`: Path to your Company_Handbook.md
- `HANDBOOK_ENFORCEMENT_LEVEL`: `STRICT` (production) | `WARN` (staging) | `SUGGEST` (dev)
- `HANDBOOK_APPROVAL_TIMEOUT`: Seconds to wait for approval (default: 4 hours)

### 3. Integrate with Agent Workflows

The skill automatically validates actions during:
- Feature planning (`/sp.plan`)
- Task generation (`/sp.tasks`)
- Implementation (`/sp.implement`)
- Git operations (`/sp.git.commit_pr`)

## Policy Categories

### Communication Guidelines
- Tone and language standards
- Prohibited phrases (e.g., "URGENT", "ASAP")
- Required elements (greeting, explanation, next steps)

### Financial Policies
- Payment authorization limits
- Approval workflows
- Prohibited transaction types

### Privacy & Security
- PII handling requirements
- Encryption standards (at rest and in transit)
- Data retention policies

### Operational Constraints
- Deployment windows (e.g., Tue-Thu 10:00-16:00 UTC)
- Change freeze periods (holidays, quarter-end)
- SLA response times

### Ethical Guidelines
- AI transparency requirements
- Human-in-the-loop for critical decisions
- Bias detection and fairness standards

## Enforcement Levels

### STRICT (Production)
- **Block** all policy violations
- **Require approval** for threshold exceedances
- **Hard stop** for critical violations
- Full audit logging

### WARN (Staging)
- **Log** violations but allow action
- **Alert** compliance team
- Test approval workflows

### SUGGEST (Development)
- **Provide alternatives** without blocking
- Advisory mode for learning
- No enforcement

## Approval Workflow

When an action requires approval:

1. **Violation Detected**
   ```
   ❌ VIOLATION: Process payment of $5,000
   Policy: financial.payment_limit_without_approval = $1,000
   Exceeds by: $4,000
   Requires: Finance Manager approval
   ```

2. **Approval Request Created**
   - Notification sent to approver
   - Timeout configured (default: 4 hours)
   - Tracking ID generated

3. **Approval Response**
   - `APPROVED`: Action proceeds with approval reference
   - `REJECTED`: Action blocked with explanation
   - `TIMEOUT`: Action blocked, escalated per policy

4. **Audit Logging**
   - All steps logged for compliance reporting
   - Immutable audit trail

## Validation Result Format

```json
{
  "compliant": false,
  "severity": "HIGH",
  "violations": [
    {
      "policy": "financial.payment_limit_without_approval",
      "reasoning": "Payment amount ($5,000) exceeds limit ($1,000)",
      "current_value": 5000,
      "required_value": 1000
    }
  ],
  "alternative": {
    "available": true,
    "description": "Create approval request for Finance Manager",
    "changes_required": [
      "Request approval from Finance Manager",
      "Wait for approval (SLA: 4 hours)",
      "Process payment with approval reference"
    ]
  },
  "approval": {
    "required": true,
    "approver": "finance-manager",
    "request_id": "APR-12345",
    "expires_at": "2024-01-15T18:00:00Z"
  }
}
```

## Example Usage

### Example 1: Communication Validation

**Action:**
```javascript
{
  type: "email",
  content: "URGENT: Fix this ASAP!"
}
```

**Result:**
```
❌ VIOLATION: Email contains prohibited phrases

Prohibited phrases detected:
- "URGENT" (use "Important" instead)
- "ASAP" (provide specific deadline)

✅ COMPLIANT ALTERNATIVE:
"Important: Action Required by 5:00 PM

Dear [Customer],

We need your attention on [specific issue] by end of business day today.

Here's what you need to do:
1. [Clear step 1]
2. [Clear step 2]

If you have questions, contact us at support@company.com.

Best regards,
[Team]"
```

### Example 2: Financial Validation

**Action:**
```javascript
{
  type: "payment",
  amount: 5000,
  description: "Customer refund"
}
```

**Result:**
```
❌ VIOLATION: Payment exceeds authorization limit

Policy: financial.payment_limit_without_approval
Limit: $1,000
Requested: $5,000
Exceeds by: $4,000

Required: Finance Manager approval

✅ COMPLIANT PATH:
1. Create approval request:
   - Amount: $5,000
   - Reason: Customer refund
   - Approver: Finance Manager
2. Wait for approval (SLA: 4 hours)
3. Process payment with approval reference

Would you like me to create the approval request?
```

### Example 3: Privacy Validation

**Action:**
```javascript
{
  type: "data_storage",
  field: "customer.ssn",
  value: "123-45-6789",
  encrypted: false
}
```

**Result:**
```
❌ VIOLATION: PII stored without encryption

Policy: privacy.prohibited_storage
Issue: SSN in plain text

✅ COMPLIANT ALTERNATIVE:
```javascript
const encryptedSSN = await encrypt(ssn, process.env.ENCRYPTION_KEY);
await db.customers.update({
  id: customerId,
  ssn_encrypted: encryptedSSN  // Use encrypted field
});

// Never log PII
logger.info('Customer SSN updated', { customer_id: customerId });
```

Changes required:
1. Encrypt SSN before storage
2. Use separate encrypted field (ssn_encrypted)
3. Apply access controls (authorized roles only)
4. Enable audit logging for SSN access
```

## Files Structure

```
.claude/skills/compliance/company_handbook_enforcer/
├── SKILL.md                           # Main skill definition
├── README.md                          # This file
├── references/
│   ├── patterns.md                    # Implementation patterns
│   ├── impact-checklist.md            # Validation checklists
│   └── gotchas.md                     # Common pitfalls and edge cases
└── assets/
    ├── Company_Handbook.template.md   # Handbook template
    ├── .env.example                   # Configuration template
    └── validation-result.template.json # Result format template
```

## Advanced Configuration

### Multi-Environment Setup

```yaml
# .env.production
HANDBOOK_ENFORCEMENT_LEVEL=STRICT
HANDBOOK_MOCK_APPROVALS=false
HANDBOOK_AUDIT_LOG_LEVEL=info

# .env.staging
HANDBOOK_ENFORCEMENT_LEVEL=WARN
HANDBOOK_MOCK_APPROVALS=false
HANDBOOK_AUDIT_LOG_LEVEL=debug

# .env.development
HANDBOOK_ENFORCEMENT_LEVEL=SUGGEST
HANDBOOK_MOCK_APPROVALS=true
HANDBOOK_AUDIT_LOG_LEVEL=debug
```

### Custom Policy Extensions

Add organization-specific policies to your handbook YAML front matter:

```yaml
---
# Standard policies...

# Custom extension
custom:
  code_quality:
    test_coverage_minimum: 80
    linting_required: true
    code_review_required: true
  deployment:
    canary_percentage: 10
    rollback_threshold: 5  # % error rate
---
```

### Webhook Integration

Configure approval and escalation webhooks:

```bash
# Approval webhook (POST request on approval required)
HANDBOOK_APPROVAL_WEBHOOK_URL=https://api.company.com/approvals
HANDBOOK_APPROVAL_WEBHOOK_SECRET=your_secret_here

# Payload:
{
  "request_id": "APR-12345",
  "action": { ... },
  "violation": { ... },
  "approver": "finance-manager",
  "expires_at": "2024-01-15T18:00:00Z"
}

# Escalation webhook (POST request on violation)
HANDBOOK_ESCALATION_WEBHOOK_URL=https://api.company.com/escalations

# Payload:
{
  "severity": "CRITICAL",
  "policy": "privacy.pii_handling",
  "action": { ... },
  "violation": { ... }
}
```

## Compliance Reporting

### Audit Log Format

```jsonl
{"timestamp":"2024-01-15T10:30:00Z","action":"payment","result":"violation","policy":"financial.payment_limit","severity":"HIGH"}
{"timestamp":"2024-01-15T10:35:00Z","action":"email","result":"pass","policy":"communication.tone","severity":"PASS"}
```

### Generate Compliance Report

```bash
# Weekly report
grep '"result":"violation"' logs/audit.jsonl | \
  jq -s 'group_by(.policy) | map({policy: .[0].policy, count: length})' > weekly-report.json

# Top violated policies
jq -s 'group_by(.policy) | map({policy: .[0].policy, count: length}) | sort_by(.count) | reverse' \
  logs/audit.jsonl > top-violations.json
```

## Troubleshooting

### Issue: Handbook not found

```
Error: ENOENT: no such file or directory, open './Company_Handbook.md'
```

**Solution:**
1. Verify `HANDBOOK_PATH` in `.env`
2. Ensure file exists at specified path
3. Check file permissions (readable by agent)

### Issue: Validation too slow

```
Warning: Validation took 5000ms (expected <500ms)
```

**Solution:**
1. Enable caching: `HANDBOOK_CACHE_TTL=300`
2. Reduce handbook size (split into modules)
3. Enable parallel validation: `HANDBOOK_PARALLEL_VALIDATION=true`
4. Increase cache size: `HANDBOOK_CACHE_MAX_SIZE=100`

### Issue: Approval timeout

```
Error: Approval request APR-12345 timed out
```

**Solution:**
1. Increase timeout: `HANDBOOK_APPROVAL_TIMEOUT=28800` (8 hours)
2. Configure escalation on timeout
3. Set up approval notification alerts

## Best Practices

1. **Keep handbook up-to-date**: Review quarterly, update as policies change
2. **Use YAML front matter**: Machine-readable policies in YAML, human-readable docs in Markdown
3. **Version your handbook**: Track changes, communicate updates to team
4. **Test in staging**: Use `WARN` mode to validate without blocking
5. **Monitor compliance**: Set up dashboards for violation trends
6. **Document exceptions**: When policies are overridden, document why
7. **Train your team**: Ensure everyone understands policies and enforcement

## Support

- **Documentation**: See `SKILL.md` for detailed implementation guide
- **Patterns**: See `references/patterns.md` for validation patterns
- **Gotchas**: See `references/gotchas.md` for common pitfalls
- **Issues**: Report bugs or request features via your internal support channel

## License

This skill is part of the AI-Employee project and follows the project's licensing terms.

---

**Note:** This skill enforces policies but does not replace human judgment. Critical decisions should always involve human review and approval.
