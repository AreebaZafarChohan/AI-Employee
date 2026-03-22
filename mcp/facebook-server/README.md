# MCP Facebook Server

MCP server for Facebook Graph API v18.0 integration.

## Features

- Publish posts to Facebook Page
- Schedule posts for later
- Get page information
- Get page insights/analytics
- Reply to comments

## Configuration

Set the following environment variables:

```bash
FACEBOOK_ACCESS_TOKEN=your_facebook_access_token
FACEBOOK_PAGE_ID=your_facebook_page_id
FACEBOOK_API_VERSION=v18.0
FACEBOOK_TIMEOUT=30000
```

## Getting Facebook Access Token

1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Create a new app or select existing
3. Add Facebook Login product
4. Generate Page Access Token with permissions:
   - `pages_manage_posts`
   - `pages_read_engagement`
   - `pages_read_user_content`
   - `publish_to_groups`

## Installation

```bash
cd mcp/facebook-server
npm install
```

## Usage

```bash
# Start server
npm start

# Development mode
npm run dev
```

## Available Tools

| Tool | Description |
|------|-------------|
| `publish_facebook_post` | Publish a post to Facebook Page |
| `schedule_facebook_post` | Schedule a post for later |
| `get_facebook_page_info` | Get page information |
| `get_facebook_insights` | Get page analytics |
| `reply_facebook_comment` | Reply to a comment |

## Example Tool Calls

### Publish Post

```json
{
  "tool": "publish_facebook_post",
  "params": {
    "content": "Exciting news! Check out our latest product launch.",
    "link": "https://example.com/product",
    "photo": "https://example.com/image.jpg"
  }
}
```

### Schedule Post

```json
{
  "tool": "schedule_facebook_post",
  "params": {
    "content": "Happy Monday! Start your week with positivity.",
    "scheduled_at": "2026-03-10T09:00:00Z"
  }
}
```

### Get Insights

```json
{
  "tool": "get_facebook_insights",
  "params": {
    "metrics": ["page_impressions", "page_engagements"],
    "since": "2026-03-01",
    "until": "2026-03-31"
  }
}
```

### Reply to Comment

```json
{
  "tool": "reply_facebook_comment",
  "params": {
    "comment_id": "123456789_987654321",
    "message": "Thank you for your feedback!"
  }
}
```

## Testing

```bash
npm test
```
