#!/usr/bin/env python3
"""
Production Error Logger for AI Employee.

Features:
- Structured JSON logging to vault /Logs
- File rotation (10MB per file, 5 backups)
- Error categorization and routing to /Errors subfolders
- Vault-integrated markdown error reports
- Notification hooks (file-based + optional webhook)
- Correlation IDs for tracing across services
"""

import json
import logging
import logging.handlers
import os
import sys
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

VAULT_PATH = Path(os.getenv(
    "VAULT_PATH",
    os.path.join(os.path.dirname(__file__), "AI-Employee-Vault"),
))
LOGS_DIR = VAULT_PATH / "Logs"
ERRORS_DIR = VAULT_PATH / "Errors"

# Ensure dirs
for d in [LOGS_DIR, ERRORS_DIR,
          ERRORS_DIR / "auth_errors",
          ERRORS_DIR / "network_errors",
          ERRORS_DIR / "validation_errors",
          ERRORS_DIR / "runtime_errors"]:
    d.mkdir(parents=True, exist_ok=True)


# ── JSON Formatter ────────────────────────────────────────────────────────────

class StructuredFormatter(logging.Formatter):
    """JSON-lines formatter with correlation support."""

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": getattr(record, "service", "system"),
            "component": getattr(record, "component", record.module),
            "msg": record.getMessage(),
            "correlation_id": getattr(record, "correlation_id", None),
        }
        # Optional fields
        for key in ("event", "operation", "duration_ms", "user_id",
                     "error_type", "error_severity", "retry_attempt"):
            val = getattr(record, key, None)
            if val is not None:
                entry[key] = val

        if record.exc_info and record.exc_info[1]:
            entry["exception"] = {
                "type": type(record.exc_info[1]).__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info),
            }
        return json.dumps(entry, default=str)


# ── Vault File Handler ────────────────────────────────────────────────────────

class VaultRotatingHandler(logging.handlers.RotatingFileHandler):
    """Rotating handler that writes to vault /Logs with date-based naming."""

    def __init__(self, service: str, max_bytes: int = 10 * 1024 * 1024, backup_count: int = 5):
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        filepath = LOGS_DIR / f"{service}-{today}.jsonl"
        super().__init__(str(filepath), maxBytes=max_bytes, backupCount=backup_count)
        self.setFormatter(StructuredFormatter())


# ── Error Router ──────────────────────────────────────────────────────────────

def _categorize_error(exc: Exception) -> str:
    """Route error to appropriate /Errors subfolder."""
    msg = str(exc).lower()
    etype = type(exc).__name__.lower()

    if any(k in msg for k in ("401", "403", "auth", "token", "credential")):
        return "auth_errors"
    if any(k in msg or k in etype for k in ("timeout", "connection", "network", "dns")):
        return "network_errors"
    if any(k in msg for k in ("validation", "invalid", "missing", "schema")):
        return "validation_errors"
    return "runtime_errors"


def log_error_to_vault(
    service: str,
    operation: str,
    exc: Exception,
    severity: str = "error",
    context: dict | None = None,
    correlation_id: str | None = None,
) -> Path:
    """Write structured error report to /Errors/{category}/."""
    category = _categorize_error(exc)
    target_dir = ERRORS_DIR / category
    target_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc)
    cid = correlation_id or str(uuid.uuid4())[:8]

    report = {
        "timestamp": ts.isoformat(),
        "correlation_id": cid,
        "service": service,
        "operation": operation,
        "severity": severity,
        "category": category,
        "error": {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        },
        "context": context or {},
    }

    filename = f"{ts.strftime('%Y-%m-%d_%H%M%S')}_{service}_{cid}.json"
    filepath = target_dir / filename
    filepath.write_text(json.dumps(report, indent=2, default=str))
    return filepath


# ── Notification System ───────────────────────────────────────────────────────

class NotificationManager:
    """File-based notification system with optional webhook support."""

    def __init__(self):
        self.notifications_dir = VAULT_PATH / "Needs_Action"
        self.notifications_dir.mkdir(parents=True, exist_ok=True)

    def notify_critical(self, service: str, error_msg: str, filepath: Path | None = None):
        """Create a Needs_Action file for critical errors requiring human attention."""
        ts = datetime.now(timezone.utc)
        content = f"""---
type: error_alert
priority: critical
service: {service}
created: {ts.isoformat()}
status: needs_action
---

# Critical Error Alert

**Service**: {service}
**Time**: {ts.strftime('%Y-%m-%d %H:%M:%S UTC')}
**Error**: {error_msg}

## Action Required

This error requires immediate human attention. The service may be degraded.

"""
        if filepath:
            content += f"**Error details**: [[{filepath.name}]]\n"

        slug = f"ERROR_{service}_{ts.strftime('%Y%m%d_%H%M%S')}.md"
        out = self.notifications_dir / slug
        out.write_text(content)
        return out

    def notify_degraded(self, service: str, details: str):
        """Log service degradation to Logs (less urgent than critical)."""
        ts = datetime.now(timezone.utc)
        logfile = LOGS_DIR / f"degradation-{ts.strftime('%Y-%m-%d')}.jsonl"
        entry = {
            "ts": ts.isoformat(),
            "event": "service_degraded",
            "service": service,
            "details": details,
        }
        with open(logfile, "a") as f:
            f.write(json.dumps(entry, default=str) + "\n")


_notifier = NotificationManager()


# ── Logger Factory ────────────────────────────────────────────────────────────

_loggers: dict[str, logging.Logger] = {}


def get_logger(
    service: str,
    level: str = "INFO",
    console: bool = True,
    vault: bool = True,
) -> logging.Logger:
    """Get or create a structured logger for a service."""
    if service in _loggers:
        return _loggers[service]

    lg = logging.getLogger(f"ai_employee.{service}")
    lg.setLevel(getattr(logging, level.upper(), logging.INFO))
    lg.propagate = False

    if console and not any(isinstance(h, logging.StreamHandler) for h in lg.handlers):
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(StructuredFormatter())
        lg.addHandler(ch)

    if vault:
        lg.addHandler(VaultRotatingHandler(service))

    _loggers[service] = lg
    return lg


# ── Convenience ───────────────────────────────────────────────────────────────

def new_correlation_id() -> str:
    return str(uuid.uuid4())[:12]


def log_and_alert(
    service: str,
    operation: str,
    exc: Exception,
    severity: str = "critical",
    context: dict | None = None,
):
    """Log error to vault AND create notification if critical."""
    cid = new_correlation_id()
    filepath = log_error_to_vault(service, operation, exc, severity, context, cid)

    lg = get_logger(service)
    lg.error(
        f"[{operation}] {exc}",
        extra={"correlation_id": cid, "error_type": type(exc).__name__,
               "error_severity": severity, "service": service},
        exc_info=True,
    )

    if severity == "critical":
        _notifier.notify_critical(service, str(exc), filepath)
    elif severity == "degraded":
        _notifier.notify_degraded(service, str(exc))

    return cid
