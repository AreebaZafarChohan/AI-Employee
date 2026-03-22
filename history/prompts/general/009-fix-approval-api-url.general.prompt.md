---
ID: 9
TITLE: Fixed incorrect API URL in approval store
STAGE: red
DATE_ISO: 2026-03-08
SURFACE: agent
MODEL: gemini-2.0-flash
FEATURE: connectivity
BRANCH: main
USER: G S COMPUTER
COMMAND: "Unhandled Runtime Error Error: Failed to approve item"
LABELS: ["bug-fix", "api", "404", "refactor"]
LINKS:
  SPEC: null
  TICKET: null
  ADR: null
  PR: null
FILES_YAML:
  - frontend/src/store/approval-store.ts
TESTS_YAML:
  - Approval action verification
PROMPT_TEXT: "[Error log showing Failed to approve item in approval-store.ts]"
RESPONSE_TEXT: "I've refactored approval-store.ts to use standardized API helpers, fixing the double /api/v1 URL issue."
OUTCOME: "Approval actions now correctly target the backend API endpoints without path duplication."
---

# Prompt History Record: Approval URL Fix

The user encountered a failure when clicking the 'Approve' button.

## Accomplishments
- Identified that manual URL construction in `approval-store.ts` was doubling the `/api/v1` prefix.
- Refactored the store to use `approveFile`, `rejectFile`, and other helpers from `lib/vault-api.ts`.
- Standardized the data fetching logic to ensure consistency across the dashboard.
