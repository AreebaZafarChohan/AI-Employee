# Skill: engagement_summary

Fetch and summarize engagement metrics across all social platforms.

## Trigger
When the user asks about social media performance, engagement, analytics, or metrics.

## Workflow

1. **Call summarize tools** for each configured platform:
   - `fb_summarize_engagement`
   - `ig_summarize_engagement`
   - `tw_summarize_engagement`
   - `li_summarize_engagement`
2. **Aggregate results** into a cross-platform summary:
   - Total engagement (likes + comments + shares + retweets)
   - Per-platform breakdown
   - Top performing posts
   - Engagement rate trends
3. **Save to vault** at `/Social/Analytics/`
4. **Present** formatted summary to user

## Output Format

```
## Social Media Engagement Summary
**Period**: Last 7 days

| Platform   | Posts | Likes | Comments | Shares | Eng. Rate |
|------------|-------|-------|----------|--------|-----------|
| Facebook   | 5     | 120   | 35       | 18     | 3.2%      |
| Instagram  | 3     | 450   | 28       | -      | 4.1%      |
| Twitter    | 12    | 89    | 15       | 42     | 2.8%      |
| LinkedIn   | 2     | 67    | 12       | 8      | 5.1%      |
| **Total**  | 22    | 726   | 90       | 68     | 3.5%      |

### Top Posts
1. [Instagram] "New product launch..." — 180 likes, 12 comments
2. [LinkedIn] "Industry insights..." — 45 likes, 8 comments
```

## Rules
- Gracefully handle platforms that fail (show as "N/A")
- Always save analytics to vault
- Compare with previous period if available
