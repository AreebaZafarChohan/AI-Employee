#!/usr/bin/env python3
"""
Gold Tier Social Media Watcher

Monitors LinkedIn, Facebook, Instagram, and Twitter for engagement events.
Creates markdown files in Needs_Action/ for responses needed.

Usage:
    python social_watcher.py              # run one poll cycle
    python social_watcher.py --watch      # continuous monitoring
    DRY_RUN=true python social_watcher.py # log without writing files
"""

import argparse
import json
import logging
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Add project root to path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

try:
    import httpx
    from src.utils.logger import log_action
    from src.utils.cross_dedup import CrossSourceDedup
except ImportError:
    httpx = None
    CrossSourceDedup = object

# Initialize deduplication
_cross_dedup = CrossSourceDedup() if CrossSourceDedup else object()

# ============================================================================
# Configuration
# ============================================================================

VAULT_PATH = Path(os.getenv("VAULT_PATH", ROOT / "AI-Employee-Vault")).resolve()
NEEDS_ACTION_DIR = VAULT_PATH / "Needs_Action"
LOGS_DIR = VAULT_PATH / "Logs"
SOCIAL_DIR = VAULT_PATH / "Social"

POLL_INTERVAL = int(os.getenv("SOCIAL_POLL_INTERVAL", "300"))
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"

# Platform configurations
LINKEDIN_CONFIG = {
    "access_token": os.getenv("LINKEDIN_ACCESS_TOKEN", ""),
    "organization_id": os.getenv("LINKEDIN_ORG_ID", ""),
    "enabled": bool(os.getenv("LINKEDIN_ACCESS_TOKEN")),
}

FACEBOOK_CONFIG = {
    "access_token": os.getenv("FACEBOOK_ACCESS_TOKEN", ""),
    "page_id": os.getenv("FACEBOOK_PAGE_ID", ""),
    "enabled": bool(os.getenv("FACEBOOK_ACCESS_TOKEN")),
}

INSTAGRAM_CONFIG = {
    "access_token": os.getenv("INSTAGRAM_ACCESS_TOKEN", ""),
    "business_account_id": os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID", ""),
    "enabled": bool(os.getenv("INSTAGRAM_ACCESS_TOKEN")),
}

TWITTER_CONFIG = {
    "bearer_token": os.getenv("TWITTER_BEARER_TOKEN", ""),
    "enabled": bool(os.getenv("TWITTER_BEARER_TOKEN")),
}

# Keyword triggers for auto-response
AUTO_RESPOND_KEYWORDS = ["thank", "great", "awesome", "excellent", "love"]
ESCALATION_KEYWORDS = ["complaint", "angry", "refund", "sue", "terrible", "worst"]

# Logging setup
logger = logging.getLogger("social_watcher")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | social_watcher | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


# ============================================================================
# Helper Functions
# ============================================================================


def get_timestamp() -> str:
    """Get current ISO timestamp."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def analyze_sentiment(text: str) -> str:
    """Simple sentiment analysis based on keywords."""
    text_lower = text.lower()
    
    positive_words = ["great", "awesome", "excellent", "love", "thank", "good", "amazing"]
    negative_words = ["terrible", "worst", "hate", "angry", "complaint", "bad", "awful"]
    
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    
    if negative_count > positive_count:
        return "negative"
    elif positive_count > negative_count:
        return "positive"
    return "neutral"


def determine_risk_level(sentiment: str, content: str) -> str:
    """Determine risk level based on sentiment and content."""
    content_lower = content.lower()
    
    # High risk: negative sentiment or escalation keywords
    if sentiment == "negative":
        return "high"
    
    for keyword in ESCALATION_KEYWORDS:
        if keyword in content_lower:
            return "high"
    
    # Medium risk: sales inquiries
    if any(word in content_lower for word in ["price", "cost", "buy", "purchase", "demo"]):
        return "medium"
    
    # Low risk: positive or neutral
    return "low"


import requests

def notify_backend(filename: str, metadata: dict = None):
    backend_url = os.getenv("BACKEND_URL", "http://localhost:8000/api/v1")
    try:
        requests.post(f"{backend_url}/events/new", json={
            "source": "social_watcher",
            "file": filename,
            "metadata": metadata or {}
        }, timeout=5)
    except:
        pass

def create_needs_action_file(
    platform: str,
    event_type: str,
    author: str,
    author_profile: str,
    content: str,
    post_id: str,
    original_post_context: str = "",
    sentiment: str = "neutral",
    risk_level: str = "low",
) -> Optional[Path]:
    """Create markdown file in Needs_Action folder."""
    
    # Generate unique filename
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"social-{platform}-{event_type}-{timestamp}.md"
    file_path = NEEDS_ACTION_DIR / filename
    
    # Check for duplicates
    if hasattr(_cross_dedup, 'is_processed') and _cross_dedup.is_processed(f"{platform}:{post_id}"):
        logger.debug(f"Skipping duplicate: {platform}:{post_id}")
        return None
    
    # Generate suggested response
    suggested_response = generate_suggested_response(content, sentiment, event_type)
    
    # Create markdown content
    markdown_content = f"""---
type: social_media
source: social_watcher
platform: {platform}
post_id: {post_id}
author: "{author}"
author_profile: "{author_profile}"
content: {json.dumps(content)}
event_type: {event_type}
received_at: "{get_timestamp()}"
domain: business
risk_level: {risk_level}
requires_approval: true
sentiment: {sentiment}
---

# Social Media Event

**Platform:** {platform.title()}  
**Type:** {event_type.replace('_', ' ').title()}  
**Author:** {author}  
**Received:** {get_timestamp()}

## Content

{content}

## Original Post Context

{original_post_context if original_post_context else "N/A"}

---

## Suggested Response

{suggested_response}

---

## Actions

- [ ] Approve and post response
- [ ] Edit response
- [ ] Ignore
- [ ] Escalate to human
"""
    
    if DRY_RUN:
        logger.info(f"[DRY_RUN] Would create: {filename}")
        return None
    
    # Ensure directory exists
    NEEDS_ACTION_DIR.mkdir(parents=True, exist_ok=True)
    
    # Write file
    file_path.write_text(markdown_content, encoding="utf-8")
    
    # Log action
    log_action("social_event_created", filename, {
        "platform": platform,
        "event_type": event_type,
        "author": author,
    })
    
    # Mark as processed
    if hasattr(_cross_dedup, 'mark_processed'):
        _cross_dedup.mark_processed(f"{platform}:{post_id}")
    
    logger.info(f"Created: {filename}")
    
    # Notify backend
    notify_backend(filename, {"platform": platform, "event_type": event_type, "sentiment": sentiment})
    
    return file_path


def generate_suggested_response(content: str, sentiment: str, event_type: str) -> str:
    """Generate AI-suggested response based on content and sentiment."""
    
    content_lower = content.lower()
    
    # Thank you responses
    if any(word in content_lower for word in ["thank", "thanks"]):
        return "You're welcome! We're always here to help. Feel free to reach out if you have any questions! 😊"
    
    # Positive feedback
    if any(word in content_lower for word in ["great", "awesome", "excellent", "love"]):
        return "Thank you so much for your kind words! We're thrilled that you had a positive experience. 🙏"
    
    # Sales inquiry
    if any(word in content_lower for word in ["price", "cost", "buy", "purchase"]):
        return "Thanks for your interest! Please send us a DM with your requirements, and we'll share a customized quote. 💼"
    
    # Negative feedback (requires human review)
    if sentiment == "negative":
        return "⚠️ This requires human review. Suggested: 'We're sorry to hear about your experience. Please send us a DM so we can make this right.'"
    
    # Default response
    return "Thank you for reaching out! We appreciate your engagement. 🙏"


# ============================================================================
# Platform Pollers
# ============================================================================


async def poll_linkedin() -> int:
    """Poll LinkedIn for comments and messages."""
    if not LINKEDIN_CONFIG["enabled"]:
        logger.debug("LinkedIn not configured, skipping")
        return 0
    
    count = 0
    
    try:
        # Note: Actual LinkedIn API implementation would go here
        # This is a placeholder for the API integration
        logger.info("LinkedIn poll: API integration pending")
        
        # Example of what would be done:
        # 1. Fetch recent comments on posts
        # 2. Fetch new messages
        # 3. For each engagement, create_needs_action_file()
        
    except Exception as e:
        logger.error(f"LinkedIn poll error: {e}")
    
    return count


async def poll_facebook() -> int:
    """Poll Facebook for comments and messages."""
    if not FACEBOOK_CONFIG["enabled"]:
        logger.debug("Facebook not configured, skipping")
        return 0
    
    count = 0
    
    try:
        # Facebook Graph API would be called here
        logger.info("Facebook poll: API integration pending")
        
    except Exception as e:
        logger.error(f"Facebook poll error: {e}")
    
    return count


async def poll_instagram() -> int:
    """Poll Instagram for comments and DMs."""
    if not INSTAGRAM_CONFIG["enabled"]:
        logger.debug("Instagram not configured, skipping")
        return 0
    
    count = 0
    
    try:
        # Instagram Graph API would be called here
        logger.info("Instagram poll: API integration pending")
        
    except Exception as e:
        logger.error(f"Instagram poll error: {e}")
    
    return count


async def poll_twitter() -> int:
    """Poll Twitter for mentions and replies."""
    if not TWITTER_CONFIG["enabled"]:
        logger.debug("Twitter not configured, skipping")
        return 0
    
    count = 0
    
    try:
        # Twitter API v2 would be called here
        logger.info("Twitter poll: API integration pending")
        
    except Exception as e:
        logger.error(f"Twitter poll error: {e}")
    
    return count


# ============================================================================
# Main Polling Loop
# ============================================================================


async def poll_all_platforms() -> dict:
    """Poll all configured platforms."""
    results = {
        "linkedin": await poll_linkedin(),
        "facebook": await poll_facebook(),
        "instagram": await poll_instagram(),
        "twitter": await poll_twitter(),
    }
    
    total = sum(results.values())
    logger.info(f"Poll complete: {total} events found")
    
    return results


async def run_watch_loop():
    """Run continuous watch loop."""
    logger.info("Starting Social Media Watcher...")
    logger.info(f"Poll interval: {POLL_INTERVAL}s")
    logger.info(f"Vault: {VAULT_PATH}")
    logger.info(f"Platforms: LinkedIn={LINKEDIN_CONFIG['enabled']}, "
                f"Facebook={FACEBOOK_CONFIG['enabled']}, "
                f"Instagram={INSTAGRAM_CONFIG['enabled']}, "
                f"Twitter={TWITTER_CONFIG['enabled']}")
    
    if DRY_RUN:
        logger.warning("DRY_RUN mode enabled - no files will be written")
    
    cycle_count = 0
    
    try:
        while True:
            cycle_count += 1
            logger.info(f"=== Poll Cycle {cycle_count} ===")
            
            results = await poll_all_platforms()
            
            logger.info(f"Results: {results}")
            
            # Wait for next poll
            for _ in range(POLL_INTERVAL):
                await asyncio.sleep(1)
                
    except KeyboardInterrupt:
        logger.info("Shutting down...")


def run_single_poll():
    """Run a single poll cycle."""
    logger.info("Running single poll cycle...")
    
    import asyncio
    results = asyncio.run(poll_all_platforms())
    
    logger.info(f"Final results: {results}")
    return results


# ============================================================================
# CLI
# ============================================================================


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Social Media Watcher")
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Run in continuous watch mode",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    # Ensure directories exist
    NEEDS_ACTION_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    SOCIAL_DIR.mkdir(parents=True, exist_ok=True)
    
    if args.watch:
        import asyncio
        asyncio.run(run_watch_loop())
    else:
        run_single_poll()


if __name__ == "__main__":
    main()
