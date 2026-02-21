"""Response processor for Claude API responses."""

import re
from typing import Any, Dict, List, Optional
from datetime import datetime

from ..utils.logger import get_logger


class ResponseProcessor:
    """Processes and validates Claude API responses."""

    def __init__(self):
        """Initialize the response processor."""
        self.logger = get_logger("response_processor")

    def process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Process a Claude API response.

        Args:
            response: Raw response from Claude API.

        Returns:
            Processed response dictionary.
        """
        result = {
            "success": False,
            "content": "",
            "metadata": {},
            "errors": []
        }

        try:
            if not response.get("success"):
                result["errors"].append("API response indicates failure")
                return result

            content = response.get("content", "")

            # Validate content
            is_valid, error = self.validate_response(content)
            if not is_valid:
                result["errors"].append(error)
                return result

            # Sanitize content
            sanitized = self.sanitize_response(content)

            result["success"] = True
            result["content"] = sanitized
            result["metadata"] = {
                "model": response.get("model"),
                "tokens_used": response.get("tokens_used"),
                "timestamp": response.get("timestamp"),
                "processed_at": datetime.now().isoformat()
            }

        except Exception as e:
            result["errors"].append(str(e))
            self.logger.error(f"Response processing failed: {e}")

        return result

    def validate_response(self, content: str) -> tuple[bool, str]:
        """Validate Claude response content.

        Args:
            content: Response content to validate.

        Returns:
            Tuple of (is_valid, error_message).
        """
        if not content:
            return False, "Empty response content"

        if len(content) < 10:
            return False, "Response too short"

        # Check for potential issues
        dangerous_patterns = [
            r'<script[^>]*>',
            r'javascript:',
            r'on\w+\s*=',
            r'data:text/html',
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return False, f"Potentially unsafe content detected"

        return True, ""

    def sanitize_response(self, content: str) -> str:
        """Sanitize Claude response content.

        Args:
            content: Response content to sanitize.

        Returns:
            Sanitized content.
        """
        # Remove potential script tags
        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)

        # Remove HTML comments that might hide content
        content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)

        # Normalize line endings
        content = content.replace('\r\n', '\n').replace('\r', '\n')

        # Remove excessive whitespace
        content = re.sub(r'\n{3,}', '\n\n', content)

        return content.strip()

    def extract_plan_sections(self, content: str) -> Dict[str, str]:
        """Extract sections from a plan response.

        Args:
            content: Plan content.

        Returns:
            Dictionary with section names and content.
        """
        sections = {}
        current_section = "preamble"
        current_content = []

        for line in content.split('\n'):
            # Check for section headers (## Header)
            if line.startswith('## '):
                if current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = line[3:].strip().lower().replace(' ', '_')
                current_content = []
            else:
                current_content.append(line)

        # Don't forget the last section
        if current_content:
            sections[current_section] = '\n'.join(current_content).strip()

        return sections

    def extract_action_items(self, content: str) -> List[str]:
        """Extract action items from plan content.

        Args:
            content: Plan content.

        Returns:
            List of action items.
        """
        action_items = []

        # Find checkbox items
        checkbox_pattern = r'- \[[ x]\] (.+)'
        matches = re.findall(checkbox_pattern, content, re.IGNORECASE)
        action_items.extend(matches)

        # Find numbered items in action-related sections
        lines = content.split('\n')
        in_action_section = False

        for line in lines:
            if '## ' in line and any(word in line.lower() for word in ['action', 'step', 'task', 'todo']):
                in_action_section = True
            elif '## ' in line:
                in_action_section = False
            elif in_action_section:
                # Match numbered items
                match = re.match(r'^\d+\.\s+(.+)', line.strip())
                if match:
                    action_items.append(match.group(1))

        return action_items
