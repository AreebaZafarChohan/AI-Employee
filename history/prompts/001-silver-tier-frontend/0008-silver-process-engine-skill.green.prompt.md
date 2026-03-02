---
id: "0008"
title: "Silver Process Engine Agent Skill"
stage: green
date: "2026-02-25"
surface: agent
model: qwen/qwen3-coder:free
feature: 001-silver-tier-frontend
branch: 001-silver-tier-frontend
user: areeba_zafar
command: "Create Agent Skill: silver_process_engine.md"
labels: ["silver-tier", "skill", "process-engine", "triage", "planning", "approval-workflow"]
links:
  spec: "null"
  ticket: "null"
  adr: "null"
  pr: "null"
files:
  - .claude/skills/silver/silver_process_engine/SKILL.md
  - .claude/skills/silver/silver_process_engine/MANIFEST.md
  - .claude/skills/silver/silver_process_engine/README.md
  - .claude/skills/silver/silver_process_engine/assets/silver_process_engine.py
  - .claude/skills/silver/silver_process_engine/assets/run.sh
  - .claude/commands/silver_process_engine.md
tests:
  - Ran engine against 2 real email items in Needs_Action
  - email-no-subject-576f57dd.md → type=email, risk=high → Plan + Approval created
  - email-no-subject-53c75fd5.md → type=email, risk=low → Plan only
  - Both items moved to Done
  - Pending_Approval contains approval request for high-risk item
---

# Prompt

Create Agent Skill: silver_process_engine.md

Skill Behavior:
1. Scan /Needs_Action
2. Classify item type: email, file_drop, whatsapp
3. Create structured Plan in /Plans (Objective, Context Summary, Risk Level, Steps, Requires Approval)
4. If risk level medium or high: Create approval file in /Pending_Approval
5. Log all actions
6. Move processed input to /Done only after plan creation

Constraints:
- Never execute real-world actions
- Only prepare structured outputs

# Response

Created the `silver_process_engine` skill with the following components:

## Files Created

- **SKILL.md** — Full skill spec: classification rules, risk matrix, plan schema, approval schema, flow diagram, Python blueprint, execution checklist, error handling table, security constraints
- **MANIFEST.md** — Skill overview, integration points, component list
- **README.md** — Quick start guide with usage examples
- **assets/silver_process_engine.py** — Standalone Python engine (~200 LOC)
- **assets/run.sh** — Shell wrapper with `--dry-run` and `--debug` flags
- **commands/silver_process_engine.md** — Claude command file for `/silver_process_engine` invocation

## Classification Logic

| Source | Detected As |
|---|---|
| `type: email` in frontmatter | `email` |
| `type: whatsapp` in frontmatter | `whatsapp` |
| Filename `email-*` | `email` |
| Filename `whatsapp-*` | `whatsapp` |
| Anything else | `file_drop` |

## Risk Matrix

| Condition | Risk |
|---|---|
| priority=high + type=email | high |
| priority=high or medium | medium |
| file_drop with no priority | medium |
| priority=low | low |
| Keyword match (urgent/legal/payment/etc.) | escalate one level |

## Test Results

```
Found 2 item(s) in Needs_Action.
Item: email-no-subject-53c75fd5.md | type=email | risk=low | approval=False
[OK] Plan created: no-subject-b5d57df2-plan.md
[OK] Moved to Done: email-no-subject-53c75fd5.md
Item: email-no-subject-576f57dd.md | type=email | risk=high | approval=True
[OK] Plan created: no-subject-69ee8d56-plan.md
[OK] Approval request created: no-subject-5f700bcd-approval.md
[OK] Moved to Done: email-no-subject-576f57dd.md
Done — processed=2, errors=0
```
