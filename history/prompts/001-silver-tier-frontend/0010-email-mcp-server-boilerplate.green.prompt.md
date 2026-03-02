---
id: "0010"
title: "Email MCP Server Node.js Boilerplate"
stage: green
date: "2026-02-25"
surface: agent
model: qwen/qwen3-coder:free
feature: 001-silver-tier-frontend
branch: 001-silver-tier-frontend
user: areeba_zafar
command: "Generate setup instructions and Node.js boilerplate for Email MCP server"
labels: ["mcp", "email", "gmail", "nodejs", "silver-tier", "boilerplate"]
links:
  spec: "null"
  ticket: "null"
  adr: "null"
  pr: "null"
files:
  - mcp/email-server/package.json
  - mcp/email-server/src/index.js
  - mcp/email-server/.env.example
  - mcp/email-server/mcp.json
  - mcp/email-server/README.md
tests: []
---

# Prompt

Generate setup instructions and Node.js boilerplate for Email MCP server.

Requirements:
- Send email
- Draft email
- Search inbox
- Support environment variables for credentials
- Add DRY_RUN flag
- Expose: send_email, draft_email

Include: package.json, index.js structure, example mcp.json config entry

# Response

Created `mcp/email-server/` — a complete MCP server using `@modelcontextprotocol/sdk` + `googleapis`.

## Files

| File | Purpose |
|---|---|
| `package.json` | ESM Node.js package, deps: `@modelcontextprotocol/sdk`, `googleapis`, `zod`, `dotenv` |
| `src/index.js` | MCP server: tool registry, Gmail auth, 3 tool implementations |
| `.env.example` | Credential template with all env vars documented |
| `mcp.json` | Ready-to-use MCP config entry for Claude Code / Claude Desktop |
| `README.md` | Full setup guide, tool reference, DRY_RUN docs, Gmail scope list |

## Tools Exposed

| Tool | Gmail API | Behaviour |
|---|---|---|
| `send_email` | `users.messages.send` | Sends immediately; DRY_RUN returns preview |
| `draft_email` | `users.drafts.create` | Saves to Drafts, never sends; DRY_RUN returns preview |
| `search_inbox` | `users.messages.list` + `.get` | Metadata or full body; DRY_RUN returns preview |

## Key Design Decisions

- ESM (`"type": "module"`) for compatibility with MCP SDK
- Zod schemas validate all tool inputs before touching the API
- `buildRawMessage()` constructs RFC 2822 MIME and base64url-encodes it
- `DRY_RUN=true` short-circuits before any `gmail.users.*` call
- Credentials loaded from `.env` via `dotenv`; missing creds throw a clear error
- Stdio transport — works with Claude Desktop and `claude mcp add`
