---
ID: 2
TITLE: Instructions to run backend and frontend
STAGE: explainer
DATE_ISO: 2026-03-08
SURFACE: agent
MODEL: gemini-2.0-flash
FEATURE: documentation
BRANCH: main
USER: G S COMPUTER
COMMAND: ok frontend run k se hoga or backend commands btao taa k mee run krlu isko
LABELS: ["instructions", "setup", "run"]
LINKS:
  SPEC: null
  TICKET: null
  ADR: null
  PR: null
FILES_YAML:
  - backend/package.json
  - frontend/package.json
TESTS_YAML: null
PROMPT_TEXT: "ok frontend run k se hoga or backend commands btao taa k mee run krlu isko"
RESPONSE_TEXT: "Backend aur Frontend ko run karne ke liye aap ye commands follow karein: [Instructions for npm run dev in both directories]."
OUTCOME: "User has clear instructions on how to start the development environment for both backend and frontend."
---

# Prompt History Record: Run Instructions

The user asked for the specific commands to run the backend and frontend parts of the application.

## Accomplishments
- Inspected `package.json` in both `backend` and `frontend` to confirm scripts.
- Provided clear, step-by-step instructions for `npm install` and `npm run dev`.
- Added reminders about environment variables and Prisma generation.
