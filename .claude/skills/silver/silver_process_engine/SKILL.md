# Silver Process Engine Skill

## Overview

**Skill Name:** `silver_process_engine`
**Domain:** `silver`
**Purpose:** Scan `/Needs_Action`, classify incoming items, generate structured Plans, route for approval when needed, log all actions, and move processed items to `/Done`. Never executes real-world actions — only prepares structured outputs.

**Core Capabilities:**
- Item classification: `email`, `file_drop`, `whatsapp`
- Structured Plan generation in `/Plans` with Objective, Context Summary, Risk Level, Steps, Requires Approval
- Approval routing: medium/high risk → creates approval request in `/Pending_Approval`
- Full action logging to `/Logs`
- Safe item archival: moves source file to `/Done` only after plan creation succeeds

**When to Use:**
- New files appear in `/Needs_Action` and need structured processing
- Classifying and triaging incoming work items before any real-world action
- Building an auditable, human-reviewable plan for any incoming request
- Enforcing approval gates before high-risk actions proceed

**When NOT to Use:**
- Executing actions directly (send email, call API, write to external system)
- When human has already reviewed and approved — use `approval-executor` instead
- Items already processed (present in `/Done` or `/Plans`)

## Impact Analysis

### Security Impact: LOW
- Read-only on source items in `/Needs_Action`
- Writes only to `/Plans`, `/Pending_Approval`, `/Logs`, `/Done`
- No network calls, no secrets accessed
- Approval gate enforced for medium/high risk

### System Impact: LOW
- Filesystem operations only within the vault
- Idempotent: re-running on an already-moved item is a no-op
- No external dependencies

### Operational Impact: HIGH
- Ensures no unreviewed item proceeds to execution
- Creates full audit trail for every processed item
- Approval bottleneck prevents accidental real-world side effects

### Business Impact: HIGH
- Enforces structured decision-making on all incoming work
- Traceability from inbox item → plan → approval → execution
- Risk classification reduces likelihood of unintended actions

## Environment Variables

### Required Variables
```
VAULT_PATH=./AI-Employee-Vault   # Root of the AI Employee vault
```

### Optional Variables
```
SILVER_PE_DRY_RUN=false          # Log actions without writing files
SILVER_PE_LOG_LEVEL=INFO         # DEBUG / INFO / WARNING / ERROR
SILVER_PE_DEFAULT_RISK=low       # Fallback risk level when classifier uncertain
```

## Item Classification Rules

| Frontmatter `type` | Detected Pattern | Assigned Type |
|---|---|---|
| `type: email` | YAML frontmatter present | `email` |
| `type: whatsapp` | YAML frontmatter present | `whatsapp` |
| `type: file_drop` | YAML frontmatter present | `file_drop` |
| *(none)* | Filename contains `email-` | `email` |
| *(none)* | Filename contains `whatsapp-` | `whatsapp` |
| *(none)* | Any other `.md` file | `file_drop` |

## Risk Classification Rules

### Risk Scoring System

The engine uses a **scored risk assessment** (0-100) with confidence levels (0-100%).

| Score Range | Risk Level | Approval Required |
|-------------|------------|-------------------|
| 0-39        | **LOW**    | No                |
| 40-69       | **MEDIUM** | Yes               |
| 70-100      | **HIGH**   | Yes               |

### Scoring Rules

| Rule | Condition | Score Impact |
|------|-----------|--------------|
| **Financial > $100** | Amount extracted from content/metadata > $100 | +50 (HIGH risk) |
| **Financial > $0** | Any amount mentioned | +20 |
| **Unknown Sender** | Sender not in internal domains (company.com, internal) | +25 (MEDIUM risk) |
| **Known Sender** | Sender from internal domain | +5 |
| **Urgent Keywords** | "urgent", "asap", "immediately", "rush", "deadline" | +25 (MEDIUM risk) |
| **Risk Keywords** | "legal", "payment", "password", "terminate", "critical" | +30 |
| **High Priority** | `priority: high` in frontmatter | +30 |
| **Medium Priority** | `priority: medium` in frontmatter | +20 |
| **Low Priority** | `priority: low` in frontmatter | +10 |
| **Internal File Drop** | file_drop + known sender | -20 |

### Base Scores by Type

| Item Type | Base Score |
|-----------|------------|
| email     | +20        |
| file_drop | +30        |
| whatsapp  | +25        |

### Confidence Score Calculation

Confidence represents how much data is available for assessment:

- **Base:** 60%
- **+10%** for each available factor:
  - Sender information present
  - Priority field present
  - Financial amount detected
  - Content available for analysis
- **Maximum:** 100%

### Examples

**Example 1: High Risk Email**
```
From: external@gmail.com
Priority: high
Content: "Urgent! Payment of $500 needed immediately"

Scoring:
- Base (email): +20
- High priority: +30
- Unknown sender: +25
- Urgent keyword: +25
- Amount > $100: +50
Total: 150 → capped at 100 → HIGH risk
Confidence: 100% (all factors present)
```

**Example 2: Low Risk Internal File**
```
From: john@company.com
Type: file_drop
Content: "Monthly report attached"

Scoring:
- Base (file_drop): +30
- Known sender: +5
- Internal file_drop: -20
Total: 15 → LOW risk
Confidence: 70% (sender, content present)
```

**Example 3: Medium Risk Email**
```
From: client@external.com
Priority: medium
Content: "Question about the project"

Scoring:
- Base (email): +20
- Medium priority: +20
- Unknown sender: +25
Total: 65 → MEDIUM risk
Confidence: 80% (sender, priority, content)
```

## Plan Schema (`/Plans/<slug>-plan.md`)

```markdown
---
plan_id: <uuid-short>
source_file: <original filename in Needs_Action>
item_type: email | file_drop | whatsapp
risk_level: low | medium | high
risk_score: <0-100>
confidence_score: <0-100>
requires_approval: true | false
status: pending_approval | ready_to_execute | draft
created_at: <ISO8601>
---

# Plan: <title>

## Objective
<One sentence: what this plan achieves>

## Context Summary
<2-4 sentences summarizing the source item: who, what, when, why>

## Risk Level
**<LOW | MEDIUM | HIGH>** (Score: <score>/100, Confidence: <confidence>%)

**Risk Score:** <score>/100
**Confidence:** <confidence>%

**Factors:**
  - <factor 1>
  - <factor 2>
  - ...

<risk justification with factors>

## Steps
1. <Step 1 — specific, actionable, safe>
2. <Step 2>
3. ...

## Requires Approval?
**<Yes | No>**
<If yes: reason why approval is needed>

## Source Excerpt
> <snippet or key content from source item>
```

## Approval Request Schema (`/Pending_Approval/<slug>-approval.md`)

```markdown
---
approval_id: <uuid-short>
plan_file: Plans/<slug>-plan.md
source_file: <original filename>
risk_level: medium | high
requested_at: <ISO8601>
status: pending
---

# Approval Request: <title>

## Why Approval Is Required
<Risk level + specific reason>

## Proposed Plan Summary
<3-5 bullet summary of the plan steps>

## Action Required
- [ ] Review linked plan: `Plans/<slug>-plan.md`
- [ ] Approve → move this file to `/Approved`
- [ ] Reject → move this file to `/Rejected`
```

## Processing Flow

```
/Needs_Action/<item>.md
        │
        ▼
  1. Read & parse item
        │
        ▼
  2. Classify type
  (email / file_drop / whatsapp)
        │
        ▼
  3. Assess risk level
  (low / medium / high)
        │
        ▼
  4. Generate Plan → write /Plans/<slug>-plan.md
        │
        ├─ risk = medium or high ──▶ 5. Write /Pending_Approval/<slug>-approval.md
        │
        ▼
  6. Log action → /Logs/silver-process-engine-YYYY-MM-DD.log
        │
        ▼
  7. Move item → /Done/<item>.md
```

## Blueprints

### Blueprint 1: Core Processing Loop (Python)

```python
#!/usr/bin/env python3
"""silver_process_engine.py — Silver Tier process engine."""

import re
import uuid
import logging
from datetime import datetime, timezone
from pathlib import Path

VAULT = Path("AI-Employee-Vault")
NEEDS_ACTION = VAULT / "Needs_Action"
PLANS = VAULT / "Plans"
PENDING_APPROVAL = VAULT / "Pending_Approval"
DONE = VAULT / "Done"
LOGS = VAULT / "Logs"

RISK_KEYWORDS = {"urgent", "legal", "payment", "password", "terminate", "lawsuit", "critical"}

def _read_frontmatter(text: str) -> dict:
    """Parse YAML frontmatter block from markdown text."""
    meta = {}
    if not text.startswith("---"):
        return meta
    end = text.find("\n---", 3)
    if end == -1:
        return meta
    for line in text[3:end].splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip().strip('"')
    return meta

def _classify_type(filename: str, meta: dict) -> str:
    if "type" in meta:
        return meta["type"]
    name = filename.lower()
    if "email" in name:
        return "email"
    if "whatsapp" in name:
        return "whatsapp"
    return "file_drop"

def _classify_risk(item_type: str, meta: dict, content: str) -> str:
    priority = meta.get("priority", "").lower()
    base = "low"
    if priority == "high" and item_type == "email":
        base = "high"
    elif priority in ("high", "medium"):
        base = "medium"
    elif item_type == "file_drop" and not priority:
        base = "medium"

    # Keyword escalation
    content_lower = content.lower()
    if any(kw in content_lower for kw in RISK_KEYWORDS):
        if base == "low":
            base = "medium"
        elif base == "medium":
            base = "high"
    return base

def _short_id() -> str:
    return str(uuid.uuid4())[:8]

def _slug(text: str) -> str:
    s = re.sub(r"[^\w\s-]", "", text.lower())
    s = re.sub(r"[\s_]+", "-", s).strip("-")
    return s[:50] or "item"

def _render_plan(source_file: str, item_type: str, risk: str, meta: dict, snippet: str) -> tuple[str, str]:
    plan_id = _short_id()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    requires_approval = risk in ("medium", "high")
    subject = meta.get("subject") or meta.get("filename") or source_file
    title = f"Process {item_type}: {subject}"
    slug = _slug(subject)

    steps = {
        "email": [
            "Read and understand the full email content.",
            "Identify the sender's intent and any required action.",
            "Draft a response or delegate to appropriate owner.",
            "Archive the email in Done after response is sent.",
        ],
        "whatsapp": [
            "Read and understand the WhatsApp message content.",
            "Identify the sender's intent and urgency.",
            "Prepare a response or escalate to appropriate owner.",
            "Archive the item in Done after handling.",
        ],
        "file_drop": [
            "Review the dropped file content and metadata.",
            "Classify the file purpose (report, attachment, task, etc.).",
            "Route to appropriate folder or owner.",
            "Archive the item in Done after routing.",
        ],
    }.get(item_type, ["Review item.", "Determine action.", "Execute or delegate.", "Archive."])

    steps_md = "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))
    approval_text = (
        f"**Yes** — Risk level is {risk.upper()}. Human review required before execution."
        if requires_approval
        else "**No** — Low risk. Can proceed directly to execution."
    )

    frontmatter = (
        "---\n"
        f"plan_id: {plan_id}\n"
        f"source_file: {source_file}\n"
        f"item_type: {item_type}\n"
        f"risk_level: {risk}\n"
        f"requires_approval: {str(requires_approval).lower()}\n"
        f"status: {'pending_approval' if requires_approval else 'ready_to_execute'}\n"
        f"created_at: \"{now}\"\n"
        "---\n"
    )
    body = (
        f"# Plan: {title}\n\n"
        f"## Objective\n"
        f"Process the incoming {item_type} item, determine required action, and prepare a structured response.\n\n"
        f"## Context Summary\n"
        f"Item received from `{meta.get('from', 'unknown')}` at `{meta.get('received_at', now)}`. "
        f"Type: `{item_type}`. Priority: `{meta.get('priority', 'unspecified')}`. "
        f"Source file: `{source_file}`.\n\n"
        f"## Risk Level\n**{risk.upper()}** — "
        + ("High priority email requires careful handling."
           if risk == "high" else
           "Medium risk — review before acting."
           if risk == "medium" else
           "Low risk — standard processing applies.")
        + "\n\n"
        f"## Steps\n{steps_md}\n\n"
        f"## Requires Approval?\n{approval_text}\n\n"
        f"## Source Excerpt\n> {snippet[:300]}\n"
    )

    filename = f"{slug}-{plan_id}-plan.md"
    return filename, frontmatter + "\n" + body

def _render_approval(plan_filename: str, source_file: str, risk: str, meta: dict, steps_md: str) -> tuple[str, str]:
    approval_id = _short_id()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    subject = meta.get("subject") or meta.get("filename") or source_file
    slug = _slug(subject)

    frontmatter = (
        "---\n"
        f"approval_id: {approval_id}\n"
        f"plan_file: Plans/{plan_filename}\n"
        f"source_file: {source_file}\n"
        f"risk_level: {risk}\n"
        f"requested_at: \"{now}\"\n"
        "status: pending\n"
        "---\n"
    )
    body = (
        f"# Approval Request: {subject}\n\n"
        f"## Why Approval Is Required\n"
        f"Risk level is **{risk.upper()}**. This item requires human review before any action is taken.\n\n"
        f"## Proposed Plan Summary\n{steps_md}\n\n"
        "## Action Required\n"
        f"- [ ] Review linked plan: `Plans/{plan_filename}`\n"
        "- [ ] Approve → move this file to `/Approved`\n"
        "- [ ] Reject → move this file to `/Rejected`\n"
    )

    filename = f"{slug}-{approval_id}-approval.md"
    return filename, frontmatter + "\n" + body

def process_item(item_path: Path, logger: logging.Logger, dry_run: bool = False) -> str:
    """Process a single Needs_Action item. Returns outcome string."""
    text = item_path.read_text(encoding="utf-8")
    meta = _read_frontmatter(text)
    snippet = meta.get("snippet") or text.replace("---", "").strip()[:300]

    item_type = _classify_type(item_path.name, meta)
    risk = _classify_risk(item_type, meta, text)
    requires_approval = risk in ("medium", "high")

    logger.info("Processing: %s | type=%s | risk=%s", item_path.name, item_type, risk)

    # Generate plan
    plan_filename, plan_content = _render_plan(item_path.name, item_type, risk, meta, snippet)
    plan_path = PLANS / plan_filename

    if not dry_run:
        PLANS.mkdir(parents=True, exist_ok=True)
        plan_path.write_text(plan_content, encoding="utf-8")
    logger.info("Plan created: %s", plan_filename)

    # Generate approval request if needed
    if requires_approval:
        steps_md = "\n".join(
            f"- Step {i+1}: {line.strip()}"
            for i, line in enumerate(plan_content.split("## Steps")[1].split("## Requires")[0].strip().splitlines())
            if line.strip()
        )
        approval_filename, approval_content = _render_approval(plan_filename, item_path.name, risk, meta, steps_md)
        approval_path = PENDING_APPROVAL / approval_filename
        if not dry_run:
            PENDING_APPROVAL.mkdir(parents=True, exist_ok=True)
            approval_path.write_text(approval_content, encoding="utf-8")
        logger.info("Approval request created: %s", approval_filename)

    # Move to Done
    done_path = DONE / item_path.name
    if not dry_run:
        DONE.mkdir(parents=True, exist_ok=True)
        item_path.rename(done_path)
    logger.info("Moved to Done: %s", item_path.name)

    return f"ok | type={item_type} | risk={risk} | plan={plan_filename}"

def run(dry_run: bool = False) -> None:
    import os, sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    from src.utils.logger import log_action, set_default_logs_dir

    LOGS.mkdir(parents=True, exist_ok=True)
    set_default_logs_dir(LOGS)

    level = getattr(logging, os.getenv("SILVER_PE_LOG_LEVEL", "INFO").upper(), logging.INFO)
    logging.basicConfig(level=level, format="%(asctime)s | %(levelname)-8s | silver_process_engine | %(message)s")
    logger = logging.getLogger("silver_process_engine")

    items = sorted(NEEDS_ACTION.glob("*.md")) if NEEDS_ACTION.exists() else []
    if not items:
        logger.info("No items in Needs_Action. Nothing to process.")
        return

    logger.info("Found %d item(s) in Needs_Action.", len(items))
    for item in items:
        try:
            outcome = process_item(item, logger, dry_run=dry_run)
            log_action("process_engine", item.name, f"success | {outcome}")
        except Exception as exc:
            logger.error("Failed to process %s: %s", item.name, exc, exc_info=True)
            log_action("process_engine_error", item.name, f"error: {exc}")

if __name__ == "__main__":
    import os
    run(dry_run=os.getenv("SILVER_PE_DRY_RUN", "false").lower() in ("true", "1", "yes"))
```

### Blueprint 2: Minimal Shell Invocation

```bash
#!/usr/bin/env bash
# Run the silver process engine
PYTHONPATH=/tmp/gapi python3 .claude/skills/silver/silver_process_engine/assets/silver_process_engine.py
```

### Blueprint 3: DRY_RUN Validation

```bash
SILVER_PE_DRY_RUN=true PYTHONPATH=/tmp/gapi python3 \
  .claude/skills/silver/silver_process_engine/assets/silver_process_engine.py
```

## Execution Checklist

Before running:
- [ ] `/Needs_Action/` contains at least one `.md` item
- [ ] `/Plans/`, `/Pending_Approval/`, `/Done/` directories exist (auto-created if missing)
- [ ] `VAULT_PATH` points to correct vault root

After running:
- [ ] Each processed item has a corresponding `*-plan.md` in `/Plans`
- [ ] Medium/high risk items have a corresponding `*-approval.md` in `/Pending_Approval`
- [ ] Source items are no longer in `/Needs_Action` (moved to `/Done`)
- [ ] Actions logged in `/Logs/silver-process-engine-*.log`

## Error Handling

| Situation | Behavior |
|---|---|
| Item cannot be read | Log error, skip item, continue loop |
| Plan write fails | Log error, item stays in Needs_Action |
| Approval write fails | Log error, plan still written, item moved |
| Item already in Done | Skip silently |
| Unknown type | Default to `file_drop` classification |

## Security Constraints

- **NEVER** execute real-world actions (no email sends, no API calls, no external writes)
- **NEVER** access secrets or credentials
- **NEVER** delete source items — only move to `/Done`
- **ALWAYS** require approval for medium and high risk items
- **ALWAYS** log every action with timestamp and outcome
