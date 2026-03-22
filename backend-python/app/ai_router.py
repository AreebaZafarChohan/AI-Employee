"""AI Router with Grok as primary (Gemini rate-limited)."""

import httpx
import logging
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)


class AIRouter:
    """AI router with Grok primary, Gemini fallback."""

    def __init__(self):
        self.grok_key = settings.GROK_API_KEY
        self.gemini_key = settings.GEMINI_API_KEY
        self.grok_model = settings.GROK_MODEL
        self.gemini_model = settings.GEMINI_MODEL
        self.primary_provider = settings.AI_PROVIDER

    async def generate(self, prompt: str, max_tokens: int = 1000) -> str:
        """Generate response using Grok (primary) or Gemini (fallback)."""
        # Try Grok first
        if self.primary_provider == "grok" and self.grok_key:
            try:
                return await self._call_grok(prompt, max_tokens)
            except Exception as e:
                logger.warning(f"Grok failed, trying Gemini: {e}")

        # Try Gemini
        if self.gemini_key:
            try:
                return await self._call_gemini(prompt, max_tokens)
            except Exception as e:
                logger.warning(f"Gemini also failed: {e}")

        # Last resort: Grok even if not primary
        if self.grok_key and self.primary_provider != "grok":
            try:
                return await self._call_grok(prompt, max_tokens)
            except Exception as e:
                logger.error(f"All AI providers failed: {e}")

        return f"[AI unavailable] Received: {prompt[:100]}..."

    async def _call_grok(self, prompt: str, max_tokens: int) -> str:
        """Call xAI Grok API."""
        url = "https://api.x.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.grok_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.grok_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def _call_gemini(self, prompt: str, max_tokens: int) -> str:
        """Call Google Gemini API."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:generateContent"
        params = {"key": self.gemini_key}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.7},
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, params=params, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]


# Global instance
ai_router = AIRouter()
