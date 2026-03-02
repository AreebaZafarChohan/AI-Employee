---
id: "0018"
title: "WhatsApp Watcher Silver Tier"
stage: green
date: "2026-02-25"
surface: agent
model: qwen/qwen3-coder:free
feature: 001-silver-tier-frontend
branch: 001-silver-tier-frontend
user: areeba_zafar
command: "upgrade whatsapp_watcher.py to Silver Tier"
labels: ["whatsapp", "playwright", "silver-tier", "watcher", "needs_action"]
links:
  spec: "null"
  ticket: "null"
  adr: "null"
  pr: "null"
files:
  - whatsapp_watcher.py
tests: []
---

## Prompt

Upgrade whatsapp_watcher.py to Silver Tier level.

Requirements:
- Use Playwright persistent context
- Monitor unread chats
- Extract: sender name, full latest message, timestamp
- Trigger only if keywords: invoice, payment, urgent, project, proposal
- Save structured markdown to /Needs_Action

Frontmatter:
---
type: whatsapp
sender:
message:
received:
risk_level: auto-detect
requires_approval: false
---

Add:
- Exponential retry
- Session validation
- Graceful failure handling
- Logging

## Response

Created `whatsapp_watcher.py` from scratch at project root, following the same
structure and conventions as `gmail_watcher.py` (Silver Tier reference).

Key implementation details:
- **Playwright persistent context** launched from `WA_PROFILE_DIR` (.whatsapp_profile/)
  so the WhatsApp Web session survives across runs.
- **Session validation** via `_validate_session()`: checks for `div[aria-label="Chat list"]`
  before each poll cycle; re-navigates and reloads on failure.
- **QR login flow** handled by `_wait_for_qr_or_login()` on first run (headless=false).
- **Unread chat detection** via badge selectors; clicks each unread chat and extracts the
  last message bubble's text and timestamp.
- **Keyword filtering** — `_matches_keywords()` checks for invoice/payment/urgent/project/proposal.
- **Risk auto-detection** — urgent/payment → high; invoice/proposal → medium; project → low.
- **Exponential retry** — `_with_retry()` with MAX_RETRIES=4, base delay 2s, doubles each attempt.
- **YAML frontmatter** exactly matches spec: type, sender, message, received, risk_level, requires_approval.
- **Logging** to both stdout and `AI-Employee-Vault/Logs/whatsapp-watcher-{date}.log`.
- **DRY_RUN** env var support — skips file writes when set.
- `--watch` flag for continuous polling; single-shot by default.
- Uses `src.utils.logger.log_action` and `set_default_logs_dir` consistent with gmail_watcher.py.
