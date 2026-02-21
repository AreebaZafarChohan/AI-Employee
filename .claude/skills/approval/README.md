# Approval Skills

This directory contains skills related to approval workflows and human authorization for agent actions.

---

## Available Skills

### approval_request_creator

Generate formal human approval request markdown files for sensitive actions requiring human authorization.

**Use Cases:**
- Financial transactions (payments, refunds)
- External communications (bulk emails, social media posts)
- Infrastructure changes (deployments, database migrations)
- Data operations (deletions, exports)
- Security operations (API key rotation, access grants)

**Key Features:**
- Structured markdown files with YAML frontmatter
- Unique cryptographic request IDs
- Email and Slack notifications
- Timeout and escalation handling
- Full audit trail
- Policy linkage

**Quick Start:**
```javascript
const { createApprovalRequest } = require('./approval_request_creator');

const result = await createApprovalRequest({
  action: {
    type: "payment",
    description: "Process $5,500 payment to vendor",
    details: { amount: 5500, recipient: "Vendor Inc." }
  },
  violation: {
    policy: "financial.payment_limit_without_approval",
    severity: "MEDIUM"
  },
  justification: {
    business_reason: "Q1 service contract payment",
    urgency: "medium"
  },
  approval: {
    approver_email: "manager@company.com",
    approval_level: "manager",
    sla_hours: 24
  }
});
```

**Documentation:**
- `SKILL.md` - Complete specification with impact analysis
- `README.md` - Quick start and configuration guide
- `EXAMPLES.md` - Copy-paste examples for common scenarios
- `references/patterns.md` - Code patterns and workflows
- `references/gotchas.md` - Common pitfalls and edge cases
- `references/impact-checklist.md` - Production readiness checklist

---

## Integration with Other Skills

### Upstream Skills (Trigger Approval Requests)

- **company_handbook_enforcer**: Detects policy violations → Creates approval request
- **task_lifecycle_manager**: Task execution blocked → Creates approval request

### Downstream Skills (Read Approval Status)

- **vault_state_manager**: Reads approval status → Unblocks execution
- **needs_action_triage**: Scans for expired approvals → Triggers escalation

### Related Skills

- **dashboard_writer**: Displays pending approval count in dashboard

---

## Approval Workflow Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Agent Action                             │
│         (payment, email, deployment, etc.)                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│             Policy Check (company_handbook_enforcer)         │
│         Does action violate company policy?                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
           ┌───────────┴───────────┐
           │                       │
       NO (allowed)            YES (violation)
           │                       │
           ▼                       ▼
┌──────────────────┐   ┌──────────────────────────────────────┐
│  Execute Action  │   │  Create Approval Request             │
│   Immediately    │   │  (approval_request_creator)          │
└──────────────────┘   └──────────┬───────────────────────────┘
                                  │
                                  ▼
                       ┌──────────────────────────────────────┐
                       │  Notify Approver (email/Slack)       │
                       │  Write file to Pending_Approval/     │
                       └──────────┬───────────────────────────┘
                                  │
                                  ▼
                       ┌──────────────────────────────────────┐
                       │  Wait for Human Decision             │
                       │  (Agent polls approval status)       │
                       └──────────┬───────────────────────────┘
                                  │
           ┌──────────────────────┼──────────────────────┐
           │                      │                      │
       APPROVED                REJECTED              TIMEOUT
           │                      │                      │
           ▼                      ▼                      ▼
┌──────────────────┐   ┌──────────────────┐   ┌─────────────────┐
│  Execute Action  │   │   Abort Action   │   │   Escalate to   │
│  Log Approval    │   │  Log Rejection   │   │  Higher Level   │
└──────────────────┘   └──────────────────┘   └─────────────────┘
```

---

## File Structure

```
.claude/skills/approval/
├── README.md                              # This file
└── approval_request_creator/
    ├── SKILL.md                          # Complete specification
    ├── README.md                         # Quick start guide
    ├── EXAMPLES.md                       # Copy-paste examples
    ├── references/
    │   ├── patterns.md                  # Code patterns
    │   ├── gotchas.md                   # Common pitfalls
    │   └── impact-checklist.md          # Production checklist
    └── assets/
        ├── approval-request.template.md  # Markdown template
        └── .env.example                  # Configuration example
```

---

## Configuration

### Environment Variables

**Required:**
```bash
VAULT_PATH="/absolute/path/to/vault"
```

**Optional:**
```bash
APPROVAL_DEFAULT_TIMEOUT_HOURS="4"
APPROVAL_NOTIFY_EMAIL="approver@company.com"
APPROVAL_NOTIFY_SLACK_WEBHOOK="https://hooks.slack.com/..."
APPROVAL_AUTO_ESCALATE="true"
APPROVAL_ESCALATION_EMAIL="ceo@company.com"
```

See `approval_request_creator/assets/.env.example` for complete configuration options.

---

## Action Types Supported

| Action Type | Description | Approval Level |
|------------|-------------|----------------|
| `payment` | Financial transactions | Manager → CFO |
| `refund` | Customer refunds | Manager → Director |
| `bulk_email` | Mass customer emails | Director |
| `social_media_post` | Public social posts | Manager |
| `database_migration` | Production schema changes | CTO |
| `api_key_rotation` | Credential rotation | CISO |
| `deployment` | Production deployments | CTO |
| `data_deletion` | Delete production data | Director |
| `access_grant` | Permission changes | CISO |

---

## Approval Levels

| Level | Description | Typical SLA |
|-------|-------------|-------------|
| `manager` | Team manager | 4-24 hours |
| `director` | Department director | 24-48 hours |
| `vp` | Vice President | 48-72 hours |
| `cfo` | Chief Financial Officer | 24-48 hours |
| `cto` | Chief Technology Officer | 24-48 hours |
| `ceo` | Chief Executive Officer | 48-72 hours |
| `ciso` | Chief Information Security Officer | 24-48 hours |

---

## Testing Checklist

Before production deployment:

- [ ] Create approval request for each action type
- [ ] Test approval workflow (manual file edit)
- [ ] Test rejection workflow
- [ ] Test timeout expiration
- [ ] Test email notifications
- [ ] Test Slack notifications
- [ ] Test audit log creation
- [ ] Test deduplication
- [ ] Test with invalid inputs
- [ ] Test concurrent approvals (race conditions)

---

## Troubleshooting

### Common Issues

**Issue:** Approval file not created
- **Cause:** No write access to `Pending_Approval/` folder
- **Solution:** Verify agent has write permissions: `ls -ld $VAULT_PATH/Pending_Approval`

**Issue:** Notification not sent
- **Cause:** SMTP or Slack webhook misconfigured
- **Solution:** Check configuration in `.env`, test with manual curl/telnet

**Issue:** Approval status not detected
- **Cause:** YAML frontmatter malformed
- **Solution:** Validate YAML syntax, ensure no tabs (use spaces)

**Issue:** Duplicate approval requests
- **Cause:** Multiple agents creating requests for same action
- **Solution:** Enable deduplication: `APPROVAL_ENABLE_DEDUPLICATION="true"`

For more troubleshooting, see `approval_request_creator/references/gotchas.md`.

---

## Version History

- **v1.0.0** (2025-02-04): Initial release
  - `approval_request_creator` skill
  - Payment, email, social media, database, API key support
  - Email and Slack notifications
  - Audit trail integration

---

## Future Skills (Planned)

- **approval_status_monitor**: Real-time monitoring of pending approvals
- **approval_analytics**: Generate reports on approval patterns and bottlenecks
- **approval_delegator**: Auto-delegate to alternate approver if primary unavailable
- **approval_batch_processor**: Bulk approve/reject multiple requests

---

## Contributing

When adding new approval-related skills:

1. Follow the existing skill structure (SKILL.md, README.md, EXAMPLES.md, references/, assets/)
2. Include comprehensive impact analysis in SKILL.md
3. Provide copy-paste examples in EXAMPLES.md
4. Document common pitfalls in references/gotchas.md
5. Create production checklist in references/impact-checklist.md
6. Update this README with integration points

---

## Support

For questions or issues:
- Review skill documentation in respective folders
- Check `references/gotchas.md` for common problems
- File bug reports in project issue tracker
