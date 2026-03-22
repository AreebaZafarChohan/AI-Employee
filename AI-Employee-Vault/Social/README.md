# Social Media Management

This folder contains all social media automation files for Facebook, Instagram, Twitter, and LinkedIn.

## Folder Structure

```
Social/
├── Templates/           # Content templates for each platform
├── Drafts/
│   ├── linkedin/        # LinkedIn post drafts
│   ├── facebook/        # Facebook post drafts
│   ├── instagram/       # Instagram post drafts
│   └── twitter/         # Twitter tweet drafts
├── Scheduled/
│   ├── linkedin/        # Scheduled LinkedIn posts
│   ├── facebook/        # Scheduled Facebook posts
│   ├── instagram/       # Scheduled Instagram posts
│   └── twitter/         # Scheduled tweets
├── Published/
│   ├── linkedin/        # Published LinkedIn posts
│   ├── facebook/        # Published Facebook posts
│   ├── instagram/       # Published Instagram posts
│   └── twitter/         # Published tweets
└── Analytics/
    ├── linkedin-analytics.md
    ├── facebook-insights.md
    ├── instagram-insights.md
    └── twitter-analytics.md
```

## Supported Platforms

| Platform | MCP Server | Content Types |
|----------|------------|---------------|
| LinkedIn | linkedin-server | Posts, Articles |
| Facebook | facebook-server | Posts, Photos |
| Instagram | instagram-server | Posts, Stories, Reels |
| Twitter | twitter-server | Tweets, Threads |

## Content Generation

AI-generated content is created using the `content_generator` skill and stored in `Drafts/` for review.

### Approval Workflow

1. Content generated → `Drafts/{platform}/`
2. Human review → Move to `Scheduled/{platform}/`
3. Published → Move to `Published/{platform}/`

## File Naming Convention

```
{platform}-{type}-{date}-{id}.md

Examples:
- linkedin-draft-2026-03-06-001.md
- twitter-scheduled-2026-03-10-001.md
- instagram-published-2026-03-05-003.md
```

## Configuration

Set the following environment variables in `.env`:

```bash
# Facebook
FACEBOOK_ACCESS_TOKEN=
FACEBOOK_PAGE_ID=

# Instagram
INSTAGRAM_ACCESS_TOKEN=
INSTAGRAM_BUSINESS_ACCOUNT_ID=

# Twitter
TWITTER_BEARER_TOKEN=
TWITTER_API_KEY=
TWITTER_API_SECRET=
```

## Related Files

- `social_watcher.py` - Monitors social media for engagement
- `mcp/facebook-server/`, `mcp/instagram-server/`, `mcp/twitter-server/`
- `.claude/skills/gold/social_media_automation/` - Social media skills
