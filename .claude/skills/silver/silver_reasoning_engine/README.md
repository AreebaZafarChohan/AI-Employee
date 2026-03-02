# Silver Reasoning Engine

Deep-reasoning triage for `/Needs_Action` items. Produces confidence-scored, risk-classified Plans with full approval gating.

## Quick Start

```bash
# From project root
python3 .claude/skills/silver/silver_reasoning_engine/assets/silver_reasoning_engine.py

# Dry run (no writes)
SRE_DRY_RUN=true python3 .claude/skills/silver/silver_reasoning_engine/assets/silver_reasoning_engine.py

# Via shell wrapper
bash .claude/skills/silver/silver_reasoning_engine/assets/run.sh
bash .claude/skills/silver/silver_reasoning_engine/assets/run.sh --dry-run
bash .claude/skills/silver/silver_reasoning_engine/assets/run.sh --debug
```

## What It Does

For each `.md` file in `/Needs_Action`:

1. **Summarize** — 2–3 sentence summary of content
2. **Objective** — single sentence: what is being requested
3. **Domain** — `personal` | `business` | `finance` | `social`
4. **Risk Score** — `high` / `medium` / `low` based on keyword rules
5. **Confidence** — 0–100% based on content clarity signals
6. **Plan** → written to `/Plans/<slug>-plan.md`
7. **Approval** → written to `/Pending_Approval/` if risk is high or medium

## Plan Format

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
## Context
## Step Checklist
## Proposed MCP Actions
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `VAULT_PATH` | `./AI-Employee-Vault` | Vault root directory |
| `SRE_DRY_RUN` | `false` | Preview without writing files |
| `SRE_LOG_LEVEL` | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |

## Constraints

- Never executes any external action
- Never modifies or deletes source files in `/Needs_Action`
- All high/medium risk items gated behind human approval
- Idempotent: running twice creates a second plan (use `--dry-run` to preview)
