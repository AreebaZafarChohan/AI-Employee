"""Configuration for the file system watcher."""

from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path


@dataclass
class WatcherConfig:
    """Configuration for file system watcher."""

    watch_path: str
    vault_path: str
    recursive: bool = False
    file_patterns: List[str] = field(default_factory=lambda: ["*.md", "*.txt"])
    polling_interval: float = 1.0  # seconds
    debounce_time: float = 0.5  # seconds to wait before processing

    def __post_init__(self):
        """Validate and normalize configuration."""
        self.watch_path = str(Path(self.watch_path).absolute())
        self.vault_path = str(Path(self.vault_path).absolute())

    @classmethod
    def from_config(cls, config: "Config") -> "WatcherConfig":
        """Create WatcherConfig from main Config object.

        Args:
            config: Main configuration object.

        Returns:
            WatcherConfig instance.
        """
        return cls(
            watch_path=config.watch_path,
            vault_path=config.vault_path,
            recursive=config.watch_recursive,
            file_patterns=config.watch_patterns
        )

    def validate(self) -> tuple[bool, List[str]]:
        """Validate the watcher configuration.

        Returns:
            Tuple of (is_valid, list of error messages).
        """
        errors = []

        watch = Path(self.watch_path)
        if not watch.exists():
            errors.append(f"Watch path does not exist: {self.watch_path}")
        elif not watch.is_dir():
            errors.append(f"Watch path is not a directory: {self.watch_path}")

        vault = Path(self.vault_path)
        if not vault.exists():
            errors.append(f"Vault path does not exist: {self.vault_path}")

        if not self.file_patterns:
            errors.append("At least one file pattern is required")

        return len(errors) == 0, errors

    def get_needs_action_path(self) -> Path:
        """Get the path to the Needs_Action folder.

        Returns:
            Path to Needs_Action folder.
        """
        return Path(self.vault_path) / "Needs_Action"
