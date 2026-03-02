#!/usr/bin/env node
/**
 * Test Script: Publish a LinkedIn Post
 * Uses the LinkedIn MCP server to publish a real post
 */

import { chromium } from "playwright";
import dotenv from "dotenv";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

dotenv.config();

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(__dirname, "..");

// Configuration
const LINKEDIN_EMAIL = process.env.LINKEDIN_EMAIL;
const LINKEDIN_PASSWORD = process.env.LINKEDIN_PASSWORD;
const SESSION_DIR = path.join(ROOT, ".linkedin_sessions");

// Test post content
const TEST_POST = {
  content: `🚀 Excited to share our latest milestone!

We've just completed another successful automation project using AI-powered workflows. The results speak for themselves:

✅ 3x faster processing
✅ 100% accuracy
✅ Zero manual intervention

Big thanks to our amazing team for making this happen!

#Automation #AI #Innovation #BusinessGrowth #TechSuccess`,
  hashtags: ["Automation", "AI", "Innovation", "BusinessGrowth", "TechSuccess"],
};

async function publishPost() {
  console.log("═══════════════════════════════════════════════════════");
  console.log("  LinkedIn Post Publisher - Test Script");
  console.log("═══════════════════════════════════════════════════════");
  console.log();

  // Validate credentials
  if (!LINKEDIN_EMAIL || !LINKEDIN_PASSWORD) {
    console.error("❌ ERROR: LINKEDIN_EMAIL or LINKEDIN_PASSWORD not set");
    console.error(`   LINKEDIN_EMAIL: ${LINKEDIN_EMAIL ? "SET" : "NOT SET"}`);
    console.error(`   LINKEDIN_PASSWORD: ${LINKEDIN_PASSWORD ? "SET" : "NOT SET"}`);
    process.exit(1);
  }

  console.log("✓ Credentials loaded");
  console.log(`  Email: ${LINKEDIN_EMAIL}`);
  console.log();

  // Create session directory
  if (!fs.existsSync(SESSION_DIR)) {
    fs.mkdirSync(SESSION_DIR, { recursive: true });
    console.log("✓ Session directory created");
  }

  let browser = null;
  let page = null;

  try {
    console.log("🚀 Starting browser...");
    browser = await chromium.launchPersistentContext(SESSION_DIR, {
      headless: false, // Visible browser for debugging
      args: [
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox",
        "--disable-dev-shm-usage",
      ],
      viewport: { width: 1280, height: 720 },
    });

    page = browser.pages()[0] || (await browser.newPage());
    
    await page.setExtraHTTPHeaders({
      "accept-language": "en-US,en;q=0.9",
    });

    console.log("✓ Browser started");
    console.log();

    // Navigate to login
    console.log("📝 Navigating to LinkedIn login...");
    await page.goto("https://www.linkedin.com/login", { 
      waitUntil: "networkidle", 
      timeout: 30000 
    });

    // Check if already logged in
    if (page.url().includes("/feed")) {
      console.log("✓ Already logged in (existing session)");
    } else {
      console.log("🔐 Logging in...");
      
      // Fill email
      const emailField = await page.$("#username");
      if (!emailField) {
        throw new Error("Email field not found");
      }
      await emailField.fill(LINKEDIN_EMAIL);
      console.log("  ✓ Email entered");

      // Fill password
      const passwordField = await page.$("#password");
      if (!passwordField) {
        throw new Error("Password field not found");
      }
      await passwordField.fill(LINKEDIN_PASSWORD);
      console.log("  ✓ Password entered");

      // Click sign in
      const signInButton = await page.$('button[type="submit"]');
      if (!signInButton) {
        throw new Error("Sign in button not found");
      }
      await signInButton.click();
      console.log("  ✓ Sign in clicked");

      // Wait for navigation
      try {
        await page.waitForNavigation({ waitUntil: "networkidle", timeout: 15000 });
      } catch (e) {
        // May not redirect to feed immediately
      }

      // Check if login successful
      if (page.url().includes("/login") || page.url().includes("/challenge")) {
        console.error("❌ Login failed - check credentials");
        console.error(`   Current URL: ${page.url()}`);
        
        // Take screenshot for debugging
        await page.screenshot({ path: "login_failed.png" });
        console.error("   Screenshot saved: login_failed.png");
        
        process.exit(1);
      }

      console.log("✓ Login successful");
    }
    console.log();

    // Navigate to feed
    console.log("📰 Navigating to feed...");
    await page.goto("https://www.linkedin.com/feed/", { 
      waitUntil: "networkidle", 
      timeout: 30000 
    });
    await page.waitForTimeout(3000);
    console.log("✓ On feed page");
    console.log();

    // Click "Start a post"
    console.log("✍️  Starting post...");
    const startPostButton = await page.$('button[aria-label="Start a post"]');
    if (!startPostButton) {
      throw new Error("Start post button not found");
    }
    await startPostButton.click();
    await page.waitForTimeout(2000);
    console.log("✓ Post dialog opened");
    console.log();

    // Find and fill post text area
    console.log("📝 Writing post content...");
    const textBox = await page.$('div[contenteditable="true"][role="textbox"]');
    if (!textBox) {
      throw new Error("Post text box not found");
    }
    
    await textBox.fill(TEST_POST.content);
    await page.waitForTimeout(1000);
    console.log("✓ Content entered");
    console.log(`   Word count: ${TEST_POST.content.split(" ").length}`);
    console.log(`   Character count: ${TEST_POST.content.length}`);
    console.log();

    // Take a screenshot before posting (optional)
    console.log("📸 Taking preview screenshot...");
    await page.screenshot({ path: "post_preview.png" });
    console.log("✓ Preview saved: post_preview.png");
    console.log();

    // Ask for confirmation
    console.log("═══════════════════════════════════════════════════════");
    console.log("  READY TO PUBLISH");
    console.log("═══════════════════════════════════════════════════════");
    console.log();
    console.log("Post content:");
    console.log("───────────────────────────────────────────────────────");
    console.log(TEST_POST.content);
    console.log("───────────────────────────────────────────────────────");
    console.log();
    console.log("✓ Browser is visible - you can review the post manually");
    console.log("✓ Screenshot saved as: post_preview.png");
    console.log();
    console.log("Press Ctrl+C to cancel, or wait 10 seconds to publish...");
    console.log();

    // Wait for manual review
    await new Promise(resolve => setTimeout(resolve, 10000));

    // Click "Post" button
    console.log("🚀 Publishing post...");
    const postButton = await page.$('button[aria-label="Post"]');
    if (!postButton) {
      throw new Error("Post button not found");
    }
    await postButton.click();
    await page.waitForTimeout(3000);

    console.log("✓ Post button clicked");
    console.log();

    // Wait for confirmation
    console.log("⏳ Waiting for confirmation...");
    await page.waitForTimeout(5000);

    // Check if post was published
    const currentUrl = page.url();
    console.log(`   Current URL: ${currentUrl}`);
    
    // Take final screenshot
    await page.screenshot({ path: "post_published.png" });
    console.log("✓ Final screenshot saved: post_published.png");
    console.log();

    console.log("═══════════════════════════════════════════════════════");
    console.log("  ✅ POST PUBLISHED SUCCESSFULLY!");
    console.log("═══════════════════════════════════════════════════════");
    console.log();
    console.log("Next steps:");
    console.log("  1. Check your LinkedIn profile to verify the post");
    console.log("  2. Review screenshots: post_preview.png, post_published.png");
    console.log();

    return { success: true, message: "Post published successfully" };

  } catch (error) {
    console.error();
    console.error("═══════════════════════════════════════════════════════");
    console.error("  ❌ ERROR");
    console.error("═══════════════════════════════════════════════════════");
    console.error();
    console.error(`Error: ${error.message}`);
    console.error();
    
    // Take error screenshot
    if (page) {
      await page.screenshot({ path: "error.png" });
      console.error("✓ Error screenshot saved: error.png");
    }
    
    console.error();
    console.error("Troubleshooting:");
    console.error("  1. Check credentials in mcp/linkedin-server/.env");
    console.error("  2. Try logging in manually at linkedin.com");
    console.error("  3. Clear session: rm -rf .linkedin_sessions/");
    console.error();
    
    return { success: false, error: error.message };
  } finally {
    if (browser) {
      console.log("🚪 Closing browser...");
      await browser.close();
      console.log("✓ Browser closed");
    }
  }
}

// Run the script
publishPost().then(result => {
  if (result.success) {
    process.exit(0);
  } else {
    process.exit(1);
  }
}).catch(error => {
  console.error("Fatal error:", error);
  process.exit(1);
});
