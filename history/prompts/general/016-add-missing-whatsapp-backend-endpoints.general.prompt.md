---
id: "016"
title: "Add Missing WhatsApp Backend Endpoints"
stage: general
date: 2026-03-18
surface: agent
model: qwen/qwen3-coder:free
feature: none
branch: 001-platinum-tier-frontend
user: areeba_zafar
command: implement
labels: ["whatsapp", "backend", "endpoints", "bugfix"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - backend/src/controllers/whatsapp.controller.ts
  - backend/src/routes/whatsapp.routes.ts
  - frontend/src/lib/api.ts
  - frontend/src/app/whatsapp/page.tsx
tests: []
---

## Prompt

Fix WhatsApp dashboard showing zero data. Backend only had 3 endpoints (GET /messages, POST /send, GET /status) but frontend calls 7. Add missing endpoints and fix frontend type exports.

## Response

Added 4 missing backend endpoints:
- `GET /whatsapp/pending` — returns pending messages
- `GET /whatsapp/contacts` — extracts contacts from message senders
- `POST /whatsapp/approve` — moves message to Done/
- `POST /whatsapp/reject` — moves message to Rejected/

Added `WhatsAppMessage` and `WhatsAppContact` type exports to `frontend/src/lib/api.ts`.
Fixed response parsing in `loadMessages()` on the WhatsApp page.

Root cause of zero data: `Needs_Action/messages/` directory is empty — watcher hasn't written files.

## Outcome

Backend now implements all endpoints the frontend expects. 404 errors eliminated. Data will appear when watcher writes message files.
