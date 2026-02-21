# Email Drafter - Usage Patterns

This document provides concrete code examples and workflow patterns for the `email_drafter` skill.

---

## Pattern 1: Customer Support Response

**Use Case:** Responding to customer complaint about service disruption

**Code Example:**

```javascript
const { draftEmail } = require('./email_drafter');
const crypto = require('crypto');

async function draftCustomerSupportEmail(customerDetails, issueContext) {
  // Generate unique draft ID
  const draftId = `DRAFT-${new Date().toISOString().replace(/[:.]/g, '-')}-${crypto.randomBytes(4).toString('hex').toUpperCase()}`;

  const draft = {
    draft_id: draftId,
    intent: "customer_inquiry_response",
    recipient: {
      name: customerDetails.name,
      email: customerDetails.email,
      type: "customer",
      account_id: customerDetails.account_id,
      plan: customerDetails.plan
    },
    context: {
      original_subject: issueContext.subject,
      original_message: issueContext.message,
      issue_type: issueContext.issue_type,
      ticket_id: issueContext.ticket_id,
      resolution_status: issueContext.resolution_status,
      compensation_offered: issueContext.compensation || null
    },
    tone: "friendly",
    key_points: [
      "Acknowledge the issue and apologize",
      "Explain what happened (brief technical summary)",
      "Describe resolution steps taken",
      "Offer compensation if applicable",
      "Provide contact for further assistance"
    ],
    metadata: {
      agent: "lex",
      session_id: process.env.EMAIL_SESSION_ID,
      timestamp: new Date().toISOString()
    }
  };

  // Create email draft
  const result = await draftEmail(draft);

  if (!result.success) {
    console.error('❌ Failed to create email draft:', result.error);
    return null;
  }

  console.log(`✅ Email draft created: ${result.file_path}`);
  console.log(`📋 Draft ID: ${result.draft_id}`);
  console.log(`📧 Recipient: ${customerDetails.email}`);

  return result;
}

// Usage
await draftCustomerSupportEmail(
  {
    name: "Alice Johnson",
    email: "alice@example.com",
    account_id: "cust_67890",
    plan: "Enterprise"
  },
  {
    subject: "Service was down for 3 hours today",
    message: "Our team couldn't access the platform all morning. This is unacceptable for an Enterprise customer.",
    issue_type: "service_outage",
    ticket_id: "TICKET-12345",
    resolution_status: "resolved",
    compensation: "20% credit for this month"
  }
);
```

**Output:**
```
✅ Email draft created: Email_Drafts/20250204-150022-customer-inquiry-alice-johnson.md
📋 Draft ID: DRAFT-20250204-150022-A1B2C3D4
📧 Recipient: alice@example.com
```

**Generated Email Body:**
```markdown
Hi Alice,

I sincerely apologize for the service disruption you experienced this morning. I understand how frustrating it must have been for your team to be unable to access the platform for three hours, especially as an Enterprise customer who relies on our service for critical operations.

**What Happened:**
We experienced an unexpected database connectivity issue starting at 8:00 AM UTC that affected a subset of our Enterprise customers. Our engineering team identified the root cause within 30 minutes and implemented a fix by 11:00 AM UTC, fully restoring service.

**What We've Done:**
- Resolved the immediate connectivity issue
- Implemented additional monitoring to detect similar issues faster
- Scheduled a post-incident review to prevent recurrence
- Applied a 20% credit to your account for this month as compensation

**Next Steps:**
Your ticket (TICKET-12345) has been marked as resolved, but please don't hesitate to reach out if you have any concerns or if you notice any lingering issues. You can reply to this email or contact me directly.

We value your partnership and are committed to providing the reliable service you expect from us.

Best regards,
AI Assistant
Automation System
Company Name
support@company.com
```

---

## Pattern 2: Internal Status Update

**Use Case:** Sending weekly project status update to team

**Code Example:**

```javascript
async function draftStatusUpdateEmail(projectDetails, statusData) {
  const draftId = `DRAFT-${new Date().toISOString().replace(/[:.]/g, '-')}-${crypto.randomBytes(4).toString('hex').toUpperCase()}`;

  const draft = {
    draft_id: draftId,
    intent: "status_update",
    recipient: {
      name: "Project Team",
      email: "team@company.com",
      type: "internal_team"
    },
    context: {
      project_name: projectDetails.name,
      reporting_period: statusData.period,
      overall_status: statusData.overall_status, // "on_track" | "at_risk" | "blocked"
      completed_milestones: statusData.completed,
      in_progress_tasks: statusData.in_progress,
      upcoming_milestones: statusData.upcoming,
      blockers: statusData.blockers || [],
      metrics: statusData.metrics || {},
      next_meeting: projectDetails.next_meeting
    },
    tone: "semi-formal",
    key_points: [
      "Summarize overall project status",
      "Highlight completed work",
      "Identify current focus areas",
      "Call out blockers requiring attention",
      "Preview upcoming milestones"
    ],
    metadata: {
      agent: "lex",
      session_id: process.env.EMAIL_SESSION_ID,
      timestamp: new Date().toISOString()
    }
  };

  const result = await draftEmail(draft);

  if (result.success) {
    console.log(`✅ Status update draft created`);
    console.log(`📋 Draft ID: ${result.draft_id}`);
    console.log(`📊 Status: ${statusData.overall_status}`);
    console.log(`📄 View draft: ${result.file_path}`);
  }

  return result;
}

// Usage
await draftStatusUpdateEmail(
  {
    name: "Customer Portal Redesign",
    next_meeting: "2025-02-08T15:00:00Z"
  },
  {
    period: "Week of February 3-9, 2025",
    overall_status: "on_track",
    completed: [
      "User research synthesis completed",
      "Wireframes approved by stakeholders",
      "Design system components finalized"
    ],
    in_progress: [
      "High-fidelity mockups (80% complete)",
      "Frontend component implementation (40% complete)",
      "API integration planning"
    ],
    upcoming: [
      "Complete mockups by Feb 7",
      "Begin user testing by Feb 10",
      "Launch beta by Feb 20"
    ],
    blockers: [
      "Waiting on legal approval for new terms of service language"
    ],
    metrics: {
      completion_percentage: 45,
      tasks_completed: 12,
      tasks_remaining: 15
    }
  }
);
```

**Generated Email:**
```markdown
Hi Team,

Here's our status update for the Customer Portal Redesign project for the week of February 3-9, 2025.

**Overall Status: 🟢 On Track** (45% complete)

**Completed This Week:**
✅ User research synthesis completed
✅ Wireframes approved by stakeholders
✅ Design system components finalized

**Currently In Progress:**
🔄 High-fidelity mockups (80% complete)
🔄 Frontend component implementation (40% complete)
🔄 API integration planning

**Upcoming Milestones:**
📅 Complete mockups by Feb 7
📅 Begin user testing by Feb 10
📅 Launch beta by Feb 20

**Blockers Requiring Attention:**
⚠️ Waiting on legal approval for new terms of service language
   → Action: [Team Lead] to follow up with legal team by EOD Feb 5

**Metrics:**
- Tasks completed: 12 of 27
- Velocity: On pace for Feb 20 beta launch
- Team capacity: Fully staffed

**Next Meeting:**
Friday, February 8 at 3:00 PM UTC

Please reach out if you have any questions or concerns. Looking forward to our continued progress!

Best regards,
AI Assistant
```

---

## Pattern 3: Meeting Follow-Up with Action Items

**Use Case:** Sending meeting summary with assigned action items

**Code Example:**

```javascript
async function draftMeetingFollowUpEmail(meetingDetails) {
  const draftId = `DRAFT-${new Date().toISOString().replace(/[:.]/g, '-')}-${crypto.randomBytes(4).toString('hex').toUpperCase()}`;

  const draft = {
    draft_id: draftId,
    intent: "follow_up",
    recipient: {
      name: "Meeting Attendees",
      email: "project-team@company.com",
      type: "internal_team",
      cc: meetingDetails.cc_list || []
    },
    context: {
      meeting_date: meetingDetails.date,
      meeting_title: meetingDetails.title,
      attendees: meetingDetails.attendees,
      key_decisions: meetingDetails.decisions || [],
      action_items: meetingDetails.action_items,
      next_meeting_date: meetingDetails.next_meeting || null,
      meeting_recording_link: meetingDetails.recording_link || null,
      notes_link: meetingDetails.notes_link || null
    },
    tone: "semi-formal",
    key_points: [
      "Thank attendees for participation",
      "Summarize key decisions made",
      "List action items with owners and due dates",
      "Include links to recording and notes",
      "Confirm next meeting date"
    ],
    metadata: {
      agent: "lex",
      session_id: process.env.EMAIL_SESSION_ID,
      timestamp: new Date().toISOString()
    }
  };

  const result = await draftEmail(draft);

  if (result.success) {
    console.log(`✅ Meeting follow-up draft created`);
    console.log(`📋 Draft ID: ${result.draft_id}`);
    console.log(`📅 Meeting: ${meetingDetails.title}`);
    console.log(`✅ Action items: ${meetingDetails.action_items.length}`);
  }

  return result;
}

// Usage
await draftMeetingFollowUpEmail({
  date: "2025-02-04T14:00:00Z",
  title: "Q1 Product Planning Meeting",
  attendees: [
    "Sarah (Product Manager)",
    "David (Engineering Lead)",
    "Emma (Design Lead)",
    "Michael (Marketing)"
  ],
  decisions: [
    "Prioritize mobile app redesign for Q1",
    "Delay social media integration to Q2",
    "Allocate 2 engineers to mobile team"
  ],
  action_items: [
    {
      task: "Create technical specification for mobile redesign",
      owner: "David",
      due_date: "2025-02-10"
    },
    {
      task: "Conduct user interviews for mobile pain points",
      owner: "Emma",
      due_date: "2025-02-08"
    },
    {
      task: "Draft product marketing messaging",
      owner: "Michael",
      due_date: "2025-02-15"
    }
  ],
  next_meeting: "2025-02-11T14:00:00Z",
  recording_link: "https://zoom.us/rec/abc123",
  notes_link: "https://docs.company.com/q1-planning-notes"
});
```

**Generated Email:**
```markdown
Hi Team,

Thank you all for joining today's Q1 Product Planning Meeting. I've summarized the key decisions and action items below.

**Meeting Details:**
- **Date:** February 4, 2025 at 2:00 PM UTC
- **Attendees:** Sarah (Product Manager), David (Engineering Lead), Emma (Design Lead), Michael (Marketing)

**Key Decisions Made:**
1. ✅ Prioritize mobile app redesign for Q1
2. ✅ Delay social media integration to Q2
3. ✅ Allocate 2 engineers to mobile team

**Action Items:**

| Task | Owner | Due Date |
|------|-------|----------|
| Create technical specification for mobile redesign | David | Feb 10, 2025 |
| Conduct user interviews for mobile pain points | Emma | Feb 8, 2025 |
| Draft product marketing messaging | Michael | Feb 15, 2025 |

**Resources:**
- 📹 [Meeting Recording](https://zoom.us/rec/abc123)
- 📝 [Meeting Notes](https://docs.company.com/q1-planning-notes)

**Next Meeting:**
Monday, February 11, 2025 at 2:00 PM UTC

Please let me know if I've missed anything or if you have questions about your action items.

Best regards,
AI Assistant
```

---

## Pattern 4: Vendor Negotiation Email

**Use Case:** Negotiating better pricing with vendor

**Code Example:**

```javascript
async function draftVendorNegotiationEmail(vendorDetails, negotiationContext) {
  const draftId = `DRAFT-${new Date().toISOString().replace(/[:.]/g, '-')}-${crypto.randomBytes(4).toString('hex').toUpperCase()}`;

  const draft = {
    draft_id: draftId,
    intent: "negotiation",
    recipient: {
      name: vendorDetails.contact_name,
      email: vendorDetails.contact_email,
      type: "vendor",
      company: vendorDetails.company_name
    },
    context: {
      current_contract: negotiationContext.current_contract,
      renewal_date: negotiationContext.renewal_date,
      current_pricing: negotiationContext.current_pricing,
      desired_pricing: negotiationContext.desired_pricing,
      usage_stats: negotiationContext.usage_stats,
      competitor_offers: negotiationContext.competitor_offers || [],
      relationship_duration: negotiationContext.relationship_duration,
      payment_history: negotiationContext.payment_history
    },
    tone: "formal",
    key_points: [
      "Express appreciation for partnership",
      "Reference usage and payment history",
      "Present data justifying pricing discussion",
      "Make specific counter-offer",
      "Mention competitive alternatives (tactfully)",
      "Request meeting to discuss"
    ],
    metadata: {
      agent: "lex",
      session_id: process.env.EMAIL_SESSION_ID,
      timestamp: new Date().toISOString()
    }
  };

  const result = await draftEmail(draft);

  if (result.success) {
    console.log(`✅ Vendor negotiation draft created`);
    console.log(`📋 Draft ID: ${result.draft_id}`);
    console.log(`💼 Vendor: ${vendorDetails.company_name}`);
    console.log(`💰 Target pricing: ${negotiationContext.desired_pricing}`);
  }

  return result;
}

// Usage
await draftVendorNegotiationEmail(
  {
    contact_name: "Robert Williams",
    contact_email: "robert@cloudservices.com",
    company_name: "CloudServices Inc."
  },
  {
    current_contract: "Enterprise Plan - 100 users",
    renewal_date: "2025-03-01",
    current_pricing: "$5,000/month",
    desired_pricing: "$3,500/month",
    usage_stats: "Average 65 active users per month (35% below capacity)",
    competitor_offers: [
      "CompetitorA: $3,200/month for 100 users",
      "CompetitorB: $3,800/month for 120 users"
    ],
    relationship_duration: "3 years",
    payment_history: "Perfect payment history, never late"
  }
);
```

**Generated Email:**
```markdown
Dear Robert,

I hope this message finds you well. We have greatly valued our partnership with CloudServices Inc. over the past three years, and your team's support has been instrumental to our operations.

As we approach our contract renewal date of March 1, 2025, I wanted to reach out to discuss our pricing structure for the upcoming year.

**Current Situation:**
- **Plan:** Enterprise Plan - 100 users
- **Current Pricing:** $5,000/month
- **Usage:** Average 65 active users per month (35% below our licensed capacity)
- **Payment History:** Perfect record with no late payments over 3 years

**Discussion Points:**
Given our consistent partnership and actual usage patterns, we would like to explore a pricing adjustment that better aligns with our utilization. Based on our analysis and current market rates, we believe a monthly rate of $3,500 would be fair for both parties moving forward.

We have received competitive offers in the $3,200-$3,800 range for similar service levels, but we strongly prefer to continue our relationship with CloudServices Inc. given the excellent service and integration we've established.

**Next Steps:**
I would appreciate the opportunity to discuss this proposal with you. Would you be available for a brief call next week to explore how we can structure a renewal that works well for both organizations?

I look forward to your response and to continuing our successful partnership.

Best regards,
AI Assistant
Automation System
Company Name
support@company.com
```

---

## Pattern 5: Batch Email Generation

**Use Case:** Generate multiple email drafts in a single workflow

**Code Example:**

```javascript
async function batchGenerateEmailDrafts(emailRequests) {
  const results = [];

  for (const request of emailRequests) {
    try {
      const draft = await draftEmail(request);

      if (draft.success) {
        results.push({
          status: 'success',
          draft_id: draft.draft_id,
          recipient: request.recipient.email,
          file_path: draft.file_path
        });
        console.log(`✅ Draft created for ${request.recipient.email}`);
      } else {
        results.push({
          status: 'failed',
          recipient: request.recipient.email,
          error: draft.error
        });
        console.error(`❌ Failed to create draft for ${request.recipient.email}: ${draft.error}`);
      }
    } catch (error) {
      results.push({
        status: 'error',
        recipient: request.recipient.email,
        error: error.message
      });
      console.error(`❌ Error creating draft for ${request.recipient.email}:`, error);
    }
  }

  // Summary
  const successful = results.filter(r => r.status === 'success').length;
  const failed = results.filter(r => r.status !== 'success').length;

  console.log(`\n📊 Batch Email Draft Summary:`);
  console.log(`   ✅ Successful: ${successful}`);
  console.log(`   ❌ Failed: ${failed}`);
  console.log(`   📧 Total: ${results.length}`);

  return results;
}

// Usage: Generate customer onboarding emails for new signups
const newCustomers = [
  { name: "Alice Brown", email: "alice@startup.com", plan: "Pro" },
  { name: "Bob Smith", email: "bob@enterprise.com", plan: "Enterprise" },
  { name: "Carol White", email: "carol@agency.com", plan: "Team" }
];

const emailRequests = newCustomers.map(customer => ({
  intent: "customer_onboarding",
  recipient: {
    name: customer.name,
    email: customer.email,
    type: "customer",
    plan: customer.plan
  },
  context: {
    signup_date: new Date().toISOString(),
    plan: customer.plan,
    trial_days: 14
  },
  tone: "friendly",
  key_points: [
    "Welcome new customer",
    "Explain next steps to get started",
    "Highlight key features for their plan",
    "Offer onboarding call",
    "Provide support contact"
  ],
  metadata: {
    agent: "lex",
    session_id: process.env.EMAIL_SESSION_ID,
    timestamp: new Date().toISOString()
  }
}));

const results = await batchGenerateEmailDrafts(emailRequests);
```

**Output:**
```
✅ Draft created for alice@startup.com
✅ Draft created for bob@enterprise.com
✅ Draft created for carol@agency.com

📊 Batch Email Draft Summary:
   ✅ Successful: 3
   ❌ Failed: 0
   📧 Total: 3
```

---

## Best Practices

### 1. Always Provide Sufficient Context

```javascript
// ❌ BAD - insufficient context
context: {
  original_message: "Can you help?"
}

// ✅ GOOD - comprehensive context
context: {
  original_subject: "Need help with API integration",
  original_message: "Can you help? I'm getting 401 errors when calling the /users endpoint.",
  customer_plan: "Enterprise",
  customer_since: "2024-01-15",
  previous_tickets: 2,
  ticket_id: "TICKET-67890",
  error_code: "401_UNAUTHORIZED",
  api_endpoint: "/api/v2/users"
}
```

### 2. Choose Appropriate Tone for Recipient

```javascript
// Customer emails: friendly
tone: "friendly"

// Executive/legal emails: formal
tone: "formal"

// Team communications: semi-formal
tone: "semi-formal"
```

### 3. Include Actionable Key Points

```javascript
// ❌ BAD - vague key points
key_points: [
  "Respond to customer",
  "Be helpful"
]

// ✅ GOOD - specific, actionable points
key_points: [
  "Acknowledge the 401 authentication error",
  "Explain API key renewal process",
  "Provide step-by-step instructions to regenerate key",
  "Include link to API documentation",
  "Offer to schedule technical onboarding call"
]
```

### 4. Structure Complex Information

```javascript
// For emails with multiple sections or data
context: {
  sections: {
    summary: "High-level overview",
    details: {
      technical: "Technical specifics",
      business: "Business implications"
    },
    action_items: ["Item 1", "Item 2"],
    timeline: "Expected completion dates"
  }
}
```

### 5. Handle Sensitive Communications Carefully

```javascript
// For rejections, complaints, or sensitive topics
const draft = await draftEmail({
  intent: "escalation_response",
  tone: "formal",
  key_points: [
    "Acknowledge customer frustration with empathy",
    "Take ownership without making excuses",
    "Explain concrete steps to resolve",
    "Offer compensation/remedy",
    "Provide direct escalation contact"
  ],
  metadata: {
    requires_review: true,  // Flag for human review
    sensitivity: "high"
  }
});
```

---

## Integration with Other Skills

### With company_handbook_enforcer:

```javascript
// Check email draft against communication policies
const { checkPolicyCompliance } = require('../compliance/company_handbook_enforcer');

async function createCompliantEmailDraft(emailDetails) {
  // Create initial draft
  const draft = await draftEmail(emailDetails);

  if (!draft.success) {
    return draft;
  }

  // Validate against policies
  const compliance = await checkPolicyCompliance({
    type: "email_communication",
    content: draft.email_body,
    recipient_type: emailDetails.recipient.type
  });

  if (compliance.violations.length > 0) {
    console.warn(`⚠️ Policy violations detected:`);
    compliance.violations.forEach(v => {
      console.warn(`   - ${v.policy}: ${v.reasoning}`);
    });

    // Flag draft for review
    draft.requires_review = true;
    draft.compliance_issues = compliance.violations;
  }

  return draft;
}
```

### With approval_request_creator:

```javascript
// Require approval for sensitive external communications
async function createEmailWithApproval(emailDetails) {
  const draft = await draftEmail(emailDetails);

  if (emailDetails.recipient.type === "external_stakeholder" ||
      emailDetails.intent === "vendor_negotiation") {

    // Create approval request
    const { createApprovalRequest } = require('../approval/approval_request_creator');

    const approval = await createApprovalRequest({
      action: {
        type: "email",
        description: `Send email to ${emailDetails.recipient.email}`,
        details: {
          recipient: emailDetails.recipient.email,
          subject: draft.subject,
          body_preview: draft.email_body.substring(0, 200) + "..."
        }
      },
      justification: {
        business_reason: emailDetails.context.business_reason || "External communication"
      },
      approval: {
        required_approver: "Manager",
        approver_email: "manager@company.com",
        sla_hours: 24
      }
    });

    console.log(`📋 Approval required: ${approval.request_id}`);
    draft.approval_required = true;
    draft.approval_request_id = approval.request_id;
  }

  return draft;
}
```

---

## Error Recovery Patterns

### Retry Logic for Failed Drafts:

```javascript
async function draftEmailWithRetry(emailDetails, maxRetries = 3) {
  let lastError;

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      console.log(`📧 Attempt ${attempt}/${maxRetries} to create draft...`);

      const draft = await draftEmail(emailDetails);

      if (draft.success) {
        console.log(`✅ Draft created successfully on attempt ${attempt}`);
        return draft;
      }

      lastError = draft.error;
      console.warn(`⚠️ Attempt ${attempt} failed: ${draft.error}`);

      // Wait before retry (exponential backoff)
      if (attempt < maxRetries) {
        const waitTime = Math.pow(2, attempt) * 1000;
        await new Promise(resolve => setTimeout(resolve, waitTime));
      }
    } catch (error) {
      lastError = error.message;
      console.error(`❌ Attempt ${attempt} threw error:`, error);
    }
  }

  console.error(`❌ All ${maxRetries} attempts failed. Last error: ${lastError}`);
  return { success: false, error: lastError };
}
```

---

## Performance Optimization

### Parallel Draft Generation:

```javascript
async function generateMultipleDraftsParallel(emailRequests) {
  console.log(`📧 Generating ${emailRequests.length} drafts in parallel...`);

  const startTime = Date.now();

  // Generate all drafts in parallel
  const draftPromises = emailRequests.map(request =>
    draftEmail(request).catch(error => ({
      success: false,
      error: error.message,
      recipient: request.recipient.email
    }))
  );

  const results = await Promise.all(draftPromises);

  const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
  const successful = results.filter(r => r.success).length;

  console.log(`✅ Generated ${successful}/${results.length} drafts in ${elapsed}s`);
  console.log(`   Average: ${(elapsed / results.length).toFixed(2)}s per draft`);

  return results;
}
```
