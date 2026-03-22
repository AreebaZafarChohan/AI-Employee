---
id: "0008"
title: "Full WhatsApp Pipeline — Watcher Auto-Start + Real-Time Dashboard"
stage: green
date: 2026-03-18
surface: agent
model: qwen/qwen3-coder:free
feature: 001-platinum-tier-frontend
branch: 001-platinum-tier-frontend
user: areeba_zafar
command: implement
labels: ["whatsapp", "watcher", "backend", "pipeline", "real-time"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - src/watcher/whatsapp_watcher.py
  - backend/src/controllers/whatsapp.controller.ts
  - backend/src/services/whatsapp-watcher.service.ts
  - backend/src/index.ts
tests: []
---

## Prompt

Implement the following plan:

# Plan: Full WhatsApp Pipeline — Watcher Auto-Start + Real-Time Dashboard

## Context
The WhatsApp dashboard shows zero data because:
1. Python watcher defaults `DRY_RUN=true` — never writes files
2. Watcher only captures keyword-matching messages, not ALL unread
3. Watcher frontmatter uses `received`/`message`, but backend looks for `timestamp`/`status` — mismatch
4. Watcher is not started with the backend
5. Sent/approved messages don't save a Done file
6. `parseMarkdownMetadata` breaks on timestamps containing `:`

## Changes
1. Fix WhatsApp Watcher — Capture ALL unread messages
2. Fix Backend Metadata Parsing
3. New Watcher Service — Auto-start watcher with backend
4. Start Watcher on Backend Boot
5. Fix Approve Flow — Send reply + move to Done
6. Fix Send Flow — Save record to Done

## Response

Implemented all 6 changes across 4 files:

1. **`src/watcher/whatsapp_watcher.py`** — Changed DRY_RUN default to false, updated docstring
2. **`backend/src/controllers/whatsapp.controller.ts`** — Fixed parseMarkdownMetadata to split on first `:` only; mapped watcher fields (received→timestamp, sender→from); filtered only whatsapp-*.md files; fixed getStatus to count messages/ subdir; approveMessage sends reply via MCP then moves to Done; sendMessage writes outbound record to Done
3. **`backend/src/services/whatsapp-watcher.service.ts`** (NEW) — Spawns Python watcher as child process with auto-restart and exponential backoff
4. **`backend/src/index.ts`** — Starts watcher on boot, stops on SIGINT/SIGTERM

TypeScript compiles cleanly with no errors.
