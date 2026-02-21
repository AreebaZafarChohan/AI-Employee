---
id: 0004
title: ai-employee-tasks
stage: tasks
date: 2026-02-09
surface: agent
model: Qwen
feature: 001-ai-employee-foundation
branch: 001-ai-employee-foundation
user: user
command: "/sp.tasks"
labels: ["tasks", "ai-employee", "bronze-tier"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - "specs/001-ai-employee-foundation/tasks.md"
tests:
  - "task-validation-passed"
---

## Prompt

/sp.tasks
Generate an actionable, dependency-ordered tasks.md for the feature based on available design artifacts. Personal AI Employee – Bronze Tier Tasks Context: You are generating executable development tasks based on the approved Bronze plan. Task Rules: - Tasks must be atomic and actionable - Each task should be completable in 30–90 minutes - Tasks should map directly to files or scripts - Tasks should respect Bronze constraints only For each task include: - Task ID - Description - Input (if any) - Output / Artifact - Validation condition (how to know it worked) Expected Task Categories: - Obsidian vault setup - Folder creation - Company_Handbook.md authoring - Dashboard.md skeleton - Watcher script creation - Claude Code prompt/skill usage - Manual test run Output Format: - Markdown checklist - Grouped by phase - Clear completion criteria Do NOT: - Combine multiple concerns in one task - Introduce Silver/Gold/Platinum features - Assume background daemons or cloud services

## Response snapshot

Successfully generated a comprehensive tasks.md file for the Personal AI Employee Bronze Tier implementation with 100+ specific, actionable tasks organized across 10 phases. The tasks follow the required checklist format with proper IDs, story labels, and file paths. The implementation follows an incremental delivery approach starting with User Story 1 (P1) as the MVP, with clear dependencies and parallel execution opportunities identified.

## Outcome

- ✅ Impact: Created a complete, executable task breakdown that maps directly to the approved Bronze tier plan and specification
- 🧪 Tests: All tasks follow the required checklist format and are organized by user story for independent implementation and testing
- 📁 Files: tasks.md created with 100+ specific, actionable tasks organized across 10 implementation phases
- 🔁 Next prompts: Ready for implementation phase
- 🧠 Reflection: The task breakdown enables incremental delivery starting with the foundational vault structure (MVP), followed by the watcher, Claude integration, processing workflow, and completion workflow

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): PASS - All tasks follow the required format and organization
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Begin implementation with Phase 1 tasks
