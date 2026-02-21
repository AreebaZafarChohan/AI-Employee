# Email Drafter - Real-World Examples

This document provides complete, copy-paste-ready examples for common business email scenarios.

---

## Example 1: Customer Complaint Response

**Scenario:** Customer received damaged product, wants refund.

**Input:**
```javascript
const { draftEmail } = require('./email_drafter');

await draftEmail({
  intent: "escalation_response",
  recipient: {
    name: "Robert Martinez",
    email: "robert@example.com",
    type: "customer",
    account_id: "cust_98765",
    plan: "Pro"
  },
  context: {
    original_subject: "Damaged product received - requesting immediate refund",
    original_message: "I received my order yesterday and the item was damaged. The box was clearly dropped during shipping. This is unacceptable. I want a full refund immediately.",
    order_id: "ORD-2025-001234",
    order_date: "2025-01-28",
    order_amount: "$149.99",
    shipping_carrier: "FedEx",
    issue_type: "damaged_product",
    ticket_id: "TICKET-COMPLAINT-567",
    compensation_offered: "Full refund + $25 store credit"
  },
  tone: "formal",
  key_points: [
    "Sincerely apologize for inconvenience",
    "Take ownership - don't blame shipping carrier",
    "Explain immediate resolution steps",
    "Offer full refund plus store credit",
    "Provide direct contact for urgent follow-up",
    "Ensure customer feels valued"
  ],
  metadata: {
    agent: "lex",
    session_id: "session_complaint_567",
    timestamp: new Date().toISOString()
  }
});
```

**Generated Email:**
```markdown
---
draft_id: DRAFT-20250204-153022-XYZ789
created_at: 2025-02-04T15:30:22Z
status: draft
email_type: escalation_response
priority: high
recipient: robert@example.com
tone: formal
requires_review: false
---

# Email Draft: Escalation Response - Damaged Product

**Draft ID:** DRAFT-20250204-153022-XYZ789
**Created:** 2025-02-04 15:30:22 UTC
**Status:** 📝 Draft
**Recipient:** Robert Martinez <robert@example.com>

---

## Email Details

**To:** robert@example.com
**Subject:** Re: Damaged product received - requesting immediate refund
**Priority:** High

---

## Email Body

Dear Mr. Martinez,

I sincerely apologize for the condition in which you received your order (ORD-2025-001234). This is absolutely not the experience we want any customer to have, and I take full responsibility for ensuring this is resolved immediately.

**What Happened:**
Your order was damaged during transit, and I understand how frustrating this must be, especially after looking forward to your purchase.

**Immediate Resolution:**

I have processed the following for you right away:

1. **Full refund of $149.99** - Processed to your original payment method (arrives within 3-5 business days)
2. **$25 store credit** - Applied to your account as a sincere apology for the inconvenience
3. **Prepaid return label** - Emailed separately for the damaged item (no cost to you)

You do NOT need to wait for the return to be received for your refund to process - it has already been initiated.

**Ticket Reference:** TICKET-COMPLAINT-567

**Direct Contact:**
If you have any concerns or need immediate assistance, please don't hesitate to reach out to me directly at this email address or call our priority support line at 1-800-XXX-XXXX (reference ticket #567 for expedited service).

We truly value your business and hope this resolution demonstrates our commitment to making things right. If there's anything else I can do, please let me know.

Sincerely,

AI Assistant
Automation System
Company Name
support@company.com

---

## Alternative Subject Lines

1. Re: Damaged product received - requesting immediate refund (Primary)
2. Your Order #2025-001234 - Immediate Resolution Processed
3. Apology and Full Refund - Order ORD-2025-001234

---

## Follow-Up Actions

- [ ] Send email immediately (within 1 hour of complaint)
- [ ] Verify refund is processed in payment system
- [ ] Email prepaid return label separately
- [ ] Apply $25 store credit to account
- [ ] Follow up in 5 days to confirm refund received
- [ ] Flag account for VIP treatment on future orders
- [ ] Update ticket TICKET-COMPLAINT-567 status to "resolved"

---

## Tone Analysis

**Selected Tone:** Formal
**Characteristics:**
- Sincere and professional apology
- Takes full ownership without excuses
- Clear, specific action items
- Emphasizes customer value
- Provides direct escalation contact
- Avoids defensive language

---

## Content Checklist

- [x] Addressed customer by name with proper title
- [x] Acknowledged frustration with empathy
- [x] Took ownership without blaming carrier
- [x] Provided specific resolution (refund + credit)
- [x] Explained process and timeline clearly
- [x] Offered direct escalation contact
- [x] Expressed appreciation for business
- [x] Professional signature with contact info

---

## Risk Assessment

**Complaint Severity:** High
**Customer Satisfaction Risk:** Critical
**Churn Risk:** High without proper resolution
**Recommended Action:** Immediate response with overcompensation

---

## Metadata

- **Agent:** lex (Local Executive Agent)
- **Session ID:** session_complaint_567
- **Order ID:** ORD-2025-001234
- **Ticket ID:** TICKET-COMPLAINT-567
- **Issue Type:** damaged_product
- **Resolution:** Full refund + $25 credit
- **Customer Plan:** Pro
- **Account ID:** cust_98765
```

---

## Example 2: Partnership Proposal Email

**Scenario:** Reaching out to potential partner for collaboration.

**Input:**
```javascript
await draftEmail({
  intent: "introduction",
  recipient: {
    name: "Jennifer Wu",
    email: "jwu@techstartup.com",
    type: "external_stakeholder",
    company: "TechStartup Inc.",
    role: "VP of Partnerships"
  },
  context: {
    partnership_type: "technology_integration",
    mutual_benefit: "Our API + Their platform = Enhanced user experience",
    research_notes: "Their company serves 50K users, growing 20% MoM",
    common_customers: ["Acme Corp", "Beta Industries"],
    referral_source: "Met at TechConf 2025"
  },
  tone: "formal",
  key_points: [
    "Reference TechConf meeting briefly",
    "Explain mutual value proposition clearly",
    "Highlight alignment with their growth trajectory",
    "Propose exploratory call (low commitment)",
    "Mention common customers as social proof",
    "Professional but warm closing"
  ],
  metadata: {
    agent: "lex",
    session_id: "session_partnership_789"
  }
});
```

**Generated Email:**
```markdown
Subject: Partnership Opportunity Following TechConf 2025

Dear Jennifer,

It was a pleasure meeting you at TechConf 2025 last week. Our brief conversation about your platform's impressive growth trajectory stayed with me, and I wanted to reach out to explore a potential partnership opportunity.

**The Opportunity:**

We've developed an API that seamlessly integrates with platforms like yours to enhance user analytics capabilities. Given your focus on serving mid-market SaaS companies (a segment we know well through shared customers like Acme Corp and Beta Industries), I believe there's strong mutual value here:

**For TechStartup:**
- Enhanced analytics features for your 50K+ users without internal development lift
- Differentiation from competitors in your space
- Additional revenue stream through our revenue-share model

**For Us:**
- Access to your growing user base (20% MoM growth is impressive!)
- Partnership with a company that shares our target market
- Opportunity to co-market to our combined customer bases

**Next Step:**

I'd love to schedule a 30-minute exploratory call to share more details and hear your thoughts. No commitment required - just an opportunity to see if there's a fit worth pursuing.

Are you available for a quick call during the week of February 10-14? I'm happy to work around your schedule.

Looking forward to continuing our conversation.

Best regards,

AI Assistant
Automation System
Company Name
partnerships@company.com

---

## Follow-Up Actions

- [ ] Send within 3-5 days of TechConf (while memory is fresh)
- [ ] Research recipient's LinkedIn for additional personalization
- [ ] Prepare partnership deck if call is scheduled
- [ ] Set calendar reminder to follow up if no response in 7 days
- [ ] Notify partnerships team of outreach
```

---

## Example 3: Internal Incident Report Follow-Up

**Scenario:** Following up after production outage with postmortem.

**Input:**
```javascript
await draftEmail({
  intent: "follow_up",
  recipient: {
    name: "Engineering Team",
    email: "engineering@company.com",
    type: "internal_team",
    cc: ["cto@company.com", "sre-team@company.com"]
  },
  context: {
    incident_id: "INC-2025-0204-001",
    incident_date: "2025-02-04T03:00:00Z",
    incident_duration: "2 hours 15 minutes",
    affected_services: ["API", "Dashboard", "Mobile App"],
    root_cause: "Database connection pool exhaustion",
    resolution: "Increased connection pool size + added monitoring",
    customers_affected: 1234,
    postmortem_link: "https://docs.company.com/postmortem/INC-2025-0204-001",
    action_items: [
      { task: "Implement connection pool monitoring", owner: "SRE Team", due: "2025-02-10" },
      { task: "Add load testing to CI/CD pipeline", owner: "Platform Team", due: "2025-02-15" },
      { task: "Document incident response improvements", owner: "CTO", due: "2025-02-08" }
    ]
  },
  tone: "semi-formal",
  key_points: [
    "Acknowledge incident impact professionally",
    "Explain root cause clearly (no jargon for non-technical stakeholders in CC)",
    "Detail resolution steps taken",
    "List action items with owners and due dates",
    "Link to full postmortem",
    "Thank team for rapid response",
    "Emphasize continuous improvement mindset"
  ]
});
```

**Generated Email:**
```markdown
Subject: Incident Follow-Up: INC-2025-0204-001 - Postmortem & Action Items

Hi Team,

Thank you all for your quick response during this morning's incident (INC-2025-0204-001). I wanted to share the postmortem findings and next steps.

**Incident Summary:**

- **Occurred:** Feb 4, 2025 at 3:00 AM UTC
- **Duration:** 2 hours 15 minutes
- **Affected Services:** API, Dashboard, Mobile App
- **Customers Impacted:** 1,234 users (approx. 12% of active users)
- **Severity:** SEV-2 (High)

**Root Cause:**

Our database connection pool reached maximum capacity due to a combination of:
1. Higher than normal morning traffic (20% above baseline)
2. Connection pool size set at previous capacity levels
3. A slow query that held connections longer than expected

**Resolution:**

Our SRE team resolved the issue by:
1. Increasing database connection pool size from 100 to 200
2. Identifying and optimizing the slow query
3. Adding real-time connection pool utilization monitoring

Service was fully restored by 5:15 AM UTC.

**Action Items:**

| Task | Owner | Due Date |
|------|-------|----------|
| Implement connection pool monitoring with alerts | SRE Team | Feb 10, 2025 |
| Add load testing to CI/CD pipeline | Platform Team | Feb 15, 2025 |
| Document incident response improvements | CTO | Feb 8, 2025 |

**Full Postmortem:** [Read Here](https://docs.company.com/postmortem/INC-2025-0204-001)

**What Went Well:**
- Incident detected within 2 minutes (alerting worked)
- All hands on deck response from SRE team
- Customer communication sent within 10 minutes
- Root cause identified quickly

**What We're Improving:**
- Proactive monitoring of connection pool saturation
- Better load testing coverage before peak hours
- Automated scaling triggers for database resources

Thanks again for the professionalism and teamwork during this incident. Let's use this as a learning opportunity to strengthen our systems.

Questions or concerns? Reply here or ping me on Slack.

Best,
AI Assistant

---

Attachments:
- [Full Postmortem](https://docs.company.com/postmortem/INC-2025-0204-001)
- [Connection Pool Monitoring Dashboard](https://metrics.company.com/db-pool)
```

---

## Example 4: Quarterly Business Review Invitation

**Scenario:** Inviting enterprise customer to quarterly review.

**Input:**
```javascript
await draftEmail({
  intent: "meeting_request",
  recipient: {
    name: "David Park",
    email: "david.park@enterprise.com",
    type: "customer",
    company: "Enterprise Corp",
    plan: "Enterprise",
    account_value: "$50,000/year"
  },
  context: {
    meeting_purpose: "Q4 2024 Business Review",
    last_qbr_date: "2024-10-15",
    relationship_duration: "2 years",
    account_health: "green",
    key_metrics_to_discuss: [
      "Platform adoption: 85% of licensed users active",
      "Support tickets reduced by 40% YoY",
      "Cost savings: $120K in operational efficiency"
    ],
    proposed_dates: [
      "2025-02-18T15:00:00Z",
      "2025-02-20T14:00:00Z",
      "2025-02-22T16:00:00Z"
    ],
    agenda_items: [
      "Review Q4 2024 usage and outcomes",
      "Discuss upcoming feature releases (Q1 2025)",
      "Explore expansion opportunities",
      "Address any feedback or concerns"
    ]
  },
  tone: "semi-formal",
  key_points: [
    "Reference previous QBR to show continuity",
    "Highlight positive metrics to celebrate success",
    "Frame as partnership check-in, not sales pitch",
    "Propose multiple time slots (respect their schedule)",
    "Include clear agenda so they can prepare",
    "Emphasize two-way conversation"
  ]
});
```

**Generated Email:**
```markdown
Subject: Let's Schedule Your Q4 2024 Business Review

Hi David,

I hope you're doing well! As we move into 2025, I'd like to schedule our quarterly business review to reflect on Q4 2024 results and discuss what's ahead.

**A Quick Look Back:**

Since our last QBR in October, we've seen some impressive results from your team's use of our platform:
- **Platform adoption:** 85% of your licensed users are actively engaged
- **Support efficiency:** 40% reduction in support tickets year-over-year
- **Operational impact:** Estimated $120K in operational cost savings

**Meeting Purpose:**

This QBR is an opportunity to:
1. Review Q4 2024 usage metrics and business outcomes
2. Preview exciting features launching in Q1 2025
3. Explore potential expansion opportunities (if aligned with your goals)
4. Hear your feedback and address any concerns

**Proposed Times (all in UTC):**
- February 18, 2025 at 3:00 PM
- February 20, 2025 at 2:00 PM
- February 22, 2025 at 4:00 PM

**Duration:** 45-60 minutes (video call)

**Who Should Attend:**
- Your side: Yourself + any relevant team members
- Our side: Account team + product specialist

Could you let me know which time works best, or suggest alternative times if none of these fit your calendar? I'm happy to be flexible.

Looking forward to celebrating your team's success and planning for an even better Q1!

Best regards,
AI Assistant

---

## Follow-Up Actions

- [ ] Send 2 weeks before desired meeting date
- [ ] Prepare QBR deck with customer-specific metrics
- [ ] Send calendar invite once time is confirmed
- [ ] Share pre-read materials 3 days before meeting
- [ ] Follow up if no response within 5 business days
```

---

## Example 5: Vendor Price Increase Pushback

**Scenario:** Negotiating with vendor who proposed 30% price increase.

**Input:**
```javascript
await draftEmail({
  intent: "negotiation",
  recipient: {
    name: "Christine Lee",
    email: "christine@cloudprovider.com",
    type: "vendor",
    company: "CloudProvider Inc.",
    role: "Account Executive"
  },
  context: {
    current_contract: "Enterprise Plan - $10,000/month",
    proposed_increase: "$13,000/month (+30%)",
    renewal_date: "2025-03-31",
    relationship_duration: "4 years",
    payment_history: "Perfect, always on time",
    usage_stats: "Using 70% of allocated resources",
    market_research: "Competitor A: $9,500/month for similar features",
    negotiation_position: "Strong - multiple alternatives available",
    target_price: "$10,500/month (+5%)",
    acceptable_range: "$10,000-$11,000/month"
  },
  tone: "formal",
  key_points: [
    "Express appreciation for partnership",
    "Acknowledge their business needs (don't dismiss increase entirely)",
    "Present data showing under-utilization",
    "Reference competitive pricing (tactfully)",
    "Make specific counter-offer",
    "Emphasize long-term relationship value",
    "Propose call to discuss, not ultimatum"
  ]
});
```

**Generated Email:**
```markdown
Subject: Re: Contract Renewal Proposal - Let's Discuss

Dear Christine,

Thank you for sending over the renewal proposal for our Enterprise Plan. We've valued our partnership with CloudProvider Inc. over the past four years, and I wanted to reach out to discuss the pricing before our March 31 renewal date.

**Our Perspective:**

While we understand the need for occasional price adjustments to reflect increased value and operational costs, the proposed 30% increase to $13,000/month represents a significant jump that's challenging for us to justify internally given our current usage patterns.

**Current Situation:**
- We're utilizing approximately 70% of our allocated resources
- Our needs have remained relatively stable over the past year
- We have a perfect payment history over 4 years of partnership

**Market Context:**

In preparing for this renewal, we've reviewed alternatives in the market. Comparable offerings are available in the $9,500-$10,500 range for our usage profile. While we strongly prefer to continue with CloudProvider given our integration and relationship, we need pricing that reflects market rates and our actual utilization.

**Our Proposal:**

We'd like to propose a renewal at $10,500/month (+5% increase), which:
- Recognizes the value CloudProvider provides
- Reflects a fair adjustment for inflation and improvements
- Aligns with our actual resource utilization
- Keeps us within budget while maintaining our partnership

**Next Steps:**

I believe there's a path forward that works for both organizations. Would you be available for a call next week to discuss this? I'm confident we can find a mutually beneficial solution.

Looking forward to your thoughts.

Best regards,

AI Assistant
Procurement Team
Company Name
procurement@company.com

---

P.S. Our CFO has asked me to have clarity on pricing by February 15 to finalize our Q1 budget, so I appreciate your timely response.

---

## Negotiation Strategy

**Our Position:** Strong (multiple alternatives, under-utilizing current plan)
**Their Position:** Moderate (we're a long-term customer, good payment history)
**Target Outcome:** $10,500/month
**Walk-Away Point:** $11,000/month
**Timeline Pressure:** Renewal date March 31, budget deadline Feb 15

**Tactics:**
- Lead with partnership appreciation (not confrontational)
- Use data to justify position (70% utilization)
- Reference market without threatening to leave
- Make first offer close to target ($10,500)
- Emphasize mutual benefit and long-term relationship
- Create soft deadline pressure (Feb 15 budget)

**If They Counter:**
- $12,000+: Push back, emphasize alternatives, request meeting
- $11,500: Counter at $11,000, likely acceptable
- $11,000: Accept if includes added value (more resources, better SLA)
- $10,500: Accept immediately
```

---

## Using These Examples

All examples above are production-ready and can be adapted by:

1. **Replacing placeholder details** with your actual data
2. **Adjusting tone** if recipient relationship is different
3. **Modifying key_points** to match your specific situation
4. **Adding/removing context** fields as needed

Each example demonstrates best practices:
- ✅ Comprehensive context
- ✅ Appropriate tone for recipient
- ✅ Specific, actionable key points
- ✅ Professional structure
- ✅ Clear next steps

Copy, customize, and use with confidence!
