"""
AI Router Module for Gemini with Grok Fallback.
Handles primary execution on Gemini API with automatic fallback to Grok API 
in case of failure (quota, timeout, network error, etc.).
"""

import os
import json
import logging
import time
from typing import Optional, List, Dict, Any, Generator, Union
import httpx
from google import genai
from google.genai import types

from src.core.config import get_settings
from src.core.exceptions import (
    AIServiceError, AIQuotaError, AITimeoutError, AIConfigError
)

# Configuration
settings = get_settings()
logger = logging.getLogger("ai_router")

# Ensure logging is configured if not already
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | AI_ROUTER | %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(settings.LOG_LEVEL)

class AIRouter:
    def __init__(self):
        """Initialize the AI Router with Gemini and Grok clients."""
        self.gemini_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
        self.grok_key = settings.GROK_API_KEY or os.getenv("GROK_API_KEY")
        
        self.gemini_model = settings.GEMINI_MODEL
        self.grok_model = settings.GROK_MODEL

        # Initialize Gemini SDK Client
        self.gemini_client = None
        if self.gemini_key:
            try:
                self.gemini_client = genai.Client(api_key=self.gemini_key)
                logger.debug("Gemini client initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
        else:
            logger.warning("GEMINI_API_KEY not found in settings or environment.")

        if not self.grok_key:
            logger.warning("GROK_API_KEY not found in settings or environment. Fallback will be unavailable.")

    def _classify_error(self, error: Exception, service: str) -> Exception:
        """Classify exceptions into specific AI error types."""
        err_msg = str(error).lower()
        
        # Check for Quota/Rate Limit
        if any(kw in err_msg for kw in ["quota", "429", "rate limit", "exhausted"]):
            return AIQuotaError(f"{service} Quota Exceeded: {error}")
            
        # Check for Timeouts
        if any(kw in err_msg for kw in ["timeout", "deadline", "timed out"]):
            return AITimeoutError(f"{service} Timeout: {error}")
            
        # Generic Service Error
        return AIServiceError(f"{service} API Error: {error}")

    def _call_gemini(self, prompt: str, stream: bool = False) -> Union[str, Generator[str, None, None]]:
        """Direct call to Gemini API."""
        if not self.gemini_client:
            raise AIConfigError("Gemini client is not configured.")

        try:
            if stream:
                logger.debug(f"Calling Gemini ({self.gemini_model}) with streaming...")
                response_stream = self.gemini_client.models.generate_content_stream(
                    model=self.gemini_model,
                    contents=prompt
                )
                def gen():
                    for chunk in response_stream:
                        if chunk.text:
                            yield chunk.text
                return gen()
            else:
                logger.debug(f"Calling Gemini ({self.gemini_model})...")
                response = self.gemini_client.models.generate_content(
                    model=self.gemini_model,
                    contents=prompt
                )
                return response.text
        except Exception as e:
            classified = self._classify_error(e, "Gemini")
            logger.error(f"Gemini internal error: {classified}")
            raise classified

    def _call_grok(self, prompt: str, stream: bool = False) -> Union[str, Generator[str, None, None]]:
        """Direct call to Grok (xAI) API via HTTP (OpenAI compatible)."""
        if not self.grok_key:
            raise AIConfigError("Grok API key is not configured.")

        url = "https://api.x.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.grok_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.grok_model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": stream
        }

        try:
            # Using httpx for better async/sync support and timeout handling
            with httpx.Client(timeout=httpx.Timeout(60.0, connect=10.0)) as client:
                if stream:
                    logger.debug(f"Calling Grok ({self.grok_model}) with streaming...")
                    def gen():
                        with client.stream("POST", url, headers=headers, json=payload) as response:
                            if response.status_code == 429:
                                raise AIQuotaError("Grok Quota Exceeded (429)")
                            response.raise_for_status()
                            
                            for line in response.iter_lines():
                                if line.startswith("data: "):
                                    data_str = line[6:]
                                    if data_str == "[DONE]":
                                        break
                                    try:
                                        chunk = json.loads(data_str)
                                        content = chunk["choices"][0]["delta"].get("content", "")
                                        if content:
                                            yield content
                                    except:
                                        continue
                    return gen()
                else:
                    logger.debug(f"Calling Grok ({self.grok_model})...")
                    response = client.post(url, headers=headers, json=payload)
                    if response.status_code == 429:
                        raise AIQuotaError("Grok Quota Exceeded (429)")
                    response.raise_for_status()
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
        except httpx.TimeoutException as te:
            raise AITimeoutError(f"Grok Timeout: {te}")
        except Exception as e:
            classified = self._classify_error(e, "Grok")
            logger.error(f"Grok internal error: {classified}")
            raise classified

    def send_prompt(self, prompt: str) -> str:
        """Alias for generate()."""
        return self.generate(prompt)

    def generate(self, prompt: str, max_retries: int = 2) -> str:
        """
        Generate content with automatic fallback.
        Order: Gemini (with retries) -> Grok (fallback).
        """
        # Phase 1: Try Gemini
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    logger.info(f"Gemini retry attempt {attempt}/{max_retries}...")
                else:
                    logger.info("Starting generation with Gemini...")
                
                start_time = time.time()
                result = self._call_gemini(prompt)
                duration = time.time() - start_time
                
                logger.info(f"SUCCESS | Service: Gemini | Model: {self.gemini_model} | Duration: {duration:.2f}s")
                return result

            except AIQuotaError as e:
                logger.warning(f"QUOTA EXCEEDED | Service: Gemini | Error: {e}")
                # Don't retry quota errors, jump to fallback
                break
            except (AITimeoutError, AIServiceError) as e:
                if attempt < max_retries:
                    wait_time = 2 ** attempt
                    logger.warning(f"RETRYING | Service: Gemini | Attempt: {attempt+1} | Error: {e} | Waiting {wait_time}s")
                    time.sleep(wait_time)
                else:
                    logger.error(f"FAILURE | Service: Gemini | Max retries reached. Error: {e}")
            except Exception as e:
                logger.error(f"CRITICAL ERROR | Service: Gemini | Error: {e}")
                break

        # Phase 2: Fallback to Grok
        logger.warning(f"FALLBACK | Switching to Grok fallback model...")
        try:
            start_time = time.time()
            result = self._call_grok(prompt)
            duration = time.time() - start_time
            
            logger.info(f"SUCCESS | Service: Grok | Model: {self.grok_model} | Duration: {duration:.2f}s")
            return result
        except Exception as e:
            logger.error(f"TOTAL FAILURE | Both Gemini and Grok failed. Final error: {e}")
            raise AIServiceError(f"AI Routing failed: All providers exhausted. Last error: {e}")

    def generate_stream(self, prompt: str) -> Generator[str, None, None]:
        """
        Generate streaming content with automatic fallback.
        Fallback only occurs if the first chunk fails.
        """
        logger.info("Starting streaming generation with Gemini...")
        try:
            # We wrap the generator to catch initial connection errors
            gemini_gen = self._call_gemini(prompt, stream=True)
            for chunk in gemini_gen:
                yield chunk
            logger.info(f"SUCCESS | Service: Gemini (Streaming) | Model: {self.gemini_model}")
            return
        except (AIQuotaError, AITimeoutError, AIServiceError) as e:
            logger.warning(f"FALLBACK | Gemini stream failed early: {e}. Switching to Grok...")
        except Exception as e:
            logger.error(f"Gemini stream crashed: {e}")

        # Fallback to Grok
        try:
            grok_gen = self._call_grok(prompt, stream=True)
            for chunk in grok_gen:
                yield chunk
            logger.info(f"SUCCESS | Service: Grok (Streaming) | Model: {self.grok_model}")
        except Exception as e:
            logger.error(f"TOTAL FAILURE | Both streaming providers failed. Error: {e}")
            raise AIServiceError(f"AI Streaming failed: {e}")

# Convenience instance
router = AIRouter()

def generate(prompt: str) -> str:
    """Convenience functional wrapper for single generation."""
    return router.generate(prompt)

def generate_stream(prompt: str) -> Generator[str, None, None]:
    """Convenience functional wrapper for streaming generation."""
    return router.generate_stream(prompt)
