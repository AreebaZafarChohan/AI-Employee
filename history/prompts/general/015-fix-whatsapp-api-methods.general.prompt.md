---
id: "015"
title: "Fix WhatsApp API Methods"
stage: general
date: 2026-03-18
surface: agent
model: qwen/qwen3-coder:free
feature: none
branch: 001-platinum-tier-frontend
user: areeba_zafar
command: implement plan
labels: ["whatsapp", "api-client", "bugfix"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - frontend/src/lib/api.ts
tests: []
---

## Prompt

Implement the following plan: Fix WhatsApp Integration Gaps — Add missing `approveMessage` and `rejectMessage` to API client in `frontend/src/lib/api.ts`.

## Response

Added two missing methods to `whatsappApi` in `frontend/src/lib/api.ts`:
- `approveMessage(message_id, reply_content?)` → POST `/whatsapp/approve`
- `rejectMessage(message_id, reason?)` → POST `/whatsapp/reject`

These match the existing calls in `frontend/src/app/whatsapp/page.tsx` (lines 142, 158) that would have caused runtime errors.

## Outcome

Fix applied. Frontend WhatsApp page approve/reject handlers now have matching API client methods.
