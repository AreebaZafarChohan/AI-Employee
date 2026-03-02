# LinkedIn Post Generator

Generates a professional LinkedIn draft from your vault's Business_Goals, recent completed tasks, and revenue highlights. Saves to `/Social/` for human review. Never publishes automatically.

## Quick Start

```bash
# Generate draft
PYTHONPATH=/tmp/gapi python3 .claude/skills/silver/linkedin_post_generator/assets/linkedin_post_generator.py

# Dry run (no files written)
LINKEDIN_DRY_RUN=true python3 .claude/skills/silver/linkedin_post_generator/assets/linkedin_post_generator.py
```

## Output

- `/Social/LinkedIn_Draft_YYYY-MM-DD.md` — draft with approval checklist
- `/Logs/linkedin-post-YYYY-MM-DD.log` — action log

## Constraints

- Max 200 words
- `requires_approval: true` always set
- `published: false` always set
- Never publishes to LinkedIn automatically
