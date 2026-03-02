# @ai-employee/mcp-email-server

**Version:** 2.0.0  
**Status:** Production Ready

MCP server exposing Gmail operations as tools for Claude / any MCP-compatible AI.

## Features

✅ **OAuth2 Gmail** — Secure authentication with refresh tokens  
✅ **DRY_RUN mode** — Test without sending real emails  
✅ **Rate limiting** — Max 10 emails/day (configurable)  
✅ **Approval check** — Require approval flag before sending  
✅ **JSON logging** — Structured logs for monitoring  
✅ **Schedule emails** — Queue emails for future delivery  
✅ **Search inbox** — Gmail query syntax support  

## Tools

| Tool | Description | Approval Required |
|------|-------------|-------------------|
| `send_email` | Send email immediately via Gmail API | Yes (if `REQUIRE_APPROVAL=true`) |
| `draft_email` | Save to Gmail Drafts (no send) | No (always manual send) |
| `schedule_email` | Queue email for future send | Yes (if `REQUIRE_APPROVAL=true`) |
| `search_inbox` | Search inbox with Gmail query | No |

---

## Quick Start

### 1. Install Dependencies

```bash
cd mcp/email-server
npm install
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your Gmail OAuth2 credentials
```

### 3. Get OAuth2 Refresh Token

**Option A: Using existing Python OAuth flow**

```bash
# From project root
python3 setup_email_oauth.py

# Extract refresh token from token.json
python3 -c "import json; t=json.load(open('token.json')); print(t.get('refresh_token', 'Not found'))"
```

**Option B: OAuth2 Playground**

1. Visit [OAuth2 Playground](https://developers.google.com/oauthplayground/)
2. Select scopes: `gmail.send`, `gmail.compose`, `gmail.readonly`, `gmail.modify`
3. Authorize and exchange for refresh token
4. Copy the refresh token to `.env`

### 4. Test with DRY_RUN

```bash
DRY_RUN=true npm start
```

### 5. Enable Real Sending (Production)

Edit `.env`:
```bash
DRY_RUN=false
REQUIRE_APPROVAL=true  # Keep approval gate for safety
```

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GMAIL_CLIENT_ID` | ✅ | — | OAuth2 Client ID |
| `GMAIL_CLIENT_SECRET` | ✅ | — | OAuth2 Client Secret |
| `GMAIL_REFRESH_TOKEN` | ✅ | — | OAuth2 Refresh Token |
| `GMAIL_USER` | — | `me` | Gmail user (use `me`) |
| `DRY_RUN` | — | `false` | Skip real API calls |
| `REQUIRE_APPROVAL` | — | `false` | Require `approved=true` for sends |
| `EMAIL_RATE_LIMIT_DAILY` | — | `10` | Max emails per day |
| `LOG_LEVEL` | — | `info` | `debug` / `info` / `error` |

### Required OAuth Scopes

```
https://www.googleapis.com/auth/gmail.send       # Send emails
https://www.googleapis.com/auth/gmail.compose    # Create drafts
https://www.googleapis.com/auth/gmail.readonly   # Read inbox
https://www.googleapis.com/auth/gmail.modify     # Modify labels
```

---

## MCP Configuration

### Claude Desktop (Windows)

Add to `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ai-employee-email": {
      "command": "node",
      "args": ["D:/Gemini_Cli/hackathon/hackathon_0/AI-Employee/mcp/email-server/src/index.js"],
      "env": {
        "GMAIL_CLIENT_ID": "your_client_id",
        "GMAIL_CLIENT_SECRET": "your_client_secret",
        "GMAIL_REFRESH_TOKEN": "your_refresh_token",
        "GMAIL_USER": "me",
        "DRY_RUN": "true",
        "REQUIRE_APPROVAL": "true",
        "EMAIL_RATE_LIMIT_DAILY": "10",
        "LOG_LEVEL": "info"
      }
    }
  }
}
```

### Claude Code (Project)

The included `mcp.json` uses environment variables:

```bash
export GMAIL_CLIENT_ID="..."
export GMAIL_CLIENT_SECRET="..."
export GMAIL_REFRESH_TOKEN="..."
```

---

## Tool Examples

### send_email

```json
{
  "to": "client@example.com",
  "subject": "Project Update",
  "body": "Hi,\n\nHere's the weekly update...",
  "cc": "manager@example.com",
  "approved": true
}
```

**Response:**
```json
{
  "status": "sent",
  "message_id": "18abc123",
  "thread_id": "18abc123",
  "rate": { "sent_today": 1, "limit": 10, "remaining": 9 }
}
```

### draft_email

```json
{
  "to": "partner@example.com",
  "subject": "Partnership Proposal",
  "body": "Dear Partner,\n\nWe propose..."
}
```

**Response:**
```json
{
  "status": "drafted",
  "draft_id": "r-abc123",
  "note": "Draft saved to Gmail Drafts. Review and send manually."
}
```

### schedule_email

```json
{
  "to": "team@example.com",
  "subject": "Meeting Reminder",
  "body": "Reminder: Meeting at 10 AM",
  "send_at": "2026-03-02T09:00:00Z",
  "approved": true
}
```

**Response:**
```json
{
  "status": "scheduled",
  "schedule_id": "sch_1709395200000_abc123",
  "send_at": "2026-03-02T09:00:00Z"
}
```

### search_inbox

```json
{
  "query": "is:unread from:client@example.com",
  "max_results": 5,
  "include_body": false
}
```

**Response:**
```json
{
  "status": "ok",
  "count": 2,
  "results": [
    {
      "id": "18abc123",
      "thread_id": "18abc123",
      "snippet": "Following up on...",
      "from": "Client <client@example.com>",
      "subject": "Re: Proposal",
      "date": "Mon, 24 Feb 2026 09:00:00 +0000"
    }
  ]
}
```

---

## Safety Features

### DRY_RUN Mode

When `DRY_RUN=true`:
- No real API calls
- Returns preview data
- Rate limit not incremented

### Rate Limiting

- Default: 10 emails/day
- Resets at midnight UTC
- Persisted to `rate_limit.json`

### Approval Gate

When `REQUIRE_APPROVAL=true`:
- `send_email` requires `approved: true`
- `schedule_email` requires `approved: true`
- `draft_email` always safe (manual send)

### JSON Logging

Logs written to `logs/email-server-YYYY-MM-DD.json`:

```json
{"timestamp":"2026-03-01T10:30:00Z","level":"info","tool":"send_email","message":"Email sent","dry_run":false}
```

---

## File Structure

```
mcp/email-server/
├── src/
│   └── index.js          # Main MCP server
├── logs/
│   └── email-server-*.json   # Daily logs
├── schedules.json        # Scheduled emails
├── rate_limit.json       # Rate limit state
├── .env                  # Environment variables
├── .env.example          # Template
├── mcp.json              # MCP config
├── package.json          # Dependencies
├── README.md             # This file
└── EMAIL_MCP_SERVER.md   # Full documentation
```

---

## Monitoring

```bash
# View today's logs
tail -f logs/email-server-$(date +%Y-%m-%d).json

# Check rate limit
cat rate_limit.json

# Check scheduled emails
cat schedules.json | jq '.[] | select(.status == "pending")'
```

---

## Troubleshooting

**Missing credentials:**
```
Error: Missing Gmail credentials
```
→ Check `.env` has all three: `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN`

**Rate limit exceeded:**
```
Error: Rate limit exceeded: 10/10 emails sent today
```
→ Wait until midnight UTC or increase `EMAIL_RATE_LIMIT_DAILY`

**Approval required:**
```
Error: Approval required: set approved=true
```
→ Add `"approved": true` to request or set `REQUIRE_APPROVAL=false`

**OAuth token expired:**
```
Error: invalid_grant
```
→ Re-authorize and get new refresh token

---

## Production Deployment

### Systemd Service

```ini
# /etc/systemd/system/email-mcp.service
[Unit]
Description=Email MCP Server
After=network.target

[Service]
Type=simple
User=ai-employee
WorkingDirectory=/opt/ai-employee/mcp/email-server
Environment=DRY_RUN=false
Environment=REQUIRE_APPROVAL=true
Environment=EMAIL_RATE_LIMIT_DAILY=50
ExecStart=/usr/bin/node src/index.js
Restart=always

[Install]
WantedBy=multi-user.target
```

### Docker

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY src/ ./src/
COPY .env ./
CMD ["node", "src/index.js"]
```

---

## Documentation

- **README.md** — This quick start guide
- **EMAIL_MCP_SERVER.md** — Comprehensive production guide with:
  - Detailed setup instructions
  - OAuth2 configuration
  - Tool reference with all parameters
  - Safety features explanation
  - Monitoring and troubleshooting
  - Production deployment examples

---

## License

MIT
