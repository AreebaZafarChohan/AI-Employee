# @ai-employee/mcp-linkedin-server

MCP server exposing LinkedIn automation tools via Playwright for Claude and MCP-compatible AI assistants.

## Tools Exposed

| Tool | Description |
|------|-------------|
| `publish_post` | Publish a post to LinkedIn |
| `schedule_post` | Schedule a post for later publishing |
| `reply_to_comment` | Reply to a comment on a LinkedIn post |

## Features

- ✅ **Playwright-based** — Headless browser automation
- ✅ **Persistent Sessions** — Reuse login sessions
- ✅ **DRY_RUN Mode** — Test without posting
- ✅ **Rate Limiting** — Max 3 posts/day (configurable)
- ✅ **Zod Validation** — Input validation on all tools
- ✅ **Comprehensive Logging** — JSON logs with timestamps
- ✅ **Error Handling** — Graceful error recovery

---

## Quick Start

### 1. Install Dependencies

```bash
cd mcp/linkedin-server
npm install
```

### 2. Configure Credentials

```bash
cp .env.example .env
```

Edit `.env`:
```env
LINKEDIN_EMAIL=your.email@example.com
LINKEDIN_PASSWORD=your_password
DRY_RUN=true
LOG_LEVEL=INFO
RATE_LIMIT_POSTS=3
```

### 3. Test with DRY_RUN

```bash
DRY_RUN=true npm start
```

### 4. Add to Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ai-employee-linkedin": {
      "command": "node",
      "args": ["path/to/mcp/linkedin-server/src/index.js"],
      "env": {
        "LINKEDIN_EMAIL": "your.email@example.com",
        "LINKEDIN_PASSWORD": "your_password",
        "DRY_RUN": "true",
        "LOG_LEVEL": "INFO",
        "RATE_LIMIT_POSTS": "3"
      }
    }
  }
}
```

Then restart Claude Desktop.

---

## Tool Reference

### publish_post

Publish a post to LinkedIn immediately.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `content` | string | Yes | Post content (max 3000 chars) |
| `imageUrl` | string | No | Optional image URL |
| `hashtags` | string[] | No | Hashtags (without #) |

**Example:**
```json
{
  "content": "Excited to announce our new product launch! 🚀",
  "imageUrl": "https://example.com/image.jpg",
  "hashtags": ["ProductLaunch", "Innovation"]
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Post published"
}
```

### schedule_post

Schedule a post for later publishing.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `content` | string | Yes | Post content (max 3000 chars) |
| `scheduledTime` | string | Yes | ISO 8601 timestamp |
| `imageUrl` | string | No | Optional image URL |
| `hashtags` | string[] | No | Hashtags (without #) |

**Example:**
```json
{
  "content": "Join us for a webinar tomorrow!",
  "scheduledTime": "2026-02-26T09:00:00Z",
  "hashtags": ["Webinar", "Event"]
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Post scheduled for 2026-02-26T09:00:00Z",
  "scheduleData": { ... }
}
```

### reply_to_comment

Reply to a comment on a LinkedIn post.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `postUrl` | string | Yes | URL of the post |
| `commentId` | string | Yes | ID of the comment |
| `content` | string | Yes | Reply content (max 1000 chars) |

**Example:**
```json
{
  "postUrl": "https://www.linkedin.com/feed/update/urn:li:activity:123456",
  "commentId": "comment-789",
  "content": "Thanks for your feedback!"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Reply posted"
}
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LINKEDIN_EMAIL` | (required) | LinkedIn email/username |
| `LINKEDIN_PASSWORD` | (required) | LinkedIn password |
| `DRY_RUN` | `true` | Simulate without posting |
| `LOG_LEVEL` | `INFO` | DEBUG/INFO/WARNING/ERROR |
| `RATE_LIMIT_POSTS` | `3` | Max posts per day |

### Rate Limiting

- **Default:** 3 posts per day
- **Reset:** Daily at midnight (local time)
- **Tracking:** `.linkedin_rate_limit.json`

When rate limit is exceeded:
```json
{
  "status": "error",
  "message": "Rate limit exceeded: 3/3 posts today"
}
```

### DRY_RUN Mode

When `DRY_RUN=true`:
- No actual posts are published
- Returns preview of what would be posted
- Rate limit is NOT incremented
- Safe for testing

---

## Logging

### Log Format

```
2026-02-25T12:00:00.000Z | INFO    | linkedin_mcp | Starting LinkedIn MCP Server
2026-02-25T12:00:01.000Z | INFO    | linkedin_mcp | Browser started
2026-02-25T12:00:02.000Z | INFO    | linkedin_mcp | Login successful
```

### Log Levels

| Level | Description |
|-------|-------------|
| `DEBUG` | Detailed debugging info |
| `INFO` | General operational info |
| `WARNING` | Potential issues |
| `ERROR` | Errors that prevent operation |

---

## Error Handling

### Validation Errors

```json
{
  "status": "error",
  "message": "Validation failed",
  "errors": [
    { "field": "content", "message": "Required" },
    { "field": "scheduledTime", "message": "Invalid date-time format" }
  ]
}
```

### Authentication Errors

```json
{
  "status": "error",
  "message": "Failed to login to LinkedIn"
}
```

### Rate Limit Errors

```json
{
  "status": "error",
  "message": "Rate limit exceeded: 3/3 posts today"
}
```

---

## Troubleshooting

### Login Fails

1. **Check credentials:**
   ```bash
   cat .env | grep LINKEDIN
   ```

2. **Verify account access:**
   - Try logging in manually at linkedin.com
   - Check for 2FA requirements

3. **Clear session:**
   ```bash
   rm -rf .linkedin_sessions/
   npm start
   ```

### Rate Limit Issues

- Check `.linkedin_rate_limit.json` for current count
- Wait until next day for reset
- Increase `RATE_LIMIT_POSTS` in `.env`

### Playwright Installation

```bash
# Install Playwright browsers
npx playwright install chromium

# Or install system-wide
playwright install chromium
```

---

## Security

- **Credentials:** Store in `.env` (never commit)
- **Session data:** Stored locally in `.linkedin_sessions/`
- **DRY_RUN default:** Safe for testing
- **Rate limiting:** Prevents abuse

---

## Files Created

| File | Purpose |
|------|---------|
| `src/index.js` | Main MCP server |
| `.env` | Environment variables |
| `.linkedin_rate_limit.json` | Rate limit tracking |
| `.linkedin_scheduled_posts.json` | Scheduled posts |
| `.linkedin_sessions/` | Browser session data |

---

## Best Practices

1. **Always test with DRY_RUN first:**
   ```bash
   DRY_RUN=true npm start
   ```

2. **Set appropriate rate limits:**
   - Personal accounts: 3-5 posts/day
   - Company pages: 5-10 posts/day

3. **Monitor logs:**
   ```bash
   tail -f logs/linkedin-mcp-*.log
   ```

4. **Review before publishing:**
   - Use DRY_RUN to preview
   - Check content for accuracy
   - Verify hashtags are relevant

---

## License

MIT License
