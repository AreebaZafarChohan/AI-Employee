"""Configuration management for AI Employee."""

import os
from pathlib import Path
from typing import Optional, List
from dotenv import load_dotenv


class Config:
    """Manages configuration settings for the AI Employee system."""

    def __init__(self, env_path: Optional[str] = None):
        """Initialize configuration from environment variables.

        Args:
            env_path: Optional path to .env file. If not provided, looks in current directory.
        """
        if env_path:
            load_dotenv(env_path)
        else:
            load_dotenv()

        self._load_settings()

    def _load_settings(self) -> None:
        """Load settings from environment variables."""
        # Gemini API
        self.gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")

        # Vault Configuration
        self.vault_path: str = os.getenv("VAULT_PATH", "")

        # File Watcher Configuration
        self.watch_path: str = os.getenv("WATCH_PATH", "")
        self.watch_recursive: bool = os.getenv("WATCH_RECURSIVE", "false").lower() == "true"
        self.watch_patterns: List[str] = self._parse_list(os.getenv("WATCH_PATTERNS", "*.md,*.txt"))

        # Processing Configuration
        self.max_processing_time: int = int(os.getenv("MAX_PROCESSING_TIME", "30"))
        self.retry_attempts: int = int(os.getenv("RETRY_ATTEMPTS", "3"))
        self.retention_days: int = int(os.getenv("RETENTION_DAYS", "90"))))

        # Logging Configuration
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
        self.log_dir: str = os.getenv("LOG_DIR", "logs")

    def _parse_list(self, value: str) -> List[str]:
        """Parse comma-separated string into list."""
        if not value:
            return []
        return [item.strip() for item in value.split(",") if item.strip()]

    def validate(self) -> tuple[bool, List[str]]:
        """Validate required configuration settings.

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []

        if not self.gemini_api_key:
            errors.append("GEMINI_API_KEY is required")

        if not self.vault_path:
            errors.append("VAULT_PATH is required")
        elif not Path(self.vault_path).exists():
            errors.append(f"VAULT_PATH does not exist: {self.vault_path}")

        if self.watch_path and not Path(self.watch_path).exists():
            errors.append(f"WATCH_PATH does not exist: {self.watch_path}")

        return len(errors) == 0, errors

    def get_vault_folders(self) -> dict[str, Path]:
        """Get paths to vault folders.

        Returns:
            Dictionary with folder names and their paths.
        """
        vault = Path(self.vault_path)
        return {
            "needs_action": vault / "Needs_Action",
            "plans": vault / "Plans",
            "done": vault / "Done"
        }

    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return {
            "gemini_api_key": "***" if self.gemini_api_key else "",
            "vault_path": self.vault_path,
            "watch_path": self.watch_path,
            "watch_recursive": self.watch_recursive,
            "watch_patterns": self.watch_patterns,
            "max_processing_time": self.max_processing_time,
            "retry_attempts": self.retry_attempts,
            "retention_days": self.retention_days,
            "log_level": self.log_level,
            "log_dir": self.log_dir
        }
