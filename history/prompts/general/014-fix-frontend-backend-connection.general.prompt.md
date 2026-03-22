---
id: 014
title: Fix Frontend-Backend Connection
stage: general
date: 2026-03-16
surface: agent
model: qwen/qwen3-coder:free
feature: none
branch: 001-platinum-tier-frontend
user: areeba_zafar
command: implement plan
labels: ["frontend", "backend", "connection", "port-fix", "proxy"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - frontend/.env.local
  - frontend/.env.example
  - frontend/src/lib/api-config.ts
  - frontend/src/lib/axios-client.ts
  - frontend/src/services/api-service.ts
  - frontend/src/lib/websocket-client.ts
  - frontend/next.config.js
tests:
  - Manual verification: start backend on port 3000, start frontend, confirm API calls succeed
---

## Prompt

Implement the following plan:

# Plan: Fix Frontend-Backend Connection

## Context
Frontend and backend are not connected. The root cause is a port mismatch:
- Frontend expects backend at http://localhost:8000/api/v1
- Backend Express server runs on port 3000

## Approach: Next.js Proxy Rewrites + Port Fix
Update all hardcoded port 8000 references to 3000 and add Next.js rewrites for dev proxy.

## Response snapshot

Applied all 7 changes from the plan:
1. Updated `frontend/.env.local` — port 8000→3000 for API and WS URLs
2. Updated `frontend/.env.example` — port 8000→3000 for API and WS URLs
3. Updated `frontend/src/lib/api-config.ts` — fallback default 8000→3000
4. Updated `frontend/src/lib/axios-client.ts` — fallback default 8000→3000
5. Updated `frontend/src/services/api-service.ts` — fallback default 8000→3000
6. Updated `frontend/src/lib/websocket-client.ts` — fallback default 8000→3000
7. Added Next.js rewrites in `frontend/next.config.js` to proxy `/api/*` to backend on port 3000

Step 8 (CORS) required no changes — backend already has `CORS_ORIGIN="*"`.

## Outcome

- ✅ Impact: Frontend can now reach backend APIs on port 3000; dev proxy avoids CORS issues
- 🧪 Tests: Manual — start both servers and verify API calls in Network tab
- 📁 Files: 7 files modified
- 🔁 Next prompts: Verify end-to-end with both servers running
- 🧠 Reflection: Simple port mismatch fix; proxy rewrites add resilience for dev

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
