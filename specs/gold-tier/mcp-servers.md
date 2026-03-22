# Gold Tier MCP Servers Specification

This document defines all MCP (Model Context Protocol) servers required for Gold Tier operation.

## MCP Server Overview

| # | Server Name | Port | Domain | Status |
|---|-------------|------|--------|--------|
| 1 | Email Server | 8081 | Communication | Existing |
| 2 | LinkedIn Server | 8082 | Social Media | Existing |
| 3 | WhatsApp Server | 8083 | Communication | Existing |
| 4 | Odoo Server | 8084 | Accounting | New |
| 5 | Facebook Server | 8085 | Social Media | New |
| 6 | Instagram Server | 8086 | Social Media | New |
| 7 | Twitter Server | 8087 | Social Media | New |

---

## MCP Server 1: Email Server

**Path:** `mcp/email-server/`  
**Port:** 8081  
**Status:** Existing (extend for Gold Tier)

### Tools

| Tool | Parameters | Description |
|------|------------|-------------|
| `draft_email` | `{to, subject, body, cc?, bcc?}` | Draft email for approval |
| `send_email` | `{to, subject, body, cc?, bcc?}` | Send email directly (low-risk only) |
| `list_emails` | `{folder, limit?, unread_only?}` | List emails from folder |
| `get_email` | `{email_id}` | Get email by ID |
| `mark_read` | `{email_ids}` | Mark emails as read |
| `move_to_folder` | `{email_id, folder}` | Move email to folder |

### Configuration

```json
{
  "server": {
    "name": "email-server",
    "port": 8081,
    "host": "localhost"
  },
  "gmail": {
    "credentials_file": "${GMAIL_CREDENTIALS_FILE}",
    "token_file": "${GMAIL_TOKEN_FILE}",
    "poll_interval": 60
  }
}
```

### Example Tool Call

```json
{
  "tool": "draft_email",
  "params": {
    "to": "client@example.com",
    "subject": "Re: Project Update",
    "body": "Dear Client,\n\nThank you for your inquiry...\n\nBest regards,\nAI Employee"
  }
}
```

---

## MCP Server 2: LinkedIn Server

**Path:** `mcp/linkedin-server/`  
**Port:** 8082  
**Status:** Existing (extend for Gold Tier)

### Tools

| Tool | Parameters | Description |
|------|------------|-------------|
| `publish_linkedin_post` | `{content, scheduled_at?}` | Publish post to LinkedIn |
| `schedule_linkedin_post` | `{content, scheduled_at}` | Schedule post for later |
| `get_linkedin_profile` | `{}` | Get profile information |
| `get_linkedin_analytics` | `{post_id?}` | Get post/profile analytics |

### Configuration

```json
{
  "server": {
    "name": "linkedin-server",
    "port": 8082,
    "host": "localhost"
  },
  "linkedin": {
    "access_token": "${LINKEDIN_ACCESS_TOKEN}",
    "organization_id": "${LINKEDIN_ORG_ID}"
  }
}
```

---

## MCP Server 3: WhatsApp Server

**Path:** `mcp/whatsapp-server/`  
**Port:** 8083  
**Status:** Existing (extend for Gold Tier)

### Tools

| Tool | Parameters | Description |
|------|------------|-------------|
| `send_whatsapp_message` | `{recipient, message}` | Send WhatsApp message |
| `send_whatsapp_reply` | `{thread_id, message}` | Reply to WhatsApp thread |
| `get_whatsapp_chats` | `{limit?}` | List recent chats |
| `get_whatsapp_messages` | `{chat_id, limit?}` | Get messages from chat |
| `mark_whatsapp_read` | `{chat_ids}` | Mark chats as read |

### Configuration

```json
{
  "server": {
    "name": "whatsapp-server",
    "port": 8083,
    "host": "localhost"
  },
  "whatsapp": {
    "profile_dir": "${WA_PROFILE_DIR}",
    "headless": "${WA_HEADLESS:-false}",
    "browser_timeout": 30000
  }
}
```

---

## MCP Server 4: Odoo Server (NEW)

**Path:** `mcp/odoo-server/`  
**Port:** 8084  
**Status:** New Implementation Required

### Architecture

```
┌─────────────────┐     JSON-RPC      ┌─────────────────┐
│  MCP Odoo       │──────────────────▶│  Odoo Instance  │
│  Server         │     XML-RPC       │  (v16/v17)      │
│  (Node.js)      │◀──────────────────│                 │
└────────┬────────┘                   └─────────────────┘
         │
         │ HTTP REST
         │
         ▼
┌─────────────────┐
│  Orchestrator   │
└─────────────────┘
```

### Tools

| Tool | Parameters | Description |
|------|------------|-------------|
| `list_unpaid_invoices` | `{partner_id?, date_from?, date_to?, limit?}` | Get unpaid invoices |
| `list_overdue_payments` | `{days_overdue?, limit?}` | Get overdue payments |
| `create_invoice` | `{partner_id, lines, date_due, description?}` | Create new invoice |
| `register_payment` | `{invoice_id, amount, date, payment_method?}` | Record payment |
| `get_financial_summary` | `{period, comparison?}` | Get P&L summary |
| `get_partner_balance` | `{partner_id}` | Get customer/vendor balance |
| `list_partners` | `{type?, limit?}` | List customers/vendors |
| `create_partner` | `{name, email, phone, type}` | Create new partner |
| `list_journal_entries` | `{date_from?, date_to?, journal_id?}` | Get journal entries |
| `create_journal_entry` | `{date, lines, journal_id, ref?}` | Create journal entry |

### Tool Schemas

#### list_unpaid_invoices

```json
{
  "name": "list_unpaid_invoices",
  "description": "Retrieve unpaid invoices from Odoo",
  "inputSchema": {
    "type": "object",
    "properties": {
      "partner_id": {"type": "integer", "description": "Filter by partner"},
      "date_from": {"type": "string", "format": "date", "description": "Start date"},
      "date_to": {"type": "string", "format": "date", "description": "End date"},
      "limit": {"type": "integer", "default": 50, "description": "Max results"}
    }
  }
}
```

#### create_invoice

```json
{
  "name": "create_invoice",
  "description": "Create a new customer invoice in Odoo",
  "inputSchema": {
    "type": "object",
    "properties": {
      "partner_id": {"type": "integer", "description": "Customer ID"},
      "lines": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "product_id": {"type": "integer"},
            "name": {"type": "string"},
            "quantity": {"type": "number"},
            "price_unit": {"type": "number"},
            "tax_ids": {"type": "array", "items": {"type": "integer"}}
          },
          "required": ["name", "quantity", "price_unit"]
        }
      },
      "date_due": {"type": "string", "format": "date"},
      "description": {"type": "string"}
    },
    "required": ["partner_id", "lines", "date_due"]
  }
}
```

### Odoo JSON-RPC Client

```javascript
class OdooClient {
  constructor(config) {
    this.url = config.url;
    this.db = config.db;
    this.username = config.username;
    this.password = config.password;
    this.uid = null;
  }

  async authenticate() {
    const response = await fetch(`${this.url}/jsonrpc`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        jsonrpc: '2.0',
        method: 'call',
        params: {
          service: 'common',
          method: 'authenticate',
          args: [this.db, this.username, this.password, {}]
        }
      })
    });
    const result = await response.json();
    this.uid = result.result;
    return this.uid;
  }

  async execute(model, method, args = [], kwargs = {}) {
    const response = await fetch(`${this.url}/jsonrpc`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        jsonrpc: '2.0',
        method: 'call',
        params: {
          service: 'object',
          method: 'execute_kw',
          args: [this.db, this.uid, this.password, model, method, args],
          kwargs: kwargs
        }
      })
    });
    const result = await response.json();
    return result.result;
  }

  async searchRead(model, domain, fields = [], limit = 80) {
    return this.execute(model, 'search_read', [domain], { fields, limit });
  }

  async create(model, values) {
    return this.execute(model, 'create', [values]);
  }

  async write(model, ids, values) {
    return this.execute(model, 'write', [ids, values]);
  }
}
```

### Configuration

```json
{
  "server": {
    "name": "odoo-server",
    "port": 8084,
    "host": "localhost"
  },
  "odoo": {
    "url": "${ODOO_URL}",
    "database": "${ODOO_DB}",
    "username": "${ODOO_USERNAME}",
    "password": "${ODOO_PASSWORD}",
    "timeout": 30000
  }
}
```

### Error Handling

| Error Type | HTTP Code | Retry | Description |
|------------|-----------|-------|-------------|
| AuthenticationFailed | 401 | No | Invalid credentials |
| AccessDenied | 403 | No | Insufficient permissions |
| NotFound | 404 | No | Record not found |
| ValidationError | 400 | No | Invalid data |
| ServerError | 500 | Yes | Odoo server error |
| Timeout | 504 | Yes | Request timeout |

---

## MCP Server 5: Facebook Server (NEW)

**Path:** `mcp/facebook-server/`  
**Port:** 8085  
**Status:** New Implementation Required

### Tools

| Tool | Parameters | Description |
|------|------------|-------------|
| `publish_facebook_post` | `{content, link?, photo?, scheduled_at?}` | Publish post to Facebook |
| `schedule_facebook_post` | `{content, scheduled_at}` | Schedule post for later |
| `get_facebook_page_info` | `{page_id?}` | Get page information |
| `get_facebook_insights` | `{post_id?, metric?}` | Get post/page insights |
| `reply_facebook_comment` | `{comment_id, message}` | Reply to comment |

### Facebook Graph API Integration

```javascript
class FacebookClient {
  constructor(accessToken) {
    this.accessToken = accessToken;
    this.base_url = 'https://graph.facebook.com/v18.0';
  }

  async publishPost(pageId, content, options = {}) {
    const params = new URLSearchParams({
      message: content,
      access_token: this.accessToken,
    });

    if (options.link) params.append('link', options.link);
    if (options.photo) params.append('picture', options.photo);
    if (options.scheduled_at) params.append('scheduled_publish_time', options.scheduled_at);

    const response = await fetch(`${this.base_url}/${pageId}/feed?${params}`, {
      method: 'POST',
    });
    return response.json();
  }

  async getInsights(pageId, metrics = ['page_impressions', 'page_engagements']) {
    const params = new URLSearchParams({
      metric: metrics.join(','),
      access_token: this.accessToken,
    });

    const response = await fetch(`${this.base_url}/${pageId}/insights?${params}`);
    return response.json();
  }
}
```

### Configuration

```json
{
  "server": {
    "name": "facebook-server",
    "port": 8085,
    "host": "localhost"
  },
  "facebook": {
    "access_token": "${FACEBOOK_ACCESS_TOKEN}",
    "page_id": "${FACEBOOK_PAGE_ID}",
    "api_version": "v18.0"
  }
}
```

---

## MCP Server 6: Instagram Server (NEW)

**Path:** `mcp/instagram-server/`  
**Port:** 8086  
**Status:** New Implementation Required

### Tools

| Tool | Parameters | Description |
|------|------------|-------------|
| `publish_instagram_post` | `{caption, media_url, media_type?, scheduled_at?}` | Publish post to Instagram |
| `publish_instagram_story` | `{media_url, media_type?}` | Publish story to Instagram |
| `publish_instagram_reel` | `{caption, media_url, scheduled_at?}` | Publish reel to Instagram |
| `get_instagram_insights` | `{metric?, period?}` | Get Instagram insights |
| `get_instagram_media` | `{limit?}` | Get recent media |

### Instagram Graph API Integration

```javascript
class InstagramClient {
  constructor(accessToken, instagramBusinessAccountId) {
    this.accessToken = accessToken;
    this.instagramBusinessAccountId = instagramBusinessAccountId;
    this.base_url = 'https://graph.facebook.com/v18.0';
  }

  async publishPost(caption, mediaUrl, mediaType = 'IMAGE') {
    // Step 1: Create media container
    const containerResponse = await fetch(
      `${this.base_url}/${this.instagramBusinessAccountId}/media`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          image_source: mediaUrl,
          caption: caption,
          access_token: this.accessToken,
        }),
      }
    );
    const container = await containerResponse.json();

    // Step 2: Publish container
    const publishResponse = await fetch(
      `${this.base_url}/${this.instagramBusinessAccountId}/media_publish`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          creation_id: container.id,
          access_token: this.accessToken,
        }),
      }
    );
    return publishResponse.json();
  }
}
```

### Configuration

```json
{
  "server": {
    "name": "instagram-server",
    "port": 8086,
    "host": "localhost"
  },
  "instagram": {
    "access_token": "${INSTAGRAM_ACCESS_TOKEN}",
    "business_account_id": "${INSTAGRAM_BUSINESS_ACCOUNT_ID}",
    "api_version": "v18.0"
  }
}
```

---

## MCP Server 7: Twitter Server (NEW)

**Path:** `mcp/twitter-server/`  
**Port:** 8087  
**Status:** New Implementation Required

### Tools

| Tool | Parameters | Description |
|------|------------|-------------|
| `publish_tweet` | `{content, media_ids?}` | Publish tweet |
| `publish_thread` | `{tweets: [{content, media_ids?}]}` | Publish tweet thread |
| `reply_tweet` | `{tweet_id, content}` | Reply to tweet |
| `retweet` | `{tweet_id}` | Retweet a tweet |
| `get_twitter_analytics` | `{tweet_id?, metric?}` | Get tweet analytics |
| `search_tweets` | `{query, limit?}` | Search tweets |

### Twitter API v2 Integration

```javascript
class TwitterClient {
  constructor(bearerToken) {
    this.bearerToken = bearerToken;
    this.base_url = 'https://api.twitter.com/2';
  }

  async publishTweet(content, mediaIds = []) {
    const response = await fetch(`${this.base_url}/tweets`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.bearerToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text: content,
        media: mediaIds.length > 0 ? { media_ids: mediaIds } : undefined,
      }),
    });
    return response.json();
  }

  async publishThread(tweets) {
    const results = [];
    let previousTweetId = null;

    for (const tweet of tweets) {
      const tweetData = { text: tweet.content };
      if (previousTweetId) {
        tweetData.reply = { in_reply_to_tweet_id: previousTweetId };
      }
      if (tweet.media_ids?.length > 0) {
        tweetData.media = { media_ids: tweet.media_ids };
      }

      const response = await fetch(`${this.base_url}/tweets`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.bearerToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(tweetData),
      });
      const result = await response.json();
      results.push(result);
      previousTweetId = result.data.id;
    }

    return results;
  }
}
```

### Configuration

```json
{
  "server": {
    "name": "twitter-server",
    "port": 8087,
    "host": "localhost"
  },
  "twitter": {
    "bearer_token": "${TWITTER_BEARER_TOKEN}",
    "api_key": "${TWITTER_API_KEY}",
    "api_secret": "${TWITTER_API_SECRET}",
    "access_token": "${TWITTER_ACCESS_TOKEN}",
    "access_token_secret": "${TWITTER_ACCESS_TOKEN_SECRET}"
  }
}
```

---

## MCP Server Common Patterns

### Health Check Endpoint

All MCP servers expose a health check endpoint:

```
GET /health
```

Response:
```json
{
  "status": "healthy",
  "server": "email-server",
  "version": "1.0.0",
  "uptime_seconds": 3600,
  "last_error": null
}
```

### Logging Format

All servers use consistent logging:

```javascript
const logger = {
  info: (message, context) => {
    console.log(JSON.stringify({
      level: 'info',
      timestamp: new Date().toISOString(),
      server: SERVER_NAME,
      message,
      context,
    }));
  },
  error: (message, error) => {
    console.error(JSON.stringify({
      level: 'error',
      timestamp: new Date().toISOString(),
      server: SERVER_NAME,
      message,
      error: error?.message,
      stack: error?.stack,
    }));
  },
};
```

### Error Response Format

All errors follow this format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": {},
    "retryable": false
  }
}
```

---

## MCP Server Startup Scripts

### Package.json Scripts

```json
{
  "scripts": {
    "start:mcp:email": "node mcp/email-server/src/index.js",
    "start:mcp:linkedin": "node mcp/linkedin-server/src/index.js",
    "start:mcp:whatsapp": "node mcp/whatsapp-server/src/index.js",
    "start:mcp:odoo": "node mcp/odoo-server/src/index.js",
    "start:mcp:facebook": "node mcp/facebook-server/src/index.js",
    "start:mcp:instagram": "node mcp/instagram-server/src/index.js",
    "start:mcp:twitter": "node mcp/twitter-server/src/index.js",
    "start:mcp:all": "npm-run-all --parallel start:mcp:*"
  }
}
```

### PM2 Ecosystem Configuration

```javascript
// ecosystem.config.js
module.exports = {
  apps: [
    {
      name: 'mcp-email',
      script: './mcp/email-server/src/index.js',
      env: { PORT: 8081 },
    },
    {
      name: 'mcp-linkedin',
      script: './mcp/linkedin-server/src/index.js',
      env: { PORT: 8082 },
    },
    {
      name: 'mcp-whatsapp',
      script: './mcp/whatsapp-server/src/index.js',
      env: { PORT: 8083 },
    },
    {
      name: 'mcp-odoo',
      script: './mcp/odoo-server/src/index.js',
      env: { PORT: 8084 },
    },
    {
      name: 'mcp-facebook',
      script: './mcp/facebook-server/src/index.js',
      env: { PORT: 8085 },
    },
    {
      name: 'mcp-instagram',
      script: './mcp/instagram-server/src/index.js',
      env: { PORT: 8086 },
    },
    {
      name: 'mcp-twitter',
      script: './mcp/twitter-server/src/index.js',
      env: { PORT: 8087 },
    },
  ],
};
```

---

## MCP Server Testing

### Test Structure

```
mcp/
├── email-server/
│   ├── src/
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── tools/
│   └── package.json
├── ...
```

### Example Tool Test

```javascript
const { test } = require('node:test');
const assert = require('node:assert');
const { EmailServer } = require('../src/server');

test('draft_email tool creates valid draft', async () => {
  const server = new EmailServer(mockConfig);
  const result = await server.tools.draft_email({
    to: 'test@example.com',
    subject: 'Test Subject',
    body: 'Test Body',
  });

  assert.ok(result.draft_id);
  assert.equal(result.status, 'draft_created');
  assert.equal(result.to, 'test@example.com');
});
```

---

**Document End**
