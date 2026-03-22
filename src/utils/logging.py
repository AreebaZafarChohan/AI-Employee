"""
Structured JSON logging for Gold Tier API.
Production-ready logging with correlation IDs and context.
"""
import logging
from src.utils.structured_logging import setup_logging, JSONFormatter


def get_logger(name: str = "gold_tier") -> logging.Logger:
    """Get a configured logger instance."""
    return logging.getLogger(name)


def configure_logging(level: str = "INFO", json_output: bool = True) -> None:
    """
    Configure root logger for the application.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_output: If True, use JSON format; if False, use human-readable format
    """
    setup_logging(level=level, json_output=json_output)


__all__ = ["get_logger", "configure_logging", "JSONFormatter"]
