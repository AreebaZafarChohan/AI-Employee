#!/usr/bin/env python3
"""
AI Employee Agent — Interactive social media content generator & poster.
Uses Gemini (primary) with Grok fallback for AI content generation.
Posts to Twitter, LinkedIn, Facebook, Instagram, WhatsApp, Email, Odoo.
"""
import os
import sys
import json
import time
import hmac
import hashlib
import base64
import uuid
import urllib.parse
import urllib.request
import urllib.error
import subprocess
import re
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

VAULT = ROOT / "AI-Employee-Vault"
PENDING_DIR = VAULT / "Pending_Approval"
DONE_DIR = VAULT / "Done"
LOGS_DIR = VAULT / "Logs"

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_AI_API_KEY")
GROK_API_KEY = os.getenv("GROK_API_KEY")

# Twitter OAuth 1.0a
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY", "")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET", "")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN", "")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")

# Platform content rules
PLATFORM_RULES = {
    "twitter": {
        "max_chars": 280,
        "prompt": (
            "Write a single tweet (max 270 characters) about: {topic}\n"
            "Rules:\n- Under 270 characters total\n- Include 2-3 relevant hashtags\n"
            "- Professional but engaging tone\n- No quotes or markdown, just the tweet text"
        ),
    },
    "linkedin": {
        "max_chars": 1500,
        "prompt": (
            "Write a professional LinkedIn post (500-1500 characters) about: {topic}\n"
            "Rules:\n- Professional, insightful tone\n- Include business value/insights\n"
            "- 3-5 relevant hashtags at the end\n- No markdown formatting\n- Engaging hook in first line"
        ),
    },
    "facebook": {
        "max_chars": 800,
        "prompt": (
            "Write a Facebook post (300-800 characters) about: {topic}\n"
            "Rules:\n- Casual-professional tone\n- Encourage engagement (questions, call to action)\n"
            "- 2-3 hashtags\n- No markdown"
        ),
    },
    "instagram": {
        "max_chars": 500,
        "prompt": (
            "Write an Instagram caption (300-500 characters) about: {topic}\n"
            "Rules:\n- Visual and descriptive\n- 5-10 relevant hashtags at the end\n"
            "- Engaging and trendy tone\n- No markdown"
        ),
    },
    "whatsapp": {
        "max_chars": 300,
        "prompt": (
            "Write a short WhatsApp broadcast message (under 300 characters) about: {topic}\n"
            "Rules:\n- Short, direct, personal tone\n- No hashtags\n- Conversational"
        ),
    },
    "email": {
        "max_chars": 5000,
        "prompt": (
            "Write a professional email about: {topic}\n"
            "Format as:\nSubject: <subject line>\n\n<email body>\n"
            "Rules:\n- Professional tone\n- Clear and concise\n- Include a call to action"
        ),
    },
}

# Platform keywords for detection (supports Urdu/English)
PLATFORM_KEYWORDS = {
    "twitter": ["twitter", "tweet", "x.com"],
    "linkedin": ["linkedin"],
    "facebook": ["facebook", "fb"],
    "instagram": ["instagram", "insta", "ig"],
    "whatsapp": ["whatsapp", "wa"],
    "email": ["email", "mail", "gmail"],
    "odoo": ["odoo", "erp"],
}


# ─── AI Content Generation ───────────────────────────────────────────

def generate_gemini(prompt: str) -> str | None:
    """Generate content using Gemini API."""
    if not GEMINI_API_KEY:
        return None
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    data = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            return result["candidates"][0]["content"]["parts"][0]["text"].strip().strip('"').strip("'").strip()
    except Exception as e:
        print(f"  Gemini error: {e}")
        return None


def generate_grok(prompt: str) -> str | None:
    """Generate content using Grok/xAI API (fallback)."""
    if not GROK_API_KEY:
        return None
    url = "https://api.x.ai/v1/chat/completions"
    data = json.dumps({
        "model": "grok-3",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 500,
    }).encode()
    req = urllib.request.Request(url, data=data, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROK_API_KEY}",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            return result["choices"][0]["message"]["content"].strip().strip('"').strip("'").strip()
    except Exception as e:
        print(f"  Grok error: {e}")
        return None


def generate_content(platform: str, topic: str) -> str | None:
    """Generate content with Gemini primary, Grok fallback."""
    rules = PLATFORM_RULES.get(platform, PLATFORM_RULES["twitter"])
    prompt = rules["prompt"].format(topic=topic)

    # Try Gemini first
    text = generate_gemini(prompt)
    if text:
        max_c = rules["max_chars"]
        if len(text) > max_c:
            text = text[:max_c - 3] + "..."
        return text

    # Fallback to Grok
    text = generate_grok(prompt)
    if text:
        max_c = rules["max_chars"]
        if len(text) > max_c:
            text = text[:max_c - 3] + "..."
        return text

    return None


# ─── Platform Posting ─────────────────────────────────────────────────

def percent_encode(s):
    return urllib.parse.quote(str(s), safe="")


def post_twitter(content: str) -> dict | None:
    """Post tweet via Twitter API v2 OAuth 1.0a."""
    if not TWITTER_API_KEY or not TWITTER_ACCESS_TOKEN:
        print("  Twitter credentials not configured in .env")
        return None

    url = "https://api.twitter.com/2/tweets"
    oauth_params = {
        "oauth_consumer_key": TWITTER_API_KEY,
        "oauth_nonce": uuid.uuid4().hex,
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_token": TWITTER_ACCESS_TOKEN,
        "oauth_version": "1.0",
    }
    param_string = "&".join(
        f"{percent_encode(k)}={percent_encode(v)}" for k, v in sorted(oauth_params.items())
    )
    base_string = f"POST&{percent_encode(url)}&{percent_encode(param_string)}"
    signing_key = f"{percent_encode(TWITTER_API_SECRET)}&{percent_encode(TWITTER_ACCESS_TOKEN_SECRET)}"
    signature = base64.b64encode(
        hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha1).digest()
    ).decode()
    oauth_params["oauth_signature"] = signature
    auth_header = "OAuth " + ", ".join(
        f'{percent_encode(k)}="{percent_encode(v)}"' for k, v in sorted(oauth_params.items())
    )

    data = json.dumps({"text": content}).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", auth_header)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"  Twitter API Error {e.code}: {e.read().decode()}")
        return None


def post_via_mcp(platform: str, content: str) -> bool:
    """Post via MCP executor scripts (LinkedIn, Facebook, Instagram)."""
    script_map = {
        "linkedin": ROOT / "mcp" / "linkedin-server" / "post_executor.js",
        "facebook": ROOT / "mcp" / "facebook-server" / "src" / "post_executor.js",
        "instagram": ROOT / "mcp" / "instagram-server" / "src" / "post_executor.js",
    }
    script = script_map.get(platform)
    if not script or not script.exists():
        print(f"  MCP executor not found for {platform}")
        return False

    temp = ROOT / f".temp_{platform}_content.txt"
    temp.write_text(content, encoding="utf-8")
    try:
        subprocess.run(["node", str(script), str(temp)], check=True, timeout=60)
        return True
    except Exception as e:
        print(f"  MCP post failed: {e}")
        return False
    finally:
        if temp.exists():
            temp.unlink()


def post_content(platform: str, content: str) -> dict:
    """Post content to the specified platform. Returns result info."""
    result = {"platform": platform, "success": False, "details": {}}

    if platform == "twitter":
        resp = post_twitter(content)
        if resp:
            tweet_id = resp.get("data", {}).get("id", "unknown")
            result["success"] = True
            result["details"] = {"tweet_id": tweet_id, "url": f"https://x.com/i/status/{tweet_id}"}
    elif platform in ("linkedin", "facebook", "instagram"):
        if post_via_mcp(platform, content):
            result["success"] = True
    elif platform == "whatsapp":
        print("  WhatsApp broadcast posting not yet fully implemented.")
    elif platform == "email":
        print("  Email sending via Odoo mail.mail not yet fully implemented.")
    elif platform == "odoo":
        print("  Odoo direct posting not yet fully implemented.")
    else:
        print(f"  Unknown platform: {platform}")

    return result


# ─── Intent Parsing ───────────────────────────────────────────────────

def parse_intent(user_input: str) -> tuple[str | None, str]:
    """Parse platform and topic from natural language input (Urdu/English)."""
    lower = user_input.lower()

    # Detect platform — check longer/more-specific keywords first
    platform = None
    # Order matters: check multi-word/longer names before short ones
    check_order = ["instagram", "linkedin", "facebook", "whatsapp", "twitter", "email", "odoo"]
    for p in check_order:
        for kw in PLATFORM_KEYWORDS[p]:
            if re.search(rf'\b{re.escape(kw)}\b', lower):
                platform = p
                break
        if platform:
            break

    # Extract topic: remove platform keywords and common filler words
    topic = user_input
    filler = [
        "pr", "pe", "par", "per", "ke", "ka", "ki", "mein", "about",
        "post", "karo", "kro", "likho", "likh", "write", "create",
        "bhi", "same", "topic", "ek", "acha", "baare",
    ]
    # Remove platform keywords
    for keywords in PLATFORM_KEYWORDS.values():
        for kw in keywords:
            topic = re.sub(rf'\b{re.escape(kw)}\b', '', topic, flags=re.IGNORECASE)
    # Remove filler words
    for f in filler:
        topic = re.sub(rf'\b{re.escape(f)}\b', '', topic, flags=re.IGNORECASE)
    topic = re.sub(r'\s+', ' ', topic).strip()

    if not topic or len(topic) < 3:
        topic = "AI and the future of technology"

    return platform, topic


# ─── Vault Logging ────────────────────────────────────────────────────

def save_to_vault(platform: str, content: str, result: dict, stage: str = "Done"):
    """Save post record to vault."""
    target_dir = DONE_DIR if stage == "Done" else PENDING_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d%H%M%S")
    slug = re.sub(r'[^a-z0-9]+', '-', content[:40].lower()).strip('-')
    fname = f"social-post-{platform}-{slug}-{ts}.md"
    details = json.dumps(result.get("details", {}), indent=2)
    (target_dir / fname).write_text(
        f"---\nplatform: {platform}\nstatus: {stage.lower()}\n"
        f"posted_at: {time.strftime('%Y-%m-%dT%H:%M:%S')}\n"
        f"details: {details}\n---\n\n## Content\n\n{content}\n",
        encoding="utf-8",
    )
    return str(target_dir / fname)


def log_action(action: str, details: str = ""):
    """Append to daily log file."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / f"agent-{time.strftime('%Y%m%d')}.log"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%H:%M:%S')}] {action} {details}\n")


# ─── Status Check ─────────────────────────────────────────────────────

def check_status():
    """Return status of available services."""
    status = {}
    status["Gemini"] = "ok" if GEMINI_API_KEY else "no key"
    status["Grok"] = "ok" if GROK_API_KEY else "no key"
    status["Twitter"] = "ok" if (TWITTER_API_KEY and TWITTER_ACCESS_TOKEN) else "no creds"
    status["LinkedIn"] = "ok" if (ROOT / "mcp" / "linkedin-server" / "post_executor.js").exists() else "missing"
    status["Facebook"] = "ok" if (ROOT / "mcp" / "facebook-server" / "src" / "post_executor.js").exists() else "missing"
    status["Instagram"] = "ok" if (ROOT / "mcp" / "instagram-server" / "src" / "post_executor.js").exists() else "missing"
    return status


# ─── Interactive CLI ──────────────────────────────────────────────────

def print_banner():
    status = check_status()

    def icon(v):
        return "\u2705" if v == "ok" else "\u26a0\ufe0f"

    print()
    print("\u2501" * 50)
    print("  AI Employee Agent")
    print("\u2501" * 50)
    ai = f"Gemini: {icon(status['Gemini'])}  Grok: {icon(status['Grok'])}"
    platforms = "  ".join(f"{k}: {icon(v)}" for k, v in status.items() if k not in ("Gemini", "Grok"))
    print(f"  AI: {ai}")
    print(f"  Platforms: {platforms}")
    print("\u2501" * 50)
    print("  Type a command like: twitter pr AI ke baare mein post karo")
    print("  Commands: status, help, quit")
    print("\u2501" * 50)
    print()


def interactive_loop():
    """Main interactive loop."""
    print_banner()

    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not user_input:
            continue

        lower = user_input.lower()
        if lower in ("quit", "exit", "q"):
            print("Bye!")
            break
        if lower == "status":
            for k, v in check_status().items():
                print(f"  {k}: {v}")
            continue
        if lower == "help":
            print("  Usage: <platform> <topic description>")
            print("  Example: twitter pr AI ke baare mein post karo")
            print("  Example: linkedin post about agentic AI trends")
            print("  Platforms: twitter, linkedin, facebook, instagram, whatsapp, email")
            continue

        # Parse intent
        platform, topic = parse_intent(user_input)
        if not platform:
            print("  Could not detect platform. Please mention: twitter, linkedin, facebook, instagram, whatsapp, or email")
            continue

        print(f"\n  Generating content for {platform.title()}...")
        log_action("GENERATE", f"platform={platform} topic={topic}")

        content = generate_content(platform, topic)
        if not content:
            print("  Failed to generate content (no AI provider available).")
            continue

        # Show draft
        print()
        print("\u2501" * 50)
        print(content)
        print("\u2501" * 50)
        print(f"  ({len(content)} chars)")
        print()
        print("  [ok] Post it?  [edit] Regenerate?  [cancel] Skip?")

        try:
            choice = input("  > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if choice in ("cancel", "c", "no", "nahi", "chodo"):
            print("  Skipped.")
            log_action("CANCEL", f"platform={platform}")
            continue

        if choice in ("edit", "e", "dobara", "regenerate"):
            print(f"  Regenerating...")
            content = generate_content(platform, topic)
            if not content:
                print("  Failed to regenerate.")
                continue
            print()
            print("\u2501" * 50)
            print(content)
            print("\u2501" * 50)
            print(f"  ({len(content)} chars)")
            print()
            try:
                choice = input("  Post this? [ok/cancel] > ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\nBye!")
                break
            if choice not in ("ok", "y", "yes", "ha", "haan"):
                print("  Skipped.")
                continue

        if choice in ("ok", "y", "yes", "ha", "haan", ""):
            print(f"\n  Posting to {platform.title()}...")
            log_action("POST", f"platform={platform}")

            result = post_content(platform, content)
            if result["success"]:
                path = save_to_vault(platform, content, result, "Done")
                print(f"\n  Posted to {platform.title()}!")
                for k, v in result["details"].items():
                    print(f"    {k}: {v}")
                print(f"    Saved: {path}")
                log_action("SUCCESS", f"platform={platform} details={json.dumps(result['details'])}")
            else:
                save_to_vault(platform, content, result, "Pending_Approval")
                print(f"\n  Post failed or platform not fully implemented.")
                print(f"    Content saved to Pending_Approval/ for manual posting.")
                log_action("FAILED", f"platform={platform}")
        else:
            print("  Skipped.")

        print()


if __name__ == "__main__":
    interactive_loop()
