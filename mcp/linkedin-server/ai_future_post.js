#!/usr/bin/env node
/**
 * AI Future Post - Automated LinkedIn Publisher
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

// AI Future Post Content (Short & Impactful)
const POST_CONTENT = `🤖 AI ka future yahan hai!

Kya aap ready hain?

AI sirf automation nahi hai - ye transformation hai:

📈 10x productivity
🎯 Smart decision making
⚡ Real-time insights
🚀 Unlimited possibilities

Jo businesses AI adopt karenge, wo lead karenge.
Jo wait karenge, wo peeche reh jayenge.

**The future belongs to AI-first companies.**

Aapka business AI-ready hai? 💭

#AI #FutureOfWork #DigitalTransformation #Innovation #BusinessGrowth #TechTrends #Automation #Leadership`;

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function autoPost() {
  console.log("\n" + "═".repeat(60));
  console.log("  AI FUTURE - LINKEDIN POST");
  console.log("═".repeat(60) + "\n");

  if (!LINKEDIN_EMAIL || !LINKEDIN_PASSWORD) {
    console.error("❌ Credentials not set!");
    process.exit(1);
  }

  console.log("✓ Credentials loaded");
  console.log();

  if (!fs.existsSync(SESSION_DIR)) {
    fs.mkdirSync(SESSION_DIR, { recursive: true });
  }

  let browser = null;
  let page = null;

  try {
    // Step 1
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
    await page.setExtraHTTPHeaders({ "accept-language": "en-US,en;q=0.9" });
    await sleep(1000);
    console.log("   ✓ Browser started\n");

    // Step 2
    console.log("📱 Step 2/6: Navigating to LinkedIn...");
    await page.goto("https://www.linkedin.com/login", { waitUntil: "networkidle", timeout: 30000 });
    await sleep(2000);

    if (page.url().includes("/feed")) {
      console.log("   ✓ Already logged in\n");
    } else {
      console.log("   ✓ On login page\n");
    }

    // Step 3
    if (!page.url().includes("/feed")) {
      console.log("📱 Step 3/6: Logging in...");
      
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
        try { await page.waitForNavigation({ waitUntil: "networkidle", timeout: 10000 }); } catch (e) {}
      }

      if (page.url().includes("/login")) {
        console.error("   ❌ Login failed!");
        await page.screenshot({ path: "login_failed.png" });
        process.exit(1);
      }
      console.log("   ✓ Login successful\n");
    }

    // Step 4
    console.log("📱 Step 4/6: Navigating to feed...");
    await page.goto("https://www.linkedin.com/feed/", { waitUntil: "networkidle", timeout: 30000 });
    await sleep(3000);
    console.log("   ✓ On feed page\n");

    // Step 5
    console.log("📱 Step 5/6: Opening post dialog...");
    const startPostButton = await page.$('button[aria-label="Start a post"]');
    if (!startPostButton) throw new Error("Start post button not found");
    await startPostButton.click();
    await sleep(2000);
    console.log("   ✓ Post dialog opened\n");

    // Step 6
    console.log("📱 Step 6/6: Writing AI post...");
    const textBox = await page.$('div[contenteditable="true"][role="textbox"]');
    if (!textBox) throw new Error("Text box not found");
    
    await textBox.fill(POST_CONTENT);
    await sleep(1000);
    console.log("   ✓ Content written");
    console.log(`   Characters: ${POST_CONTENT.length}`);
    console.log(`   Words: ${POST_CONTENT.split(" ").length}\n`);

    await page.screenshot({ path: "ai_post_preview.png" });
    console.log("   ✓ Preview: ai_post_preview.png\n");

    await sleep(2000);

    // Publish
    console.log("📱 Publishing AI post...");
    const postButton = await page.$('button[aria-label="Post"]');
    if (!postButton) throw new Error("Post button not found");
    
    await postButton.click();
    await sleep(5000);
    console.log("   ✓ Post published!\n");

    await page.screenshot({ path: "ai_post_published.png" });

    console.log("═".repeat(60));
    console.log("  ✅ AI FUTURE POST PUBLISHED!");
    console.log("═".repeat(60));
    console.log();
    console.log("📸 Screenshots:");
    console.log("   - ai_post_preview.png");
    console.log("   - ai_post_published.png");
    console.log();
    console.log("🔗 Check your LinkedIn!");
    console.log();

    return { success: true };

  } catch (error) {
    console.error();
    console.error("═".repeat(60));
    console.error("  ❌ ERROR:", error.message);
    console.error("═".repeat(60));
    console.error();
    
    if (page) {
      await page.screenshot({ path: "ai_error.png" });
      console.error("📸 Error: ai_error.png");
    }
    
    return { success: false, error: error.message };
  } finally {
    if (browser) {
      await browser.close();
    }
  }
}

autoPost().then(r => {
  console.log(r.success ? "Done! ✓\n" : "Failed! ✗\n");
  process.exit(r.success ? 0 : 1);
}).catch(e => {
  console.error("Fatal:", e);
  process.exit(1);
});
