#!/usr/bin/env python3
"""
Post to Twitter using OAuth 1.0a API (no browser needed).
Uses Gemini to generate content, then posts via Twitter API v2.
"""
import os
import sys
import json
import time
import hmac
import hashlib
import base64
import urllib.parse
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

# Gemini for content generation
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_AI_API_KEY")

# Twitter OAuth 1.0a creds
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY", "")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET", "")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN", "")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")

def percent_encode(s):
    return urllib.parse.quote(str(s), safe="")

def generate_oauth_header(method, url):
    import uuid
    oauth_params = {
        "oauth_consumer_key": TWITTER_API_KEY,
        "oauth_nonce": uuid.uuid4().hex,
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_token": TWITTER_ACCESS_TOKEN,
        "oauth_version": "1.0",
    }
    param_string = "&".join(
        f"{percent_encode(k)}={percent_encode(v)}"
        for k, v in sorted(oauth_params.items())
    )
    base_string = f"{method.upper()}&{percent_encode(url)}&{percent_encode(param_string)}"
    signing_key = f"{percent_encode(TWITTER_API_SECRET)}&{percent_encode(TWITTER_ACCESS_TOKEN_SECRET)}"
    signature = base64.b64encode(
        hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha1).digest()
    ).decode()
    oauth_params["oauth_signature"] = signature
    header = "OAuth " + ", ".join(
        f'{percent_encode(k)}="{percent_encode(v)}"'
        for k, v in sorted(oauth_params.items())
    )
    return header

def generate_with_gemini(topic):
    """Generate tweet content using Gemini API."""
    if not GEMINI_API_KEY:
        print("No GEMINI_API_KEY found, using default content")
        return f"Exploring the future of Agentic AI - autonomous systems that plan, reason, and act. The next wave of innovation is here. #AgenticAI #AI #Automation"

    import urllib.request
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    prompt = f"""Write a single tweet (max 270 characters) about: {topic}
Rules:
- Must be under 270 characters total
- Include 2-3 relevant hashtags
- Professional but engaging tone
- No quotes or markdown, just the tweet text"""

    data = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}]
    }).encode()

    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            text = result["candidates"][0]["content"]["parts"][0]["text"].strip()
            # Clean up any quotes
            text = text.strip('"').strip("'").strip()
            if len(text) > 280:
                text = text[:277] + "..."
            return text
    except Exception as e:
        print(f"Gemini error: {e}, using fallback")
        return f"Agentic AI is transforming how businesses operate - autonomous systems that think, plan, and execute. The future is now. #AgenticAI #AI #FutureOfWork"

def post_tweet(content):
    """Post a tweet using Twitter API v2 with OAuth 1.0a."""
    import urllib.request

    url = "https://api.twitter.com/2/tweets"
    auth_header = generate_oauth_header("POST", url)

    data = json.dumps({"text": content}).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", auth_header)
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            return result
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"Twitter API Error {e.code}: {body}")
        raise

def main():
    topic = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Agentic AI and the future of autonomous business automation"

    print("=" * 60)
    print("Twitter AI Poster (OAuth 1.0a API)")
    print("=" * 60)

    # Check credentials
    if not TWITTER_API_KEY or not TWITTER_ACCESS_TOKEN:
        print("ERROR: Twitter API credentials not set in .env")
        print("Need: TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET")
        sys.exit(1)

    print(f"\nTopic: {topic}")
    print(f"Generating tweet with Gemini...")

    content = generate_with_gemini(topic)
    print(f"\nGenerated tweet ({len(content)} chars):")
    print(f"---\n{content}\n---")

    print(f"\nPosting to Twitter via API...")
    try:
        result = post_tweet(content)
        tweet_id = result.get("data", {}).get("id", "unknown")
        print(f"\nPosted successfully!")
        print(f"Tweet ID: {tweet_id}")
        print(f"URL: https://x.com/i/status/{tweet_id}")

        # Save to vault
        vault_done = ROOT / "AI-Employee-Vault" / "Done"
        vault_done.mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y%m%d%H%M%S")
        fname = f"twitter-post-{ts}.md"
        (vault_done / fname).write_text(
            f"---\nplatform: twitter\ntweet_id: {tweet_id}\nposted_at: {time.strftime('%Y-%m-%dT%H:%M:%S')}\n---\n\n{content}\n",
            encoding="utf-8"
        )
        print(f"Saved to: AI-Employee-Vault/Done/{fname}")
    except Exception as e:
        print(f"\nFailed to post: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
