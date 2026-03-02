---
id: 2
title: "Monday CEO Briefing Skill Implementation"
stage: green
date: "2026-03-01"
surface: agent
model: qwen/qwen3-coder:free
feature: 001-silver-tier-frontend
branch: 001-silver-tier-frontend
user: areeba_zafar
command: implement
labels: ["monday-briefing", "weekly-report", "ceo-briefing", "silver-tier"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - monday_ceo_briefing.py
  - .claude/skills/silver/monday_ceo_briefing/SKILL.md
  - .claude/skills/silver/monday_ceo_briefing/MANIFEST.md
  - .claude/skills/silver/monday_ceo_briefing/README.md
  - .claude/skills/silver/monday_ceo_briefing/assets/run.sh
  - .claude/commands/monday_ceo_briefing.md
  - scripts/monday_ceo_briefing.sh
  - SCHEDULING_GUIDE.md
tests:
  - "DRY_RUN=true python3 monday_ceo_briefing.py — passed, found 6 tasks, 4 pending approvals"
---

## Prompt

Implement the Monday CEO Briefing Agent Skill plan: create monday_ceo_briefing.py (7-day window, 6 sections including revenue, bottlenecks, subscriptions, suggestions, pending approvals), skill docs (SKILL.md, MANIFEST.md, README.md), shell wrappers (assets/run.sh, scripts/monday_ceo_briefing.sh), command file, and update SCHEDULING_GUIDE.md with Sunday 11 PM cron entry.

## Response

Created 8 files implementing the Monday CEO Briefing skill:
1. `monday_ceo_briefing.py` — Main Python script with 7-day data window, 6 report sections, dashboard update
2. `.claude/skills/silver/monday_ceo_briefing/SKILL.md` — Full skill specification
3. `.claude/skills/silver/monday_ceo_briefing/MANIFEST.md` — Integration points and scheduling
4. `.claude/skills/silver/monday_ceo_briefing/README.md` — Quick start guide
5. `.claude/skills/silver/monday_ceo_briefing/assets/run.sh` — Shell wrapper
6. `.claude/commands/monday_ceo_briefing.md` — Claude command with step-by-step instructions
7. `scripts/monday_ceo_briefing.sh` — Cron wrapper for Sunday 11 PM scheduling
8. Updated `SCHEDULING_GUIDE.md` with weekly cron entry

Dry-run test passed: 6 tasks, 4 pending approvals, revenue signals detected.
