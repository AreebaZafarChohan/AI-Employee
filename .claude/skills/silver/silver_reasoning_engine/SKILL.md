# Silver Reasoning Engine Skill

## Overview

**Skill Name:** `silver_reasoning_engine`
**Domain:** `silver`
**Version:** 1.0.0
**Purpose:** Deep-reason over every item in `/Needs_Action`: summarize, identify objective, assign domain, compute risk and confidence scores, generate a structured Plan in `/Plans`, and route high/medium risk items to `/Pending_Approval`. Never executes any external action.

**Core Capabilities:**
- Full-text summarization of each `/Needs_Action` item
- Objective extraction (what the item is ultimately asking for)
- Domain classification: `personal` | `business` | `finance` | `social`
- Risk scoring with explicit keyword rules:
  - `high` — payment, invoice, new contact, credentials, legal
  - `medium` — public posting, external communication, scheduling
  - `low` — internal notes, status updates, read-only tasks
- Confidence scoring (0–100%) based on clarity of content, presence of keywords, domain signal strength
- Structured Plan generation with YAML frontmatter, objective, context, step checklist, proposed MCP actions
- Approval routing: `requires_approval: true` → creates file in `/Pending_Approval`
- Full action logging to `/Logs`

**When to Use:**
- Items appear in `/Needs_Action` that need deep analysis before planning
- When silver_process_engine classification is insufficient and richer reasoning is needed
- Auditing incoming work with confidence-weighted risk assessment
- Building human-reviewable plans for ambiguous or multi-domain items

**When NOT to Use:**
- Executing approved plans (use `approval-executor`)
- Items already processed (present in `/Plans` or `/Done`)
- Direct API or external calls (this skill is read/write vault only)

---

## Workflow

```
/Needs_Action/*.md
       │
       ▼
┌─────────────────────────────────────────────────┐
│  1. SCAN — list all .md files in /Needs_Action  │
└─────────────────────────────────────────────────┘
       │
       ▼  for each item:
┌─────────────────────────────────────────────────┐
│  2. REASON                                      │
│     a) Summarize (2–3 sentences)                │
│     b) Identify objective (1 sentence)          │
│     c) Classify domain                          │
│        personal / business / finance / social   │
│     d) Risk scoring                             │
│        high   → payment, invoice, new_contact,  │
│                 credentials, legal, breach       │
│        medium → public_post, external_email,    │
│                 scheduling, outreach             │
│        low    → internal, status, read-only     │
│     e) Confidence score 0–100%                  │
│        (keyword match strength + domain clarity)│
└─────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────┐
│  3. GENERATE PLAN → /Plans/<slug>-plan.md       │
│                                                 │
│  ---                                            │
│  status: pending                                │
│  risk_level: high|medium|low                    │
│  confidence: 0-100                              │
│  requires_approval: true|false                  │
│  domain: personal|business|finance|social       │
│  created_at: ISO datetime                       │
│  source_file: <original filename>               │
│  ---                                            │
│                                                 │
│  ## Objective                                   │
│  ## Context                                     │
│  ## Step Checklist                              │
│  ## Proposed MCP Actions                        │
└─────────────────────────────────────────────────┘
       │
       ├── requires_approval: true?
       │         │
       │         ▼
       │  ┌──────────────────────────────────────┐
       │  │  4. CREATE /Pending_Approval file     │
       │  └──────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────┐
│  5. LOG action to /Logs                         │
└─────────────────────────────────────────────────┘
```

---

## Risk Scoring Rules

| Trigger Keywords | Risk Level |
|---|---|
| `payment`, `invoice`, `wire`, `transfer`, `bank`, `new contact`, `unknown sender`, `credentials`, `password`, `legal`, `lawsuit`, `breach` | **high** |
| `post`, `publish`, `linkedin`, `twitter`, `email to`, `outreach`, `schedule`, `meeting request` | **medium** |
| `update`, `status`, `internal`, `note`, `reminder`, `draft`, `read` | **low** |

Domain modifier: `finance` domain auto-escalates `low` → `medium`.

---

## Confidence Scoring

| Signal | Points |
|---|---|
| Clear subject line / title | +20 |
| Explicit action verb found | +20 |
| Domain keyword match ≥2 | +20 |
| Risk keywords unambiguous | +20 |
| Body length > 50 words | +10 |
| Single domain detected (no conflict) | +10 |
| **Max total** | **100** |

---

## Plan Schema

```yaml
---
status: pending
risk_level: high|medium|low
confidence: 0-100
requires_approval: true|false
domain: personal|business|finance|social
created_at: "YYYY-MM-DDTHH:MM:SSZ"
source_file: "original-item.md"
engine: silver_reasoning_engine
---

## Objective
One sentence: what this item is ultimately requesting.

## Context
2–3 sentence summary of the item content.

## Step Checklist
- [ ] Step 1
- [ ] Step 2
- [ ] Step 3

## Proposed MCP Actions
- tool: <mcp_tool_name>
  input: <description of input>
  note: "Human must approve before execution"
```

---

## Approval Request Schema (`/Pending_Approval/`)

```yaml
---
type: approval_request
source_plan: "Plans/<plan-file>.md"
risk_level: high|medium|low
confidence: 0-100
domain: personal|business|finance|social
requested_at: "YYYY-MM-DDTHH:MM:SSZ"
status: awaiting_approval
---

## Summary
Brief description of what requires approval.

## Risk Reason
Why this was flagged as requiring approval.

## Plan Reference
See: Plans/<plan-file>.md
```

---

## Environment Variables

```
VAULT_PATH=./AI-Employee-Vault      # Vault root
SRE_DRY_RUN=false                   # true = no file writes
SRE_LOG_LEVEL=INFO                  # DEBUG/INFO/WARNING/ERROR
```

---

## Impact Analysis

### Security Impact: LOW
- Read-only on `/Needs_Action`
- Writes only to `/Plans`, `/Pending_Approval`, `/Logs`
- No network calls, no secrets accessed
- All high/medium risk items gated behind human approval

### System Impact: LOW
- Vault filesystem operations only
- Idempotent: skips items already having a plan

### Operational Impact: HIGH
- Every incoming item gets an auditable reasoning record
- Confidence score gives human reviewer context on plan quality
- Approval gate prevents accidental external execution

### Business Impact: HIGH
- Full traceability: inbox item → reasoning → plan → approval → execution
- Risk classification reduces unintended real-world side effects
- Domain awareness enables correct routing to specialized agents
