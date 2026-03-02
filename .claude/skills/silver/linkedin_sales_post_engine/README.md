# LinkedIn Sales Post Engine

Automatically generates LinkedIn sales post drafts from your vault's business goals, revenue data, and completed tasks. Creates engaging posts (≤180 words) with CTAs for human review.

## Quick Start

```bash
# Generate post
python linkedin_sales_post_engine.py

# Preview mode (no file created)
DRY_RUN=true python linkedin_sales_post_engine.py
```

## What It Does

1. **Reads** business goals from Company_Handbook.md
2. **Extracts** revenue summary from Dashboard.md
3. **Scans** /Done folder for last 5 completed tasks
4. **Generates** engaging LinkedIn post:
   - Hook with emoji
   - Wins section (up to 3 tasks)
   - Revenue/metrics highlight
   - Business goal alignment
   - Call-to-action
   - Hashtags
5. **Enforces** 180 word limit
6. **Saves** to `/Pending_Approval/` for human review
7. **Logs** generation to `/Logs/`

## Output Example

```markdown
---
type: social_post
platform: linkedin
action: publish
requires_approval: true
risk_level: medium
generated_at: "2026-02-25T12:00:00Z"
word_count: 145
status: pending_approval
---

# LinkedIn Sales Post Draft

🚀 Exciting progress this week!

✅ 3 key wins this week:
   • Invoice Request Acme Corp
   • Daily Briefing Generated
   • Email Response Sent

📈 Business momentum continues...
   • Revenue: $2,500 project completed

🎯 Focused on: Deliver exceptional client value

💬 Let's connect if you're looking to drive similar results!

#BusinessGrowth #Success #Partnership #Innovation
```

## Configuration

| Env Var | Default | Description |
|---------|---------|-------------|
| `DRY_RUN` | `false` | Preview without writing |
| `LOG_LEVEL` | `INFO` | DEBUG/INFO/WARNING/ERROR |

## Schedule

Generate posts 2x per week (Tuesday & Thursday at 9 AM):

**macOS/Linux:**
```cron
0 9 * * 2,4 python linkedin_sales_post_engine.py
```

**Windows:**
```powershell
# Add to Task Scheduler
# Trigger: Tuesday & Thursday at 9:00 AM
# Action: python linkedin_sales_post_engine.py
```

## Files Generated

| File | Purpose |
|------|---------|
| `Pending_Approval/LINKEDIN_POST_YYYY-MM-DD.md` | Draft post |
| `Logs/linkedin-sales-post-YYYY-MM-DD.log` | Generation log |

## Approval Workflow

```
1. Post generated → /Pending_Approval/
2. Human reviews content
3. If approved → Move to /Approved/
4. Publish to LinkedIn (manual)
5. If rejected → Move to /Rejected/ with feedback
```

## Troubleshooting

### No post generated
```bash
# Check Python
python --version

# Install dependency
pip install pyyaml

# Run with debug logging
LOG_LEVEL=DEBUG python linkedin_sales_post_engine.py
```

### Post too generic
- Add goals to Company_Handbook.md
- Complete more tasks (saved to /Done)
- Update Dashboard with metrics

## Test

```bash
# Dry run
DRY_RUN=true python linkedin_sales_post_engine.py

# Check output
cat AI-Employee-Vault/Pending_Approval/LINKEDIN_POST_*.md | head -40
```
