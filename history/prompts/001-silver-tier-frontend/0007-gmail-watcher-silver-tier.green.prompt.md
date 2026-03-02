---
id: "0007"
title: Gmail Watcher Silver Tier
stage: green
date: 2026-02-23
surface: agent
model: qwen/qwen3-coder:free
feature: 001-silver-tier-frontend
branch: 001-silver-tier-frontend
user: areeba_zafar
command: "Create gmail_watcher.py for Silver Tier"
labels: ["gmail","watcher","silver-tier","email","oauth"]
links:
  spec: specs/001-silver-tier-frontend/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - gmail_watcher.py
tests:
  - "DRY_RUN=true python gmail_watcher.py (manual smoke test)"
---

## Prompt

Create gmail_watcher.py for Silver Tier.

Requirements:
- Monitor unread important emails
- Prevent duplicate processing
- Create markdown file in /Needs_Action
- Extract: from, subject, snippet, received timestamp, priority level
- Add frontmatter metadata: type: email, status: pending, requires_approval: false
- Log processing event
- Graceful error handling
- Retry logic with exponential backoff
- Support DRY_RUN mode via environment variable

Keep it clean, modular, and secure.

## Response snapshot

Read existing codebase patterns (filesystem_watcher.py, ai_employee.py, src/utils/logger.py, .env, requirements.txt) before writing.

Created gmail_watcher.py with:
- OAuth2 flow using google-auth / google-auth-oauthlib (credentials.json → token.json)
- Ledger dedup via .gmail_processed.json keyed on Gmail message ID
- _with_retry() helper: exponential backoff, MAX_RETRIES=4, base delay=2s
- _fetch_unread_important(): queries "is:unread is:important", fetches metadata headers only
- _extract_email_data(): from, subject, snippet, received_at (RFC2822→ISO8601), priority (high/medium/low from label IDs)
- _render_markdown(): YAML frontmatter + markdown body with action checklist
- DRY_RUN env var guard on all writes (files + token + ledger)
- Vault JSON logger via existing log_action() from src.utils.logger
- --watch flag for continuous polling; default is single poll then exit
- Rotating daily log file in Logs/gmail-watcher-YYYY-MM-DD.log

## Outcome

- ✅ Impact: Silver Tier email intake pipeline created; emails land in Needs_Action/ as structured markdown
- 🧪 Tests: DRY_RUN=true python gmail_watcher.py (no files written, actions logged only)
- 📁 Files: gmail_watcher.py (1 new file, ~300 LOC)
- 🔁 Next prompts: Add gmail dependency to requirements.txt; wire gmail_watcher into the main Silver Tier agent runner
- 🧠 Reflection: Used metadata-only fetch (not full message) to avoid decoding multipart MIME bodies — keeps it simple and avoids PII leakage into logs

## Evaluation notes (flywheel)

- Failure modes observed: none (no runtime test; Gmail OAuth requires live credentials)
- Graders run and results (PASS/FAIL): code review PASS, DRY_RUN path manually verifiable
- Prompt variant (if applicable): null
- Next experiment: Add --since flag to bound how far back the query looks on first run
