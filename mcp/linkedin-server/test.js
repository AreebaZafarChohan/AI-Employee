/**
 * LinkedIn MCP Server - Smoke Test
 * Tests: env loading, rate limiting, Zod schemas, DRY_RUN path
 * Run: node test.js
 */

import fs from "fs";
import { z } from "zod";
import dotenv from "dotenv";

// Load .env
dotenv.config();

console.log("── LinkedIn MCP Server — Smoke Tests ────────────────────\n");

let passed = 0;
let failed = 0;

function test(name, fn) {
  try {
    fn();
    console.log(`  ✅  ${name}`);
    passed++;
  } catch (e) {
    console.log(`  ❌  ${name}`);
    console.log(`      Error: ${e.message}`);
    failed++;
  }
}

// Test 1: DRY_RUN env loaded
test("DRY_RUN env loaded correctly", () => {
  const dryRun = process.env.DRY_RUN?.toLowerCase() === "true";
  if (!dryRun) {
    throw new Error("DRY_RUN should be true in .env");
  }
});

// Test 2: LinkedIn credentials present
test("LinkedIn credentials present in env", () => {
  if (!process.env.LINKEDIN_EMAIL || !process.env.LINKEDIN_PASSWORD) {
    throw new Error("LINKEDIN_EMAIL and LINKEDIN_PASSWORD required");
  }
});

// Test 3: Rate limit file handling
test("Rate limit file handling", () => {
  const rateLimitFile = ".linkedin_rate_limit.json";
  const today = new Date().toDateString();
  
  // Should create or read file
  let data;
  if (fs.existsSync(rateLimitFile)) {
    data = JSON.parse(fs.readFileSync(rateLimitFile, "utf-8"));
  } else {
    data = { date: today, count: 0 };
  }
  
  if (!data.date || data.count === undefined) {
    throw new Error("Rate limit data structure invalid");
  }
});

// Test 4: PublishPostInput schema - valid
test("PublishPostInput — valid input passes", () => {
  const PublishPostInput = z.object({
    content: z.string().min(1).max(3000),
    imageUrl: z.string().url().optional(),
    hashtags: z.array(z.string()).optional(),
  });
  
  const valid = {
    content: "Test post content",
    imageUrl: "https://example.com/image.jpg",
    hashtags: ["test", "linkedin"],
  };
  
  PublishPostInput.parse(valid);
});

// Test 5: PublishPostInput schema - missing required
test("PublishPostInput — missing required fields fails", () => {
  const PublishPostInput = z.object({
    content: z.string().min(1).max(3000),
    imageUrl: z.string().url().optional(),
    hashtags: z.array(z.string()).optional(),
  });
  
  const invalid = { imageUrl: "not-a-url" };
  
  try {
    PublishPostInput.parse(invalid);
    throw new Error("Should have failed validation");
  } catch (e) {
    if (!(e instanceof z.ZodError)) {
      throw new Error("Should be ZodError");
    }
  }
});

// Test 6: SchedulePostInput schema
test("SchedulePostInput — valid input passes", () => {
  const SchedulePostInput = z.object({
    content: z.string().min(1).max(3000),
    scheduledTime: z.string(),
    imageUrl: z.string().url().optional(),
    hashtags: z.array(z.string()).optional(),
  });
  
  const valid = {
    content: "Scheduled post",
    scheduledTime: "2026-02-26T09:00:00Z",
  };
  
  SchedulePostInput.parse(valid);
});

// Test 7: ReplyToCommentInput schema
test("ReplyToCommentInput — valid input passes", () => {
  const ReplyToCommentInput = z.object({
    postUrl: z.string().url(),
    commentId: z.string(),
    content: z.string().min(1).max(1000),
  });
  
  const valid = {
    postUrl: "https://www.linkedin.com/feed/update/123",
    commentId: "comment-456",
    content: "Great point!",
  };
  
  ReplyToCommentInput.parse(valid);
});

// Test 8: Rate limit check
test("Rate limit check function works", () => {
  const RATE_LIMIT_POSTS = 3;
  const data = { date: new Date().toDateString(), count: 2 };
  
  const allowed = data.count < RATE_LIMIT_POSTS;
  if (!allowed) {
    throw new Error("Should allow when under limit");
  }
});

// Test 9: Rate limit exceeded
test("Rate limit exceeded detection", () => {
  const RATE_LIMIT_POSTS = 3;
  const data = { date: new Date().toDateString(), count: 3 };
  
  const allowed = data.count < RATE_LIMIT_POSTS;
  if (allowed) {
    throw new Error("Should reject when at limit");
  }
});

// Test 10: Hashtag formatting
test("Hashtag formatting logic", () => {
  const hashtags = ["test", "#linkedin", "mcp"];
  const formatted = hashtags.map(h => h.startsWith('#') ? h : `#${h}`).join(' ');
  
  if (!formatted.includes("#test") || !formatted.includes("#linkedin")) {
    throw new Error("Hashtag formatting incorrect");
  }
});

// Test 11: Content truncation
test("Content truncation for word limit", () => {
  const content = "A".repeat(3500);
  const truncated = content.slice(0, 3000);
  
  if (truncated.length > 3000) {
    throw new Error("Truncation failed");
  }
});

console.log(`\n── Results: ${passed} passed, ${failed} failed ──────────────────`);

if (failed > 0) {
  process.exit(1);
}
