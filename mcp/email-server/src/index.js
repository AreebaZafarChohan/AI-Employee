#!/usr/bin/env node
/**
 * @ai-employee/mcp-email-server  v2.0.0
 *
 * MCP server exposing Gmail operations:
 *   - send_email       Send immediately via Gmail API
 *   - draft_email      Save to Gmail Drafts (requires_approval gate)
 *   - schedule_email   Queue email for future send (stored in schedules.json)
 *
 * Features:
 *   - OAuth2 Gmail (GMAIL_CLIENT_ID / SECRET / REFRESH_TOKEN)
 *   - DRY_RUN mode — no real API calls, returns preview
 *   - Rate limiting — max EMAIL_RATE_LIMIT_DAILY (default 10) sends per day
 *   - Approval check — send_email blocked if REQUIRE_APPROVAL=true unless approved flag set
 *   - JSON structured logging to logs/email-server-YYYY-MM-DD.json
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { google } from "googleapis";
import { z } from "zod";
import * as dotenv from "dotenv";
import {
  readFileSync, writeFileSync, existsSync, mkdirSync, appendFileSync,
} from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

// ─────────────────────────────────────────────
// Bootstrap
// ─────────────────────────────────────────────

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT      = join(__dirname, "..");
const envPath   = join(ROOT, ".env");
if (existsSync(envPath)) dotenv.config({ path: envPath });

const DRY_RUN        = process.env.DRY_RUN?.toLowerCase() === "true";
const LOG_LEVEL      = (process.env.LOG_LEVEL ?? "info").toLowerCase();
const GMAIL_USER     = process.env.GMAIL_USER ?? "me";
const RATE_LIMIT     = parseInt(process.env.EMAIL_RATE_LIMIT_DAILY ?? "10", 10);
const REQUIRE_APPROVAL = process.env.REQUIRE_APPROVAL?.toLowerCase() === "true";

const LOGS_DIR       = join(ROOT, "logs");
const SCHEDULE_FILE  = join(ROOT, "schedules.json");
const RATE_FILE      = join(ROOT, "rate_limit.json");

mkdirSync(LOGS_DIR, { recursive: true });

// ─────────────────────────────────────────────
// JSON Logger
// ─────────────────────────────────────────────

function logEvent(level, tool, message, extra = {}) {
  const entry = {
    timestamp: new Date().toISOString(),
    level,
    tool,
    message,
    dry_run: DRY_RUN,
    ...extra,
  };

  // stderr for MCP (stdout is the protocol stream)
  if (level === "error" || ["debug","info"].includes(LOG_LEVEL)) {
    console.error(JSON.stringify(entry));
  }

  // Append to daily JSON log file (one JSON object per line — NDJSON)
  const today    = new Date().toISOString().slice(0, 10);
  const logFile  = join(LOGS_DIR, `email-server-${today}.json`);
  appendFileSync(logFile, JSON.stringify(entry) + "\n", "utf-8");
}

if (DRY_RUN) logEvent("info", "server", "DRY RUN MODE — no real emails will be sent");

// ─────────────────────────────────────────────
// Rate Limiter  (persisted to rate_limit.json)
// ─────────────────────────────────────────────

function loadRateState() {
  if (!existsSync(RATE_FILE)) return { date: "", count: 0 };
  try { return JSON.parse(readFileSync(RATE_FILE, "utf-8")); }
  catch { return { date: "", count: 0 }; }
}

function saveRateState(state) {
  writeFileSync(RATE_FILE, JSON.stringify(state, null, 2), "utf-8");
}

function checkAndIncrementRate() {
  const today = new Date().toISOString().slice(0, 10);
  const state = loadRateState();
  if (state.date !== today) {
    // New day — reset
    const fresh = { date: today, count: 0 };
    saveRateState(fresh);
    return fresh;
  }
  if (state.count >= RATE_LIMIT) {
    throw new Error(
      `Rate limit exceeded: ${state.count}/${RATE_LIMIT} emails sent today (${today}). ` +
      `Increase EMAIL_RATE_LIMIT_DAILY or wait until tomorrow.`
    );
  }
  state.count += 1;
  saveRateState(state);
  return state;
}

function peekRateState() {
  const today = new Date().toISOString().slice(0, 10);
  const state = loadRateState();
  if (state.date !== today) return { date: today, count: 0, remaining: RATE_LIMIT };
  return { ...state, remaining: RATE_LIMIT - state.count };
}

// ─────────────────────────────────────────────
// Schedule store  (persisted to schedules.json)
// ─────────────────────────────────────────────

function loadSchedules() {
  if (!existsSync(SCHEDULE_FILE)) return [];
  try { return JSON.parse(readFileSync(SCHEDULE_FILE, "utf-8")); }
  catch { return []; }
}

function saveSchedules(list) {
  writeFileSync(SCHEDULE_FILE, JSON.stringify(list, null, 2), "utf-8");
}

function addSchedule(entry) {
  const list = loadSchedules();
  list.push(entry);
  saveSchedules(list);
  return entry;
}

// ─────────────────────────────────────────────
// Gmail auth
// ─────────────────────────────────────────────

function buildGmailClient() {
  const { GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, GMAIL_REFRESH_TOKEN } = process.env;
  if (!GMAIL_CLIENT_ID || !GMAIL_CLIENT_SECRET || !GMAIL_REFRESH_TOKEN) {
    throw new Error(
      "Missing Gmail credentials. Set GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, " +
      "GMAIL_REFRESH_TOKEN in .env"
    );
  }
  const auth = new google.auth.OAuth2(GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET);
  auth.setCredentials({ refresh_token: GMAIL_REFRESH_TOKEN });
  return google.gmail({ version: "v1", auth });
}

// ─────────────────────────────────────────────
// MIME builder
// ─────────────────────────────────────────────

function buildRawMessage({ to, cc, bcc, subject, body, replyTo }) {
  const lines = [
    `To: ${Array.isArray(to) ? to.join(", ") : to}`,
    `Subject: ${subject}`,
    "Content-Type: text/plain; charset=UTF-8",
    "MIME-Version: 1.0",
  ];
  if (cc)      lines.push(`Cc: ${Array.isArray(cc) ? cc.join(", ") : cc}`);
  if (bcc)     lines.push(`Bcc: ${Array.isArray(bcc) ? bcc.join(", ") : bcc}`);
  if (replyTo) lines.push(`Reply-To: ${replyTo}`);
  lines.push("", body ?? "");
  return Buffer.from(lines.join("\r\n")).toString("base64url");
}

// ─────────────────────────────────────────────
// Zod input schemas
// ─────────────────────────────────────────────

const SendEmailInput = z.object({
  to:               z.union([z.string(), z.array(z.string())]),
  subject:          z.string(),
  body:             z.string(),
  cc:               z.union([z.string(), z.array(z.string())]).optional(),
  bcc:              z.union([z.string(), z.array(z.string())]).optional(),
  reply_to:         z.string().optional(),
  thread_id:        z.string().optional(),
  approved:         z.boolean().optional().describe(
    "Set true to bypass REQUIRE_APPROVAL gate. Required when REQUIRE_APPROVAL=true."
  ),
});

const DraftEmailInput = z.object({
  to:        z.union([z.string(), z.array(z.string())]),
  subject:   z.string(),
  body:      z.string(),
  cc:        z.union([z.string(), z.array(z.string())]).optional(),
  bcc:       z.union([z.string(), z.array(z.string())]).optional(),
  reply_to:  z.string().optional(),
  thread_id: z.string().optional(),
});

const ScheduleEmailInput = z.object({
  to:          z.union([z.string(), z.array(z.string())]),
  subject:     z.string(),
  body:        z.string(),
  send_at:     z.string().describe("ISO 8601 datetime for scheduled send, e.g. 2026-02-27T08:00:00Z"),
  cc:          z.union([z.string(), z.array(z.string())]).optional(),
  bcc:         z.union([z.string(), z.array(z.string())]).optional(),
  reply_to:    z.string().optional(),
  approved:    z.boolean().optional(),
});

const SearchInboxInput = z.object({
  query:         z.string().describe("Gmail search query syntax, e.g. 'is:unread from:client@example.com'"),
  max_results:   z.number().optional().default(10),
  include_body:  z.boolean().optional().default(false),
});

// ─────────────────────────────────────────────
// Tool implementations
// ─────────────────────────────────────────────

async function sendEmail(args) {
  const { to, subject, body, cc, bcc, reply_to, thread_id, approved } = SendEmailInput.parse(args);

  // Approval gate
  if (REQUIRE_APPROVAL && !approved) {
    const msg = "Approval required: set approved=true or disable REQUIRE_APPROVAL in .env";
    logEvent("warn", "send_email", msg, { to, subject, blocked: true });
    throw new Error(msg);
  }

  logEvent("info", "send_email", "Sending email", { to, subject, dry_run: DRY_RUN });

  if (DRY_RUN) {
    return {
      status: "dry_run",
      message: "DRY RUN: email not sent",
      preview: { to, subject, body: body.slice(0, 120) },
      rate: peekRateState(),
    };
  }

  // Rate limit check + increment
  const rateState = checkAndIncrementRate();

  const gmail = buildGmailClient();
  const raw   = buildRawMessage({ to, cc, bcc, subject, body, replyTo: reply_to });
  const requestBody = { raw };
  if (thread_id) requestBody.threadId = thread_id;

  const res = await gmail.users.messages.send({ userId: GMAIL_USER, requestBody });

  logEvent("info", "send_email", "Email sent", {
    message_id: res.data.id,
    thread_id: res.data.threadId,
    rate_today: rateState.count,
    rate_limit: RATE_LIMIT,
  });

  return {
    status:     "sent",
    message_id: res.data.id,
    thread_id:  res.data.threadId,
    label_ids:  res.data.labelIds,
    rate:       { sent_today: rateState.count, limit: RATE_LIMIT, remaining: RATE_LIMIT - rateState.count },
  };
}

async function draftEmail(args) {
  const { to, subject, body, cc, bcc, reply_to, thread_id } = DraftEmailInput.parse(args);

  logEvent("info", "draft_email", "Saving draft", { to, subject, dry_run: DRY_RUN });

  if (DRY_RUN) {
    return {
      status: "dry_run",
      message: "DRY RUN: draft not saved",
      preview: { to, subject, body: body.slice(0, 120) },
    };
  }

  const gmail  = buildGmailClient();
  const raw    = buildRawMessage({ to, cc, bcc, subject, body, replyTo: reply_to });
  const msgBody = { raw };
  if (thread_id) msgBody.threadId = thread_id;

  const res = await gmail.users.drafts.create({
    userId: GMAIL_USER,
    requestBody: { message: msgBody },
  });

  logEvent("info", "draft_email", "Draft saved", {
    draft_id:   res.data.id,
    message_id: res.data.message?.id,
    requires_approval: true,
  });

  return {
    status:             "drafted",
    draft_id:           res.data.id,
    message_id:         res.data.message?.id,
    thread_id:          res.data.message?.threadId,
    requires_approval:  true,
    note:               "Draft saved to Gmail Drafts. Review and send manually.",
  };
}

async function scheduleEmail(args) {
  const { to, subject, body, send_at, cc, bcc, reply_to, approved } = ScheduleEmailInput.parse(args);

  // Validate send_at is a future datetime
  const sendDate = new Date(send_at);
  if (isNaN(sendDate.getTime())) {
    throw new Error(`Invalid send_at datetime: "${send_at}". Use ISO 8601 format.`);
  }
  if (sendDate <= new Date()) {
    throw new Error(`send_at must be in the future. Got: ${send_at}`);
  }

  // Approval gate for scheduled sends too
  if (REQUIRE_APPROVAL && !approved) {
    const msg = "Approval required for scheduled email: set approved=true";
    logEvent("warn", "schedule_email", msg, { to, subject });
    throw new Error(msg);
  }

  const schedule_id = `sch_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;

  const entry = {
    schedule_id,
    status:    "pending",
    to,
    subject,
    body,
    send_at,
    cc:        cc ?? null,
    bcc:       bcc ?? null,
    reply_to:  reply_to ?? null,
    approved:  approved ?? false,
    created_at: new Date().toISOString(),
    dry_run:   DRY_RUN,
  };

  if (!DRY_RUN) {
    addSchedule(entry);
  }

  logEvent("info", "schedule_email", "Email scheduled", {
    schedule_id,
    send_at,
    to,
    subject,
    dry_run: DRY_RUN,
  });

  return {
    status:      DRY_RUN ? "dry_run" : "scheduled",
    schedule_id,
    send_at,
    message:     DRY_RUN
      ? `DRY RUN: email not scheduled. Would send to ${to} at ${send_at}`
      : `Email queued for ${send_at}. Run process_schedules to execute.`,
    note: "Scheduled emails are stored in schedules.json. A cron/scheduler must call process_schedules to send them.",
  };
}

async function searchInbox(args) {
  const { query, max_results, include_body } = SearchInboxInput.parse(args);

  logEvent("info", "search_inbox", "Searching inbox", {
    query,
    max_results,
    include_body,
    dry_run: DRY_RUN,
  });

  if (DRY_RUN) {
    return {
      status: "dry_run",
      message: "DRY RUN: inbox not searched",
      preview: { query, max_results, include_body },
    };
  }

  try {
    const gmail = buildGmailClient();

    // Search messages
    const response = await gmail.users.messages.list({
      userId: GMAIL_USER,
      q: query,
      maxResults: Math.min(max_results, 100), // Gmail API max is 100
    });

    const messages = response.data.messages || [];

    if (!include_body || messages.length === 0) {
      // Return metadata only
      const results = messages.map(msg => ({
        id: msg.id,
        thread_id: msg.threadId,
        snippet: msg.snippet || "",
      }));

      return {
        status: "ok",
        count: results.length,
        query,
        results,
      };
    }

    // Fetch full message details
    const results = [];
    for (const msg of messages) {
      try {
        const fullMsg = await gmail.users.messages.get({
          userId: GMAIL_USER,
          id: msg.id,
          format: "metadata",
          metadataHeaders: ["From", "To", "Subject", "Date"],
        });

        const headers = fullMsg.data.payload?.headers || [];
        const getHeader = (name) => headers.find(h => h.name === name)?.value || "";

        results.push({
          id: msg.id,
          thread_id: msg.threadId,
          snippet: msg.snippet || "",
          from: getHeader("From"),
          to: getHeader("To"),
          subject: getHeader("Subject"),
          date: getHeader("Date"),
          labels: fullMsg.data.labelIds || [],
        });
      } catch (err) {
        logEvent("warn", "search_inbox", `Failed to fetch message ${msg.id}: ${err.message}`);
      }
    }

    return {
      status: "ok",
      count: results.length,
      query,
      results,
    };
  } catch (err) {
    logEvent("error", "search_inbox", `Search failed: ${err.message}`, { query });
    throw new Error(`Inbox search failed: ${err.message}`);
  }
}

// ─────────────────────────────────────────────
// Tool registry
// ─────────────────────────────────────────────

const TOOLS = [
  {
    name: "send_email",
    description:
      "Send an email immediately via Gmail API. " +
      `Rate limited to ${RATE_LIMIT} emails/day. ` +
      (REQUIRE_APPROVAL ? "REQUIRE_APPROVAL is ON — pass approved=true to send. " : "") +
      "Set DRY_RUN=true in env to preview without sending.",
    inputSchema: {
      type: "object",
      properties: {
        to:        { type: "string",  description: "Recipient address(es)" },
        subject:   { type: "string",  description: "Subject line" },
        body:      { type: "string",  description: "Plain-text body" },
        cc:        { type: "string",  description: "CC — optional" },
        bcc:       { type: "string",  description: "BCC — optional" },
        reply_to:  { type: "string",  description: "Reply-To — optional" },
        thread_id: { type: "string",  description: "Gmail thread ID — optional" },
        approved:  { type: "boolean", description: "Set true to pass approval gate when REQUIRE_APPROVAL=true" },
      },
      required: ["to", "subject", "body"],
    },
  },
  {
    name: "draft_email",
    description:
      "Save an email as a Gmail draft. Always sets requires_approval=true. " +
      "Draft appears in Gmail Drafts and must be sent manually.",
    inputSchema: {
      type: "object",
      properties: {
        to:        { type: "string", description: "Recipient address(es)" },
        subject:   { type: "string", description: "Subject line" },
        body:      { type: "string", description: "Plain-text body" },
        cc:        { type: "string", description: "CC — optional" },
        bcc:       { type: "string", description: "BCC — optional" },
        reply_to:  { type: "string", description: "Reply-To — optional" },
        thread_id: { type: "string", description: "Gmail thread ID — optional" },
      },
      required: ["to", "subject", "body"],
    },
  },
  {
    name: "schedule_email",
    description:
      "Queue an email to be sent at a future datetime. " +
      "Stored in schedules.json — requires a scheduler to call process_schedules to actually send. " +
      "Set DRY_RUN=true in env to preview.",
    inputSchema: {
      type: "object",
      properties: {
        to:       { type: "string",  description: "Recipient address(es)" },
        subject:  { type: "string",  description: "Subject line" },
        body:     { type: "string",  description: "Plain-text body" },
        send_at:  { type: "string",  description: "ISO 8601 future datetime, e.g. 2026-02-27T08:00:00Z" },
        cc:       { type: "string",  description: "CC — optional" },
        bcc:      { type: "string",  description: "BCC — optional" },
        reply_to: { type: "string",  description: "Reply-To — optional" },
        approved: { type: "boolean", description: "Approval flag — required when REQUIRE_APPROVAL=true" },
      },
      required: ["to", "subject", "body", "send_at"],
    },
  },
  {
    name: "search_inbox",
    description:
      "Search Gmail inbox using query syntax. " +
      "Supports all Gmail search operators (is:unread, from:, subject:, after:, before:, etc.). " +
      "Set include_body=true to fetch full message details.",
    inputSchema: {
      type: "object",
      properties: {
        query:        { type: "string",  description: "Gmail search query, e.g. 'is:unread from:client@example.com'" },
        max_results:  { type: "number",  description: "Max results to return (default: 10, max: 100)" },
        include_body: { type: "boolean", description: "Fetch full message metadata (default: false)" },
      },
      required: ["query"],
    },
  },
];

// ─────────────────────────────────────────────
// MCP Server
// ─────────────────────────────────────────────

const server = new Server(
  { name: "ai-employee-email", version: "2.0.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools: TOOLS }));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  logEvent("debug", name, "Tool called", { args });

  try {
    let result;
    switch (name) {
      case "send_email":     result = await sendEmail(args);     break;
      case "draft_email":    result = await draftEmail(args);    break;
      case "schedule_email": result = await scheduleEmail(args); break;
      case "search_inbox":   result = await searchInbox(args);   break;
      default: throw new Error(`Unknown tool: ${name}`);
    }
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  } catch (err) {
    logEvent("error", name, err.message);
    return {
      content: [{ type: "text", text: JSON.stringify({ error: err.message }) }],
      isError: true,
    };
  }
});

// ─────────────────────────────────────────────
// Start
// ─────────────────────────────────────────────

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  logEvent("info", "server", "Email MCP server started (stdio)", {
    version:          "2.0.0",
    dry_run:          DRY_RUN,
    rate_limit:       RATE_LIMIT,
    require_approval: REQUIRE_APPROVAL,
    tools:            TOOLS.map(t => t.name),
    gmail_user:       GMAIL_USER,
  });
}

main().catch((err) => {
  logEvent("error", "server", "Fatal startup error", { error: err.message });
  process.exit(1);
});
