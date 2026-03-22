# MCP Instagram Server

MCP server for Instagram Graph API v18.0 integration.

## Features

- Publish posts (IMAGE, VIDEO, CAROUSEL)
- Publish stories
- Publish reels
- Get account insights
- Get recent media

## Configuration

Set the following environment variables:

```bash
INSTAGRAM_ACCESS_TOKEN=your_instagram_access_token
INSTAGRAM_BUSINESS_ACCOUNT_ID=your_instagram_business_account_id
INSTAGRAM_API_VERSION=v18.0
INSTAGRAM_TIMEOUT=30000
```

## Getting Instagram Credentials

1. Convert to Instagram Business or Creator account
2. Connect to Facebook Page
3. Go to [Facebook Developers](https://developers.facebook.com/)
4. Create app with Instagram Graph API
5. Generate token with permissions:
   - `instagram_basic`
   - `instagram_content_publish`
   - `instagram_manage_insights`
   - `pages_read_engagement`

## Installation

```bash
cd mcp/instagram-server
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
| `publish_instagram_post` | Publish a post (IMAGE/VIDEO/CAROUSEL) |
| `publish_instagram_story` | Publish a story |
| `publish_instagram_reel` | Publish a reel |
| `get_instagram_insights` | Get account insights |
| `get_instagram_media` | Get recent media |

## Example Tool Calls

### Publish Post

```json
{
  "tool": "publish_instagram_post",
  "params": {
    "caption": "Beautiful sunset today! 🌅",
    "media_url": "https://example.com/sunset.jpg",
    "media_type": "IMAGE"
  }
}
```

### Publish Story

```json
{
  "tool": "publish_instagram_story",
  "params": {
    "media_url": "https://example.com/story.jpg",
    "media_type": "IMAGE"
  }
}
```

### Publish Reel

```json
{
  "tool": "publish_instagram_reel",
  "params": {
    "caption": "Quick tutorial on AI! 🤖",
    "video_url": "https://example.com/reel.mp4"
  }
}
```

### Get Insights

```json
{
  "tool": "get_instagram_insights",
  "params": {
    "metrics": ["follower_count", "reach", "impressions"],
    "period": "week"
  }
}
```

### Get Recent Media

```json
{
  "tool": "get_instagram_media",
  "params": {
    "limit": 5
  }
}
```

## Media Requirements

| Type | Format | Max Size | Aspect Ratio |
|------|--------|----------|--------------|
| IMAGE | JPG, PNG | 8MB | 1.91:1 to 4:5 |
| VIDEO | MP4, MOV | 1GB | 9:16 to 16:9 |
| CAROUSEL | JPG, PNG | 8MB each | 1.91:1 to 4:5 |

## Testing

```bash
npm test
```
