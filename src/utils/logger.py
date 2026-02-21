"""Structured logging for AI Employee."""

import json
import logging
import os
import fcntl
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional


_loggers: dict[str, logging.Logger] = {}


def setup_logger(
    name: str = "ai_employee",
    log_dir: str = "logs",
    log_level: str = "INFO",
    console_output: bool = True
) -> logging.Logger:
    """Set up a structured logger.

    Args:
        name: Logger name.
        log_dir: Directory for log files.
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        console_output: Whether to output to console.

    Returns:
        Configured logger instance.
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    logger.handlers = []

    # Create log directory
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Log format
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # File handler - application log
    app_log_file = log_path / "application.log"
    file_handler = logging.FileHandler(app_log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # File handler - errors only
    error_log_file = log_path / "errors.log"
    error_handler = logging.FileHandler(error_log_file, encoding="utf-8")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)

    # Console handler
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    _loggers[name] = logger
    return logger


def get_logger(name: str = "ai_employee") -> logging.Logger:
    """Get an existing logger or create a new one.

    Args:
        name: Logger name.

    Returns:
        Logger instance.
    """
    if name not in _loggers:
        return setup_logger(name)
    return _loggers[name]


class ProcessingLogger:
    """Logger for tracking processing operations with timing."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize processing logger.

        Args:
            logger: Optional logger instance. Creates default if not provided.
        """
        self.logger = logger or get_logger("processing")
        self._start_times: dict[str, datetime] = {}

    def start_operation(self, operation_id: str, message: str) -> None:
        """Start timing an operation.

        Args:
            operation_id: Unique identifier for the operation.
            message: Description of the operation.
        """
        self._start_times[operation_id] = datetime.now()
        self.logger.info(f"[START] {operation_id}: {message}")

    def end_operation(self, operation_id: str, message: str, success: bool = True) -> float:
        """End timing an operation.

        Args:
            operation_id: Unique identifier for the operation.
            message: Description of the result.
            success: Whether the operation succeeded.

        Returns:
            Duration in seconds.
        """
        start_time = self._start_times.pop(operation_id, None)
        if start_time:
            duration = (datetime.now() - start_time).total_seconds()
        else:
            duration = 0.0

        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"[{status}] {operation_id}: {message} (Duration: {duration:.2f}s)")

        return duration

    def log_error(self, operation_id: str, error: Exception) -> None:
        """Log an error for an operation.

        Args:
            operation_id: Unique identifier for the operation.
            error: The exception that occurred.
        """
        self.logger.error(f"[ERROR] {operation_id}: {type(error).__name__}: {str(error)}")


# ---------------------------------------------------------------------------
# Vault JSON logger  —  log_action()
# ---------------------------------------------------------------------------

# Module-level default so callers can set once at startup
_default_logs_dir: Optional[Path] = None


def set_default_logs_dir(logs_dir: str | Path) -> None:
    """Set the default vault Logs/ directory used by log_action().

    Call once at startup so every subsequent log_action() call
    writes to the correct vault without needing an explicit path.
    """
    global _default_logs_dir
    _default_logs_dir = Path(logs_dir).resolve()


def log_action(
    action_type: str,
    target: str,
    result: str,
    *,
    logs_dir: Optional[str | Path] = None,
) -> Path:
    """Append a structured JSON entry to the vault's daily log file.

    Args:
        action_type: What happened (e.g. "file_copy", "plan_created").
        target: The object acted upon (e.g. a filename or path).
        result: Outcome (e.g. "success", "error: …").
        logs_dir: Explicit Logs/ directory. Falls back to the default
                  set via set_default_logs_dir(), then to "Logs/" in cwd.

    Returns:
        Path to the log file that was written.
    """
    dir_path = (
        Path(logs_dir).resolve()
        if logs_dir
        else (_default_logs_dir or Path("Logs").resolve())
    )
    dir_path.mkdir(parents=True, exist_ok=True)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log_file = dir_path / f"{today}.json"

    entry = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "action_type": action_type,
        "target": target,
        "result": result,
    }

    # Append safely with file locking to prevent corruption from
    # concurrent writers (e.g. watcher + skill running in parallel).
    _append_json_entry(log_file, entry)

    return log_file


def _append_json_entry(log_file: Path, entry: dict) -> None:
    """Read-modify-write a JSON array file under an exclusive lock."""
    with open(log_file, "a+", encoding="utf-8") as fh:
        try:
            fcntl.flock(fh, fcntl.LOCK_EX)

            # Read existing entries
            fh.seek(0)
            raw = fh.read().strip()
            if raw:
                try:
                    entries = json.loads(raw)
                except json.JSONDecodeError:
                    entries = []
            else:
                entries = []

            entries.append(entry)

            # Rewrite the whole file
            fh.seek(0)
            fh.truncate()
            fh.write(json.dumps(entries, indent=2, ensure_ascii=False))
            fh.write("\n")
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)
