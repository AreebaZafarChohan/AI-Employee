---
id: 009
title: Create Process Needs Action Skill
stage: green
date: 2026-02-22
surface: agent
model: qwen/qwen3-coder
feature: bronze-tier-frontend
branch: 1-bronze-tier-frontend
user: areeba_zafar
command: direct-prompt
labels: ["skill", "needs-action", "plans", "bronze-tier", "vault"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - process_needs_action.md
  - src/claude/agent_skills/process_needs_action.py
  - src/claude/agent_skills/__init__.py
  - .claude/skills/vault/process_needs_action/SKILL.md
tests:
  - "E2E: drop file in Needs_Action → plan created in Plans/ → original moved to Done/ → JSON log appended (PASS)"
---

## Prompt

Create an Agent Skill called:

process_needs_action.md

Skill behavior:

1. Read all files in /Needs_Action
2. For each file:
   - Analyze content
   - Create a Plan file in /Plans with:
       Objective
       Steps
       Status: pending
   - Move original file to /Done when processed

Constraints:
- Do not execute any external action
- Only read/write inside vault
- Log action in /Logs/YYYY-MM-DD.json

Return skill markdown content.

## Response snapshot

Created a complete agent skill with three artifacts: standalone process_needs_action.md, Python ProcessNeedsAction class extending SkillBase, and SKILL.md in the .claude/skills/ structure. The skill reads Needs_Action files, extracts objectives and steps from content, writes Plans with YAML frontmatter and checkbox steps, moves originals to Done, and appends structured JSON logs. Fully offline — no external calls. E2E tested with a realistic client email task.

## Outcome

- ✅ Impact: Full process_needs_action skill pipeline — analyse, plan, archive, log
- 🧪 Tests: 1 E2E test passed (content extraction + plan creation + move + log)
- 📁 Files: 3 created, 1 modified
- 🔁 Next prompts: Unit tests for edge cases (empty files, binary files, large content)
- 🧠 Reflection: Used offline content analysis to stay within Bronze Tier no-external-action constraint; fallback generic steps prevent empty plans

## Evaluation notes (flywheel)

- Failure modes observed: google.genai import prevents full package-level import (pre-existing issue in claude_client.py, unrelated to this skill)
- Graders run and results (PASS/FAIL): manual E2E PASS
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): add LLM-powered analysis as optional upgrade path for Silver tier
