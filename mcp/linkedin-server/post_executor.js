#!/usr/bin/env node
/**
 * Post Executor - Automatically posts content from a file to LinkedIn.
 */

import { chromium } from "playwright";
import dotenv from "dotenv";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

dotenv.config();

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(__dirname, "..");

const LINKEDIN_EMAIL = process.env.LINKEDIN_EMAIL;
const LINKEDIN_PASSWORD = process.env.LINKEDIN_PASSWORD;
const SESSION_DIR = path.join(ROOT, ".linkedin_sessions");

// Get content from file (passed as argument)
const contentFile = process.argv[2];
if (!contentFile || !fs.existsSync(contentFile)) {
  console.error("❌ ERROR: Content file not provided or does not exist.");
  process.exit(1);
}

const POST_CONTENT = fs.readFileSync(contentFile, "utf-8");

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function run() {
  console.log("\n🚀 Starting LinkedIn Post Executor...");
  
  if (!LINKEDIN_EMAIL || !LINKEDIN_PASSWORD) {
    console.error("❌ ERROR: Credentials not set in .env");
    process.exit(1);
  }

  if (!fs.existsSync(SESSION_DIR)) {
    fs.mkdirSync(SESSION_DIR, { recursive: true });
  }

  let browser = null;
  let page = null;

  try {
    browser = await chromium.launchPersistentContext(SESSION_DIR, {
      headless: false, // Set to true for background operation
      args: ["--no-sandbox", "--disable-setuid-sandbox"],
      viewport: { width: 1280, height: 720 },
    });

    page = browser.pages()[0] || (await browser.newPage());
    await page.goto("https://www.linkedin.com/login", { waitUntil: "networkidle", timeout: 30000 });
    
    // Login if needed
    if (!page.url().includes("/feed")) {
      await page.fill("#username", LINKEDIN_EMAIL);
      await page.fill("#password", LINKEDIN_PASSWORD);
      await page.click('button[type="submit"]');
      await page.waitForNavigation({ waitUntil: "networkidle", timeout: 15000 }).catch(() => {});
    }

    if (!page.url().includes("/feed")) {
        // Try direct navigation to feed
        await page.goto("https://www.linkedin.com/feed/", { waitUntil: "networkidle" });
    }

    console.log("✓ Logged in. Opening post dialog...");
    await page.click('button[aria-label="Start a post"]');
    await sleep(2000);

    console.log("✓ Writing content...");
    const textBox = await page.waitForSelector('div[contenteditable="true"][role="textbox"]');
    await textBox.fill(POST_CONTENT);
    await sleep(1000);

    console.log("✓ Publishing...");
    await page.click('button[aria-label="Post"]');
    await sleep(5000);

    console.log("✅ Post published successfully!");
    return { success: true };

  } catch (error) {
    console.error("❌ Error:", error.message);
    if (page) await page.screenshot({ path: "post_error.png" });
    return { success: false, error: error.message };
  } finally {
    if (browser) await browser.close();
  }
}

run().then(res => process.exit(res.success ? 0 : 1));
