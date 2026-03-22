"""Social Media Service for generating and managing posts."""

import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from src.core.config import get_settings

settings = get_settings()

def generate_social_post(topic: str, platform: str) -> dict:
    """Use Gemini to generate a social media post and save it to Pending_Approval."""
    
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        return {"error": "GEMINI_API_KEY not found in environment"}

    # Clear GOOGLE_API_KEY if it exists to prevent SDK overriding
    if "GOOGLE_API_KEY" in os.environ:
        del os.environ["GOOGLE_API_KEY"]

    try:
        from google import genai
        # Explicitly pass api_key to the client
        client = genai.Client(api_key=gemini_api_key)

        prompt = f"""You are a professional social media manager for an AI-First company.
Write a highly engaging, impactful post for {platform} about the following topic:
Topic: {topic}

Requirements:
- Platform: {platform}
- Tone: Professional, forward-thinking, and inspiring.
- Include 3-5 relevant hashtags.
- Use emojis appropriately for the platform.
- Output ONLY the post content. No explanations.

Post:"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        content = response.text.strip()

        # Save to Pending_Approval
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        safe_topic = re.sub(r"[^\w\s-]", "", topic.lower())
        safe_topic = re.sub(r"[\s_]+", "-", safe_topic).strip("-")[:30]
        filename = f"social-post-{platform}-{safe_topic}-{ts}.md"
        
        vault_path = Path(settings.VAULT_PATH)
        pending_dir = vault_path / "Pending_Approval"
        pending_dir.mkdir(parents=True, exist_ok=True)
        
        dest = pending_dir / filename
        
        markdown_content = f"""---
type: social_post_pending
platform: {platform}
topic: "{topic.replace('"', '\\"')}"
created_at: "{now_iso}"
status: pending_approval
---

# Pending {platform.title()} Post: {topic}

**Platform:** {platform.title()}  
**Generated At:** {now_iso}

## Content

{content}

---

## Instructions
- **Approve:** Move this file to `Approved/` to trigger automatic posting.
- **Reject:** Move this file to `Rejected/` or delete it.
"""
        dest.write_text(markdown_content, encoding="utf-8")
        
        return {
            "id": filename,
            "platform": platform,
            "topic": topic,
            "content": content,
            "filename": filename,
            "status": "pending_approval"
        }

    except Exception as e:
        return {"error": str(e)}
