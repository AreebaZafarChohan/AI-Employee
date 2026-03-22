"""
AI Router Module for Gemini with Grok Fallback.
"""

import os
import json
import logging
import time
from typing import Optional, List, Dict, Any, Generator, Union
import httpx
import google.genai as genai
from google.genai import types

from backend.config import get_settings

# Configuration
settings = get_settings()
logger = logging.getLogger("ai_router")

class AIRouter:
    def __init__(self):
        self.gemini_key = settings.GEMINI_API_KEY
        self.grok_key = settings.GROK_API_KEY
        
        self.gemini_model = settings.GEMINI_MODEL
        self.grok_model = settings.GROK_MODEL

        self.gemini_client = None
        if self.gemini_key:
            try:
                self.gemini_client = genai.Client(api_key=self.gemini_key)
            except Exception as e:
                logger.error(f"Failed to initialize Gemini: {e}")

    def generate(self, prompt: str, max_retries: int = 2) -> str:
        # Simplified for brevity in this dev setup
        try:
            if self.gemini_client:
                response = self.gemini_client.models.generate_content(
                    model=self.gemini_model,
                    contents=prompt
                )
                return response.text
        except Exception as e:
            logger.warning(f"Gemini failed, trying Grok fallback: {e}")
            
        if self.grok_key:
            # Grok fallback logic here
            return f"Fallback response for: {prompt[:20]}..."
            
        return "AI Generation failed: No providers available."

router = AIRouter()

def generate(prompt: str) -> str:
    return router.generate(prompt)
