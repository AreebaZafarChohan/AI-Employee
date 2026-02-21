# Email Drafter Skill

Professional email reply drafting system for business workflows.

## Quick Start

```javascript
const { draftEmail } = require('./email_drafter');

const draft = await draftEmail({
  intent: "customer_inquiry_response",
  recipient: {
    name: "John Doe",
    email: "john@example.com",
    type: "customer"
  },
  context: {
    original_subject: "Question about API",
    original_message: "How do I authenticate?",
    customer_plan: "Pro"
  },
  tone: "friendly",
  key_points: [
    "Explain API authentication",
    "Provide code example",
    "Link to documentation"
  ]
});

console.log(`Draft created: ${draft.file_path}`);
```

## Features

- ✅ **Multiple Email Types**: Customer support, meeting requests, status updates, rejections, and more
- ✅ **Tone Adaptation**: Formal, semi-formal, or friendly based on recipient and context
- ✅ **Professional Formatting**: Structured markdown with YAML frontmatter
- ✅ **Subject Line Generation**: Provides 3 alternative subject lines per draft
- ✅ **Follow-Up Actions**: Suggests next steps and action items
- ✅ **Audit Trail**: Tracks who created drafts, when, and why
- ✅ **Review Workflow**: Built-in approval process for sensitive emails
- ✅ **Batch Processing**: Generate multiple drafts efficiently

## Installation

1. **Set up environment variables:**

```bash
cp .claude/skills/communication/email_drafter/assets/.env.example .env
```

2. **Configure vault path:**

```bash
export VAULT_PATH="/path/to/vault"
```

3. **Create required directories:**

```bash
mkdir -p "$VAULT_PATH/Email_Drafts"
```

## Usage

### Basic Customer Response

```javascript
await draftEmail({
  intent: "customer_inquiry_response",
  recipient: {
    name: "Alice Johnson",
    email: "alice@example.com",
    type: "customer"
  },
  context: {
    original_subject: "Feature Request",
    original_message: "Can you add dark mode?",
    ticket_id: "TICKET-12345"
  },
  tone: "friendly",
  key_points: [
    "Acknowledge request",
    "Share that it's on roadmap",
    "Provide timeline estimate",
    "Thank customer for feedback"
  ]
});
```

### Meeting Scheduling

```javascript
await draftEmail({
  intent: "meeting_request",
  recipient: {
    name: "Sarah Smith",
    email: "sarah@partnercorp.com",
    type: "external_stakeholder"
  },
  context: {
    meeting_purpose: "Q1 Partnership Review",
    meeting_duration: "60 minutes",
    proposed_dates: [
      "2025-02-10T14:00:00Z",
      "2025-02-12T10:00:00Z"
    ]
  },
  tone: "formal"
});
```

### Status Update

```javascript
await draftEmail({
  intent: "status_update",
  recipient: {
    name: "Project Team",
    email: "team@company.com",
    type: "internal_team"
  },
  context: {
    project_name: "Mobile App Redesign",
    reporting_period: "Week of Feb 3-9",
    overall_status: "on_track",
    completed_milestones: ["Wireframes approved", "API integration done"],
    blockers: ["Waiting on design assets"]
  },
  tone: "semi-formal"
});
```

## Supported Email Types

| Intent | Use Case | Default Tone |
|--------|----------|--------------|
| `customer_inquiry_response` | Answer customer questions | Friendly |
| `meeting_request` | Schedule meetings | Formal |
| `status_update` | Project updates | Semi-formal |
| `polite_rejection` | Decline requests | Formal |
| `escalation_response` | Address complaints | Formal |
| `approval_request` | Seek authorization | Formal |
| `follow_up` | Post-meeting follow-up | Semi-formal |
| `thank_you` | Express gratitude | Semi-formal |
| `apology` | Address errors | Formal |
| `negotiation` | Vendor pricing | Formal |

## Tone Guide

### Formal
- Executive communications
- Legal/contract emails
- Official announcements
- Vendor negotiations

### Semi-Formal
- Internal team updates
- Project status reports
- Cross-team collaboration

### Friendly
- Customer support
- Thank-you notes
- New customer onboarding
- Community engagement

## Output Structure

Each draft is saved as a markdown file with:

```markdown
---
draft_id: DRAFT-20250204-143022-ABC123
created_at: 2025-02-04T14:30:22Z
status: draft
email_type: customer_inquiry_response
recipient: john@example.com
tone: friendly
---

# Email Draft: Customer Inquiry Response

## Email Details
**To:** john@example.com
**Subject:** Re: Question about API

## Email Body
[Professional email content]

## Alternative Subject Lines
1. [Option 1]
2. [Option 2]
3. [Option 3]

## Follow-Up Actions
- [ ] Action 1
- [ ] Action 2

## Metadata
[Audit trail information]
```

## Configuration

### Basic Setup

```bash
VAULT_PATH="/path/to/vault"
EMAIL_DEFAULT_TONE="formal"
```

### With Custom Signature

```bash
EMAIL_SIGNATURE_NAME="Customer Success Team"
EMAIL_SIGNATURE_TITLE="Support Specialist"
EMAIL_SIGNATURE_COMPANY="Acme Corp"
EMAIL_SIGNATURE_CONTACT="support@acme.com"
```

### Production Setup

```bash
VAULT_PATH="/path/to/vault"
EMAIL_DEFAULT_TONE="formal"
EMAIL_REQUIRE_REVIEW="true"
EMAIL_CONFIDENTIALITY_NOTICE="true"
EMAIL_AUDIT_LOG_PATH="$VAULT_PATH/Audit_Logs"
```

## Best Practices

### 1. Provide Sufficient Context

```javascript
// ❌ Too vague
context: { original_message: "Help" }

// ✅ Comprehensive
context: {
  original_subject: "API Error 500",
  original_message: "Getting 500 errors on /users endpoint",
  error_details: "Stack trace shows database timeout",
  customer_plan: "Enterprise",
  ticket_id: "TICKET-67890"
}
```

### 2. Choose Appropriate Tone

```javascript
// Customer emails
tone: "friendly"

// Executive/legal
tone: "formal"

// Internal team
tone: "semi-formal"
```

### 3. Keep Key Points Focused

```javascript
// ❌ Too many points
key_points: [/* 10+ items */]

// ✅ Focused and actionable
key_points: [
  "Acknowledge issue",
  "Explain root cause",
  "Describe fix",
  "Offer follow-up"
]
```

### 4. Specify Recipient Type

```javascript
recipient: {
  name: "John Doe",
  email: "john@example.com",
  type: "customer",  // Always specify!
  account_id: "cust_123"
}
```

## Integration

### With Company Handbook Enforcer

```javascript
const draft = await draftEmail({ ... });
const compliance = await checkPolicyCompliance({
  type: "email",
  content: draft.body
});
```

### With Approval Request Creator

```javascript
if (recipient.type === "external_stakeholder") {
  const approval = await createApprovalRequest({
    action: { type: "email", details: draft }
  });
}
```

## Troubleshooting

### Drafts Not Being Created

```bash
# Check directory exists
ls -la "$VAULT_PATH/Email_Drafts"

# Check permissions
test -w "$VAULT_PATH/Email_Drafts" && echo "Writable" || echo "Not writable"
```

### Invalid Email Format Error

```javascript
// Ensure proper email format
recipient: {
  email: "john@example.com"  // ✅ Valid
  // NOT: "john@example" ❌ Invalid
}
```

### Tone Seems Wrong

```javascript
// Override explicitly
tone: "formal",
style_override: {
  avoid_contractions: true,
  use_full_names: true
}
```

## Documentation

- **SKILL.md** - Comprehensive skill documentation
- **patterns.md** - Usage patterns and code examples
- **gotchas.md** - Common pitfalls and troubleshooting
- **impact-checklist.md** - Deployment impact assessment
- **EXAMPLES.md** - Real-world examples

## Support

For issues or questions:
- Check **references/gotchas.md** for common problems
- Review **references/patterns.md** for usage examples
- File issues in project issue tracker

## Version

**v1.0.0** - Initial release (2025-02-04)
