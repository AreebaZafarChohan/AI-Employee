# LinkedIn Sales Post Engine Skill

## Overview

**Skill Name:** `linkedin_sales_post_engine`
**Domain:** `silver`
**Purpose:** Read vault context (Business_Goals, revenue summary, completed tasks), generate one engaging LinkedIn sales post draft (≤180 words, business value focused, with CTA), save to `/Pending_Approval/` for human review. Never auto-publishes.

**Core Capabilities:**
- Context extraction from Company_Handbook.md, Dashboard.md, and /Done
- Sales-focused post generation
- Word count enforcement (max 180)
- Approval routing (always requires_approval: true)
- Draft management in Pending_Approval/

## When to Use

- Weekly LinkedIn content generation
- Sharing business milestones
- Promoting completed work
- Driving engagement and leads

## When NOT to Use

- Publishing directly to LinkedIn (requires human review)
- Personal/non-business posts
- Sensitive company announcements (use PR workflow)

## Data Sources

### 1. Business Goals
**Source:** `Company_Handbook.md`

Extracts:
- Mission/vision statements
- Strategic objectives
- Active goals from "## Goals" or "## Objectives" sections
- Maximum 5 goals

### 2. Revenue Summary
**Source:** `Dashboard.md` and `/Accounting/*.md`

Extracts:
- Revenue mentions
- Growth metrics
- Financial highlights
- Transaction amounts

### 3. Completed Tasks
**Source:** `/Done/*.md` (last 5)

Extracts:
- Task titles
- Completion context
- Key achievements

## Post Structure

```
[Hook emoji + engaging opener]

✅ [X] key wins this week:
   • [Win 1]
   • [Win 2]
   • [Win 3]

📈 Business momentum continues...
   • [Revenue/metric highlight]

🎯 Focused on: [Top business goal]

[Call-to-action]

#BusinessGrowth #Success #Partnership #Innovation
```

## Constraints

| Constraint | Limit | Enforcement |
|------------|-------|-------------|
| **Word Count** | Max 180 words | Truncate with sentence boundary |
| **Approval** | Always required | requires_approval: true |
| **Risk Level** | Medium | Social media exposure |
| **Auto-publish** | Never | Draft only |

## Frontmatter Schema

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

## Output Format

**Location:** `/Pending_Approval/LINKEDIN_POST_YYYY-MM-DD.md`

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

**Platform:** LinkedIn
**Generated:** 2026-02-25T12:00:00Z
**Word Count:** 145
**Status:** Pending Approval

---

🚀 Exciting progress this week!

✅ 3 key wins this week:
   • Email No Subject 576F57Dd
   • Onboard New Client Acme Corp
   • Follow Up Invoice

📈 Business momentum continues...
   • Revenue: Growing

🎯 Focused on: Deliver exceptional client value

💬 Let's connect if you're looking to drive similar results!

#BusinessGrowth #Success #Partnership #Innovation

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

## Generation Logic

### Hook Selection
```python
hooks = [
    "🚀 Exciting progress this week!",
    "💼 Another week, another milestone!",
    "✨ Proud of what we've accomplished!",
    "🎯 Driving results for our clients!",
]
# Select based on task count modulo
hook = hooks[len(tasks) % len(hooks)]
```

### Wins Section
- Show up to 3 completed tasks
- Format as bullet points
- Truncate titles to 60 chars

### Revenue Section
- Display metrics from Dashboard if available
- Fall back to revenue highlights
- Truncate to 80 chars

### CTA Selection
```python
ctas = [
    "💬 Let's connect if you're looking to drive similar results!",
    "📩 DM me to explore how we can help your business grow!",
    "🤝 Open to partnerships and collaborations!",
    "🔗 Reach out if you'd like to learn more!",
]
# Select based on goal count modulo
```

### Word Count Enforcement
```python
if count_words(post) > 180:
    post = truncate_to_word_limit(post, 180)
    # Tries to end at sentence boundary
```

## Configuration

| Env Var | Default | Description |
|---------|---------|-------------|
| `VAULT_PATH` | `./AI-Employee-Vault` | Path to vault |
| `DRY_RUN` | `false` | Preview mode |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `MAX_POST_WORDS` | `180` | Word limit |

## Usage

```bash
# Generate post
python linkedin_sales_post_engine.py

# Preview mode
DRY_RUN=true python linkedin_sales_post_engine.py

# Debug mode
LOG_LEVEL=DEBUG python linkedin_sales_post_engine.py
```

## Approval Workflow

```
/Pending_Approval/LINKEDIN_POST_*.md
         │
         │ Human Review
         │
    ┌────┴────┐
    │         │
    ↓         ↓
/Approved  /Rejected
    │
    │ (Ready to publish)
    ↓
LinkedIn (manual)
```

## Logging

**Location:** `Logs/linkedin-sales-post-YYYY-MM-DD.log`

**Entry Format:**
```json
{
  "timestamp": "2026-02-25T12:00:00Z",
  "filename": "LINKEDIN_POST_20260225.md",
  "status": "success",
  "dry_run": false,
  "word_count": 145
}
```

## Quality Checks

### Content Validation
- [ ] Post ≤ 180 words
- [ ] Contains hook/opener
- [ ] Contains wins section (if tasks available)
- [ ] Contains CTA
- [ ] Contains hashtags
- [ ] Frontmatter complete

### File Validation
- [ ] Saved to Pending_Approval/
- [ ] requires_approval: true
- [ ] risk_level: medium
- [ ] Log entry created

## Examples

### Example 1: Task-Focused Post

```
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

### Example 2: Revenue-Focused Post

```
💼 Another week, another milestone!

✅ 2 key wins this week:
   • Client Onboarding Complete
   • Contract Signed

📈 Business momentum continues...
   • Growth: 25% QoQ
   • New partnership announced

🎯 Focused on: Scale operations sustainably

🤝 Open to partnerships and collaborations!

#BusinessGrowth #Success #Partnership #Innovation
```

## Troubleshooting

### No Goals Found
- Check Company_Handbook.md exists
- Verify "## Goals" or "## Objectives" section present
- Ensure bullet points under goals section

### No Tasks Found
- Check /Done folder has recent files
- Verify files are markdown (.md)
- Ensure files have valid frontmatter

### Post Too Generic
- Add more specific business goals to Company_Handbook
- Complete more tasks to show in wins section
- Update Dashboard with revenue metrics

## Best Practices

1. **Review before approval:**
   - Verify all claims are accurate
   - Check tone matches brand voice
   - Ensure CTA is appropriate

2. **Timing:**
   - Generate posts mid-week (Tue-Thu)
   - Avoid weekends/holidays

3. **Frequency:**
   - 2-3 posts per week maximum
   - Vary content types (wins, insights, announcements)

4. **Engagement:**
   - Respond to comments within 24h
   - Tag relevant partners/clients (with permission)

## Future Enhancements

1. **Image Suggestions** — Recommend relevant images/carousels
2. **Posting Schedule** — Optimal time suggestions
3. **Engagement Tracking** — Monitor post performance
4. **A/B Testing** — Generate multiple variants
5. **LinkedIn API** — Direct publishing (with approval)
