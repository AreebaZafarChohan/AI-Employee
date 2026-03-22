# Skill: weekly_marketing_report

Generate a comprehensive weekly marketing report across all social platforms.

## Trigger
When the user asks for a weekly report, marketing summary, or social media recap.

## Workflow

1. **Gather data** from all platforms via `*_summarize_engagement` tools
2. **Read vault files**:
   - `/Social/Posted/` — count posts per platform this week
   - `/Social/Queue/` — pending scheduled posts
   - `/Social/Analytics/` — previous reports for comparison
3. **Generate report** with:

### Report Sections

#### Executive Summary
- Total posts published this week
- Total engagement across platforms
- Week-over-week trend (up/down)
- Best performing platform

#### Platform Breakdown
For each platform:
- Posts published
- Total reach/impressions
- Engagement metrics (likes, comments, shares)
- Top post with metrics
- Audience growth

#### Content Performance
- Best performing content type
- Best posting times
- Hashtag performance
- Content themes that resonated

#### Recommendations
- Suggested posting frequency adjustments
- Content type recommendations
- Platform-specific optimization tips
- Upcoming content calendar suggestions

#### Queue Status
- Posts scheduled for next week
- Drafts awaiting approval
- Content gaps to fill

4. **Save report** to `/Social/Analytics/weekly-report-YYYY-MM-DD.md`
5. **Present** to user

## Rules
- Compare metrics with previous week when available
- Flag significant changes (>20% up or down)
- Be actionable in recommendations
- Save to vault for historical tracking
