# Silver Process Engine — Manifest

**Created:** 2026-02-25
**Domain:** silver
**Status:** Production Ready
**Version:** 1.0.0

## Overview

The `silver_process_engine` skill is the core triage and planning engine for the Silver Tier AI Employee. It scans `/Needs_Action`, classifies each item, generates a structured Plan, routes medium/high risk items for human approval, logs every action, and archives the source item to `/Done`.

**Constraint:** This skill never executes real-world actions. It only prepares structured outputs.

## Components

### Core Files
- `SKILL.md` — Complete skill specification including blueprints, schemas, flow diagram
- `README.md` — Quick start guide
- `MANIFEST.md` — This file

### Assets
- `assets/silver_process_engine.py` — Standalone Python engine (~150 LOC)
- `assets/run.sh` — Shell wrapper

### Docs
- `docs/classification-rules.md` — Full type and risk classification rules
- `docs/plan-schema.md` — Plan and approval file schema reference

## Capabilities

- Item classification: `email`, `file_drop`, `whatsapp`
- Risk assessment: `low`, `medium`, `high` with keyword escalation
- Plan generation with Objective, Context Summary, Risk Level, Steps, Requires Approval
- Approval request generation for medium/high risk
- Action logging to `/Logs`
- Safe archival: source moved to `/Done` only after successful plan creation

## Integration Points

- Input: `/Needs_Action/*.md`
- Output Plans: `/Plans/<slug>-<id>-plan.md`
- Output Approvals: `/Pending_Approval/<slug>-<id>-approval.md`
- Archive: `/Done/<original-filename>.md`
- Logs: `/Logs/silver-process-engine-YYYY-MM-DD.log`
- Upstream: `gmail_watcher.py` writes to `/Needs_Action`
- Downstream: `approval-executor` agent reads `/Approved`
