"""Gemini API client for AI processing."""

import time
from typing import Any, Dict, Optional, List
from datetime import datetime

from google import genai

from ..utils.config import Config
from ..utils.logger import get_logger


class ClaudeClient:
    """Client for interacting with Gemini API."""

    def __init__(self, config: Config):
        """Initialize the Gemini client.

        Args:
            config: Configuration object with API credentials.
        """
        self.config = config
        self.api_key = config.gemini_api_key
        self.logger = get_logger("gemini_client")
        self._request_count = 0
        self._last_request: Optional[datetime] = None
        self._model = "gemini-2.5-flash"

        # Initialize Gemini client
        if self.api_key:
            self._client = genai.Client(api_key=self.api_key)
        else:
            self._client = None

    def send_request(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Send a request to Gemini API.

        Args:
            prompt: The user prompt to send.
            system_prompt: Optional system prompt for context.
            max_tokens: Maximum tokens in response.
            temperature: Sampling temperature.

        Returns:
            Dictionary with response data.

        Raises:
            ClaudeAPIError: If API request fails.
        """
        if not self.api_key:
            raise ClaudeAPIError("Gemini API key not configured")

        self.logger.info(f"Sending request to Gemini API (prompt length: {len(prompt)})")

        try:
            # Build the full prompt with system context
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"

            # Call Gemini API
            config = genai.types.GenerateContentConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
            )

            response = self._client.models.generate_content(
                model=self._model,
                contents=full_prompt,
                config=config,
            )

            response_text = response.text

            self._request_count += 1
            self._last_request = datetime.now()

            return {
                "success": True,
                "content": response_text,
                "model": self._model,
                "tokens_used": len(response_text.split()),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Gemini API request failed: {e}")
            raise ClaudeAPIError(f"API request failed: {e}")

    def validate_connection(self) -> tuple[bool, str]:
        """Validate the API connection.

        Returns:
            Tuple of (is_valid, message).
        """
        if not self.api_key:
            return False, "API key not configured"

        try:
            if len(self.api_key) < 10:
                return False, "API key appears invalid"
            return True, "Connection validated"
        except Exception as e:
            return False, str(e)

    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics.

        Returns:
            Dictionary with usage statistics.
        """
        return {
            "request_count": self._request_count,
            "last_request": self._last_request.isoformat() if self._last_request else None,
            "api_configured": bool(self.api_key)
        }


class ClaudeAPIError(Exception):
    """Exception raised when Gemini API request fails."""
    pass
