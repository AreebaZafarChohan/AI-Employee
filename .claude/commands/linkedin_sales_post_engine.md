# LinkedIn Sales Post Engine

You are executing the **LinkedIn Sales Post Engine** skill. Follow every step precisely.

## Step 1 — Read Data Sources

### 1.1 Business Goals
Read `AI-Employee-Vault/Company_Handbook.md`:
- Extract sections with "Goal", "Objective", "Mission", or "Vision" in headers
- List all bullet points under these sections
- Maximum 5 goals

### 1.2 Revenue Summary
Read `AI-Employee-Vault/Dashboard.md`:
- Look for revenue, growth, sales, profit, income mentions
- Extract metrics (key: value pairs)
- Collect highlights (lines with financial keywords)

Also check `AI-Employee-Vault/Accounting/*.md` (if exists):
- Extract transaction amounts
- Note significant financial events

### 1.3 Completed Tasks
Read `AI-Employee-Vault/Done/*.md` files:
- Sort by modification time (most recent first)
- Take last 5 tasks
- Extract: title, metadata, body preview (200 chars)
- Skip daily_briefing type files

## Step 2 — Generate LinkedIn Post

### 2.1 Hook (1-2 lines)
Choose from:
```
🚀 Exciting progress this week!
💼 Another week, another milestone!
✨ Proud of what we've accomplished!
🎯 Driving results for our clients!
```
Select based on: `hooks[len(tasks) % len(hooks)]`

### 2.2 Wins Section
If tasks available:
```
✅ [X] key wins this week:
   • [Task 1 title (max 60 chars)]
   • [Task 2 title (max 60 chars)]
   • [Task 3 title (max 60 chars)]
```
Show up to 3 wins.

### 2.3 Revenue Section
If revenue data available:
```
📈 Business momentum continues...
   • [Metric 1 or highlight]
   • [Metric 2 if available]
```

### 2.4 Goals Alignment
If goals available:
```
🎯 Focused on: [First goal (max 70 chars)]
```

### 2.5 Call-to-Action
Choose from:
```
💬 Let's connect if you're looking to drive similar results!
📩 DM me to explore how we can help your business grow!
🤝 Open to partnerships and collaborations!
🔗 Reach out if you'd like to learn more!
```
Select based on: `ctas[len(goals) % len(ctas)]`

### 2.6 Hashtags
Always include:
```
#BusinessGrowth #Success #Partnership #Innovation
```

## Step 3 — Enforce Word Limit

Count words in generated post.

If > 180 words:
- Truncate to 180 words
- Try to end at sentence boundary (last period)
- Log warning about truncation

## Step 4 — Create Approval File

Create: `AI-Employee-Vault/Pending_Approval/LINKEDIN_POST_YYYY-MM-DD.md`

### Frontmatter
```yaml
---
type: social_post
platform: linkedin
action: publish
requires_approval: true
risk_level: medium
generated_at: "ISO-timestamp"
word_count: <number>
status: pending_approval
---
```

### Body
```markdown
# LinkedIn Sales Post Draft

**Platform:** LinkedIn
**Generated:** <timestamp>
**Word Count:** <count>
**Status:** Pending Approval

---

[Generated post content]

---

## Approval Required

⚠️ **Do NOT publish without human review**

This is an AI-generated draft. Please review for:
- Accuracy of claims and metrics
- Tone and brand alignment
- Appropriate timing
- CTA relevance

## Action Required
- [ ] Review post content
- [ ] Edit if needed
- [ ] **Approve** → Move to `/Approved` for publishing
- [ ] **Reject** → Move to `/Rejected` with feedback
```

## Step 5 — Log Generation

Append to `AI-Employee-Vault/Logs/linkedin-sales-post-YYYY-MM-DD.log`:

```json
{
  "timestamp": "ISO-timestamp",
  "filename": "LINKEDIN_POST_YYYYMMDD.md",
  "status": "success",
  "dry_run": false,
  "word_count": 145
}
```

## Output Validation

Before completing, verify:
- [ ] Post ≤ 180 words
- [ ] Contains hook/opener
- [ ] Contains wins section (if tasks available)
- [ ] Contains CTA
- [ ] Contains hashtags
- [ ] Frontmatter complete and valid
- [ ] File saved to Pending_Approval/
- [ ] Log entry created

## Safety Constraints

1. **Never auto-publish** — Always save to Pending_Approval/
2. **Always require approval** — requires_approval: true
3. **Enforce word limit** — Max 180 words
4. **Log all generations** — Audit trail required

## Usage Examples

```bash
# Generate post
python linkedin_sales_post_engine.py

# Preview only
DRY_RUN=true python linkedin_sales_post_engine.py

# Debug mode
LOG_LEVEL=DEBUG python linkedin_sales_post_engine.py
```

## Completion Report

After finishing, report:

```
LinkedIn Sales Post Generated
──────────────────────────────
File: Pending_Approval/LINKEDIN_POST_YYYY-MM-DD.md
Word Count: XXX
Status: Pending Approval
Log: linkedin-sales-post-YYYY-MM-DD.log
```
