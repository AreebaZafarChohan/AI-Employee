#!/usr/bin/env node
/**
 * Fully automated LinkedIn post - headless mode
 */

import { chromium } from "playwright";
import dotenv from "dotenv";

dotenv.config();

const LINKEDIN_EMAIL = process.env.LINKEDIN_EMAIL;
const LINKEDIN_PASSWORD = process.env.LINKEDIN_PASSWORD;

const POST_CONTENT = `🤖 AI ka future yahan hai!

Kya aap ready hain?

AI sirf automation nahi hai - ye transformation hai:

📈 10x productivity
🎯 Smart decision making
⚡ Real-time insights
🚀 Unlimited possibilities

Jo businesses AI adopt karenge, wo lead karenge.
Jo wait karenge, wo peeche reh jayenge.

The future belongs to AI-first companies.

Aapka business AI-ready hai? 💭

#AI #FutureOfWork #DigitalTransformation #Innovation #BusinessGrowth #TechTrends #Automation #Leadership`;

console.log("\n=== Automated LinkedIn Post ===\n");
console.log("Email:", LINKEDIN_EMAIL ? "✓ SET" : "✗ NOT SET");
console.log("Post length:", POST_CONTENT.length, "chars\n");

if (!LINKEDIN_EMAIL || !LINKEDIN_PASSWORD) {
  console.error("ERROR: Check .env file");
  process.exit(1);
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

let browser = null;
let page = null;

try {
  console.log("1. Launching browser (headless)...");
  browser = await chromium.launch({ headless: true });
  page = await browser.newPage();
  await page.setViewportSize({ width: 1280, height: 800 });
  console.log("   ✓ Browser ready\n");

  console.log("2. Navigating to LinkedIn login...");
  await page.goto("https://www.linkedin.com/login", { waitUntil: "domcontentloaded", timeout: 30000 });
  console.log("   ✓ Login page loaded\n");

  console.log("3. Entering credentials...");
  await page.fill("#username", LINKEDIN_EMAIL);
  await page.fill("#password", LINKEDIN_PASSWORD);
  console.log("   ✓ Credentials filled\n");

  console.log("4. Submitting login...");
  await page.click('button[type="submit"]');
  await sleep(8000);

  const currentUrl = page.url();
  console.log("   Current URL:", currentUrl);

  if (currentUrl.includes("/login") || currentUrl.includes("/checkpoint")) {
    await page.screenshot({ path: "login_error.png" });
    console.error("\n❌ Login failed! Screenshot saved: login_error.png");
    console.error("Check credentials in .env file");
    process.exit(1);
  }
  console.log("   ✓ Login successful!\n");

  console.log("5. Navigating to feed...");
  await page.goto("https://www.linkedin.com/feed/", { waitUntil: "domcontentloaded", timeout: 30000 });
  await sleep(4000);
  console.log("   ✓ Feed loaded\n");

  await page.screenshot({ path: "feed_loaded.png" });
  console.log("   Screenshot saved: feed_loaded.png\n");

  console.log("6. Finding 'Start a post' button...");

  // Try multiple selectors for the start post button
  let startPostBtn = null;
  const selectors = [
    'button[aria-label="Start a post"]',
    'button[aria-label="Create a post"]',
    '.share-box-feed-entry__trigger',
    'button.share-box-feed-entry__trigger',
    '[data-control-name="share.sharebox_trigger"]',
    'span:has-text("Start a post")',
    'button:has-text("Start a post")',
  ];

  for (const sel of selectors) {
    try {
      startPostBtn = await page.$(sel);
      if (startPostBtn) {
        console.log("   ✓ Found button with:", sel);
        break;
      }
    } catch (e) {}
  }

  if (!startPostBtn) {
    // Try clicking the post share box placeholder text
    const placeholder = await page.$('.share-box-feed-entry__placeholder');
    if (placeholder) {
      startPostBtn = placeholder;
      console.log("   ✓ Found placeholder share box");
    }
  }

  if (!startPostBtn) {
    await page.screenshot({ path: "feed_no_button.png" });
    console.error("   ❌ Post button not found. Screenshot: feed_no_button.png");

    // List all buttons on page for debugging
    const buttons = await page.$$eval('button', btns => btns.map(b => ({
      text: b.textContent?.trim().substring(0,50),
      aria: b.getAttribute('aria-label')
    })));
    console.log("   Buttons found:", JSON.stringify(buttons.slice(0, 10), null, 2));
    process.exit(1);
  }

  await startPostBtn.click();
  await sleep(3000);
  console.log("   ✓ Post dialog opened\n");

  await page.screenshot({ path: "post_dialog.png" });
  console.log("   Screenshot: post_dialog.png\n");

  console.log("7. Writing post content...");

  // Try multiple selectors for text box
  let textBox = null;
  const textSelectors = [
    'div[contenteditable="true"][role="textbox"]',
    '.ql-editor[contenteditable="true"]',
    'div.editor-content[contenteditable="true"]',
    '[data-placeholder]',
  ];

  for (const sel of textSelectors) {
    try {
      textBox = await page.$(sel);
      if (textBox) {
        console.log("   ✓ Found textbox with:", sel);
        break;
      }
    } catch (e) {}
  }

  if (!textBox) {
    await page.screenshot({ path: "no_textbox.png" });
    console.error("   ❌ Text box not found. Screenshot: no_textbox.png");
    process.exit(1);
  }

  await textBox.click();
  await sleep(500);
  await page.keyboard.type(POST_CONTENT, { delay: 20 });
  await sleep(1500);
  console.log("   ✓ Content typed\n");

  await page.screenshot({ path: "post_ready.png" });
  console.log("   Screenshot: post_ready.png\n");

  console.log("8. Finding Post button...");

  let postBtn = null;
  const postBtnSelectors = [
    'button[aria-label="Post"]',
    'button.share-actions__primary-action',
    'button:has-text("Post")',
    '.share-box_actions button.artdeco-button--primary',
  ];

  for (const sel of postBtnSelectors) {
    try {
      postBtn = await page.$(sel);
      if (postBtn) {
        console.log("   ✓ Found post button with:", sel);
        break;
      }
    } catch (e) {}
  }

  if (!postBtn) {
    await page.screenshot({ path: "no_post_btn.png" });
    console.error("   ❌ Post button not found. Screenshot: no_post_btn.png");
    process.exit(1);
  }

  console.log("9. Publishing post...");
  await postBtn.click();
  await sleep(5000);
  console.log("   ✓ Post button clicked!\n");

  await page.screenshot({ path: "post_published.png" });
  console.log("   Screenshot: post_published.png\n");

  console.log("═".repeat(50));
  console.log("  ✅ POST PUBLISHED SUCCESSFULLY!");
  console.log("═".repeat(50));
  console.log("\nCheck your LinkedIn profile to verify!\n");

} catch (error) {
  console.error("\n❌ Error:", error.message);
  if (page) {
    await page.screenshot({ path: "error.png" });
    console.error("Screenshot saved: error.png");
  }
  process.exit(1);
} finally {
  if (browser) await browser.close();
}
