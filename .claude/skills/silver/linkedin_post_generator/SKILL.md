# LinkedIn Post Generator Skill

## Overview

**Skill Name:** `linkedin_post_generator`
**Domain:** `silver`
**Purpose:** Read vault context (Business_Goals, completed tasks, revenue highlights), generate one professional LinkedIn post draft (≤200 words, confident but not salesy, with soft CTA), save to `/Social/LinkedIn_Draft_YYYY-MM-DD.md`, and log the event. Never publishes automatically.

**Core Capabilities:**
- Context extraction from `Company_Handbook.md`, `Dashboard.md`, and `/Done`
- Goal/objective parsing from handbook prose
- Recent completed task summarization (up to 6 items)
- Revenue/growth signal extraction
- Structured post generation: hook → wins → growth signal → soft CTA
- Word count enforcement (≤200 words, sentence-boundary trimming)
- Draft file with YAML frontmatter, approval checklist, source attribution
- Action logging via `log_action()`

**When to Use:**
- Weekly or bi-weekly LinkedIn content creation
- After shipping a milestone, onboarding a client, or closing a deal
- Whenever the human wants a draft to review before posting
- As part of a content calendar automation

**When NOT to Use:**
- Publishing directly to LinkedIn (never — always requires human approval)
- When vault has no completed tasks or goals to reference
- For platform-specific formats other than LinkedIn (use separate skills)

## Impact Analysis

### Security Impact: LOW
- Read-only on vault source files
- Writes only to `/Social/` and `/Logs/`
- No network calls, no credentials accessed
- Draft marked `requires_approval: true` always

### System Impact: LOW
- Filesystem operations within vault only
- Idempotent: same-day collision handled by timestamp suffix

### Operational Impact: MEDIUM
- Output quality depends on richness of vault context
- Requires human review before publish — no autonomous social media activity

### Business Impact: HIGH
- Consistent professional presence on LinkedIn
- Reduces friction for content creation
- Full audit trail of generated drafts

## Environment Variables

```
VAULT_PATH=./AI-Employee-Vault    # Vault root (default: ./AI-Employee-Vault)
LINKEDIN_DRY_RUN=false            # Log only, no file writes
LINKEDIN_LOG_LEVEL=INFO           # DEBUG / INFO / WARNING / ERROR
```

## Context Sources

| Source | Data Extracted |
|---|---|
| `Company_Handbook.md` | Business goals, mission, objectives, revenue mentions |
| `Dashboard.md` | System status, active metrics |
| `/Done/*.md` (recent 6) | Completed task titles and summaries |
| `/Done` file mtimes | Recency ranking |

## Post Structure

```
[Hook — 1 sentence, present tense energy]

Here's what we shipped recently:

✅ [Completed task 1]
✅ [Completed task 2]
✅ [Completed task 3]

[Revenue / growth signal if available]

[Mission / goal signal]

[Soft CTA — invite connection, not a hard sell]
```

## Draft File Schema (`/Social/LinkedIn_Draft_YYYY-MM-DD.md`)

```markdown
---
type: social_post
platform: LinkedIn
status: draft
requires_approval: true
generated_at: "<ISO8601>"
word_count: <N>
published: false
---

# LinkedIn Draft — YYYY-MM-DD

## Draft Post

---

<post body ≤200 words>

---

**Word count:** N / 200

## Approval Required

- [ ] Review post content and tone
- [ ] Edit if needed
- [ ] **Approve** → publish manually on LinkedIn
- [ ] **Reject** → delete or revise

## Context Sources

**Goals read from:** Company_Handbook.md
**Recent tasks read from:** `file1.md`, `file2.md`, ...
**Revenue context:** ...

> ⚠️ This draft was auto-generated. Do NOT publish without human review.
```

## Tone Guidelines

| ✅ Do | ❌ Don't |
|---|---|
| Confident, grounded | Boastful or exaggerated |
| Specific wins | Vague buzzwords ("synergy", "disrupt") |
| Soft CTA ("let's connect") | Hard sell ("buy now", "DM for pricing") |
| First person plural ("we shipped") | Third person corporate ("the company delivered") |
| Under 200 words | Long-form thought leadership |

## Blueprints

### Blueprint 1: Run the Generator

```bash
PYTHONPATH=/tmp/gapi python3 \
  .claude/skills/silver/linkedin_post_generator/assets/linkedin_post_generator.py
```

### Blueprint 2: Dry Run (no file writes)

```bash
LINKEDIN_DRY_RUN=true python3 \
  .claude/skills/silver/linkedin_post_generator/assets/linkedin_post_generator.py
```

### Blueprint 3: Debug Context Extraction

```bash
LINKEDIN_LOG_LEVEL=DEBUG python3 \
  .claude/skills/silver/linkedin_post_generator/assets/linkedin_post_generator.py
```

## Execution Checklist

Before running:
- [ ] `Company_Handbook.md` exists in vault root
- [ ] `/Done` has at least some completed task files
- [ ] `/Social` directory exists (auto-created if missing)

After running:
- [ ] `/Social/LinkedIn_Draft_YYYY-MM-DD.md` exists
- [ ] `requires_approval: true` present in frontmatter
- [ ] `published: false` present in frontmatter
- [ ] Word count ≤ 200
- [ ] Action logged in `/Logs/linkedin-post-YYYY-MM-DD.log`

## Error Handling

| Situation | Behavior |
|---|---|
| `Company_Handbook.md` missing | Generate post with available context only |
| `/Done` is empty | Use hook-only post with goal/mission focus |
| No revenue signals found | Omit revenue line from post |
| Same-day file collision | Append `_HHMMSS` timestamp suffix |
| Write failure | Log error, print draft to stdout |

## Security Constraints

- **NEVER** post to LinkedIn or any social platform automatically
- **NEVER** access LinkedIn credentials or API tokens
- **ALWAYS** set `requires_approval: true` in frontmatter
- **ALWAYS** set `published: false` in frontmatter
- **ALWAYS** log the draft creation event
