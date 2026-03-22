"""Unified AI Client with Gemini (primary) and Grok (fallback)."""

import os
import json
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class AIClient:
    """Unified AI client wrapping Gemini and Grok APIs."""

    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY", "")
        self.grok_key = os.getenv("GROK_API_KEY", "")
        self._gemini_model = None
        self._grok_client = None
        self._last_call_time = 0
        self._min_interval = 1.0  # rate limit: 1 call/sec

    def _get_gemini(self):
        if self._gemini_model is None and self.gemini_key:
            import google.generativeai as genai
            genai.configure(api_key=self.gemini_key)
            self._gemini_model = genai.GenerativeModel("gemini-1.5-flash")
        return self._gemini_model

    def _get_grok(self):
        if self._grok_client is None and self.grok_key:
            from openai import OpenAI
            self._grok_client = OpenAI(
                base_url="https://api.x.ai/v1",
                api_key=self.grok_key,
            )
        return self._grok_client

    def _rate_limit(self):
        elapsed = time.time() - self._last_call_time
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_call_time = time.time()

    def _call_gemini(self, prompt: str) -> str:
        model = self._get_gemini()
        if not model:
            raise RuntimeError("Gemini API key not configured")
        self._rate_limit()
        response = model.generate_content(prompt)
        return response.text

    def _call_grok(self, prompt: str) -> str:
        client = self._get_grok()
        if not client:
            raise RuntimeError("Grok API key not configured")
        self._rate_limit()
        response = client.chat.completions.create(
            model="grok-beta",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content

    def generate(self, prompt: str) -> str:
        """Generate text with Gemini, falling back to Grok."""
        try:
            return self._call_gemini(prompt)
        except Exception as e:
            logger.warning("Gemini failed (%s), trying Grok fallback", e)
        try:
            return self._call_grok(prompt)
        except Exception as e:
            logger.error("Both AI providers failed: %s", e)
            raise RuntimeError("All AI providers failed") from e

    def score_lead(self, profile_data: dict) -> int:
        """Score a lead 0-100 based on profile data."""
        prompt = f"""Score this sales lead from 0-100 based on fit for AI/SaaS services.
Return ONLY a JSON object: {{"score": <number>, "reason": "<one sentence>"}}

Profile:
- Name: {profile_data.get('name', 'Unknown')}
- Title: {profile_data.get('title', 'Unknown')}
- Company: {profile_data.get('company', 'Unknown')}
- Industry: {profile_data.get('industry', 'Unknown')}
- Headline: {profile_data.get('headline', '')}
"""
        try:
            result = self.generate(prompt)
            data = json.loads(result.strip().strip("```json").strip("```"))
            return max(0, min(100, int(data.get("score", 50))))
        except Exception:
            return 50  # template fallback

    def generate_dm(self, lead: dict, context: str = "") -> str:
        """Generate a personalized DM for a lead."""
        prompt = f"""Write a short, personalized LinkedIn DM (under 300 chars) to this person.
Be professional, friendly, and mention a specific detail from their profile.
Do NOT be salesy. Focus on starting a conversation.

Lead:
- Name: {lead.get('name', '')}
- Title: {lead.get('title', '')}
- Company: {lead.get('company', '')}
- Headline: {lead.get('headline', '')}

Context: {context or 'Initial outreach for AI automation services'}

Return ONLY the message text, no quotes."""
        try:
            return self.generate(prompt).strip().strip('"')
        except Exception:
            name = lead.get('name', '').split()[0] if lead.get('name') else 'there'
            return f"Hi {name}, I came across your profile and was impressed by your work at {lead.get('company', 'your company')}. Would love to connect and exchange ideas on AI automation."

    def analyze_response(self, message: str) -> dict:
        """Analyze a lead's response to determine intent."""
        prompt = f"""Analyze this LinkedIn message response and classify the intent.
Return ONLY JSON: {{"intent": "positive|negative|neutral|meeting_request", "confidence": 0.0-1.0, "suggested_action": "<action>"}}

Message: {message}"""
        try:
            result = self.generate(prompt)
            return json.loads(result.strip().strip("```json").strip("```"))
        except Exception:
            return {"intent": "neutral", "confidence": 0.5, "suggested_action": "review_manually"}

    def suggest_next_action(self, lead: dict, history: list) -> str:
        """Suggest the next action for a lead."""
        prompt = f"""Given this sales lead and interaction history, suggest the single best next action.
Return a short action phrase (e.g., "Send follow-up DM", "Schedule meeting", "Move to nurture list").

Lead: {lead.get('name', '')} at {lead.get('company', '')} - Stage: {lead.get('stage', 'new')}
History: {json.dumps(history[-5:]) if history else 'No interactions yet'}"""
        try:
            return self.generate(prompt).strip()
        except Exception:
            stage = lead.get("stage", "new")
            fallback = {
                "new": "Send initial outreach DM",
                "contacted": "Send follow-up message",
                "responded": "Schedule a meeting",
                "meeting": "Send proposal / generate invoice",
                "closed_won": "Onboard client",
            }
            return fallback.get(stage, "Review lead manually")
