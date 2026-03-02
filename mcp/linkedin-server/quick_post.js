#!/usr/bin/env node
/**
 * Quick LinkedIn Post Publisher
 */

import { chromium } from "playwright";
import dotenv from "dotenv";

dotenv.config();

const LINKEDIN_EMAIL = process.env.LINKEDIN_EMAIL;
const LINKEDIN_PASSWORD = process.env.LINKEDIN_PASSWORD;

console.log("=== LinkedIn Post Test ===\n");
console.log("Email:", LINKEDIN_EMAIL);
console.log("Password:", LINKEDIN_PASSWORD ? "***SET***" : "NOT SET");
console.log();

if (!LINKEDIN_EMAIL || !LINKEDIN_PASSWORD) {
  console.error("ERROR: Credentials not set!");
  process.exit(1);
}

let browser = null;

try {
  console.log("Starting browser...");
  browser = await chromium.launch({
    headless: false,
    args: ["--start-maximized"],
  });

  const page = await browser.newPage();
  
  console.log("Going to LinkedIn...");
  await page.goto("https://www.linkedin.com/login");
  
  console.log("Filling credentials...");
  await page.fill("#username", LINKEDIN_EMAIL);
  await page.fill("#password", LINKEDIN_PASSWORD);
  await page.click('button[type="submit"]');
  
  console.log("Waiting for login...");
  await page.waitForNavigation({ waitUntil: "networkidle", timeout: 15000 }).catch(() => {});
  
  console.log("Current URL:", page.url());
  
  if (page.url().includes("/login")) {
    console.error("Login failed!");
    await page.screenshot({ path: "login_error.png" });
    console.log("Screenshot saved: login_error.png");
    process.exit(1);
  }
  
  console.log("Login successful!");
  console.log("\n✓ Browser is open - you can manually post");
  console.log("✓ Press Ctrl+C when done");
  
  // Keep browser open
  await new Promise(() => {});
  
} catch (error) {
  console.error("Error:", error.message);
  if (browser) await browser.close();
  process.exit(1);
}
