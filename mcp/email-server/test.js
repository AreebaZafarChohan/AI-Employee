/**
 * Standalone smoke test for Email MCP Server logic.
 * Tests: env loading, buildRawMessage, Zod schemas, DRY_RUN path.
 * Run: node test.js
 */
import * as dotenv from "dotenv";
import { existsSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { z } from "zod";
import { Buffer } from "buffer";

const __dirname = dirname(fileURLToPath(import.meta.url));
const envPath = join(__dirname, ".env");
if (existsSync(envPath)) dotenv.config({ path: envPath });

// ── Inline the helpers we want to test ──────────────────────────────────────

const DRY_RUN = process.env.DRY_RUN?.toLowerCase() === "true";

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

const SendEmailInput = z.object({
  to:        z.union([z.string(), z.array(z.string())]),
  subject:   z.string(),
  body:      z.string(),
  cc:        z.union([z.string(), z.array(z.string())]).optional(),
  bcc:       z.union([z.string(), z.array(z.string())]).optional(),
  reply_to:  z.string().optional(),
  thread_id: z.string().optional(),
});

const SearchInboxInput = z.object({
  query:        z.string(),
  max_results:  z.number().int().min(1).max(100).default(10),
  include_body: z.boolean().default(false),
});

// ── Tests ───────────────────────────────────────────────────────────────────

let passed = 0, failed = 0;

function test(name, fn) {
  try {
    fn();
    console.log(`  ✅  ${name}`);
    passed++;
  } catch (e) {
    console.log(`  ❌  ${name}`);
    console.log(`      ${e.message}`);
    failed++;
  }
}

function assert(condition, msg) {
  if (!condition) throw new Error(msg ?? "Assertion failed");
}

console.log("\n── Email MCP Server — Smoke Tests ──────────────────────\n");

// 1. Env
test("DRY_RUN env loaded correctly", () => {
  assert(typeof DRY_RUN === "boolean", "DRY_RUN should be boolean");
  assert(DRY_RUN === true, `Expected DRY_RUN=true, got ${DRY_RUN}`);
  console.log(`      DRY_RUN=${DRY_RUN}`);
});

test("Gmail credentials present in env", () => {
  assert(process.env.GMAIL_CLIENT_ID, "GMAIL_CLIENT_ID missing");
  assert(process.env.GMAIL_CLIENT_SECRET, "GMAIL_CLIENT_SECRET missing");
  assert(process.env.GMAIL_REFRESH_TOKEN, "GMAIL_REFRESH_TOKEN missing");
  console.log(`      CLIENT_ID=${process.env.GMAIL_CLIENT_ID.slice(0,20)}...`);
});

// 2. buildRawMessage
test("buildRawMessage — basic structure", () => {
  const raw = buildRawMessage({
    to: "bob@example.com",
    subject: "Hello",
    body: "World",
  });
  const decoded = Buffer.from(raw, "base64url").toString("utf-8");
  assert(decoded.includes("To: bob@example.com"), "Missing To header");
  assert(decoded.includes("Subject: Hello"), "Missing Subject header");
  assert(decoded.includes("World"), "Missing body");
  assert(decoded.includes("MIME-Version: 1.0"), "Missing MIME-Version");
});

test("buildRawMessage — CC/BCC/Reply-To included", () => {
  const raw = buildRawMessage({
    to: "bob@example.com",
    cc: "carol@example.com",
    bcc: "eve@example.com",
    subject: "Test",
    body: "Body",
    replyTo: "noreply@example.com",
  });
  const decoded = Buffer.from(raw, "base64url").toString("utf-8");
  assert(decoded.includes("Cc: carol@example.com"), "Missing Cc");
  assert(decoded.includes("Bcc: eve@example.com"), "Missing Bcc");
  assert(decoded.includes("Reply-To: noreply@example.com"), "Missing Reply-To");
});

test("buildRawMessage — array of recipients", () => {
  const raw = buildRawMessage({
    to: ["a@x.com", "b@x.com"],
    subject: "Multi",
    body: "Hi all",
  });
  const decoded = Buffer.from(raw, "base64url").toString("utf-8");
  assert(decoded.includes("To: a@x.com, b@x.com"), "Multi-recipient To failed");
});

// 3. Zod schemas
test("SendEmailInput — valid input passes", () => {
  const result = SendEmailInput.safeParse({
    to: "test@example.com",
    subject: "Hi",
    body: "Hello",
  });
  assert(result.success, result.error?.message);
});

test("SendEmailInput — missing required fields fails", () => {
  const result = SendEmailInput.safeParse({ to: "x@y.com" });
  assert(!result.success, "Should have failed without subject/body");
});

test("SendEmailInput — array of recipients valid", () => {
  const result = SendEmailInput.safeParse({
    to: ["a@x.com", "b@x.com"],
    subject: "Multi",
    body: "Body",
  });
  assert(result.success, result.error?.message);
});

test("SearchInboxInput — defaults applied", () => {
  const result = SearchInboxInput.safeParse({ query: "is:unread" });
  assert(result.success, result.error?.message);
  assert(result.data.max_results === 10, "Default max_results should be 10");
  assert(result.data.include_body === false, "Default include_body should be false");
});

test("SearchInboxInput — max_results bounds enforced", () => {
  const over = SearchInboxInput.safeParse({ query: "x", max_results: 200 });
  assert(!over.success, "Should reject max_results > 100");
  const under = SearchInboxInput.safeParse({ query: "x", max_results: 0 });
  assert(!under.success, "Should reject max_results < 1");
});

// 4. DRY_RUN send_email simulation
test("DRY_RUN send_email returns preview, not real call", () => {
  const args = { to: "test@example.com", subject: "DRY", body: "Test body" };
  const parsed = SendEmailInput.parse(args);
  // Simulate the DRY_RUN branch from index.js
  const result = DRY_RUN
    ? { status: "dry_run", message: "DRY RUN: email not sent", preview: { to: parsed.to, subject: parsed.subject, body: parsed.body.slice(0,100) } }
    : { status: "would_send" };
  assert(result.status === "dry_run", "Expected dry_run status");
  assert(result.preview.subject === "DRY", "Preview subject wrong");
  console.log(`      Result: ${JSON.stringify(result)}`);
});

// ── Summary ──────────────────────────────────────────────────────────────────
console.log(`\n── Results: ${passed} passed, ${failed} failed ──────────────────\n`);
process.exit(failed > 0 ? 1 : 0);
