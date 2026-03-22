---
id: 1
title: "Create Weekly Business Audit System"
stage: spec
date_iso: 2026-03-08
surface: agent
model: gemini-2.0-flash
feature: "Weekly Audit"
branch: main
user: G S COMPUTER
command: "Build the Weekly Business Audit system for my Personal AI Employee."
labels: ["audit", "odoo", "social", "briefing"]
links:
  SPEC: "null"
  TICKET: "null"
  ADR: "null"
  PR: "null"
FILES_YAML:
  - weekly_audit.py
TESTS_YAML:
  - "python weekly_audit.py --dry-run"
---

# Prompt History Record (PHR) - Weekly Business Audit System

## Prompt
Build the Weekly Business Audit system for my Personal AI Employee.

Goal:
Every Sunday night the AI performs a full business audit and generates a Monday Morning CEO Briefing.

Inputs the system must analyze:
1. Odoo accounting data
2. Tasks completed in /Done folder
3. Social media engagement
4. Active projects
5. Subscription spending
6. Client communication delays

Output file:
/Vault/Briefings/YYYY-MM-DD_Monday_Briefing.md

Sections required:
Executive Summary
Revenue Analysis
Completed Work
Bottlenecks
Subscription Waste
Upcoming Deadlines
AI Strategic Suggestions

Implementation requirements:
* Create Python script weekly_audit.py
* Use Claude Code for reasoning
* Schedule via cron or Task Scheduler
* Store results in Obsidian vault

Also generate the analysis algorithms needed to compute:
revenue trend
task productivity
client response time
marketing performance

## Response Text
I will build the Weekly Business Audit system by creating `weekly_audit.py`. This script will aggregate data from Odoo, the Obsidian vault (/Done, /Projects, /Accounting), and social media watchers to generate a comprehensive Monday Morning CEO Briefing. I will also implement the requested analysis algorithms for trends and productivity.

## Outcome/Evaluation
Starting the implementation of `weekly_audit.py` based on the existing project structure and requirements.
