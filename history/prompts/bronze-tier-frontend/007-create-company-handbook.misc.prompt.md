---
id: 007
title: Create Company Handbook
stage: misc
date: 2026-02-21
surface: agent
model: qwen/qwen3-coder
feature: bronze-tier-frontend
branch: 1-bronze-tier-frontend
user: areeba_zafar
command: direct-prompt
labels: ["obsidian", "handbook", "bronze-tier", "policies"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - AI-Employee-Vault/Company_Handbook.md
tests:
  - none
---

## Prompt

Create Company_Handbook.md for my Personal AI Employee.

Include:

# Company Handbook

## Communication Rules
- Always be polite and professional
- Flag emotional or conflict situations for human review
- Never send bulk messages automatically

## Financial Rules
- Any transaction above $100 requires approval
- Never auto-pay new recipients

## Autonomy Level (Bronze Tier)
- Draft only
- Never execute payments
- All sensitive actions require approval

Keep it structured and editable.

## Response snapshot

Rewrote Company_Handbook.md with the three user-specified sections (Communication Rules, Financial Rules, Autonomy Level) as the top-level sections. Preserved existing Workflow Rules, Roles, and Policies from the prior version. Added an Escalation Rules section defining clear triggers for when the AI must defer to the human. All content is plain markdown, no plugins needed.

## Outcome

- ✅ Impact: Company Handbook now defines the full Bronze Tier operating contract — communication, financial, autonomy, workflow, and escalation rules
- 🧪 Tests: none
- 📁 Files: 1 file modified (AI-Employee-Vault/Company_Handbook.md)
- 🔁 Next prompts: Reference handbook rules in agent processing logic, test escalation triggers
- 🧠 Reflection: Merged user's new sections with existing workflow content to avoid losing prior structure

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
