---
id: "0009"
title: "LinkedIn Post Generator Agent Skill"
stage: green
date: "2026-02-25"
surface: agent
model: qwen/qwen3-coder:free
feature: 001-silver-tier-frontend
branch: 001-silver-tier-frontend
user: areeba_zafar
command: "Create Agent Skill: linkedin_post_generator.md"
labels: ["silver-tier", "skill", "linkedin", "social", "content-generation", "draft"]
links:
  spec: "null"
  ticket: "null"
  adr: "null"
  pr: "null"
files:
  - .claude/skills/silver/linkedin_post_generator/SKILL.md
  - .claude/skills/silver/linkedin_post_generator/MANIFEST.md
  - .claude/skills/silver/linkedin_post_generator/README.md
  - .claude/skills/silver/linkedin_post_generator/assets/linkedin_post_generator.py
  - .claude/commands/linkedin_post_generator.md
  - AI-Employee-Vault/Social/LinkedIn_Draft_2026-02-24.md
tests:
  - Ran generator against vault with 6 completed tasks
  - Draft saved to Social/LinkedIn_Draft_2026-02-24.md
  - requires_approval=true confirmed in frontmatter
  - published=false confirmed in frontmatter
  - Word count 36/200 (low due to minimal vault context)
  - Log entry created in Logs/linkedin-post-2026-02-24.log
---

# Prompt

Create Agent Skill: linkedin_post_generator.md

Behavior:
1. Read: Business_Goals.md, Recent completed tasks, Revenue highlights
2. Generate: 1 professional LinkedIn post, Tone: confident but not salesy, Max 200 words, Include soft CTA
3. Save draft to: /Social/LinkedIn_Draft_YYYY-MM-DD.md
4. Mark as requires_approval: true
5. Log event

Do not publish automatically.

# Response

Created the `linkedin_post_generator` skill with the following components:

## Files Created

- **SKILL.md** — Full spec: context sources, post structure, tone guidelines, draft schema, blueprints, error handling, security constraints
- **MANIFEST.md** — Skill overview and integration points
- **README.md** — Quick start guide
- **assets/linkedin_post_generator.py** — Python generator (~200 LOC)
- **commands/linkedin_post_generator.md** — Claude command for `/linkedin_post_generator`

## Context Sources

| Source | Extracted |
|---|---|
| `Company_Handbook.md` | Goals, mission, revenue signals |
| `Dashboard.md` | Metrics and status |
| `/Done/*.md` (recent 6) | Completed task titles and summaries |

## Post Structure

```
[Hook] → [Completed wins ✅ x3] → [Revenue signal] → [Goal line] → [Soft CTA]
```

## Test Output

```
Big things happening this February 2026.

Here's what we shipped recently:

✅ Email: (no subject)
✅ Email: (no subject)
✅ Writing Task

If you're building something meaningful and need a team that executes — let's connect.
```

Draft saved: `Social/LinkedIn_Draft_2026-02-24.md`
Frontmatter: `requires_approval: true`, `published: false`, `word_count: 36`
