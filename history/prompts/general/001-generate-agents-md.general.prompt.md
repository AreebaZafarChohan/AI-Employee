---
id: 001
title: Generate AGENTS.md governance document
stage: spec
date: 2026-01-29
surface: agent
model: claude-haiku-4-5-20251001
feature: none
branch: master
user: Areeba_Zafar
command: Create a Prompt History Record (PHR) for the generation of the AGENTS.md file
labels: ["governance", "agents", "specification", "autonomy"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - D:/Gemini_Cli/hackathon/hackathon_0/AI-Employee/AGENTS.md
tests:
  - none
---

## Prompt

You are Claude Code.

Your task is to generate a production-grade `AGENTS.md` file for the project:

"Personal AI Employee Hackathon 0 – Building Autonomous Digital FTEs (Full-Time Equivalent)".

This AGENTS.md is the **canonical authority** that defines:
- what agents exist,
- what they own,
- how they communicate,
- what they are allowed to do,
- and what they are strictly forbidden from doing.

This document will be used by humans AND AI agents.
It must be precise, enforceable, and operational — not marketing text.

---

## CONTEXT (DO NOT REPEAT, JUST USE)

This project builds a **local-first + cloud-assisted autonomous AI employee** using:
- Claude Code as the reasoning engine
- Obsidian Vault as memory + GUI
- Python Watchers (Gmail, WhatsApp, Files, Finance)
- MCP Servers for actions (email, browser, payments, social)
- Human-in-the-loop approval via file movement
- Ralph Wiggum loop for non-lazy autonomous execution

Agents collaborate via a **file-based protocol** inside the vault.
Security, auditability, and human accountability are non-negotiable.

---

## AGENTS.md MUST FOLLOW THIS STRUCTURE (MANDATORY)

### 1. Purpose of This Document
Explain why AGENTS.md exists and how it governs agent behavior.

### 2. Agent Taxonomy
Define ALL agents clearly.

You MUST include at minimum:

- Local Executive Agent
- Cloud Executive Agent
- Watcher Agents (Gmail, WhatsApp, Finance, Filesystem)
- Orchestrator Agent
- Action Agents (MCP-backed)
- Human Actor (explicitly defined as an agent boundary)

### 3. Agent Ownership & Jurisdiction
For EACH agent, define:

- Responsibilities
- Data it can read
- Data it can write
- Actions it can trigger
- Actions it must NEVER trigger

Use clear tables where appropriate.

---

### 4. Vault-Based Communication Protocol
Define:

- Canonical folders
- Claim-by-move rule
- Single-writer rules
- Conflict avoidance
- Idempotency expectations

Mandatory folders to document:
- /Needs_Action/
- /Plans/
- /In_Progress/
- /Pending_Approval/
- /Approved/
- /Rejected/
- /Done/
- /Updates/ or /Signals/
- /Logs/

---

### 5. Human-in-the-Loop Enforcement Rules
Define:

- What requires approval
- How approval is requested
- What constitutes approval
- What happens on rejection
- Expiry rules
- Escalation rules

Be explicit: this is a safety-critical section.

---

### 6. Autonomy Levels
Define **Bronze / Silver / Gold / Platinum** autonomy expectations:

- What agents are allowed to do at each tier
- What must remain manual
- What is draft-only vs executable
- Cloud vs Local authority split (Platinum)

---

### 7. Ralph Wiggum Loop Governance
Explain:

- Which agents may use Ralph loops
- Maximum iteration limits
- Completion criteria
- When loops must terminate
- When to escalate to human

---

### 8. Security & Trust Boundaries
Define:

- Secret handling rules
- What never syncs to cloud
- Env vs vault data separation
- Audit log requirements
- Blast-radius containment

This section should read like a security policy.

---

### 9. Failure Modes & Agent Behavior on Error
Define:

- Retry rules
- Pause conditions
- Human alert thresholds
- Graceful degradation expectations

---

### 10. Explicit Anti-Patterns (MANDATORY)
List behaviors that agents must NEVER do, including but not limited to:

- Acting without approval
- Writing secrets to vault
- Editing Dashboard.md without authority
- Acting on ambiguous intent
- Cloud agent performing irreversible actions

---

### 11. Final Authority Rule
Define:

- Who has final authority
- How disputes are resolved
- How humans override agents
- That humans are always accountable

This section is mandatory and must be unambiguous.

---

## STYLE & QUALITY RULES

- Write in **clear, authoritative technical English**
- No emojis
- No fluff
- No marketing language
- This is a **governance contract**, not a blog post
- Use headings, tables, and bullet points where helpful
- Assume readers are engineers building autonomous systems

---

## OUTPUT RULES

- Output ONLY the contents of `AGENTS.md`
- Do NOT explain what you are doing
- Do NOT include markdown outside the document
- Do NOT summarize
- Do NOT ask questions

Generate the AGENTS.md now.


## Tools

You have access to a set of tools you can use to answer the user's question.
You can invoke functions by writing a "<｜DSML｜function_calls>" block like the following as part of your reply to the user:
<｜DSML｜function_calls>
<｜DSML｜invoke name="$FUNCTION_NAME">
<｜DSML｜parameter name="$PARAMETER_NAME" string="true|false">$PARAMETER_VALUE
