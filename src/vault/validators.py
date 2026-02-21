"""Input validation and sanitization for vault operations."""

import re
from typing import List, Optional
from pathlib import Path

from ..utils.logger import get_logger


class InputValidator:
    """Validates and sanitizes input content for security."""

    # Maximum file size in bytes (1MB)
    MAX_FILE_SIZE = 1024 * 1024

    # Maximum content length in characters
    MAX_CONTENT_LENGTH = 100000

    # Patterns that indicate potentially malicious content
    DANGEROUS_PATTERNS = [
        r'<script[^>]*>',  # Script tags
        r'javascript:',  # JavaScript URLs
        r'on\w+\s*=',  # Event handlers
        r'data:text/html',  # Data URLs with HTML
        r'vbscript:',  # VBScript
        r'expression\s*\(',  # CSS expressions
        r'url\s*\(\s*["\']?\s*javascript',  # CSS JavaScript URLs
        r'<!--.*?-->.*?<',  # Hidden HTML in comments
        r'\{\{.*?\}\}',  # Template injection
        r'\$\{.*?\}',  # Variable injection
        r'<%.*?%>',  # Server-side tags
        r'<\?.*?\?>',  # PHP tags
    ]

    # File extensions that should not be processed
    BLOCKED_EXTENSIONS = [
        '.exe', '.dll', '.bat', '.cmd', '.ps1', '.sh',
        '.vbs', '.js', '.jar', '.msi', '.scr', '.pif',
        '.com', '.hta', '.cpl', '.reg', '.inf'
    ]

    def __init__(self):
        """Initialize the input validator."""
        self.logger = get_logger("validator")
        self._compiled_patterns = [
            re.compile(pattern, re.IGNORECASE | re.DOTALL)
            for pattern in self.DANGEROUS_PATTERNS
        ]

    def validate_content(self, content: str) -> tuple[bool, str]:
        """Validate content for safety.

        Args:
            content: Content to validate.

        Returns:
            Tuple of (is_valid, error_message).
        """
        if not content:
            return False, "Content is empty"

        if len(content) > self.MAX_CONTENT_LENGTH:
            return False, f"Content exceeds maximum length ({self.MAX_CONTENT_LENGTH} characters)"

        # Check for dangerous patterns
        for pattern in self._compiled_patterns:
            if pattern.search(content):
                self.logger.warning(f"Dangerous pattern detected: {pattern.pattern}")
                return False, "Content contains potentially unsafe patterns"

        # Check for null bytes
        if '\x00' in content:
            return False, "Content contains null bytes"

        # Check for excessive special characters (potential binary data)
        special_ratio = sum(1 for c in content if ord(c) < 32 and c not in '\n\r\t') / max(len(content), 1)
        if special_ratio > 0.1:
            return False, "Content appears to be binary or corrupted"

        return True, ""

    def validate_file_path(self, path: str | Path) -> tuple[bool, str]:
        """Validate a file path for safety.

        Args:
            path: File path to validate.

        Returns:
            Tuple of (is_valid, error_message).
        """
        file_path = Path(path)

        # Check for path traversal
        try:
            resolved = file_path.resolve()
            # Ensure path doesn't go outside expected directories
            if '..' in str(file_path):
                self.logger.warning(f"Path traversal attempt: {path}")
                return False, "Path contains traversal characters"
        except Exception as e:
            return False, f"Invalid path: {e}"

        # Check extension
        suffix = file_path.suffix.lower()
        if suffix in self.BLOCKED_EXTENSIONS:
            return False, f"File type not allowed: {suffix}"

        # Check filename for suspicious patterns
        filename = file_path.name
        if any(c in filename for c in ['<', '>', ':', '"', '|', '?', '*']):
            return False, "Filename contains invalid characters"

        return True, ""

    def validate_file(self, path: str | Path) -> tuple[bool, str]:
        """Validate a file for processing.

        Args:
            path: Path to the file.

        Returns:
            Tuple of (is_valid, error_message).
        """
        file_path = Path(path)

        # Validate path first
        is_valid, error = self.validate_file_path(file_path)
        if not is_valid:
            return False, error

        # Check if file exists
        if not file_path.exists():
            return False, "File does not exist"

        if not file_path.is_file():
            return False, "Path is not a file"

        # Check file size
        try:
            size = file_path.stat().st_size
            if size > self.MAX_FILE_SIZE:
                return False, f"File exceeds maximum size ({self.MAX_FILE_SIZE} bytes)"
            if size == 0:
                return False, "File is empty"
        except Exception as e:
            return False, f"Cannot read file stats: {e}"

        return True, ""

    def sanitize_content(self, content: str) -> str:
        """Sanitize content for safe processing.

        Args:
            content: Content to sanitize.

        Returns:
            Sanitized content.
        """
        if not content:
            return ""

        # Remove null bytes
        content = content.replace('\x00', '')

        # Remove script tags and content
        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)

        # Remove style tags with expressions
        content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)

        # Remove event handlers
        content = re.sub(r'\s+on\w+\s*=\s*["\'][^"\']*["\']', '', content, flags=re.IGNORECASE)

        # Remove javascript: URLs
        content = re.sub(r'javascript:[^\s]*', '', content, flags=re.IGNORECASE)

        # Remove HTML comments
        content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)

        # Normalize line endings
        content = content.replace('\r\n', '\n').replace('\r', '\n')

        # Remove excessive newlines
        content = re.sub(r'\n{4,}', '\n\n\n', content)

        # Remove leading/trailing whitespace from lines while preserving structure
        lines = content.split('\n')
        cleaned_lines = [line.rstrip() for line in lines]
        content = '\n'.join(cleaned_lines)

        return content.strip()

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize a filename for safe use.

        Args:
            filename: Filename to sanitize.

        Returns:
            Sanitized filename.
        """
        if not filename:
            return "unnamed"

        # Remove path components
        filename = Path(filename).name

        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*\x00'
        for char in invalid_chars:
            filename = filename.replace(char, '_')

        # Remove leading/trailing spaces and dots
        filename = filename.strip(' .')

        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            max_name_len = 255 - len(ext) - 1 if ext else 255
            filename = name[:max_name_len] + ('.' + ext if ext else '')

        # Ensure not empty
        if not filename:
            filename = "unnamed"

        return filename


class RetryHandler:
    """Handles retry logic for transient failures."""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0
    ):
        """Initialize retry handler.

        Args:
            max_retries: Maximum number of retry attempts.
            base_delay: Initial delay between retries in seconds.
            max_delay: Maximum delay between retries in seconds.
            exponential_base: Base for exponential backoff.
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.logger = get_logger("retry_handler")

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for a retry attempt.

        Args:
            attempt: Current attempt number (0-indexed).

        Returns:
            Delay in seconds.
        """
        delay = self.base_delay * (self.exponential_base ** attempt)
        return min(delay, self.max_delay)

    def should_retry(self, exception: Exception) -> bool:
        """Determine if an exception is retryable.

        Args:
            exception: The exception that occurred.

        Returns:
            True if should retry, False otherwise.
        """
        # List of exception types that are typically transient
        retryable_types = (
            ConnectionError,
            TimeoutError,
            OSError,
        )

        # Check exception type
        if isinstance(exception, retryable_types):
            return True

        # Check for specific error messages indicating transient issues
        error_message = str(exception).lower()
        transient_indicators = [
            'timeout',
            'connection',
            'temporary',
            'retry',
            'rate limit',
            'too many requests',
            '503',
            '502',
            '504',
            'service unavailable'
        ]

        return any(indicator in error_message for indicator in transient_indicators)

    def execute_with_retry(self, func, *args, **kwargs):
        """Execute a function with retry logic.

        Args:
            func: Function to execute.
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.

        Returns:
            Function result.

        Raises:
            Exception: Last exception if all retries fail.
        """
        import time

        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e

                if attempt < self.max_retries and self.should_retry(e):
                    delay = self.calculate_delay(attempt)
                    self.logger.warning(
                        f"Attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                else:
                    self.logger.error(
                        f"Attempt {attempt + 1} failed: {e}. "
                        f"{'No more retries.' if attempt >= self.max_retries else 'Not retryable.'}"
                    )
                    break

        raise last_exception
