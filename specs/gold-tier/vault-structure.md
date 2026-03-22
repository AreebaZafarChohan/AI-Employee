# Gold Tier Vault Folder Structure

This document defines the complete folder structure for the Gold Tier AI-Employee-Vault.

## Complete Folder Tree

```
AI-Employee-Vault/
├── .obsidian/                          # Obsidian configuration
│   ├── app.json
│   ├── core-plugins.json
│   └── workspace.json
│
├── Inbox/                              # New items land here (auto-processed)
│   ├── README.md                       # Instructions for dropping files
│   └── .gitkeep
│
├── Needs_Action/                       # Items requiring AI processing
│   ├── README.md                       # Triage instructions
│   └── .gitkeep
│
├── Pending_Approval/                   # Items awaiting human approval
│   ├── README.md                       # Approval process guide
│   └── .gitkeep
│
├── Approved/                           # Approved items ready for execution
│   ├── README.md                       # Execution queue info
│   └── .gitkeep
│
├── Plans/                              # Generated action plans
│   ├── active/                         # Currently executing plans
│   ├── completed/                      # Executed plans (archived)
│   └── .gitkeep
│
├── Done/                               # Completed items (archived)
│   ├── Emails/                         # Processed emails
│   ├── WhatsApp/                       # Processed WhatsApp messages
│   ├── Social/                         # Published social posts
│   ├── Accounting/                     # Processed accounting items
│   ├── Personal/                       # Personal tasks completed
│   ├── Business/                       # Business tasks completed
│   └── .gitkeep
│
├── Quarantine/                         # Failed items requiring review
│   ├── README.md                       # Quarantine explanation
│   ├── network_errors/                 # Network-related failures
│   ├── auth_errors/                    # Authentication failures
│   ├── validation_errors/              # Validation failures
│   └── .gitkeep
│
├── Rejected/                           # Human-rejected items
│   ├── README.md                       # Rejection process
│   └── .gitkeep
│
├── Audit/                              # Immutable audit logs
│   ├── 2026/
│   │   ├── 03/
│   │   │   ├── audit-2026-03-06.json
│   │   │   ├── audit-2026-03-07.json
│   │   │   └── ...
│   │   └── ...
│   └── README.md                       # Audit log guide
│
├── Logs/                               # Operational logs (rotated daily)
│   ├── gmail-watcher-2026-03-06.log
│   ├── whatsapp-watcher-2026-03-06.log
│   ├── social-watcher-2026-03-06.log
│   ├── approval-orchestrator-2026-03-06.log
│   ├── ralph-wiggum-loop-2026-03-06.log
│   ├── audit-logger-2026-03-06.log
│   └── ...
│
├── Reports/                            # Generated reports
│   ├── Daily/
│   │   ├── 2026-03-06.md
│   │   └── ...
│   ├── Weekly/
│   │   ├── 2026-W10.md
│   │   └── ...
│   ├── Monthly/
│   │   ├── 2026-03.md
│   │   └── ...
│   └── Annual/
│       ├── 2026.md
│       └── ...
│
├── Briefings/                          # CEO Briefings
│   ├── 2026-03-10_Monday.md
│   ├── 2026-03-17_Monday.md
│   └── ...
│
├── Accounting/                         # Odoo accounting integration
│   ├── Invoices/
│   │   ├── unpaid/                     # Unpaid invoices tracking
│   │   ├── paid/                       # Paid invoices archive
│   │   └── overdue/                    # Overdue invoices alerts
│   ├── Payments/
│   │   ├── received/                   # Payments received
│   │   ├── sent/                       # Payments made
│   │   └── pending/                    # Pending payments
│   ├── Customers/
│   │   ├── balances/                   # Customer balance reports
│   │   └── statements/                 # Customer statements
│   ├── Vendors/
│   │   ├── balances/                   # Vendor balance reports
│   │   └── statements/                 # Vendor statements
│   ├── Journals/
│   │   └── entries/                    # Journal entries
│   ├── Reports/
│   │   ├── profit-loss/                # P&L reports
│   │   ├── balance-sheet/              # Balance sheet reports
│   │   └── cash-flow/                  # Cash flow reports
│   └── README.md                       # Accounting integration guide
│
├── Social/                             # Social media management
│   ├── Templates/
│   │   ├── linkedin-post-template.md
│   │   ├── facebook-post-template.md
│   │   ├── instagram-post-template.md
│   │   ├── twitter-tweet-template.md
│   │   └── content-calendar-template.md
│   ├── Drafts/
│   │   ├── linkedin/
│   │   ├── facebook/
│   │   ├── instagram/
│   │   └── twitter/
│   ├── Scheduled/
│   │   ├── linkedin/
│   │   ├── facebook/
│   │   ├── instagram/
│   │   └── twitter/
│   ├── Published/
│   │   ├── linkedin/
│   │   ├── facebook/
│   │   ├── instagram/
│   │   └── twitter/
│   ├── Analytics/
│   │   ├── linkedin-analytics.md
│   │   ├── facebook-insights.md
│   │   ├── instagram-insights.md
│   │   └── twitter-analytics.md
│   └── README.md                       # Social media guide
│
├── Updates/                            # Status updates and notifications
│   ├── System/                         # System status updates
│   ├── Personal/                       # Personal life updates
│   ├── Business/                       # Business updates
│   └── .gitkeep
│
├── Knowledge/                          # Company knowledge base
│   ├── Company_Handbook.md             # Master company handbook
│   ├── Policies/
│   │   ├── email-policy.md
│   │   ├── social-media-policy.md
│   │   ├── expense-policy.md
│   │   └── ...
│   ├── Procedures/
│   │   ├── invoice-processing.md
│   │   ├── customer-onboarding.md
│   │   ├── social-media-posting.md
│   │   └── ...
│   ├── Templates/
│   │   ├── email-templates/
│   │   ├── document-templates/
│   │   └── ...
│   └── .gitkeep
│
├── Personal/                           # Personal domain items
│   ├── Tasks/
│   │   ├── active/
│   │   ├── completed/
│   │   └── someday/
│   ├── Calendar/
│   │   └── events/
│   ├── Health/
│   │   ├── appointments/
│   │   └── tracking/
│   ├── Finance/
│   │   ├── bills/
│   │   ├── investments/
│   │   └── taxes/
│   └── README.md
│
├── Business/                           # Business domain items
│   ├── Clients/
│   │   ├── active/
│   │   ├── prospects/
│   │   └── archive/
│   ├── Projects/
│   │   ├── active/
│   │   ├── completed/
│   │   └── backlog/
│   ├── Operations/
│   │   ├── hr/
│   │   ├── finance/
│   │   └── admin/
│   └── README.md
│
├── .processed_files.json               # Ledger: processed inbox files
├── .gmail_processed.json               # Ledger: processed Gmail messages
├── .whatsapp_processed.json            # Ledger: processed WhatsApp messages
├── .social_processed.json              # Ledger: processed social items
├── .ralph_loop_state.json              # Ralph Wiggum loop state
├── Dashboard.md                        # Main dashboard (auto-updated)
├── Welcome.md                          # Getting started guide
└── README.md                           # Vault documentation
```

## Folder Purpose Reference

| Folder | Purpose | Auto-Created | Retention |
|--------|---------|--------------|-----------|
| `Inbox/` | Drop zone for new items | Yes | Processed immediately |
| `Needs_Action/` | AI triage queue | Yes | Until processed |
| `Pending_Approval/` | Human approval queue | Yes | Until approved/rejected |
| `Approved/` | Execution queue | Yes | Until executed |
| `Plans/` | Action plans | Yes | 90 days |
| `Done/` | Completed items | Yes | 365 days |
| `Quarantine/` | Failed items | Yes | Until reviewed |
| `Rejected/` | Human-rejected items | Yes | 90 days |
| `Audit/` | Immutable logs | Yes | 365 days |
| `Logs/` | Operational logs | Yes | 30 days |
| `Reports/` | Generated reports | Yes | 365 days |
| `Briefings/` | CEO briefings | Yes | 365 days |
| `Accounting/` | Odoo integration | Yes | 7 years |
| `Social/` | Social media | Yes | 365 days |
| `Updates/` | Notifications | Yes | 90 days |
| `Knowledge/` | Company KB | No | Permanent |
| `Personal/` | Personal domain | No | User-defined |
| `Business/` | Business domain | No | User-defined |

## File Naming Conventions

### General Files
```
{type}-{description}-{date}.{ext}
Examples:
- plan-email-response-2026-03-06.md
- approval-social-post-2026-03-06.md
- report-weekly-2026-W10.md
```

### Audit Logs
```
audit-YYYY-MM-DD.json
Examples:
- audit-2026-03-06.json
```

### Operational Logs
```
{component}-YYYY-MM-DD.log
Examples:
- gmail-watcher-2026-03-06.log
- ralph-wiggum-loop-2026-03-06.log
```

### Reports
```
Daily:   YYYY-MM-DD.md          (2026-03-06.md)
Weekly:  YYYY-Www.md            (2026-W10.md)
Monthly: YYYY-MM.md             (2026-03.md)
Annual:  YYYY.md                (2026.md)
```

### Briefings
```
YYYY-MM-DD_DayName.md
Examples:
- 2026-03-10_Monday.md
- 2026-03-17_Monday.md
```

### Social Media Posts
```
{platform}-draft-{date}-{id}.md
{platform}-scheduled-{date}-{id}.md
{platform}-published-{date}-{id}.md
Examples:
- linkedin-draft-2026-03-06-001.md
- twitter-scheduled-2026-03-10-001.md
```

### Accounting Files
```
Invoice: INV-{number}-{date}.md
Payment: PAY-{number}-{date}.md
Report:  {type}-{period}.md
Examples:
- INV-2026-001-2026-03-06.md
- PAY-2026-045-2026-03-06.md
- profit-loss-2026-03.md
```

## Metadata Sidecar Files

For each processed file, a metadata sidecar is created:

```
{filename}.meta.md
```

Example sidecar:
```markdown
---
type: email
source: gmail
original_name: client-inquiry.md
created_at: "2026-03-06T10:30:00Z"
processed_at: "2026-03-06T10:31:00Z"
status: completed
domain: business
risk_level: low
requires_approval: false
correlation_id: "uuid-v4"
---
```

## Ledger Files

Ledger files track processed items to prevent duplicates:

### .processed_files.json
```json
[
  "client-inquiry-2026-03-06.md",
  "meeting-request-2026-03-06.md"
]
```

### .gmail_processed.json
```json
{
  "message_ids": ["18e5f1a2b3c4d5e6", ...],
  "last_sync": "2026-03-06T10:30:00Z"
}
```

### .ralph_loop_state.json
```json
{
  "last_cycle": "2026-03-06T10:30:00Z",
  "cycle_count": 1234,
  "pending_tasks": 5,
  "active_plans": 3,
  "errors_last_hour": 0
}
```

## Dashboard Integration

The `Dashboard.md` file is auto-updated by the system:

```markdown
# AI Employee Dashboard

**Last Updated:** 2026-03-06 10:30:00 UTC

## Quick Stats
| Metric | Value |
|--------|-------|
| Inbox Items | 0 |
| Needs Action | 3 |
| Pending Approval | 1 |
| Active Plans | 2 |
| Completed Today | 15 |

## System Status
- Gmail Watcher: ✅ Running
- WhatsApp Watcher: ✅ Running
- Social Watcher: ✅ Running
- Ralph Wiggum Loop: ✅ Running
- Approval Orchestrator: ✅ Running

## Recent Activity
- 10:30 - Email processed: client-inquiry.md
- 10:25 - WhatsApp message replied
- 10:20 - Social post published: LinkedIn

## Pending Approvals
- [Review] Social post for product launch

## Today's Schedule
- 14:00 - Team meeting
- 16:00 - Client call
```

## Vault End
