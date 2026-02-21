# Communication Skills

This directory contains skills related to business communication workflows.

## Available Skills

### email_drafter

**Purpose:** Draft professional email replies for business workflows with customizable tone, templates, and follow-up suggestions.

**Use Cases:**
- Customer support responses
- Meeting scheduling
- Status updates
- Vendor communications
- Internal team updates
- Escalation handling

**Quick Start:**
```javascript
const { draftEmail } = require('./email_drafter');

await draftEmail({
  intent: "customer_inquiry_response",
  recipient: { name: "John Doe", email: "john@example.com", type: "customer" },
  tone: "friendly",
  key_points: ["Answer question", "Provide solution", "Offer follow-up"]
});
```

**Documentation:**
- [Full Documentation](./email_drafter/SKILL.md)
- [Quick Start Guide](./email_drafter/README.md)
- [Usage Examples](./email_drafter/EXAMPLES.md)
- [Common Issues](./email_drafter/references/gotchas.md)

---

## Skill Integration

Communication skills integrate with:

- **vault_state_manager** - Stores email drafts in vault
- **company_handbook_enforcer** - Validates communication compliance
- **approval_request_creator** - Requires approval for sensitive emails
- **dashboard_writer** - Displays pending draft metrics

---

## Adding New Communication Skills

When adding new skills to this category:

1. Follow the standard skill structure:
   ```
   skill_name/
   ├── SKILL.md
   ├── README.md
   ├── EXAMPLES.md
   ├── references/
   │   ├── patterns.md
   │   ├── gotchas.md
   │   └── impact-checklist.md
   └── assets/
       └── .env.example
   ```

2. Ensure integration with existing vault structure
3. Consider compliance requirements
4. Document security considerations
5. Provide comprehensive examples

---

## Communication Best Practices

### Tone Guidelines

| Recipient Type | Recommended Tone | Use Case |
|----------------|------------------|----------|
| Customer | Friendly | Support, onboarding |
| Executive | Formal | Proposals, reports |
| Vendor | Formal | Negotiations, contracts |
| Internal Team | Semi-formal | Updates, collaboration |
| Partner | Formal | Agreements, planning |

### Security Considerations

- **Never include credentials** in email body
- **Use secure portals** for sensitive data sharing
- **Sanitize PII** before logging
- **Validate recipients** before sending
- **Require review** for external stakeholder emails

### Quality Checklist

Before sending any communication:

- [ ] Recipient information verified
- [ ] Tone appropriate for relationship
- [ ] Clear subject line
- [ ] Actionable next steps included
- [ ] Links and attachments verified
- [ ] Signature information complete
- [ ] No typos or formatting issues
- [ ] Compliance requirements met

---

## Support

For issues or questions about communication skills:

1. Check skill-specific documentation first
2. Review common issues in `references/gotchas.md`
3. Consult usage patterns in `references/patterns.md`
4. File issues in project issue tracker

---

## Version History

- **2025-02-04** - Added `email_drafter` skill
  - Professional email drafting with tone adaptation
  - 10+ email types supported
  - Integration with vault and compliance systems
