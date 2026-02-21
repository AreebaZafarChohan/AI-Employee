---
name: email_drafter
description: Draft professional email replies for business workflows with customizable tone, templates, and follow-up suggestions.
---

# Email Drafter

## Purpose

This skill generates polished, professional email responses for various business scenarios. It takes email metadata and user intent as input and produces well-structured email bodies, subject lines, and optional follow-up actions. The skill is designed to maintain formal business communication standards while adapting to different contexts and recipient types.

## When to Use This Skill

Use `email_drafter` when:

- **Customer inquiries**: Responding to customer questions, complaints, or feature requests
- **Internal communication**: Drafting emails to team members, managers, or cross-functional teams
- **Vendor correspondence**: Communicating with suppliers, partners, or external service providers
- **Meeting scheduling**: Proposing meeting times, sending agenda, or following up on action items
- **Status updates**: Providing project updates, progress reports, or milestone announcements
- **Escalation responses**: Addressing escalated issues or sensitive communications
- **Rejection/Decline**: Politely declining requests, proposals, or invitations
- **Approval requests**: Asking for authorization, sign-off, or budget approval

Do NOT use this skill when:

- **Automated replies**: System-generated notifications or auto-responses (use templates instead)
- **Internal chat/Slack**: Informal messaging that doesn't require email formality
- **Legal communications**: Contracts, legal notices, or compliance-related emails requiring legal review
- **Emergency communications**: Time-sensitive crisis communications requiring human oversight
- **Personal messages**: Non-business emails

## Impact Analysis Workflow

### 1. Environment Variable Strategy

**Build-Time vs Runtime Variables:**

This skill operates at runtime only. No build-time variables required.

**Runtime variables:**
```bash
# Required
VAULT_PATH="/absolute/path/to/vault"
EMAIL_DRAFTS_PATH="$VAULT_PATH/Email_Drafts"  # Auto-created if missing

# Optional: Email configuration
EMAIL_DEFAULT_TONE="formal"                    # formal | semi-formal | friendly
EMAIL_SIGNATURE_NAME="AI Assistant"            # Default sender name
EMAIL_SIGNATURE_TITLE="Automation System"      # Default sender title
EMAIL_SIGNATURE_COMPANY="Company Name"         # Company name
EMAIL_SIGNATURE_CONTACT="support@company.com"  # Contact email

# Optional: Templates
EMAIL_TEMPLATE_PATH="$VAULT_PATH/Email_Templates"  # Custom template location
EMAIL_AUTO_SUBJECT="true"                          # Auto-generate subject if not provided
EMAIL_INCLUDE_FOLLOWUP="true"                      # Include follow-up suggestions

# Optional: Compliance
EMAIL_DISCLAIMER_TEXT=""                       # Optional footer disclaimer
EMAIL_CONFIDENTIALITY_NOTICE="true"            # Add confidentiality notice
EMAIL_REQUIRE_REVIEW="false"                   # Flag all drafts for human review

# Optional: Audit trail
EMAIL_AUDIT_LOG_PATH="$VAULT_PATH/Audit_Logs"
EMAIL_SESSION_ID=""                            # Current agent session ID
```

**Secrets Management:**

- This skill does NOT send emails (draft only)
- No email server credentials required
- May reference recipient emails, customer names (not sensitive)
- Never log email content to system logs

**Variable Discovery Process:**
```bash
# Check email configuration
cat .env | grep EMAIL_

# Verify Email_Drafts folder exists
test -d "$VAULT_PATH/Email_Drafts" && echo "OK" || mkdir -p "$VAULT_PATH/Email_Drafts"

# Count draft emails
find "$VAULT_PATH/Email_Drafts" -name '*.md' | wc -l
```

### 2. Network & Topology Implications

**Port Discovery:**

No network ports required. This skill operates on local filesystem only.

**Dependency Topology:**

```
Email Drafter
  ├── Vault State Manager (file writes to Email_Drafts/)
  │   └── Filesystem (Email_Drafts/ folder)
  └── Optional: Email Templates
      └── Filesystem (Email_Templates/ folder)
```

**Topology Notes:**
- Primary operation: local file writes (no external dependencies)
- No email server integration (draft only)
- No database dependencies
- Stateless operation (each draft is independent)

**Docker/K8s Implications:**

When containerizing agents that use this skill:
- Mount vault as read-write volume: `-v /host/vault:/vault:rw`
- Ensure `Email_Drafts/` folder is writable
- No network access required
- No persistent storage needed beyond vault mount

### 3. Auth / CORS / Security Impact

**Authentication Pattern Analysis:**

- No authentication for filesystem access (local only)
- Agent authorization: all agents have write access to Email_Drafts/ (per AGENTS.md §4)

**Security Considerations:**

| Risk | Mitigation |
|------|-----------|
| **Sensitive data exposure** | Never log email bodies or recipient information |
| **PII leakage** | Sanitize customer names and emails before logging |
| **Path traversal** | Validate all paths via vault_state_manager |
| **Content injection** | Sanitize user input to prevent XSS in HTML emails |
| **Template tampering** | Validate template files before rendering |

**Validation Rules:**

Before creating any email draft:
```javascript
function validateEmailDraft(draft) {
  // Required fields check
  if (!draft.recipient || !draft.recipient.email) {
    throw new Error("Recipient email is required");
  }

  // Email format validation
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(draft.recipient.email)) {
    throw new Error("Invalid recipient email format");
  }

  // Subject line check
  if (!draft.subject || draft.subject.length > 200) {
    throw new Error("Subject must be 1-200 characters");
  }

  // Body content check
  if (!draft.body || draft.body.length < 10) {
    throw new Error("Email body must contain meaningful content");
  }

  return true;
}
```

---

## Usage Patterns

### Pattern 1: Customer Inquiry Response

**Use Case:** Responding to customer question about product features

**Input:**
```javascript
const { draftEmail } = require('./email_drafter');

const emailDraft = await draftEmail({
  intent: "customer_inquiry_response",
  recipient: {
    name: "John Doe",
    email: "john@example.com",
    type: "customer"
  },
  context: {
    original_subject: "Question about API rate limits",
    original_message: "Hi, I'm wondering what the API rate limits are for the Pro plan? We're planning to integrate your API into our application.",
    customer_plan: "Pro",
    account_id: "cust_12345"
  },
  tone: "friendly",
  key_points: [
    "Pro plan has 10,000 requests per hour",
    "Rate limits reset every hour",
    "Enterprise plan available for higher limits",
    "Offer to schedule demo call"
  ],
  metadata: {
    agent: "lex",
    session_id: "session_abc123",
    timestamp: "2025-02-04T14:30:22Z"
  }
});

console.log(`Email draft created: ${emailDraft.file_path}`);
console.log(`Draft ID: ${emailDraft.draft_id}`);
```

**Output File:** `Email_Drafts/20250204-143022-customer-inquiry-john-doe.md`

**File Content:**
```markdown
---
draft_id: DRAFT-20250204-143022-ABC123
created_at: 2025-02-04T14:30:22Z
status: draft
email_type: customer_inquiry_response
priority: normal
recipient: john@example.com
tone: friendly
requires_review: false
---

# Email Draft: Customer Inquiry Response

**Draft ID:** DRAFT-20250204-143022-ABC123
**Created:** 2025-02-04 14:30:22 UTC
**Status:** 📝 Draft
**Recipient:** John Doe <john@example.com>

---

## Email Details

**To:** john@example.com
**Subject:** Re: Question about API rate limits
**CC:**
**BCC:**
**Priority:** Normal

---

## Email Body

Hi John,

Thank you for reaching out about our API rate limits! I'm happy to help clarify.

For your Pro plan, here are the current rate limits:

- **Requests per hour:** 10,000
- **Rate limit reset:** Every hour (on the hour)
- **Burst allowance:** Up to 200 requests per minute

These limits should provide plenty of headroom for most integration scenarios. If you find you're approaching these limits as your application scales, we also offer an Enterprise plan with customizable rate limits up to 100,000 requests per hour.

I'd be happy to schedule a quick call to discuss your integration plans and ensure you have the right setup for your needs. Would you be available for a 15-minute call this week?

Looking forward to supporting your integration!

Best regards,
AI Assistant
Automation System
Company Name
support@company.com

---

## Alternative Subject Lines

1. Re: Question about API rate limits (Primary)
2. API Rate Limit Details for Your Pro Plan
3. Your API Integration - Rate Limit Information

---

## Follow-Up Actions

- [ ] Send email within 4 business hours
- [ ] Monitor customer's response for follow-up questions
- [ ] If customer schedules call, add to calendar and send meeting invite
- [ ] Update customer record with "API inquiry" tag
- [ ] If customer upgrades to Enterprise, notify sales team

---

## Tone Analysis

**Selected Tone:** Friendly
**Characteristics:**
- Warm greeting with first name
- Conversational but professional language
- Proactive offer of additional help
- Emphasis on partnership and support

---

## Content Checklist

- [x] Addressed customer by name
- [x] Answered primary question (rate limits)
- [x] Provided specific, actionable information
- [x] Offered additional value (Enterprise plan mention)
- [x] Included clear call-to-action (schedule call)
- [x] Professional signature with contact info

---

## Metadata

- **Agent:** lex (Local Executive Agent)
- **Session ID:** session_abc123
- **Context:** Customer inquiry about API rate limits
- **Customer Plan:** Pro
- **Account ID:** cust_12345
- **Template Used:** customer_inquiry_response_v1

---

## Approval Workflow

**Review Required:** No (standard customer inquiry)

If you need to modify this draft:
1. Edit the email body above
2. Update subject line if needed
3. Mark status as `ready_to_send` in frontmatter when approved
4. Agent will detect status change and proceed with sending

To reject this draft:
1. Mark status as `rejected` in frontmatter
2. Add rejection reason in a comment below

---

## Draft History

- **v1.0** - 2025-02-04 14:30:22 UTC - Initial draft created
```

---

### Pattern 2: Meeting Scheduling Request

**Use Case:** Scheduling a meeting with multiple stakeholders

**Input:**
```javascript
const emailDraft = await draftEmail({
  intent: "meeting_request",
  recipient: {
    name: "Sarah Johnson",
    email: "sarah.johnson@partner.com",
    type: "external_stakeholder"
  },
  context: {
    meeting_purpose: "Q1 Partnership Review",
    meeting_duration: "60 minutes",
    proposed_dates: [
      "2025-02-10T14:00:00Z",
      "2025-02-12T10:00:00Z",
      "2025-02-15T15:00:00Z"
    ],
    meeting_type: "video_call",
    attendees: ["john@company.com", "sarah.johnson@partner.com"],
    agenda_items: [
      "Review Q4 2024 performance",
      "Discuss Q1 2025 goals",
      "Address outstanding action items",
      "Plan next quarter activities"
    ]
  },
  tone: "formal",
  key_points: [
    "Quarterly review meeting",
    "Propose 3 time slots",
    "Include agenda",
    "Mention video call link will be sent"
  ],
  metadata: {
    agent: "lex",
    session_id: "session_xyz789"
  }
});
```

**Output:**
```markdown
---
draft_id: DRAFT-20250204-143522-XYZ789
created_at: 2025-02-04T14:35:22Z
status: draft
email_type: meeting_request
priority: normal
recipient: sarah.johnson@partner.com
tone: formal
---

# Email Draft: Meeting Request

## Email Body

Dear Sarah,

I hope this message finds you well. I am writing to schedule our Q1 Partnership Review meeting to discuss our collaboration progress and align on upcoming objectives.

**Meeting Details:**
- **Purpose:** Q1 Partnership Review
- **Duration:** 60 minutes
- **Format:** Video call (link to be provided upon confirmation)

**Proposed Time Slots (all times in UTC):**
1. February 10, 2025 at 2:00 PM
2. February 12, 2025 at 10:00 AM
3. February 15, 2025 at 3:00 PM

**Meeting Agenda:**
1. Review Q4 2024 performance metrics and key achievements
2. Discuss Q1 2025 goals and success criteria
3. Address outstanding action items from previous meeting
4. Plan collaboration activities for next quarter

**Attendees:**
- John Smith (john@company.com)
- Sarah Johnson (sarah.johnson@partner.com)

Could you please let me know which time slot works best for you? If none of these times are convenient, I'm happy to propose additional options.

I will send a calendar invitation with video call details once we confirm the time.

Looking forward to our discussion.

Best regards,
AI Assistant
Automation System
Company Name
support@company.com

---

## Alternative Subject Lines

1. Q1 Partnership Review - Scheduling Request (Primary)
2. Let's Schedule Our Q1 Partnership Meeting
3. Meeting Request: Q1 Partnership Review

---

## Follow-Up Actions

- [ ] Wait for recipient confirmation (48 hours)
- [ ] Send calendar invite with video call link once time confirmed
- [ ] Prepare meeting materials and share agenda document
- [ ] Send reminder 24 hours before meeting
- [ ] If no response in 48 hours, send polite follow-up
```

---

### Pattern 3: Rejection Email (Declining Request)

**Use Case:** Politely declining a vendor proposal

**Input:**
```javascript
const emailDraft = await draftEmail({
  intent: "polite_rejection",
  recipient: {
    name: "Michael Chen",
    email: "michael@vendorcorp.com",
    type: "vendor"
  },
  context: {
    original_subject: "Proposal for Cloud Infrastructure Services",
    rejection_reason: "already_committed_to_another_vendor",
    additional_context: "We recently signed a multi-year agreement with another provider"
  },
  tone: "formal",
  key_points: [
    "Thank for proposal",
    "Appreciate effort and detail",
    "Already committed to another solution",
    "Keep door open for future opportunities"
  ],
  metadata: {
    agent: "lex",
    session_id: "session_def456"
  }
});
```

**Output:**
```markdown
---
draft_id: DRAFT-20250204-144022-DEF456
created_at: 2025-02-04T14:40:22Z
status: draft
email_type: polite_rejection
priority: normal
recipient: michael@vendorcorp.com
tone: formal
---

# Email Draft: Polite Rejection

## Email Body

Dear Michael,

Thank you for taking the time to prepare and present your comprehensive proposal for Cloud Infrastructure Services. We genuinely appreciate the effort and detail you put into understanding our requirements.

After careful consideration and review with our technical team, we have decided to proceed with another vendor for this particular initiative. This decision was made as we recently finalized a multi-year agreement with another cloud infrastructure provider that aligns with our current strategic direction.

Please know that this decision in no way reflects the quality of your proposal or VendorCorp's capabilities. We were impressed with your offerings and would be open to exploring potential collaboration opportunities in the future should our circumstances change or new projects arise.

We wish you continued success and hope to stay in touch.

Best regards,
AI Assistant
Automation System
Company Name
support@company.com

---

## Alternative Subject Lines

1. Re: Proposal for Cloud Infrastructure Services (Primary)
2. Thank You for Your Proposal - Update on Our Decision
3. Cloud Infrastructure Services Proposal - Our Decision

---

## Follow-Up Actions

- [ ] Send email promptly (within 24 hours of decision)
- [ ] Add vendor to "Future Opportunities" CRM list
- [ ] Log interaction in vendor management system
- [ ] No further action required unless vendor responds

---

## Tone Analysis

**Selected Tone:** Formal
**Characteristics:**
- Professional and respectful language
- Expresses gratitude for vendor's effort
- Clear but diplomatic rejection
- Leaves door open for future collaboration
- No unnecessary justification or over-explanation
```

---

## Key Guarantees

1. **Professional Quality**: All drafts maintain business-appropriate language and formatting
2. **Structured Output**: Consistent markdown format with YAML frontmatter
3. **Unique IDs**: Each draft gets a cryptographically secure unique ID
4. **Tone Adaptation**: Adjusts language based on recipient type and context
5. **Subject Line Variations**: Provides multiple subject line options
6. **Follow-Up Guidance**: Includes actionable next steps
7. **Metadata Tracking**: Full audit trail of who requested, when, and context
8. **Review Workflow**: Built-in approval process for sensitive emails

---

## Output Schema

**Email Draft File:**
- **Location:** `Email_Drafts/`
- **Naming:** `YYYYMMDD-HHMMSS-<email-type>-<recipient-slug>.md`
- **Format:** Markdown with YAML frontmatter

**Frontmatter Fields:**
```yaml
draft_id: "DRAFT-YYYYMMDD-HHMMSS-HASH"
created_at: "ISO8601 timestamp"
status: "draft | ready_to_send | sent | rejected"
email_type: "customer_inquiry_response | meeting_request | status_update | rejection | etc"
priority: "low | normal | high | urgent"
recipient: "recipient@example.com"
tone: "formal | semi-formal | friendly"
requires_review: true | false
reviewed_by: null
reviewed_at: null
sent_by: null
sent_at: null
```

---

## Supported Email Types

| Email Type | Use Case | Default Tone |
|------------|----------|--------------|
| `customer_inquiry_response` | Answering customer questions | Friendly |
| `meeting_request` | Scheduling meetings | Formal |
| `status_update` | Project/task progress | Semi-formal |
| `polite_rejection` | Declining requests | Formal |
| `escalation_response` | Addressing complaints | Formal |
| `approval_request` | Seeking authorization | Formal |
| `follow_up` | Checking in after meeting/email | Semi-formal |
| `introduction` | Introducing team/product | Friendly |
| `thank_you` | Expressing gratitude | Semi-formal |
| `apology` | Addressing mistakes/issues | Formal |

---

## Integration Points

**Upstream Skills:**
- `company_handbook_enforcer` → Ensures email complies with communication policies
- `approval_request_creator` → May require approval before sending sensitive emails

**Downstream Skills:**
- `vault_state_manager` → Stores drafts and tracks email lifecycle
- External email service (not included) → Sends emails marked as `ready_to_send`

**Related Skills:**
- `dashboard_writer` → Displays pending draft count in dashboard

---

## Error Handling

**Common Errors:**

1. **Missing Required Fields:**
   ```
   Error: Email draft missing required field 'recipient.email'
   Solution: Ensure recipient email is provided
   ```

2. **Invalid Email Format:**
   ```
   Error: Invalid email format: 'john@example'
   Solution: Provide valid email with domain
   ```

3. **Empty Email Body:**
   ```
   Error: Email body cannot be empty
   Solution: Provide context and key points for draft generation
   ```

4. **File Write Failure:**
   ```
   Error: Permission denied writing to Email_Drafts/
   Solution: Ensure agent has write access to vault directory
   ```

---

## Configuration Examples

### Minimal Configuration:
```bash
VAULT_PATH="/path/to/vault"
```

### With Custom Signature:
```bash
VAULT_PATH="/path/to/vault"
EMAIL_SIGNATURE_NAME="Customer Success Team"
EMAIL_SIGNATURE_TITLE="Support Specialist"
EMAIL_SIGNATURE_COMPANY="Acme Corp"
EMAIL_SIGNATURE_CONTACT="support@acmecorp.com"
```

### Production Setup (with review workflow):
```bash
VAULT_PATH="/path/to/vault"
EMAIL_DEFAULT_TONE="formal"
EMAIL_REQUIRE_REVIEW="true"
EMAIL_CONFIDENTIALITY_NOTICE="true"
EMAIL_AUDIT_LOG_PATH="$VAULT_PATH/Audit_Logs"
```

---

## Testing Checklist

Before deploying this skill:

- [ ] Verify `Email_Drafts/` folder exists and is writable
- [ ] Test draft creation for all email types
- [ ] Verify unique ID generation (no collisions)
- [ ] Test tone variations (formal, semi-formal, friendly)
- [ ] Verify subject line generation
- [ ] Test follow-up action generation
- [ ] Verify metadata tracking
- [ ] Test with missing required fields (expect validation error)
- [ ] Test with invalid email format (expect validation error)
- [ ] Verify audit log entries created (if configured)

---

## Version History

- **v1.0.0** (2025-02-04): Initial release
  - Core email drafting functionality
  - Support for 10+ email types
  - Tone adaptation (formal, semi-formal, friendly)
  - Subject line generation
  - Follow-up action suggestions
  - Markdown output with YAML frontmatter
  - Audit trail integration
