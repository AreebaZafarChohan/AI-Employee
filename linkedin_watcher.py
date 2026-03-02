#!/usr/bin/env python3
"""Silver Tier LinkedIn Watcher.

Monitors LinkedIn for unread DMs, mentions, and comments using Playwright.
Creates markdown files in /Needs_Action for items containing business keywords.

Features:
- Persistent session login
- Monitors: DMs, mentions, comments
- Business keyword filtering
- Duplicate prevention
- Retry logic
- DRY_RUN mode
- Comprehensive logging

Usage:
    python linkedin_watcher.py              # run once
    python linkedin_watcher.py --watch      # continuous monitoring
    DRY_RUN=true python linkedin_watcher.py # test mode

Environment Variables:
    LINKEDIN_EMAIL       - LinkedIn email/username
    LINKEDIN_PASSWORD    - LinkedIn password
    VAULT_PATH          - Path to AI-Employee vault
    DRY_RUN             - Set to "true" for test mode
    LOG_LEVEL           - DEBUG/INFO/WARNING/ERROR
    LINKEDIN_WATCH_INTERVAL - Seconds between checks (default: 300)
"""

import argparse
import hashlib
import json
import logging
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

try:
    from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
    from playwright._impl._errors import TimeoutError as PlaywrightTimeout
except ImportError:
    print("Installing Playwright...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
    subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
    from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
    from playwright._impl._errors import TimeoutError as PlaywrightTimeout

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent
VAULT = Path(os.getenv("VAULT_PATH", ROOT / "AI-Employee-Vault")).resolve()
NEEDS_ACTION = VAULT / "Needs_Action"
LOGS_DIR = VAULT / "Logs"
SESSION_DIR = ROOT / ".linkedin_sessions"

# LinkedIn URLs
LINKEDIN_LOGIN_URL = "https://www.linkedin.com/login"
LINKEDIN_MESSAGING_URL = "https://www.linkedin.com/messaging/"
LINKEDIN_NOTIFICATIONS_URL = "https://www.linkedin.com/notifications/"

# Business keywords that trigger action
BUSINESS_KEYWORDS = {
    "pricing", "price", "quote", "quotation",
    "service", "services", "solution", "solutions",
    "collaboration", "collaborate", "partner", "partnership",
    "project", "opportunity", "proposal", "contract",
    "budget", "investment", "deal", "agreement",
    "consulting", "freelance", "hire", "hiring",
    "meeting", "call", "demo", "presentation",
    "interested", "connect", "discussion", "explore",
}

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

# Dry run mode
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("linkedin_watcher")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def get_timestamp() -> str:
    """Get current ISO timestamp."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def generate_item_id(sender: str, message: str, timestamp: str) -> str:
    """Generate unique ID for duplicate prevention."""
    content = f"{sender}:{message}:{timestamp}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def contains_business_keywords(text: str) -> bool:
    """Check if text contains business-related keywords."""
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in BUSINESS_KEYWORDS)


def sanitize_filename(text: str) -> str:
    """Sanitize text for use in filename."""
    s = re.sub(r"[^\w\s-]", "", text.lower())
    s = re.sub(r"[\s_]+", "-", s).strip("-")
    return s[:50] or "message"


def load_processed_items() -> set[str]:
    """Load set of already processed item IDs."""
    ledger_file = LOGS_DIR / "linkedin_processed.json"
    if ledger_file.exists():
        try:
            with open(ledger_file, "r") as f:
                data = json.load(f)
                return set(data.get("processed_ids", []))
        except (json.JSONDecodeError, IOError):
            pass
    return set()


def save_processed_item(item_id: str) -> None:
    """Save processed item ID to prevent duplicates."""
    ledger_file = LOGS_DIR / "linkedin_processed.json"
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load existing
    processed = load_processed_items()
    processed.add(item_id)
    
    # Keep only last 1000 IDs to prevent unbounded growth
    if len(processed) > 1000:
        processed = set(list(processed)[-1000:])
    
    # Save
    with open(ledger_file, "w") as f:
        json.dump({"processed_ids": list(processed), "updated_at": get_timestamp()}, f, indent=2)


def log_event(event_type: str, details: dict) -> None:
    """Log event to daily log file."""
    log_file = LOGS_DIR / f"linkedin-watcher-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.log"
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    log_entry = {
        "timestamp": get_timestamp(),
        "event_type": event_type,
        "dry_run": DRY_RUN,
        **details
    }
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")


# ---------------------------------------------------------------------------
# LinkedIn Watcher Class
# ---------------------------------------------------------------------------


class LinkedInWatcher:
    """LinkedIn monitoring using Playwright with persistent sessions."""
    
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.processed_ids = load_processed_items()
        
    def start_browser(self) -> None:
        """Start browser with persistent context."""
        SESSION_DIR.mkdir(parents=True, exist_ok=True)
        
        playwright = sync_playwright().start()
        self.browser = playwright.chromium.launch_persistent_context(
            user_data_dir=str(SESSION_DIR),
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ]
        )
        logger.debug("Browser started with persistent session")
        
    def close_browser(self) -> None:
        """Close browser and cleanup."""
        if self.browser:
            self.browser.close()
            logger.debug("Browser closed")
    
    def login(self) -> bool:
        """Login to LinkedIn using credentials or existing session."""
        try:
            self.page = self.browser.new_page()
            self.page.set_extra_http_headers({
                "accept-language": "en-US,en;q=0.9",
            })
            
            # Navigate to login
            logger.info("Navigating to LinkedIn login...")
            self.page.goto(LINKEDIN_LOGIN_URL, wait_until="networkidle", timeout=30000)
            
            # Check if already logged in (redirected to feed)
            if "feed" in self.page.url or "mynetwork" in self.page.url:
                logger.info("Already logged in (existing session)")
                log_event("login", {"status": "success", "method": "existing_session"})
                return True
            
            # Attempt login with credentials
            logger.info("Logging in with credentials...")
            
            # Fill email
            email_field = self.page.locator("#username")
            email_field.fill(self.email)
            
            # Fill password
            password_field = self.page.locator("#password")
            password_field.fill(self.password)
            
            # Click sign in
            sign_in_button = self.page.locator('button[type="submit"]')
            sign_in_button.click()
            
            # Wait for navigation
            try:
                self.page.wait_for_url("https://www.linkedin.com/feed/*", timeout=10000)
            except PlaywrightTimeout:
                pass  # May redirect to different page
            
            # Check if login successful
            if "login" in self.page.url or "challenge" in self.page.url:
                logger.error("Login failed - check credentials")
                log_event("login", {"status": "failed", "reason": "invalid_credentials"})
                return False
            
            logger.info("Login successful")
            log_event("login", {"status": "success", "method": "credentials"})
            return True
            
        except Exception as e:
            logger.error(f"Login error: {e}")
            log_event("login", {"status": "error", "error": str(e)})
            return False
    
    def check_dms(self) -> list[dict]:
        """Check for unread DMs and extract business-related messages."""
        logger.info("Checking DMs...")
        items = []
        
        try:
            self.page.goto(LINKEDIN_MESSAGING_URL, wait_until="networkidle", timeout=30000)
            time.sleep(3)  # Allow page to load
            
            # Find conversation list
            conversations = self.page.locator("ul.conversations-list li").all()
            
            for conv in conversations[:10]:  # Check last 10 conversations
                try:
                    # Check if unread
                    if not conv.locator(".unread").count():
                        continue
                    
                    # Extract sender
                    sender_elem = conv.locator(".actor-name").first
                    sender = sender_elem.inner_text() if sender_elem.count() else "Unknown"
                    
                    # Extract message preview
                    message_elem = conv.locator(".message-preview").first
                    message = message_elem.inner_text() if message_elem.count() else ""
                    
                    # Extract timestamp
                    time_elem = conv.locator(".convo-card-time").first
                    timestamp = time_elem.inner_text() if time_elem.count() else get_timestamp()
                    
                    # Get thread URL
                    conv.click()
                    time.sleep(1)
                    thread_url = self.page.url
                    
                    # Check for business keywords
                    if contains_business_keywords(message):
                        item = {
                            "type": "linkedin_dm",
                            "sender": sender,
                            "content": message,
                            "timestamp": timestamp,
                            "thread_url": thread_url,
                            "priority": "high" if any(kw in message.lower() for kw in ["pricing", "quote", "budget"]) else "medium",
                        }
                        items.append(item)
                        logger.info(f"Business DM found: {sender} - {message[:50]}...")
                    
                except Exception as e:
                    logger.debug(f"Error processing conversation: {e}")
                    continue
            
            log_event("check_dms", {"status": "success", "items_found": len(items)})
            
        except Exception as e:
            logger.error(f"Error checking DMs: {e}")
            log_event("check_dms", {"status": "error", "error": str(e)})
        
        return items
    
    def check_mentions(self) -> list[dict]:
        """Check for mentions in notifications."""
        logger.info("Checking mentions...")
        items = []
        
        try:
            self.page.goto(LINKEDIN_NOTIFICATIONS_URL, wait_until="networkidle", timeout=30000)
            time.sleep(3)
            
            # Find mention notifications
            notifications = self.page.locator("ul.notification-list li").all()
            
            for notif in notifications[:10]:
                try:
                    # Check if it's a mention
                    notif_text = notif.inner_text()
                    if "mentioned" not in notif_text.lower():
                        continue
                    
                    # Check if unread
                    if "unread" not in notif_text.lower() and "seen" not in notif_text.lower():
                        # Try to check CSS class
                        if not notif.locator(".unread").count():
                            continue
                    
                    # Extract sender
                    sender_elem = notif.locator(".actor-name").first
                    sender = sender_elem.inner_text() if sender_elem.count() else "Unknown"
                    
                    # Extract mention context
                    content = notif_text[:200]
                    
                    # Extract timestamp
                    time_elem = notif.locator(".notification-time").first
                    timestamp = time_elem.inner_text() if time_elem.count() else get_timestamp()
                    
                    # Get notification URL
                    link_elem = notif.locator("a").first
                    thread_url = link_elem.get_attribute("href") if link_elem.count() else ""
                    if thread_url and not thread_url.startswith("http"):
                        thread_url = f"https://www.linkedin.com{thread_url}"
                    
                    # Check for business keywords
                    if contains_business_keywords(content):
                        item = {
                            "type": "linkedin_mention",
                            "sender": sender,
                            "content": content,
                            "timestamp": timestamp,
                            "thread_url": thread_url,
                            "priority": "medium",
                        }
                        items.append(item)
                        logger.info(f"Business mention found: {sender}")
                    
                except Exception as e:
                    logger.debug(f"Error processing mention: {e}")
                    continue
            
            log_event("check_mentions", {"status": "success", "items_found": len(items)})
            
        except Exception as e:
            logger.error(f"Error checking mentions: {e}")
            log_event("check_mentions", {"status": "error", "error": str(e)})
        
        return items
    
    def check_comments(self) -> list[dict]:
        """Check for new comments on posts."""
        logger.info("Checking comments...")
        items = []
        
        try:
            self.page.goto(LINKEDIN_NOTIFICATIONS_URL, wait_until="networkidle", timeout=30000)
            time.sleep(3)
            
            # Find comment notifications
            notifications = self.page.locator("ul.notification-list li").all()
            
            for notif in notifications[:10]:
                try:
                    # Check if it's a comment
                    notif_text = notif.inner_text()
                    if "commented" not in notif_text.lower() and "comment" not in notif_text.lower():
                        continue
                    
                    # Check if unread
                    if not notif.locator(".unread").count():
                        continue
                    
                    # Extract sender
                    sender_elem = notif.locator(".actor-name").first
                    sender = sender_elem.inner_text() if sender_elem.count() else "Unknown"
                    
                    # Extract comment content
                    comment_elem = notif.locator(".notification-subtitle").first
                    content = comment_elem.inner_text() if comment_elem.count() else notif_text[:200]
                    
                    # Extract timestamp
                    time_elem = notif.locator(".notification-time").first
                    timestamp = time_elem.inner_text() if time_elem.count() else get_timestamp()
                    
                    # Get post URL
                    link_elem = notif.locator("a").first
                    thread_url = link_elem.get_attribute("href") if link_elem.count() else ""
                    if thread_url and not thread_url.startswith("http"):
                        thread_url = f"https://www.linkedin.com{thread_url}"
                    
                    # Check for business keywords
                    if contains_business_keywords(content):
                        item = {
                            "type": "linkedin_comment",
                            "sender": sender,
                            "content": content,
                            "timestamp": timestamp,
                            "thread_url": thread_url,
                            "priority": "medium",
                        }
                        items.append(item)
                        logger.info(f"Business comment found: {sender}")
                    
                except Exception as e:
                    logger.debug(f"Error processing comment: {e}")
                    continue
            
            log_event("check_comments", {"status": "success", "items_found": len(items)})
            
        except Exception as e:
            logger.error(f"Error checking comments: {e}")
            log_event("check_comments", {"status": "error", "error": str(e)})
        
        return items
    
    def create_needs_action_file(self, item: dict) -> Optional[Path]:
        """Create markdown file in /Needs_Action."""
        item_id = generate_item_id(
            item["sender"],
            item["content"],
            item["timestamp"]
        )
        
        # Check for duplicates
        if item_id in self.processed_ids:
            logger.debug(f"Duplicate item skipped: {item_id}")
            return None
        
        # Generate filename
        sender_slug = sanitize_filename(item["sender"])
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"linkedin-{item['type']}-{sender_slug}-{item_id}.md"
        filepath = NEEDS_ACTION / filename
        
        # Create content
        frontmatter = f"""---
type: {item['type']}
from: "{item['sender']}"
content: "{item['content'].replace('"', '\\"')}"
thread_url: {item['thread_url']}
priority: {item['priority']}
status: pending
linkedin_item_id: {item_id}
received_at: "{item['timestamp']}"
created_at: "{get_timestamp()}"
---

# LinkedIn {item['type'].replace("_", " ").title()}

**From:** {item['sender']}
**Received:** {item['timestamp']}
**Priority:** {item['priority']}
**Thread:** [{item['thread_url']}]({item['thread_url']})

## Message Content

{item['content']}

## Actions Required

- [ ] Review message content
- [ ] Determine required response
- [ ] Draft and send response
- [ ] Mark complete when done
"""
        
        if not DRY_RUN:
            NEEDS_ACTION.mkdir(parents=True, exist_ok=True)
            filepath.write_text(frontmatter, encoding="utf-8")
            save_processed_item(item_id)
            logger.info(f"Created: {filename}")
        else:
            logger.info(f"[DRY_RUN] Would create: {filename}")
        
        log_event("file_created", {
            "filename": filename,
            "item_id": item_id,
            "sender": item["sender"],
            "type": item["type"]
        })
        
        return filepath
    
    def run_with_retry(self, func, *args, **kwargs):
        """Run function with retry logic."""
        last_error = None
        
        for attempt in range(MAX_RETRIES):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
        
        logger.error(f"All {MAX_RETRIES} attempts failed")
        log_event("retry_exhausted", {
            "function": func.__name__,
            "error": str(last_error)
        })
        raise last_error
    
    def run_check(self) -> dict:
        """Run full LinkedIn check with retry logic."""
        results = {
            "dms": [],
            "mentions": [],
            "comments": [],
            "files_created": 0,
        }
        
        try:
            # Check each source with retry
            results["dms"] = self.run_with_retry(self.check_dms)
            results["mentions"] = self.run_with_retry(self.check_mentions)
            results["comments"] = self.run_with_retry(self.check_comments)
            
            # Create files for all items
            all_items = results["dms"] + results["mentions"] + results["comments"]
            
            for item in all_items:
                if self.create_needs_action_file(item):
                    results["files_created"] += 1
            
            logger.info(f"Check complete: {len(all_items)} business items found, {results['files_created']} files created")
            
        except Exception as e:
            logger.error(f"Check failed: {e}")
            log_event("check_failed", {"error": str(e)})
        
        return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="LinkedIn Watcher")
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Run in continuous watch mode",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=int(os.getenv("LINKEDIN_WATCH_INTERVAL", "300")),
        help="Watch mode interval in seconds (default: 300)",
    )
    
    args = parser.parse_args()
    
    # Check credentials
    email = os.getenv("LINKEDIN_EMAIL")
    password = os.getenv("LINKEDIN_PASSWORD")
    
    if not email or not password:
        logger.error("LINKEDIN_EMAIL and LINKEDIN_PASSWORD environment variables required")
        logger.error("Set them in .env file or export before running")
        sys.exit(1)
    
    logger.info(f"Starting LinkedIn Watcher (DRY_RUN={DRY_RUN})")
    
    if args.watch:
        logger.info(f"Watch mode enabled (interval={args.interval}s)")
    
    watcher = LinkedInWatcher(email, password)
    
    try:
        # Start browser
        watcher.start_browser()
        
        # Login
        if not watcher.login():
            logger.error("Login failed. Exiting.")
            sys.exit(1)
        
        if args.watch:
            # Continuous monitoring
            try:
                while True:
                    results = watcher.run_check()
                    logger.info(f"Cycle complete: {results['files_created']} files created")
                    time.sleep(args.interval)
            except KeyboardInterrupt:
                logger.info("Watch mode stopped by user")
        else:
            # Single run
            results = watcher.run_check()
            logger.info(f"Complete: {results['files_created']} files created")
    
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
    
    finally:
        watcher.close_browser()


if __name__ == "__main__":
    main()
