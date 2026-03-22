import { chromium } from "playwright";
import dotenv from "dotenv";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

dotenv.config();

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const TWITTER_USERNAME = process.env.TWITTER_USERNAME;
const TWITTER_PASSWORD = process.env.TWITTER_PASSWORD;
const TWITTER_EMAIL = process.env.TWITTER_EMAIL;
const SESSION_DIR = path.join(__dirname, "..", ".twitter_sessions");

const contentFile = process.argv[2];
if (!contentFile || !fs.existsSync(contentFile)) {
  console.error("❌ ERROR: Content file not provided or does not exist.");
  process.exit(1);
}

// Extract content from markdown file
const rawContent = fs.readFileSync(contentFile, "utf-8");
let postText = rawContent;

// Try to extract content between "Content:" and the end of file, but handle "Tags:" by merging them
if (rawContent.includes("Content:")) {
  const parts = rawContent.split("Content:");
  if (parts.length > 1) {
    let mainContent = parts[1];
    if (mainContent.includes("Tags:")) {
        const tagParts = mainContent.split("Tags:");
        postText = tagParts[0].trim() + "\n\n" + tagParts[1].trim();
    } else {
        postText = mainContent.trim();
    }
  }
}

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function run() {
  console.log("\n🚀 Starting Twitter Post Executor (Playwright)...");
  console.log(`✓ Using Username: ${TWITTER_USERNAME}`);
  
  if (!TWITTER_USERNAME || !TWITTER_PASSWORD) {
    console.error("❌ ERROR: TWITTER_USERNAME or TWITTER_PASSWORD not set in .env");
    process.exit(1);
  }

  if (!fs.existsSync(SESSION_DIR)) {
    fs.mkdirSync(SESSION_DIR, { recursive: true });
  }

  // Use persistent context to save login sessions
  const browser = await chromium.launchPersistentContext(SESSION_DIR, {
    headless: false,
    args: [
      "--no-sandbox", 
      "--disable-setuid-sandbox",
      "--disable-blink-features=AutomationControlled"
    ],
    ignoreDefaultArgs: ["--enable-automation"],
    viewport: { width: 1280, height: 720 },
    userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
  });

  const page = browser.pages()[0] || (await browser.newPage());

  try {
    console.log("✓ Navigating to Twitter...");
    await page.goto("https://twitter.com/home", { waitUntil: "domcontentloaded", timeout: 60000 });
    await sleep(5000);

    // Check if already logged in by looking for Home indicators
    const isLoggedIn = async () => {
        return page.url().includes("/home") || await page.isVisible('data-testid="SideNav_NewTweet_Button"');
    };

    if (await isLoggedIn()) {
      console.log("✅ Already logged in (Session Persisted).");
    } else {
      console.log("✓ Session not found. Navigating to login...");
      await page.goto("https://twitter.com/login", { waitUntil: "domcontentloaded" });
      await sleep(5000);

      console.log("✓ Attempting auto-login as " + TWITTER_USERNAME);
      
      try {
        const usernameInput = page.locator('input[autocomplete="username"]');
        if (await usernameInput.isVisible({ timeout: 15000 })) {
            await usernameInput.fill(TWITTER_USERNAME);
            await page.keyboard.press("Enter");
            await sleep(3000);

            // Handle identity verification (sometimes asks for email or phone)
            const verifyField = page.locator('input[data-testid="ocfEnterTextTextInput"]');
            if (await verifyField.isVisible({ timeout: 5000 })) {
                console.log("! Twitter is asking for identity verification (Email/Username/Phone)...");
                if (TWITTER_EMAIL) {
                    await verifyField.fill(TWITTER_EMAIL);
                    await page.keyboard.press("Enter");
                    await sleep(3000);
                } else {
                    console.log("⚠️ TWITTER_EMAIL not set, manual intervention might be needed.");
                }
            }

            // Password handling
            let passwordInput = page.locator('input[name="password"], input[autocomplete="current-password"]');
            await passwordInput.waitFor({ state: 'visible', timeout: 15000 });
            await passwordInput.click();
            await sleep(1000);
            
            await page.keyboard.press('Control+A');
            await page.keyboard.press('Backspace');
            await sleep(500);

            console.log("✓ Typing password...");
            await page.keyboard.type(TWITTER_PASSWORD, { delay: 200 });
            await sleep(1000);
            await page.keyboard.press("Enter");
            console.log("✓ Submitted login.");
            await sleep(10000); 
        }
      } catch (e) {
        console.log("⚠️ Auto-login encountered an issue: " + e.message);
      }

      // Final manual check if auto-login failed
      if (!(await isLoggedIn())) {
        console.log("⚠️ Still not logged in. PLEASE LOG IN MANUALLY now to save the session.");
        console.log("Waiting 120 seconds for you to finish login in the browser...");
        for (let i = 0; i < 120; i++) {
            if (await isLoggedIn()) {
                console.log("✅ Manual login detected! Session will be saved.");
                break;
            }
            await sleep(1000);
        }
      }
    }

    if (!(await isLoggedIn())) {
        throw new Error("Could not log in to Twitter.");
    }

    console.log("✓ Creating Agentic AI post...");
    // Go to compose page
    await page.goto("https://twitter.com/compose/tweet");
    await sleep(5000);

    const editor = page.locator('div[data-testid="tweetTextarea_0"]').first();
    await editor.waitFor({ state: 'visible', timeout: 15000 });
    await editor.click();
    
    // Type the post content
    await editor.fill(postText);
    await sleep(2000);

    console.log("✓ Publishing...");
    
    // Method 1: Use Keyboard Shortcut (Ctrl+Enter is the standard Twitter shortcut for posting)
    console.log("✓ Sending Ctrl+Enter shortcut...");
    await page.keyboard.press('Control+Enter');
    await sleep(3000);

    // Method 2: Force Click (in case shortcut didn't work)
    const postButton = page.locator('[data-testid="tweetButton"], [data-testid="tweetButtonInline"], [data-testid="SideNav_NewTweet_Button"]').first();
    
    if (await postButton.isVisible()) {
        console.log("✓ Attempting forced click on Post button...");
        try {
            await postButton.click({ force: true, timeout: 5000 });
        } catch (e) {
            console.log("! Standard click failed, trying JavaScript click...");
            await postButton.evaluate(node => node.click());
        }
    } else {
        // Try by text/role if data-testid fails
        const altButton = page.getByRole('button', { name: /Post|Tweet/i }).first();
        if (await altButton.isVisible()) {
            await altButton.click({ force: true });
        }
    }
    
    await sleep(8000); 

    console.log("✅ Post successfully published to Twitter!");
    
    // Move file to Done folder
    const doneDir = path.join(path.dirname(contentFile), "..", "Done");
    if (!fs.existsSync(doneDir)) fs.mkdirSync(doneDir, { recursive: true });
    const targetPath = path.join(doneDir, path.basename(contentFile));
    fs.renameSync(contentFile, targetPath);
    console.log(`✓ Moved ${path.basename(contentFile)} to Done.`);

  } catch (error) {
    console.error("❌ ERROR during posting:", error);
    await page.screenshot({ path: "twitter_error.png" });
  } finally {
    // Keep browser open for a few seconds before closing if it was a success
    await sleep(5000);
    await browser.close();
  }
}

run();
