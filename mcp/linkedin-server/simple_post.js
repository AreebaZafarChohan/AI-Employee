#!/usr/bin/env node
/**
 * Simple LinkedIn Post - Keep Browser Open
 */

import { chromium } from "playwright";
import dotenv from "dotenv";

dotenv.config();

const LINKEDIN_EMAIL = process.env.LINKEDIN_EMAIL;
const LINKEDIN_PASSWORD = process.env.LINKEDIN_PASSWORD;

console.log("\n=== AI Future Post ===\n");
console.log("Email:", LINKEDIN_EMAIL ? "✓ SET" : "✗ NOT SET");
console.log("Password:", LINKEDIN_PASSWORD ? "✓ SET" : "✗ NOT SET");
console.log();

if (!LINKEDIN_EMAIL || !LINKEDIN_PASSWORD) {
  console.error("ERROR: Check .env file in mcp/linkedin-server/");
  process.exit(1);
}

let browser = null;

try {
  console.log("1. Starting browser...");
  browser = await chromium.launch({
    headless: false,
    args: ["--start-maximized"],
  });

  const page = await browser.newPage();
  console.log("   ✓ Browser open\n");

  console.log("2. Going to LinkedIn...");
  await page.goto("https://www.linkedin.com/login");
  console.log("   ✓ On login page\n");

  console.log("3. Filling credentials...");
  await page.fill("#username", LINKEDIN_EMAIL);
  await page.fill("#password", LINKEDIN_PASSWORD);
  console.log("   ✓ Filled\n");

  console.log("4. Clicking Sign In...");
  await page.click('button[type="submit"]');
  console.log("   ✓ Clicked\n");

  console.log("5. Waiting for login (15 sec)...");
  await page.waitForTimeout(15000);

  console.log("Current URL:", page.url());
  
  if (page.url().includes("/feed")) {
    console.log("\n✓ Login successful!\n");
    
    console.log("6. Going to post...");
    await page.goto("https://www.linkedin.com/feed/");
    await page.waitForTimeout(3000);
    console.log("   ✓ On feed\n");
    
    console.log("7. Click 'Start a post' button");
    console.log("   (Browser visible - you can help if needed)\n");
    
    // Keep browser open
    console.log("═══════════════════════════════════════════════════");
    console.log("  Browser is OPEN");
    console.log("  Post manually or wait for automation");
    console.log("  Press Ctrl+C to close");
    console.log("═══════════════════════════════════════════════════\n");
    
    // Wait indefinitely
    await new Promise(() => {});
  } else {
    console.log("\n⚠ Still on login - check credentials\n");
    await page.screenshot({ path: "login_issue.png" });
    console.log("Screenshot: login_issue.png\n");
  }

} catch (error) {
  console.error("Error:", error.message);
  if (browser) await browser.close();
  process.exit(1);
}
