# Email MCP Server — Production Guide

**Version:** 2.0.0  
**Status:** Production Ready  
**Last Updated:** March 2026

## Overview

Production-ready MCP server for Gmail operations with enterprise features:

- ✅ **OAuth2 Gmail** — Secure authentication
- ✅ **DRY_RUN mode** — Test without sending real emails
- ✅ **Rate limiting** — Max 10 emails/day (configurable)
- ✅ **Approval check flag** — Require approval before sending
- ✅ **JSON logging** — Structured logs for monitoring
- ✅ **Schedule emails** — Queue emails for future delivery
- ✅ **Draft support** — Save drafts for review

## Tools

| Tool | Description | Approval Required |
|------|-------------|-------------------|
| `send_email` | Send email immediately via Gmail API | Yes (if `REQUIRE_APPROVAL=true`) |
| `draft_email` | Save to Gmail Drafts (no send) | No (always requires manual send) |
| `schedule_email` | Queue email for future send | Yes (if `REQUIRE_APPROVAL=true`) |
| `search_inbox` | Search inbox with Gmail query syntax | No |

---

## Installation

### Prerequisites

- Node.js 20.x LTS or higher
- Google Cloud project with Gmail API enabled
- OAuth2 credentials (Client ID, Client Secret)
- Refresh token with Gmail scopes

### Step 1: Install Dependencies

```bash
cd mcp/email-server
npm install
```

### Step 2: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use your preferred editor
```

### Step 3: Obtain OAuth2 Refresh Token

#### Option A: Using Python OAuth Flow (Recommended)

```bash
# From project root
cd /mnt/d/Gemini_Cli/hackathon/hackathon_0/AI-Employee

# Run the existing Gmail OAuth flow
python3 setup_email_oauth.py

# This creates token.json — extract refresh token:
python3 -c "import json; t=json.load(open('token.json')); print(t.get('refresh_token', 'Not found'))"
```

#### Option B: Using OAuth2 Playground

1. Visit [OAuth2 Playground](https://developers.google.com/oauthplayground/)
2. Click gear icon → Check "Use your own OAuth credentials"
3. Enter your Client ID and Secret
4. In "Step 1", select:
   - `https://www.googleapis.com/auth/gmail.send`
   - `https://www.googleapis.com/auth/gmail.compose`
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/gmail.modify`
5. Click "Authorize APIs" → Sign in → Allow
6. Click "Exchange authorization code for tokens"
7. Copy the **Refresh token**

### Step 4: Update .env

```bash
# .env file
GMAIL_CLIENT_ID=your_client_id_here.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=your_client_secret_here
GMAIL_REFRESH_TOKEN=your_refresh_token_here
GMAIL_USER=me

# Behavior flags
DRY_RUN=true                    # Start with true to test
REQUIRE_APPROVAL=true           # Require approval flag for sends
EMAIL_RATE_LIMIT_DAILY=10       # Max emails per day
LOG_LEVEL=info                  # debug | info | error
```

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GMAIL_CLIENT_ID` | ✅ | — | OAuth2 Client ID from Google Cloud |
| `GMAIL_CLIENT_SECRET` | ✅ | — | OAuth2 Client Secret |
| `GMAIL_REFRESH_TOKEN` | ✅ | — | OAuth2 Refresh Token |
| `GMAIL_USER` | — | `me` | Gmail user (use `me` for authenticated user) |
| `DRY_RUN` | — | `false` | If `true`, no real emails are sent |
| `REQUIRE_APPROVAL` | — | `false` | If `true`, `send_email` requires `approved=true` |
| `EMAIL_RATE_LIMIT_DAILY` | — | `10` | Max emails sent per day |
| `LOG_LEVEL` | — | `info` | Logging verbosity (`debug`, `info`, `error`) |

### Required OAuth Scopes

```
https://www.googleapis.com/auth/gmail.send       # Send emails
https://www.googleapis.com/auth/gmail.compose    # Create drafts
https://www.googleapis.com/auth/gmail.readonly   # Read inbox
https://www.googleapis.com/auth/gmail.modify     # Modify labels
```

---

## Usage

### Start Server

```bash
# Development mode (with auto-reload)
npm run dev

# Production mode
npm start

# Test with DRY_RUN
DRY_RUN=true npm start
```

### MCP Configuration

#### For Claude Desktop (Windows)

Add to `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ai-employee-email": {
      "command": "node",
      "args": ["D:/Gemini_Cli/hackathon/hackathon_0/AI-Employee/mcp/email-server/src/index.js"],
      "env": {
        "GMAIL_CLIENT_ID": "your_client_id_here",
        "GMAIL_CLIENT_SECRET": "your_client_secret_here",
        "GMAIL_REFRESH_TOKEN": "your_refresh_token_here",
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

#### For Claude Code (Project-based)

The included `mcp.json` uses environment variables:

```bash
# Set environment variables
export GMAIL_CLIENT_ID="..."
export GMAIL_CLIENT_SECRET="..."
export GMAIL_REFRESH_TOKEN="..."

# Claude Code auto-discovers mcp/email-server/mcp.json
```

#### mcp.json (Included)

```json
{
  "mcpServers": {
    "ai-employee-email": {
      "command": "node",
      "args": ["mcp/email-server/src/index.js"],
      "env": {
        "GMAIL_CLIENT_ID": "${GMAIL_CLIENT_ID}",
        "GMAIL_CLIENT_SECRET": "${GMAIL_CLIENT_SECRET}",
        "GMAIL_REFRESH_TOKEN": "${GMAIL_REFRESH_TOKEN}",
        "GMAIL_USER": "me",
        "DRY_RUN": "false",
        "REQUIRE_APPROVAL": "true",
        "EMAIL_RATE_LIMIT_DAILY": "10",
        "LOG_LEVEL": "info"
      }
    }
  }
}
```

---

## Tool Reference

### `send_email`

Send an email immediately via Gmail API.

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `to` | string | ✅ | Recipient email address |
| `subject` | string | ✅ | Email subject |
| `body` | string | ✅ | Plain-text body |
| `cc` | string | — | CC recipients |
| `bcc` | string | — | BCC recipients |
| `reply_to` | string | — | Reply-To address |
| `thread_id` | string | — | Gmail thread ID (for replies) |
| `approved` | boolean | — | Set `true` to bypass approval gate |

**Example:**

```json
{
  "to": "client@example.com",
  "subject": "Project Update",
  "body": "Hi,\n\nHere's the weekly update...",
  "cc": "manager@example.com",
  "approved": true
}
```

**Response (Success):**

```json
{
  "status": "sent",
  "message_id": "18abc123def456",
  "thread_id": "18abc123def456",
  "label_ids": ["SENT"],
  "rate": {
    "sent_today": 3,
    "limit": 10,
    "remaining": 7
  }
}
```

**Response (DRY_RUN):**

```json
{
  "status": "dry_run",
  "message": "DRY RUN: email not sent",
  "preview": {
    "to": "client@example.com",
    "subject": "Project Update",
    "body": "Hi,\n\nHere's the weekly update..."
  },
  "rate": {
    "sent_today": 0,
    "limit": 10,
    "remaining": 10
  }
}
```

**Response (Approval Required):**

```json
{
  "error": "Approval required: set approved=true or disable REQUIRE_APPROVAL in .env"
}
```

---

### `draft_email`

Save an email to Gmail Drafts (does not send).

**Parameters:** Same as `send_email` (without `approved` and `thread_id`).

**Example:**

```json
{
  "to": "partner@example.com",
  "subject": "Partnership Proposal",
  "body": "Dear Partner,\n\nWe would like to propose...",
  "cc": "legal@example.com"
}
```

**Response:**

```json
{
  "status": "drafted",
  "draft_id": "r-abc123def456",
  "message_id": "18abc789",
  "thread_id": "18abc789",
  "requires_approval": true,
  "note": "Draft saved to Gmail Drafts. Review and send manually."
}
```

---

### `schedule_email`

Queue an email for future delivery.

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `to` | string | ✅ | Recipient email |
| `subject` | string | ✅ | Subject line |
| `body` | string | ✅ | Email body |
| `send_at` | string | ✅ | ISO 8601 datetime (future) |
| `cc` | string | — | CC recipients |
| `bcc` | string | — | BCC recipients |
| `reply_to` | string | — | Reply-To address |
| `approved` | boolean | — | Approval flag |

**Example:**

```json
{
  "to": "team@example.com",
  "subject": "Meeting Reminder",
  "body": "Reminder: Team meeting tomorrow at 10 AM",
  "send_at": "2026-03-02T09:00:00Z",
  "approved": true
}
```

**Response:**

```json
{
  "status": "scheduled",
  "schedule_id": "sch_1709395200000_abc123",
  "send_at": "2026-03-02T09:00:00Z",
  "message": "Email queued for 2026-03-02T09:00:00Z. Run process_schedules to execute.",
  "note": "Scheduled emails are stored in schedules.json. A cron/scheduler must call process_schedules to send them."
}
```

---

### `search_inbox`

Search inbox using Gmail query syntax.

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | ✅ | Gmail search query |
| `max_results` | number | — | Max results (default: 10) |
| `include_body` | boolean | — | Include full body (default: false) |

**Gmail Query Examples:**

```
is:unread
from:client@example.com
subject:invoice
after:2026/02/01 before:2026/02/28
is:important
label:work
```

**Example:**

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
      "snippet": "Following up on our conversation...",
      "from": "Client <client@example.com>",
      "subject": "Re: Project Proposal",
      "date": "Mon, 24 Feb 2026 09:00:00 +0000",
      "labels": ["UNREAD", "IMPORTANT"]
    }
  ]
}
```

---

## Safety Features

### 1. DRY_RUN Mode

When `DRY_RUN=true`:
- No real API calls to Gmail
- All tools return preview data
- Rate limit not incremented
- Logs marked with `dry_run: true`

**Use case:** Testing integration without sending real emails.

### 2. Rate Limiting

- Default: 10 emails/day
- Persisted to `rate_limit.json`
- Resets at midnight UTC
- Throws error when exceeded

**Response when rate exceeded:**

```json
{
  "error": "Rate limit exceeded: 10/10 emails sent today (2026-03-01). Increase EMAIL_RATE_LIMIT_DAILY or wait until tomorrow."
}
```

### 3. Approval Gate

When `REQUIRE_APPROVAL=true`:
- `send_email` requires `approved=true` parameter
- `schedule_email` requires `approved=true` parameter
- `draft_email` always requires manual send (safe by default)

**Bypass approval:**

```json
{
  "to": "urgent@example.com",
  "subject": "Urgent Matter",
  "body": "...",
  "approved": true
}
```

### 4. JSON Logging

All operations logged to `logs/email-server-YYYY-MM-DD.json` (NDJSON format).

**Log Entry Example:**

```json
{
  "timestamp": "2026-03-01T10:30:00.000Z",
  "level": "info",
  "tool": "send_email",
  "message": "Sending email",
  "dry_run": false,
  "to": "client@example.com",
  "subject": "Project Update"
}
```

**Log Levels:**
- `debug`: Tool calls with arguments
- `info`: Successful operations
- `error`: Failures and exceptions

---

## File Structure

```
mcp/email-server/
├── src/
│   └── index.js          # Main MCP server
├── logs/
│   └── email-server-*.json   # Daily log files (auto-created)
├── schedules.json        # Scheduled emails (auto-created)
├── rate_limit.json       # Rate limit state (auto-created)
├── .env                  # Environment variables (create from .env.example)
├── .env.example          # Template
├── mcp.json              # MCP config for Claude Code
├── package.json          # Node.js manifest
├── README.md             # Quick reference
└── EMAIL_MCP_SERVER.md   # This comprehensive guide
```

---

## Monitoring

### Check Daily Logs

```bash
# View today's logs
tail -f logs/email-server-$(date +%Y-%m-%d).json

# Parse with jq
cat logs/email-server-*.json | jq 'select(.level == "error")'
```

### Check Rate Limit Status

```bash
cat rate_limit.json
# Output: {"date": "2026-03-01", "count": 3}
```

### Check Scheduled Emails

```bash
cat schedules.json | jq '.[] | select(.status == "pending")'
```

### Key Metrics

| Metric | Location | Description |
|--------|----------|-------------|
| Emails sent today | `rate_limit.json` | Count resets daily |
| Scheduled pending | `schedules.json` | Emails awaiting send |
| Errors | `logs/*.json` | Filter by `level: "error"` |
| DRY_RUN status | Logs | Check `dry_run` field |

---

## Troubleshooting

### Missing Gmail Credentials

**Error:**
```
Missing Gmail credentials. Set GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, GMAIL_REFRESH_TOKEN
```

**Solution:**
1. Check `.env` file exists
2. Verify all three credentials are set
3. Ensure no trailing spaces in values

### OAuth Token Expired

**Error:**
```
invalid_grant: Bad Request
```

**Solution:**
1. Re-authorize using OAuth2 Playground
2. Get new refresh token
3. Update `GMAIL_REFRESH_TOKEN` in `.env`

### Rate Limit Exceeded

**Error:**
```
Rate limit exceeded: 10/10 emails sent today
```

**Solution:**
1. Wait until midnight UTC for reset
2. Or increase `EMAIL_RATE_LIMIT_DAILY` in `.env`
3. Or set `DRY_RUN=true` for testing

### Approval Required

**Error:**
```
Approval required: set approved=true or disable REQUIRE_APPROVAL
```

**Solution:**
1. Add `"approved": true` to your request
2. Or set `REQUIRE_APPROVAL=false` in `.env`

### MCP Server Not Starting

**Check:**
```bash
# Verify Node.js version
node --version  # Should be >= 20.0.0

# Check dependencies
npm install

# Test with verbose logging
LOG_LEVEL=debug npm start
```

---

## Production Deployment

### Systemd Service (Linux)

```ini
# /etc/systemd/system/email-mcp.service
[Unit]
Description=Email MCP Server
After=network.target

[Service]
Type=simple
User=ai-employee
WorkingDirectory=/opt/ai-employee/mcp/email-server
Environment=NODE_ENV=production
Environment=DRY_RUN=false
Environment=REQUIRE_APPROVAL=true
Environment=EMAIL_RATE_LIMIT_DAILY=50
ExecStart=/usr/bin/node src/index.js
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl enable email-mcp
sudo systemctl start email-mcp
sudo systemctl status email-mcp
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

```yaml
# docker-compose.yml
version: '3.8'
services:
  email-mcp:
    build: ./mcp/email-server
    environment:
      - GMAIL_CLIENT_ID=${GMAIL_CLIENT_ID}
      - GMAIL_CLIENT_SECRET=${GMAIL_CLIENT_SECRET}
      - GMAIL_REFRESH_TOKEN=${GMAIL_REFRESH_TOKEN}
      - DRY_RUN=false
      - REQUIRE_APPROVAL=true
      - EMAIL_RATE_LIMIT_DAILY=50
    volumes:
      - email-logs:/app/logs
    restart: unless-stopped

volumes:
  email-logs:
```

---

## Security Best Practices

### 1. Protect Credentials

- Never commit `.env` to version control
- Use secrets management in production
- Rotate refresh tokens periodically

### 2. Rate Limiting

- Start with low limit (10/day)
- Monitor usage before increasing
- Set alerts for high usage

### 3. Approval Workflow

- Keep `REQUIRE_APPROVAL=true` in production
- Log all approval bypasses
- Audit `approved=true` requests

### 4. Log Retention

```bash
# Rotate logs weekly
find logs/ -name "*.json" -mtime +7 -delete

# Or use logrotate
# /etc/logrotate.d/email-mcp
/opt/ai-employee/mcp/email-server/logs/*.json {
    weekly
    rotate 4
    compress
    missingok
    notifempty
}
```

---

## API Reference Summary

### Request/Response Flow

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  MCP Client │────▶│ Email MCP    │────▶│  Gmail API  │
│  (Claude)   │     │  Server      │     │             │
└─────────────┘     └──────────────┘     └─────────────┘
       │                    │                    │
       │  1. call_tool      │                    │
       │───────────────────▶│                    │
       │                    │  2. OAuth2         │
       │                    │───────────────────▶│
       │                    │  3. send message   │
       │                    │───────────────────▶│
       │                    │  4. response       │
       │                    │◀───────────────────│
       │  5. result         │                    │
       │◀───────────────────│                    │
```

### Error Codes

| Error | HTTP-like Code | Description |
|-------|----------------|-------------|
| `Rate limit exceeded` | 429 | Too many emails today |
| `Approval required` | 403 | Missing approval flag |
| `Missing credentials` | 500 | OAuth config missing |
| `Invalid send_at` | 400 | Past datetime or bad format |
| `OAuth token expired` | 401 | Need new refresh token |

---

## Changelog

### v2.0.0 (March 2026)
- Added `search_inbox` tool
- Added `schedule_email` tool
- Implemented rate limiting (10/day default)
- Added approval gate (`REQUIRE_APPROVAL`)
- JSON structured logging
- DRY_RUN mode for testing
- Persisted state (rate limit, schedules)

### v1.0.0 (Initial)
- Basic `send_email` and `draft_email`
- OAuth2 Gmail integration

---

## Support

For issues:
1. Check logs: `logs/email-server-*.json`
2. Verify OAuth scopes include `gmail.send` and `gmail.compose`
3. Test with `DRY_RUN=true` first
4. Check rate limit: `cat rate_limit.json`

---

**Document Version:** 1.0  
**Maintained By:** AI Employee Team  
**Review Cycle:** Quarterly
