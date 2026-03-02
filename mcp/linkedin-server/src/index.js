#!/usr/bin/env node
/**
 * @ai-employee/mcp-linkedin-server
 *
 * MCP server that exposes LinkedIn automation tools via Playwright:
 *   - publish_post    Publish a post to LinkedIn
 *   - schedule_post   Schedule a post for later
 *   - reply_to_comment Reply to a comment on a post
 *
 * Environment variables (all in .env or shell):
 *   LINKEDIN_EMAIL       - LinkedIn email/username
 *   LINKEDIN_PASSWORD    - LinkedIn password
 *   DRY_RUN              - Set to "true" to simulate without posting
 *   LOG_LEVEL            - DEBUG/INFO/WARNING/ERROR (default: INFO)
 *   RATE_LIMIT_POSTS     - Max posts per day (default: 3)
 *
 * Usage:
 *   npm start
 *   DRY_RUN=true npm start
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import { chromium } from "playwright";
import dotenv from "dotenv";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import fs from "fs";

// Load environment variables
dotenv.config();

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, "..");

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

const LINKEDIN_EMAIL = process.env.LINKEDIN_EMAIL || "";
const LINKEDIN_PASSWORD = process.env.LINKEDIN_PASSWORD || "";
const DRY_RUN = process.env.DRY_RUN?.toLowerCase() === "true";
const LOG_LEVEL = (process.env.LOG_LEVEL || "INFO").toUpperCase();
const RATE_LIMIT_POSTS = parseInt(process.env.RATE_LIMIT_POSTS || "3", 10);

const RATE_LIMIT_FILE = join(ROOT, ".linkedin_rate_limit.json");
const SESSION_DIR = join(ROOT, ".linkedin_sessions");

// LinkedIn URLs
const LINKEDIN_LOGIN_URL = "https://www.linkedin.com/login";
const LINKEDIN_FEED_URL = "https://www.linkedin.com/feed/";

// ---------------------------------------------------------------------------
// Logger
// ---------------------------------------------------------------------------

const logger = {
  debug: (msg) => log("DEBUG", msg),
  info: (msg) => log("INFO", msg),
  warn: (msg) => log("WARNING", msg),
  error: (msg) => log("ERROR", msg),
};

function log(level, message) {
  const levels = { DEBUG: 0, INFO: 1, WARNING: 2, ERROR: 3 };
  if (levels[level] >= levels[LOG_LEVEL]) {
    const timestamp = new Date().toISOString();
    console.error(`${timestamp} | ${level.padEnd(7)} | linkedin_mcp | ${message}`);
  }
}

// ---------------------------------------------------------------------------
// Rate Limiting
// ---------------------------------------------------------------------------

function loadRateLimitData() {
  try {
    if (fs.existsSync(RATE_LIMIT_FILE)) {
      const data = JSON.parse(fs.readFileSync(RATE_LIMIT_FILE, "utf-8"));
      // Reset if it's a new day
      const today = new Date().toDateString();
      if (data.date !== today) {
        return { date: today, count: 0 };
      }
      return data;
    }
  } catch (e) {
    logger.warn(`Failed to load rate limit data: ${e.message}`);
  }
  return { date: new Date().toDateString(), count: 0 };
}

function saveRateLimitData(data) {
  try {
    fs.writeFileSync(RATE_LIMIT_FILE, JSON.stringify(data, null, 2));
  } catch (e) {
    logger.warn(`Failed to save rate limit data: ${e.message}`);
  }
}

function checkRateLimit() {
  const data = loadRateLimitData();
  if (data.count >= RATE_LIMIT_POSTS) {
    return {
      allowed: false,
      remaining: 0,
      message: `Rate limit exceeded: ${data.count}/${RATE_LIMIT_POSTS} posts today`,
    };
  }
  return {
    allowed: true,
    remaining: RATE_LIMIT_POSTS - data.count,
    message: `${data.remaining} posts remaining today`,
  };
}

function incrementPostCount() {
  const data = loadRateLimitData();
  data.count++;
  saveRateLimitData(data);
  logger.info(`Post count incremented: ${data.count}/${RATE_LIMIT_POSTS}`);
}

// ---------------------------------------------------------------------------
// Input Validation Schemas
// ---------------------------------------------------------------------------

const PublishPostInput = z.object({
  content: z.string().min(1).max(3000).describe("Post content (max 3000 chars)"),
  imageUrl: z.string().url().optional().describe("Optional image URL"),
  hashtags: z.array(z.string()).optional().describe("Optional hashtags"),
});

const SchedulePostInput = z.object({
  content: z.string().min(1).max(3000).describe("Post content"),
  scheduledTime: z.string().describe("ISO 8601 timestamp for scheduling"),
  imageUrl: z.string().url().optional().describe("Optional image URL"),
  hashtags: z.array(z.string()).optional().describe("Optional hashtags"),
});

const ReplyToCommentInput = z.object({
  postUrl: z.string().url().describe("URL of the post"),
  commentId: z.string().describe("ID of the comment to reply to"),
  content: z.string().min(1).max(1000).describe("Reply content (max 1000 chars)"),
});

// ---------------------------------------------------------------------------
// LinkedIn Browser Automation
// ---------------------------------------------------------------------------

class LinkedInBrowser {
  constructor() {
    this.browser = null;
    this.page = null;
    this.loggedIn = false;
  }

  async start() {
    logger.info("Starting browser...");
    
    // Create session directory
    if (!fs.existsSync(SESSION_DIR)) {
      fs.mkdirSync(SESSION_DIR, { recursive: true });
    }

    this.browser = await chromium.launchPersistentContext(SESSION_DIR, {
      headless: true,
      args: [
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox",
        "--disable-dev-shm-usage",
      ],
      viewport: { width: 1280, height: 720 },
    });

    this.page = this.browser.pages()[0] || (await this.browser.newPage());
    
    // Set headers to avoid detection
    await this.page.setExtraHTTPHeaders({
      "accept-language": "en-US,en;q=0.9",
    });

    logger.debug("Browser started");
  }

  async stop() {
    if (this.browser) {
      await this.browser.close();
      this.browser = null;
      this.page = null;
      this.loggedIn = false;
      logger.debug("Browser stopped");
    }
  }

  async login() {
    if (this.loggedIn) {
      logger.debug("Already logged in");
      return true;
    }

    logger.info("Navigating to LinkedIn login...");
    await this.page.goto(LINKEDIN_LOGIN_URL, { waitUntil: "networkidle", timeout: 30000 });

    // Check if already logged in
    if (this.page.url().includes("/feed")) {
      logger.info("Already logged in (existing session)");
      this.loggedIn = true;
      return true;
    }

    // Attempt login
    logger.info("Logging in with credentials...");
    
    try {
      // Fill email
      const emailField = await this.page.$("#username");
      if (!emailField) {
        throw new Error("Email field not found");
      }
      await emailField.fill(LINKEDIN_EMAIL);

      // Fill password
      const passwordField = await this.page.$("#password");
      if (!passwordField) {
        throw new Error("Password field not found");
      }
      await passwordField.fill(LINKEDIN_PASSWORD);

      // Click sign in
      const signInButton = await this.page.$('button[type="submit"]');
      if (!signInButton) {
        throw new Error("Sign in button not found");
      }
      await signInButton.click();

      // Wait for navigation
      await this.page.waitForNavigation({ waitUntil: "networkidle", timeout: 10000 }).catch(() => {
        // May not redirect to feed
      });

      // Check if login successful
      if (this.page.url().includes("/login") || this.page.url().includes("/challenge")) {
        logger.error("Login failed - check credentials");
        return false;
      }

      this.loggedIn = true;
      logger.info("Login successful");
      return true;
    } catch (error) {
      logger.error(`Login error: ${error.message}`);
      return false;
    }
  }

  async publishPost(content, imageUrl, hashtags) {
    logger.info("Publishing post...");

    try {
      // Navigate to feed
      await this.page.goto(LINKEDIN_FEED_URL, { waitUntil: "networkidle", timeout: 30000 });
      await this.page.waitForTimeout(3000);

      // Click on "Start a post"
      const startPostButton = await this.page.$('button[aria-label="Start a post"]');
      if (!startPostButton) {
        throw new Error("Start post button not found");
      }
      await startPostButton.click();
      await this.page.waitForTimeout(1000);

      // Find and fill post text area
      const textBox = await this.page.$('div[contenteditable="true"][role="textbox"]');
      if (!textBox) {
        throw new Error("Post text box not found");
      }
      
      // Add hashtags if provided
      let fullContent = content;
      if (hashtags && hashtags.length > 0) {
        fullContent = `${content}\n\n${hashtags.map(h => h.startsWith('#') ? h : `#${h}`).join(' ')}`;
      }
      
      await textBox.fill(fullContent);
      await this.page.waitForTimeout(500);

      // Add image if provided
      if (imageUrl) {
        logger.debug(`Adding image: ${imageUrl}`);
        // Note: Direct image URL posting requires additional handling
        // This is a simplified version
      }

      // Click "Post" button
      const postButton = await this.page.$('button[aria-label="Post"]');
      if (!postButton) {
        throw new Error("Post button not found");
      }
      await postButton.click();
      await this.page.waitForTimeout(2000);

      logger.info("Post published successfully");
      return { success: true, message: "Post published" };
    } catch (error) {
      logger.error(`Publish error: ${error.message}`);
      return { success: false, error: error.message };
    }
  }

  async schedulePost(content, scheduledTime, imageUrl, hashtags) {
    logger.info(`Scheduling post for: ${scheduledTime}`);

    // Note: LinkedIn's native scheduling requires LinkedIn Premium/Campaign Manager
    // This is a simulation that stores the scheduled post locally
    
    const scheduleData = {
      content,
      scheduledTime,
      imageUrl,
      hashtags,
      createdAt: new Date().toISOString(),
      status: "scheduled",
    };

    const scheduleFile = join(ROOT, ".linkedin_scheduled_posts.json");
    let scheduled = [];
    
    if (fs.existsSync(scheduleFile)) {
      scheduled = JSON.parse(fs.readFileSync(scheduleFile, "utf-8"));
    }
    
    scheduled.push(scheduleData);
    fs.writeFileSync(scheduleFile, JSON.stringify(scheduled, null, 2));

    logger.info(`Post scheduled for ${scheduledTime}`);
    return { success: true, message: `Post scheduled for ${scheduledTime}`, scheduleData };
  }

  async replyToComment(postUrl, commentId, content) {
    logger.info(`Replying to comment ${commentId} on ${postUrl}`);

    try {
      // Navigate to post
      await this.page.goto(postUrl, { waitUntil: "networkidle", timeout: 30000 });
      await this.page.waitForTimeout(2000);

      // Find comment reply box (simplified - actual selector may vary)
      const replyBox = await this.page.$(`[data-comment-id="${commentId}"] textarea`);
      if (!replyBox) {
        throw new Error("Reply box not found");
      }

      await replyBox.fill(content);
      await this.page.waitForTimeout(500);

      // Click reply button
      const replyButton = await this.page.$('button[aria-label="Reply"]');
      if (!replyButton) {
        throw new Error("Reply button not found");
      }
      await replyButton.click();
      await this.page.waitForTimeout(1000);

      logger.info("Reply posted successfully");
      return { success: true, message: "Reply posted" };
    } catch (error) {
      logger.error(`Reply error: ${error.message}`);
      return { success: false, error: error.message };
    }
  }
}

// ---------------------------------------------------------------------------
// MCP Server Setup
// ---------------------------------------------------------------------------

const server = new Server(
  {
    name: "ai-employee-linkedin",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Tool definitions
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "publish_post",
        description: "Publish a post to LinkedIn",
        inputSchema: {
          type: "object",
          properties: {
            content: {
              type: "string",
              description: "Post content (max 3000 characters)",
              minLength: 1,
              maxLength: 3000,
            },
            imageUrl: {
              type: "string",
              description: "Optional image URL",
              format: "uri",
            },
            hashtags: {
              type: "array",
              items: { type: "string" },
              description: "Optional hashtags (without #)",
            },
          },
          required: ["content"],
        },
      },
      {
        name: "schedule_post",
        description: "Schedule a post for later publishing",
        inputSchema: {
          type: "object",
          properties: {
            content: {
              type: "string",
              description: "Post content (max 3000 characters)",
              minLength: 1,
              maxLength: 3000,
            },
            scheduledTime: {
              type: "string",
              description: "ISO 8601 timestamp for scheduling (e.g., 2026-02-26T09:00:00Z)",
              format: "date-time",
            },
            imageUrl: {
              type: "string",
              description: "Optional image URL",
              format: "uri",
            },
            hashtags: {
              type: "array",
              items: { type: "string" },
              description: "Optional hashtags (without #)",
            },
          },
          required: ["content", "scheduledTime"],
        },
      },
      {
        name: "reply_to_comment",
        description: "Reply to a comment on a LinkedIn post",
        inputSchema: {
          type: "object",
          properties: {
            postUrl: {
              type: "string",
              description: "URL of the LinkedIn post",
              format: "uri",
            },
            commentId: {
              type: "string",
              description: "ID of the comment to reply to",
            },
            content: {
              type: "string",
              description: "Reply content (max 1000 characters)",
              minLength: 1,
              maxLength: 1000,
            },
          },
          required: ["postUrl", "commentId", "content"],
        },
      },
    ],
  };
});

// Tool execution handler
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  
  logger.info(`Tool called: ${name}`);
  
  const linkedin = new LinkedInBrowser();
  
  try {
    // Validate credentials
    if (!LINKEDIN_EMAIL || !LINKEDIN_PASSWORD) {
      throw new Error("LINKEDIN_EMAIL and LINKEDIN_PASSWORD environment variables required");
    }

    // Start browser
    await linkedin.start();
    
    // Login
    const loginSuccess = await linkedin.login();
    if (!loginSuccess) {
      throw new Error("Failed to login to LinkedIn");
    }

    switch (name) {
      case "publish_post": {
        // Validate input
        const validated = PublishPostInput.parse(args);
        
        // Check rate limit
        const rateLimit = checkRateLimit();
        if (!rateLimit.allowed) {
          return {
            content: [{ type: "text", text: JSON.stringify({ status: "error", message: rateLimit.message }, null, 2) }],
          };
        }

        // DRY_RUN mode
        if (DRY_RUN) {
          logger.info("[DRY_RUN] Would publish post");
          return {
            content: [{
              type: "text",
              text: JSON.stringify({
                status: "dry_run",
                message: "Post would be published (DRY_RUN mode)",
                content: validated.content,
                hashtags: validated.hashtags,
                rateLimit: rateLimit,
              }, null, 2),
            }],
          };
        }

        // Publish post
        const result = await linkedin.publishPost(
          validated.content,
          validated.imageUrl,
          validated.hashtags
        );

        if (result.success) {
          incrementPostCount();
        }

        return {
          content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
        };
      }

      case "schedule_post": {
        // Validate input
        const validated = SchedulePostInput.parse(args);
        
        // DRY_RUN mode
        if (DRY_RUN) {
          logger.info("[DRY_RUN] Would schedule post");
          return {
            content: [{
              type: "text",
              text: JSON.stringify({
                status: "dry_run",
                message: "Post would be scheduled (DRY_RUN mode)",
                content: validated.content,
                scheduledTime: validated.scheduledTime,
                hashtags: validated.hashtags,
              }, null, 2),
            }],
          };
        }

        // Schedule post
        const result = await linkedin.schedulePost(
          validated.content,
          validated.scheduledTime,
          validated.imageUrl,
          validated.hashtags
        );

        return {
          content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
        };
      }

      case "reply_to_comment": {
        // Validate input
        const validated = ReplyToCommentInput.parse(args);
        
        // DRY_RUN mode
        if (DRY_RUN) {
          logger.info("[DRY_RUN] Would reply to comment");
          return {
            content: [{
              type: "text",
              text: JSON.stringify({
                status: "dry_run",
                message: "Would reply to comment (DRY_RUN mode)",
                postUrl: validated.postUrl,
                commentId: validated.commentId,
                content: validated.content,
              }, null, 2),
            }],
          };
        }

        // Reply to comment
        const result = await linkedin.replyToComment(
          validated.postUrl,
          validated.commentId,
          validated.content
        );

        return {
          content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
        };
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    logger.error(`Tool execution error: ${error.message}`);
    
    // Format error for Zod validation errors
    if (error instanceof z.ZodError) {
      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            status: "error",
            message: "Validation failed",
            errors: error.errors.map(e => ({ field: e.path.join("."), message: e.message })),
          }, null, 2),
        }],
      };
    }

    return {
      content: [{
        type: "text",
        text: JSON.stringify({
          status: "error",
          message: error.message,
        }, null, 2),
      }],
    };
  } finally {
    // Always cleanup
    await linkedin.stop();
  }
});

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function main() {
  logger.info(`Starting LinkedIn MCP Server (DRY_RUN=${DRY_RUN})`);
  logger.info(`Rate limit: ${RATE_LIMIT_POSTS} posts/day`);
  
  // Check credentials
  if (!LINKEDIN_EMAIL || !LINKEDIN_PASSWORD) {
    logger.error("Missing credentials. Set LINKEDIN_EMAIL and LINKEDIN_PASSWORD in .env");
    process.exit(1);
  }

  const transport = new StdioServerTransport();
  await server.connect(transport);
  
  logger.info("LinkedIn MCP server running on stdio");
}

main().catch((error) => {
  logger.error(`Fatal error: ${error.message}`);
  process.exit(1);
});
