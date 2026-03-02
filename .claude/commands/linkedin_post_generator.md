# LinkedIn Post Generator

You are executing the **LinkedIn Post Generator** skill. Follow every step precisely.

## Step 1 — Read Context

Read these vault sources:

1. `AI-Employee-Vault/Company_Handbook.md` — extract business goals, mission statements, objectives, revenue signals
2. `AI-Employee-Vault/Dashboard.md` — extract any metrics or status signals
3. `AI-Employee-Vault/Done/*.md` (most recent 6 files by modification time, excluding `.meta.md`) — extract completed task titles and summaries

## Step 2 — Generate Post

Write exactly **one** LinkedIn post body with these rules:

**Structure:**
```
[Hook — 1 sentence, present tense energy, references the current month/period]

Here's what we shipped recently:

✅ [Most recent completed task title]
✅ [Second completed task title]
✅ [Third completed task title]

[Revenue or growth signal line — only if found in context, else omit]

[One mission/goal line — only if found in context, else omit]

[Soft CTA — invite connection or conversation, not a hard sell]
```

**Tone rules:**
- Confident but not boastful
- Specific wins, not vague buzzwords
- First person plural ("we shipped", "we onboarded")
- Soft CTA only ("let's connect", "happy to chat", "open to conversations")
- NO hard sell language ("DM me", "buy", "pricing", "offer")

**Hard limit:** ≤ 200 words. Count carefully. Trim at sentence boundary if over.

## Step 3 — Save Draft

Save the draft to: `AI-Employee-Vault/Social/LinkedIn_Draft_YYYY-MM-DD.md`

Use today's date in the filename. If the file already exists, append `_HHMMSS`.

**File format:**
```markdown
---
type: social_post
platform: LinkedIn
status: draft
requires_approval: true
generated_at: "<ISO8601 UTC>"
word_count: <N>
published: false
---

# LinkedIn Draft — YYYY-MM-DD

## Draft Post

---

<post body>

---

**Word count:** N / 200

## Approval Required

- [ ] Review post content and tone
- [ ] Edit if needed
- [ ] **Approve** → publish manually on LinkedIn
- [ ] **Reject** → delete or revise

## Context Sources

**Goals read from:** Company_Handbook.md
**Recent tasks read from:** `<filenames>`

> ⚠️ This draft was auto-generated. Do NOT publish without human review.
```

## Step 4 — Log Event

Log the action using `log_action("linkedin_draft_created", "<filename>", "words=<N> | requires_approval=true")`.

If `log_action` is unavailable, write a log entry to `AI-Employee-Vault/Logs/linkedin-post-YYYY-MM-DD.log`.

## Step 5 — Report

After completing, report:
- Draft filename
- Word count
- Top 3 tasks used as content
- Whether any revenue/goal context was found
- Full draft post text

## Hard Constraints

- **NEVER** publish to LinkedIn or any platform automatically
- **NEVER** access LinkedIn credentials or API
- **ALWAYS** set `requires_approval: true`
- **ALWAYS** set `published: false`
- **ALWAYS** keep post ≤ 200 words
- **ALWAYS** log the creation event

## Run with Python

```bash
PYTHONPATH=/tmp/gapi python3 .claude/skills/silver/linkedin_post_generator/assets/linkedin_post_generator.py
```
