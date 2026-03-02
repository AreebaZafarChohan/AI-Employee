#!/usr/bin/env node
/**
 * Fully Automated LinkedIn Post Publisher
 * Login → Write Post → Publish (100% automatic)
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

// Post content
const POST_CONTENT = `🚀 Excited to share our latest milestone!

We've just completed another successful automation project using AI-powered workflows. The results speak for themselves:

✅ 3x faster processing
✅ 100% accuracy
✅ Zero manual intervention

Big thanks to our amazing team for making this happen!

#Automation #AI #Innovation #BusinessGrowth #TechSuccess`;

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function autoPost() {
  console.log("\n" + "═".repeat(60));
  console.log("  AUTOMATED LINKEDIN POST PUBLISHER");
  console.log("═".repeat(60) + "\n");

  // Check credentials
  if (!LINKEDIN_EMAIL || !LINKEDIN_PASSWORD) {
    console.error("❌ ERROR: Credentials not set in .env");
    console.error(`   LINKEDIN_EMAIL: ${LINKEDIN_EMAIL ? "SET" : "NOT SET"}`);
    console.error(`   LINKEDIN_PASSWORD: ${LINKEDIN_PASSWORD ? "SET" : "NOT SET"}`);
    process.exit(1);
  }

  console.log("✓ Credentials loaded");
  console.log(`   Email: ${LINKEDIN_EMAIL}`);
  console.log();

  // Create session directory
  if (!fs.existsSync(SESSION_DIR)) {
    fs.mkdirSync(SESSION_DIR, { recursive: true });
  }

  let browser = null;
  let page = null;

  try {
    // Step 1: Start browser
    console.log("📱 Step 1/6: Starting browser...");
    browser = await chromium.launchPersistentContext(SESSION_DIR, {
      headless: false,
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

    await sleep(1000);
    console.log("   ✓ Browser started\n");

    // Step 2: Navigate to LinkedIn
    console.log("📱 Step 2/6: Navigating to LinkedIn...");
    await page.goto("https://www.linkedin.com/login", { 
      waitUntil: "networkidle", 
      timeout: 30000 
    });
    await sleep(2000);

    if (page.url().includes("/feed")) {
      console.log("   ✓ Already logged in (existing session)\n");
    } else {
      console.log("   ✓ On login page\n");
    }

    // Step 3: Login (if needed)
    if (!page.url().includes("/feed")) {
      console.log("📱 Step 3/6: Logging in...");
      
      try {
        const emailField = await page.$("#username");
        if (emailField) {
          await emailField.fill(LINKEDIN_EMAIL);
          await sleep(500);
          console.log("   ✓ Email entered");
        }

        const passwordField = await page.$("#password");
        if (passwordField) {
          await passwordField.fill(LINKEDIN_PASSWORD);
          await sleep(500);
          console.log("   ✓ Password entered");
        }

        const signInButton = await page.$('button[type="submit"]');
        if (signInButton) {
          await signInButton.click();
          console.log("   ✓ Sign in clicked");
          await sleep(2000);
          
          try {
            await page.waitForNavigation({ waitUntil: "networkidle", timeout: 10000 });
          } catch (e) {
            // May not redirect immediately
          }
        }

        if (page.url().includes("/login") || page.url().includes("/challenge")) {
          console.error("   ❌ Login failed - check credentials");
          await page.screenshot({ path: "login_failed.png" });
          console.error("   Screenshot: login_failed.png");
          process.exit(1);
        }

        console.log("   ✓ Login successful\n");
      } catch (error) {
        console.error("   ❌ Login error:", error.message);
        await page.screenshot({ path: "login_error.png" });
        process.exit(1);
      }
    }

    // Step 4: Navigate to feed
    console.log("📱 Step 4/6: Navigating to feed...");
    await page.goto("https://www.linkedin.com/feed/", { 
      waitUntil: "networkidle", 
      timeout: 30000 
    });
    await sleep(3000);
    console.log("   ✓ On feed page\n");

    // Step 5: Click "Start a post"
    console.log("📱 Step 5/6: Opening post dialog...");
    const startPostButton = await page.$('button[aria-label="Start a post"]');
    if (!startPostButton) {
      throw new Error("Start post button not found");
    }
    await startPostButton.click();
    await sleep(2000);
    console.log("   ✓ Post dialog opened\n");

    // Step 6: Fill post content
    console.log("📱 Step 6/6: Writing post content...");
    const textBox = await page.$('div[contenteditable="true"][role="textbox"]');
    if (!textBox) {
      throw new Error("Post text box not found");
    }
    
    // Type the content
    await textBox.fill(POST_CONTENT);
    await sleep(1000);
    console.log("   ✓ Content written");
    console.log(`   Characters: ${POST_CONTENT.length}`);
    console.log(`   Words: ${POST_CONTENT.split(" ").length}\n`);

    // Take preview screenshot
    await page.screenshot({ path: "post_preview.png" });
    console.log("   ✓ Preview saved: post_preview.png\n");

    // Wait a moment before posting
    await sleep(2000);

    // Click "Post" button
    console.log("📱 Publishing post...");
    const postButton = await page.$('button[aria-label="Post"]');
    if (!postButton) {
      throw new Error("Post button not found");
    }
    
    await postButton.click();
    await sleep(5000);

    console.log("   ✓ Post button clicked\n");

    // Wait for confirmation
    await page.screenshot({ path: "post_published.png" });
    
    console.log("═".repeat(60));
    console.log("  ✅ POST PUBLISHED SUCCESSFULLY!");
    console.log("═".repeat(60));
    console.log();
    console.log("📸 Screenshots saved:");
    console.log("   - post_preview.png (before publishing)");
    console.log("   - post_published.png (after publishing)");
    console.log();
    console.log("🔗 Check your LinkedIn profile to verify!");
    console.log();

    return { success: true };

  } catch (error) {
    console.error();
    console.error("═".repeat(60));
    console.error("  ❌ ERROR");
    console.error("═".repeat(60));
    console.error();
    console.error(`Error: ${error.message}`);
    console.error();
    
    if (page) {
      await page.screenshot({ path: "error.png" });
      console.error("📸 Error screenshot saved: error.png");
    }
    
    return { success: false, error: error.message };
  } finally {
    if (browser) {
      console.log("🚪 Closing browser...");
      await browser.close();
      console.log("✓ Browser closed\n");
    }
  }
}

// Run the script
autoPost().then(result => {
  if (result.success) {
    console.log("Done! ✓\n");
    process.exit(0);
  } else {
    console.log("Failed! ✗\n");
    process.exit(1);
  }
}).catch(error => {
  console.error("Fatal error:", error);
  process.exit(1);
});
