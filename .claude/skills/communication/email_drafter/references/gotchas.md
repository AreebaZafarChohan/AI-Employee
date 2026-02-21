# Email Drafter - Common Gotchas and Troubleshooting

This document covers common pitfalls, edge cases, and troubleshooting guidance for the `email_drafter` skill.

---

## Common Gotchas

### 1. Tone Mismatch for Recipient Type

**Problem:**
Using "friendly" tone for formal business communications (legal, executive, vendor negotiations).

**Example:**
```javascript
// ❌ WRONG - too casual for executive communication
const draft = await draftEmail({
  intent: "meeting_request",
  recipient: {
    name: "CEO Jane Smith",
    email: "ceo@partnercorp.com",
    type: "executive"
  },
  tone: "friendly",  // ❌ Too casual!
  ...
});
```

**Generated (problematic):**
```
Hey Jane! 👋

Hope you're doing great! Quick question - wanna grab some time next week to chat about our partnership? Let me know what works!

Cheers! 🎉
```

**Solution:**
```javascript
// ✅ CORRECT - formal tone for executive communication
const draft = await draftEmail({
  intent: "meeting_request",
  recipient: {
    name: "CEO Jane Smith",
    email: "ceo@partnercorp.com",
    type: "executive"
  },
  tone: "formal",  // ✅ Appropriate!
  ...
});
```

**Generated (appropriate):**
```
Dear Ms. Smith,

I hope this message finds you well. I am writing to request a meeting to discuss our ongoing partnership and explore potential collaboration opportunities for Q1 2025.

Would you be available for a 30-minute video call during the week of February 10-14? I am happy to work around your schedule.

I look forward to your response.

Best regards,
[Signature]
```

**Fix:**
- Use `"formal"` for: executives, legal, contracts, official announcements
- Use `"semi-formal"` for: internal team updates, project communications
- Use `"friendly"` for: customer support, onboarding, thank-you notes

---

### 2. Missing Critical Context Leads to Generic Emails

**Problem:**
Insufficient context results in vague, unhelpful email drafts.

**Example:**
```javascript
// ❌ WRONG - minimal context
const draft = await draftEmail({
  intent: "customer_inquiry_response",
  recipient: {
    name: "John",
    email: "john@example.com",
    type: "customer"
  },
  context: {
    original_message: "I have a question"  // ❌ Too vague!
  },
  key_points: [
    "Answer the question"  // ❌ What question?
  ]
});
```

**Generated (unhelpful):**
```
Hi John,

Thank you for reaching out. I'd be happy to help answer your question.

[Generic response with no specific information]

Let me know if you need anything else!
```

**Solution:**
```javascript
// ✅ CORRECT - comprehensive context
const draft = await draftEmail({
  intent: "customer_inquiry_response",
  recipient: {
    name: "John Doe",
    email: "john@example.com",
    type: "customer"
  },
  context: {
    original_subject: "Can I export data in CSV format?",
    original_message: "I need to export all customer records from the last quarter into a CSV file for analysis. Is this possible with our current Pro plan?",
    customer_plan: "Pro",
    customer_since: "2024-06-15",
    feature_availability: {
      csv_export: true,
      formats_supported: ["CSV", "Excel", "JSON"]
    }
  },
  key_points: [
    "Confirm CSV export is available on Pro plan",
    "Provide step-by-step instructions",
    "Mention other supported formats",
    "Include link to documentation",
    "Offer to help if they encounter issues"
  ]
});
```

**Generated (helpful):**
```
Hi John,

Great news! CSV export is fully supported on your Pro plan. Here's how to export your customer records:

1. Navigate to Dashboard > Customers
2. Click "Export" in the top right
3. Select date range: Q4 2024 (Oct 1 - Dec 31)
4. Choose format: CSV
5. Click "Download"

Your file will include all customer fields and should download within seconds.

**Additional formats available:** Excel (.xlsx), JSON

**Documentation:** [CSV Export Guide](https://docs.company.com/export-csv)

If you encounter any issues or need help with custom field selection, just let me know!

Best regards,
[Signature]
```

**Fix:**
- Always include original message/subject for inquiries
- Provide relevant account/plan details
- Include technical specifics when applicable
- Add actionable step-by-step guidance in key_points

---

### 3. Subject Line Too Generic or Missing

**Problem:**
Email draft has vague subject line that doesn't convey purpose.

**Example:**
```javascript
// ❌ WRONG - no subject guidance
const draft = await draftEmail({
  intent: "status_update",
  recipient: { ... },
  // No context.subject provided
  // No context.original_subject
});
```

**Generated:**
```
Subject: Update  // ❌ Too vague!
```

**Solution:**
```javascript
// ✅ CORRECT - provide subject context
const draft = await draftEmail({
  intent: "status_update",
  recipient: { ... },
  context: {
    project_name: "Mobile App Redesign",
    reporting_period: "Week of Feb 3-9",
    overall_status: "on_track"
  },
  // Skill will auto-generate descriptive subject
});
```

**Generated:**
```
Subject: Mobile App Redesign Status Update - Week of Feb 3-9 (On Track)
```

**Alternative subjects provided:**
1. Mobile App Redesign Status Update - Week of Feb 3-9 (On Track)
2. Weekly Update: Mobile App Redesign - Feb 3-9
3. Project Status: Mobile App Redesign (On Track)

**Fix:**
- Always provide `context.project_name` or `context.original_subject`
- Enable `EMAIL_AUTO_SUBJECT=true` to generate subjects automatically
- Review alternative subjects in draft and choose best fit

---

### 4. Overly Long Emails (TL;DR Problem)

**Problem:**
Email drafts become excessively long, burying key information.

**Example:**
```javascript
// ❌ WRONG - too many key points
const draft = await draftEmail({
  intent: "customer_inquiry_response",
  key_points: [
    "Explain feature A in detail",
    "Explain feature B in detail",
    "Explain feature C in detail",
    "Provide history of product",
    "Discuss future roadmap",
    "Include company background",
    "List all team members",
    "Describe entire onboarding process",
    "Explain all pricing tiers",
    "List every integration available"  // ❌ Too much!
  ]
});
```

**Generated:**
```
[3000+ word email that nobody will read]
```

**Solution:**
```javascript
// ✅ CORRECT - focused key points
const draft = await draftEmail({
  intent: "customer_inquiry_response",
  key_points: [
    "Answer the specific question asked",
    "Provide one clear action item",
    "Include link to relevant documentation for details",
    "Offer to schedule call if more explanation needed"
  ]
});
```

**Generated:**
```
Hi [Name],

[Direct answer to question in 2-3 sentences]

**Next Step:** [One clear action]

**More details:** [Link to docs]

Need more help? Reply here or schedule a call: [calendar link]

Best,
[Signature]
```

**Fix:**
- Limit key_points to 3-5 most important items
- Use links to documentation for detailed info
- Offer follow-up call for complex topics
- Remember: shorter emails get higher response rates

---

### 5. Missing Recipient Type Classification

**Problem:**
Not specifying recipient type leads to inappropriate tone/format.

**Example:**
```javascript
// ❌ WRONG - no recipient type
const draft = await draftEmail({
  recipient: {
    name: "Sarah Johnson",
    email: "sarah@vendorcorp.com"
    // Missing: type field ❌
  }
});
```

**Generated:**
```
[Generic email with ambiguous tone - could be too formal or too casual]
```

**Solution:**
```javascript
// ✅ CORRECT - specify recipient type
const draft = await draftEmail({
  recipient: {
    name: "Sarah Johnson",
    email: "sarah@vendorcorp.com",
    type: "vendor",  // ✅ Clear classification
    company: "VendorCorp Inc."
  }
});
```

**Recipient Types:**
- `"customer"` - End users, paying customers
- `"vendor"` - Suppliers, service providers
- `"partner"` - Strategic partners, resellers
- `"internal_team"` - Company employees, team members
- `"executive"` - C-level, directors, senior leadership
- `"external_stakeholder"` - Investors, board members, advisors
- `"support_request"` - People requesting help/support

**Fix:**
Always specify `recipient.type` to ensure appropriate tone and formatting.

---

### 6. Forgetting to Handle Time Zones

**Problem:**
Proposing meeting times without specifying time zone.

**Example:**
```javascript
// ❌ WRONG - ambiguous time zone
context: {
  proposed_dates: [
    "February 10 at 2:00 PM"  // ❌ What time zone?
  ]
}
```

**Generated:**
```
Proposed Time: February 10 at 2:00 PM  // Confusing for international recipients
```

**Solution:**
```javascript
// ✅ CORRECT - always use ISO 8601 with UTC or explicit timezone
context: {
  proposed_dates: [
    "2025-02-10T14:00:00Z",  // UTC
    "2025-02-10T14:00:00-08:00",  // PST with offset
    "2025-02-10T14:00:00+00:00"  // Explicit UTC
  ],
  recipient_timezone: "America/New_York"  // Optional: convert display
}
```

**Generated:**
```
Proposed Times (all times in UTC):
1. February 10, 2025 at 2:00 PM UTC (9:00 AM EST)
2. February 12, 2025 at 10:00 AM UTC (5:00 AM EST)
```

**Fix:**
- Always use ISO 8601 format for dates/times
- Explicitly state time zone in email body
- Consider recipient's time zone when proposing times
- Use tools like `moment-timezone` for conversion

---

### 7. Not Handling Email Threading Properly

**Problem:**
Reply emails don't preserve subject line prefix (Re:, Fwd:).

**Example:**
```javascript
// ❌ WRONG - creates new thread
context: {
  original_subject: "API Integration Question",
  subject: "API Integration Question"  // ❌ Should be "Re: ..."
}
```

**Solution:**
```javascript
// ✅ CORRECT - preserve email threading
context: {
  original_subject: "API Integration Question",
  is_reply: true  // ✅ Triggers "Re:" prefix
}
// OR manually specify:
context: {
  subject: "Re: API Integration Question"  // ✅ Explicit
}
```

**Fix:**
- For replies: use "Re: [original subject]"
- For forwards: use "Fwd: [original subject]"
- Set `context.is_reply = true` to auto-add prefix
- Preserve threading for better email organization

---

### 8. Sensitive Information in Email Drafts

**Problem:**
Including passwords, API keys, or PII in email body.

**Example:**
```javascript
// ❌ WRONG - sensitive data in email
context: {
  api_key: "sk_live_abc123xyz789",  // ❌ NEVER!
  customer_ssn: "123-45-6789",  // ❌ NEVER!
  password: "TempPass123"  // ❌ NEVER!
}
```

**Generated:**
```
Here's your API key: sk_live_abc123xyz789  // ❌ Security violation!
```

**Solution:**
```javascript
// ✅ CORRECT - use secure delivery methods
context: {
  credential_type: "API key",
  secure_delivery_method: "Secure credential portal",
  portal_link: "https://secure.company.com/credentials/retrieve/abc123"
}
key_points: [
  "API key is available in secure portal",
  "Provide link to credential portal",
  "Explain expiration policy",
  "Never include actual key in email"
]
```

**Generated:**
```
Your API key has been generated and is available in our secure credential portal:

🔐 Access your key: https://secure.company.com/credentials/retrieve/abc123

For security reasons, we never send credentials via email. Your key will expire in 7 days if not retrieved.
```

**Fix:**
- NEVER include passwords, API keys, tokens in email
- Use secure portals or password managers for credential delivery
- Use temporary secure links that expire
- Follow security policies from `company_handbook_enforcer`

---

### 9. Action Items Without Clear Ownership

**Problem:**
Follow-up actions don't specify who is responsible.

**Example:**
```javascript
// ❌ WRONG - vague action items
context: {
  action_items: [
    "Follow up on proposal",  // ❌ Who does this?
    "Schedule meeting",  // ❌ Who schedules?
    "Review contract"  // ❌ Who reviews?
  ]
}
```

**Generated:**
```
Action Items:
- Follow up on proposal  // Nobody knows who's responsible
- Schedule meeting
- Review contract
```

**Solution:**
```javascript
// ✅ CORRECT - explicit ownership and due dates
context: {
  action_items: [
    {
      task: "Follow up on proposal with finance team",
      owner: "Sarah (Sender)",
      due_date: "2025-02-08"
    },
    {
      task: "Schedule Q1 planning meeting",
      owner: "David (Recipient)",
      due_date: "2025-02-10"
    },
    {
      task: "Review and sign contract",
      owner: "Legal Team",
      due_date: "2025-02-15"
    }
  ]
}
```

**Generated:**
```
Action Items:

| Task | Owner | Due Date |
|------|-------|----------|
| Follow up on proposal with finance team | Sarah (Sender) | Feb 8, 2025 |
| Schedule Q1 planning meeting | David (Recipient) | Feb 10, 2025 |
| Review and sign contract | Legal Team | Feb 15, 2025 |
```

**Fix:**
- Always assign explicit owner to each action item
- Include due dates for time-sensitive tasks
- Use structured format (table or list with fields)
- Clarify "(Sender)" vs "(Recipient)" when needed

---

### 10. Not Accounting for Email Client Rendering

**Problem:**
Using formatting that breaks in plain text email clients.

**Example:**
```javascript
// ❌ WRONG - complex HTML tables and styling
key_points: [
  "Create multi-column layout with CSS",
  "Use custom fonts and colors",
  "Include interactive elements"
]
```

**Generated:**
```html
<div style="display: flex; background: #f0f0f0;">
  <!-- Complex HTML that breaks in many email clients -->
</div>
```

**Solution:**
```javascript
// ✅ CORRECT - simple markdown that works everywhere
key_points: [
  "Use simple markdown formatting",
  "Stick to basic tables",
  "Ensure plain text fallback"
]
```

**Generated:**
```markdown
**Key Points:**
- Point 1
- Point 2
- Point 3

| Column 1 | Column 2 |
|----------|----------|
| Data 1   | Data 2   |

[Link text](https://example.com)
```

**Fix:**
- Use simple markdown (bold, italic, lists, tables)
- Avoid complex HTML/CSS
- Test in plain text mode
- Provide plain text alternative for all content
- Remember: many corporate email clients strip HTML

---

## Troubleshooting Guide

### Issue: Draft Files Not Being Created

**Symptoms:**
```
Error: Permission denied writing to Email_Drafts/
```

**Diagnosis:**
```bash
# Check if directory exists
ls -la "$VAULT_PATH/Email_Drafts"

# Check write permissions
test -w "$VAULT_PATH/Email_Drafts" && echo "Writable" || echo "Not writable"
```

**Solution:**
```bash
# Create directory if missing
mkdir -p "$VAULT_PATH/Email_Drafts"

# Fix permissions
chmod 755 "$VAULT_PATH/Email_Drafts"

# Verify vault path is correct
echo $VAULT_PATH
```

---

### Issue: Duplicate Draft IDs

**Symptoms:**
```
Error: Draft ID DRAFT-20250204-143022-ABC123 already exists
```

**Diagnosis:**
```bash
# Check for duplicate IDs
find "$VAULT_PATH/Email_Drafts" -name '*.md' -exec grep -H "draft_id:" {} \; | sort
```

**Solution:**
```javascript
// Use crypto.randomBytes for better uniqueness
const crypto = require('crypto');
const draftId = `DRAFT-${new Date().toISOString().replace(/[:.]/g, '-')}-${crypto.randomBytes(8).toString('hex').toUpperCase()}`;
```

---

### Issue: Email Tone Seems Off

**Diagnosis:**
- Check `tone` parameter in input
- Verify `recipient.type` is correctly classified
- Review generated email against expected tone

**Solution:**
```javascript
// Override tone explicitly
const draft = await draftEmail({
  ...emailDetails,
  tone: "formal",  // Force formal tone
  style_override: {
    avoid_contractions: true,
    use_full_names: true,
    formal_greeting: true
  }
});
```

---

### Issue: Subject Lines Too Long

**Symptoms:**
```
Subject: [Your Very Long Project Name] - Status Update for the Week of February 3-9, 2025 Including All Major Milestones and Blockers (On Track)
```

**Solution:**
```javascript
// Configure subject line length limit
EMAIL_MAX_SUBJECT_LENGTH=80

// Or manually shorten in context
context: {
  subject: "Project X - Status Update (Week Feb 3-9)"  // Keep under 80 chars
}
```

---

### Issue: Missing Signature Information

**Diagnosis:**
```bash
# Check environment variables
echo $EMAIL_SIGNATURE_NAME
echo $EMAIL_SIGNATURE_TITLE
echo $EMAIL_SIGNATURE_COMPANY
```

**Solution:**
```bash
# Set in .env file
EMAIL_SIGNATURE_NAME="Customer Success Team"
EMAIL_SIGNATURE_TITLE="Support Specialist"
EMAIL_SIGNATURE_COMPANY="Your Company"
EMAIL_SIGNATURE_CONTACT="support@company.com"
```

---

## Performance Issues

### Slow Draft Generation for Large Batches

**Problem:**
Generating 100+ drafts takes too long.

**Solution:**
```javascript
// Use parallel processing with concurrency limit
const pLimit = require('p-limit');
const limit = pLimit(10);  // Max 10 concurrent drafts

const draftPromises = emailRequests.map(request =>
  limit(() => draftEmail(request))
);

const results = await Promise.all(draftPromises);
```

---

## Best Practices Checklist

Before creating an email draft, verify:

- [ ] Recipient email is valid format
- [ ] Recipient type is specified
- [ ] Tone matches recipient and context
- [ ] Sufficient context provided (not generic)
- [ ] Key points are specific and actionable (3-5 max)
- [ ] Time zones specified for meeting requests
- [ ] Action items have clear ownership and due dates
- [ ] No sensitive information (passwords, keys) in body
- [ ] Subject line is concise (<80 chars)
- [ ] Email threading preserved for replies (Re:/Fwd:)
- [ ] Formatting is simple (markdown, not complex HTML)
- [ ] Signature information configured in environment

---

## Emergency Recovery

If drafts are corrupted or lost:

```bash
# Backup Email_Drafts folder
cp -r "$VAULT_PATH/Email_Drafts" "$VAULT_PATH/Email_Drafts.backup.$(date +%Y%m%d)"

# Restore from backup
cp -r "$VAULT_PATH/Email_Drafts.backup.20250204" "$VAULT_PATH/Email_Drafts"

# Verify drafts are readable
find "$VAULT_PATH/Email_Drafts" -name '*.md' -exec head -n 5 {} \;
```
