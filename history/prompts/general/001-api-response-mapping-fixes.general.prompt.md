---
id: 1
title: "Fix API Response Mismatches Between Backend and Frontend"
stage: "general"
date_iso: "2026-02-26T00:00:00Z"
surface: "agent"
model: "qwen3-coder:free"
feature: "none"
branch: "main"
user: "areeba_zafar"
command: "npx qwen-code"
labels: ["api", "backend", "frontend", "type-mapping", "silver-tier"]
links:
  spec: "null"
  ticket: "null"
  adr: "null"
  pr: "null"
files_yaml: |
  - backend/src/controllers/task.controller.ts
  - backend/src/controllers/plan.controller.ts
  - backend/src/controllers/system.controller.ts
  - backend/src/controllers/activity.controller.ts
  - backend/src/routes/activity.routes.ts
  - backend/.env.example
  - frontend/src/lib/api-client.ts
  - frontend/src/hooks/use-activity-log.ts
  - frontend/src/types/activity.ts
  - frontend/src/components/dashboard/activity-feed.tsx
  - whatsapp_watcher.py
tests_yaml: |
  - npm run build (backend) - passed
  - npx tsc --noEmit (frontend) - passed (excluding .next types)
prompt_text: |
  Investigate and fix why WhatsApp messages aren't showing in the frontend activity feed.
  The user reported that the activity feed shows other events but not WhatsApp messages.

response_text: |
  Found and fixed 7 API response mismatches between backend and frontend:

  1. Endpoint mismatch: Frontend called /activity but backend serves /activity-logs
  2. Response envelope: Backend returns { data: [...], meta: {...} } but frontend hooks expected raw arrays
  3. Field naming: Backend uses type/description, frontend expected eventType/message
  4. Event type values: Backend uses dot-notation (task.created), frontend expected underscores (task_created)
  5. Missing event types: ActivityEventType lacked WhatsApp/email types
  6. WhatsApp watcher never posted to backend - only wrote vault files
  7. Backend lacked POST /activity-logs endpoint

  Fixes applied:
  - frontend/src/lib/api-client.ts: Auto-unwraps { data } envelope for all hooks
  - frontend/src/hooks/use-activity-log.ts: Fixed endpoint, added field mapping
  - frontend/src/types/activity.ts: Added WhatsApp/email event types
  - frontend/src/components/dashboard/activity-feed.tsx: Added icons for new event types
  - backend/src/controllers/*.ts: Added mappers for PascalCase → kebab-case conversion
  - backend/src/routes/activity.routes.ts: Added POST endpoint
  - backend/src/controllers/activity.controller.ts: Added createActivityLog handler
  - whatsapp_watcher.py: Added _notify_backend_activity() to POST events to backend
  - .env.example: Added BACKEND_API_URL config

outcome: |
  All API response mismatches resolved. Backend now properly maps status values to frontend format.
  WhatsApp watcher will now POST activity events to backend when messages are sent/received.
  Frontend activity feed will display WhatsApp and email events with proper icons.

evaluation: |
  Success criteria:
  - [x] Backend builds without TypeScript errors
  - [x] All controllers map PascalCase status/state to kebab-case for frontend
  - [x] API client auto-unwraps { data } envelope
  - [x] Activity feed has WhatsApp/email event types with icons
  - [x] WhatsApp watcher posts to backend after writing vault files
  - [x] Backend has POST /activity-logs endpoint

  Next steps:
  - Restart backend and frontend to apply changes
  - Run WhatsApp watcher and verify messages appear in activity feed
---
