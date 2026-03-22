---
id: "013"
title: "Master Runner & AI Agent Implementation"
stage: green
date: "2026-03-13"
surface: agent
model: qwen/qwen3-coder
feature: none
branch: 001-platinum-tier-frontend
user: areeba_zafar
command: implement
labels: ["ai-agent", "watchers", "master-runner", "social-media"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - ai_agent.py
  - run_master.py
tests: []
---

## Prompt

Implement the following plan: AI Employee Master Agent + Unified Watcher Runner — create `run_master.py` (single entry point for all watchers + approval monitor) and `ai_agent.py` (interactive AI agent with Gemini/Grok for social media content generation and posting).

## Response

Created two files:

1. **`ai_agent.py`** — Interactive CLI agent with Gemini primary + Grok fallback AI content generation, natural language intent parsing (Urdu/English), platform-specific content rules, interactive approval flow, posting to Twitter (OAuth 1.0a), LinkedIn/Facebook/Instagram (MCP), and vault logging.

2. **`run_master.py`** — Unified master runner that starts all 5 Python watchers + MCP Odoo server as subprocesses, monitors Approved/ folder for auto-execution, auto-restarts crashed services, and provides graceful shutdown.

## Outcome

Both files compile successfully. Ready for testing with `python3 run_master.py` and `python3 ai_agent.py`.
