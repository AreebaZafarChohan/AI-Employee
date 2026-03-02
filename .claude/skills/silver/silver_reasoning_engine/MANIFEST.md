# Silver Reasoning Engine — Manifest

**Created:** 2026-02-26
**Domain:** silver
**Status:** Production Ready
**Version:** 1.0.0

## Overview

Deep-reasons over every `/Needs_Action` item: summarize, identify objective, classify domain, score risk and confidence, generate structured Plans, route to Pending_Approval when needed.

## Components

| File | Purpose |
|---|---|
| `SKILL.md` | Full specification, workflow diagram, schemas |
| `MANIFEST.md` | This file |
| `README.md` | Quick-start guide |
| `assets/silver_reasoning_engine.py` | Core engine (~300 LOC) |
| `assets/run.sh` | Shell wrapper |

## Inputs / Outputs

| Direction | Path | Description |
|---|---|---|
| Read | `/Needs_Action/*.md` | Source items to reason over |
| Write | `/Plans/<slug>-<id>-plan.md` | Structured plan per item |
| Write | `/Pending_Approval/<slug>-<id>-approval.md` | Approval requests (high/medium risk) |
| Write | `/Logs/silver-reasoning-engine-YYYY-MM-DD.log` | Action log |

## Risk Rules

| Risk | Triggers |
|---|---|
| `high` | payment, invoice, new contact, credentials, legal, breach |
| `medium` | post, publish, email to, outreach, schedule |
| `low` | internal, status, update, note, reminder |

## Confidence Score

0–100% based on: title clarity, action verb, domain keyword density, risk signal strength, body length, domain uniqueness.
