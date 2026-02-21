---
id: 0001
title: ai-employee-spec
stage: spec
date: 2026-02-09
surface: agent
model: Qwen
feature: 001-ai-employee-foundation
branch: 001-ai-employee-foundation
user: user
command: "/sp.specify"
labels: ["specification", "ai-employee", "bronze-tier"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - "specs/001-ai-employee-foundation/spec.md"
  - "specs/001-ai-employee-foundation/checklists/requirements.md"
tests:
  - "spec-validation-passed"
---

## Prompt

/sp.specify
Create or update the feature specification from a natural language feature description. Personal AI Employee – Bronze Tier (Foundation) Context: This system is a local-first Personal AI Employee built using Claude Code and an Obsidian vault. The goal of the Bronze tier is to prove the foundational architecture works end-to-end: Watcher → Vault → Claude Reasoning → Vault Output. Target user: - Technical student / developer - Running system locally - Comfortable with terminal, Python, Obsidian Core Objective: Build a minimum viable Digital FTE that can: - Detect new inputs - Reason about them - Write structured outputs into an Obsidian vault Success Criteria: - Obsidian vault exists with: - Dashboard.md - Company_Handbook.md - Folder structure exists: - /Needs_Action - /Plans - /Done - At least ONE working watcher (file system OR Gmail) - Claude Code can: - Read files from /Needs_Action - Create a Plan.md in /Plans - Move completed items to /Done - All AI behavior is implemented via Claude Agent Skills (no inline logic) Constraints: - Local-only execution (no cloud) - No payments - No WhatsApp automation - No social posting - No MCP actions that modify external systems - No background daemon orchestration (manual runs acceptable) Out of Scope (NOT building in Bronze): - Cloud deployment - WhatsApp integration - Banking or payments - MCP browser automation - Ralph Wiggum autonomous loops - Multi-agent orchestration - Approval workflows Non-Functional Requirements: - Simple, readable Markdown outputs - Deterministic folder transitions - No secrets stored in vault - Safe-by-default behavior Deliverables: - Working Obsidian vault - One watcher script - Demonstration of Claude Code reading + writing vault files - Clear README explaining how Bronze works

## Response snapshot

Created a comprehensive feature specification for the Personal AI Employee Bronze Tier, including:
- User scenarios and testing with prioritized user stories
- Functional requirements (12 specific requirements)
- Key entities definition
- Success criteria with 10 measurable outcomes
- Quality validation checklist

## Outcome

- ✅ Impact: Successfully created a complete feature specification that captures all requirements for the Bronze Tier foundation of the Personal AI Employee system
- 🧪 Tests: Specification quality checklist validated and completed
- 📁 Files: spec.md and requirements.md created in the feature directory
- 🔁 Next prompts: Ready for clarification and planning phases
- 🧠 Reflection: The specification comprehensively covers the core architecture: Watcher → Vault → Claude Reasoning → Vault Output

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): PASS - All validation items checked and specification is ready
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Proceed with clarification phase
