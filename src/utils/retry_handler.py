#!/usr/bin/env python3
"""
Fault-Tolerant Retry Handler for AI Employee.

Production-grade retry system with:
- Exponential backoff + jitter
- Error classification (transient vs permanent)
- Circuit breaker pattern
- Per-service retry budgets
- Quarantine integration for persistent failures
"""

import asyncio
import functools
import json
import logging
import os
import random
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional, Type

logger = logging.getLogger("ai_employee.retry")

VAULT_PATH = os.getenv(
    "VAULT_PATH",
    os.path.join(os.path.dirname(__file__), "AI-Employee-Vault"),
)


# ── Error Classification ─────────────────────────────────────────────────────

class ErrorSeverity(str, Enum):
    TRANSIENT = "transient"      # Network timeout, 503, rate limit → retry
    AUTH = "auth"                 # 401/403, expired token → retry after re-auth
    PERMANENT = "permanent"      # 400, bad input, missing resource → no retry
    UNKNOWN = "unknown"          # Unclassified → retry with caution


def classify_error(exc: Exception) -> ErrorSeverity:
    """Classify an exception to decide retry strategy."""
    msg = str(exc).lower()
    exc_type = type(exc).__name__

    # Network / transient
    if any(k in exc_type.lower() for k in ("timeout", "connection", "network")):
        return ErrorSeverity.TRANSIENT
    if any(k in msg for k in ("timeout", "timed out", "connection refused",
                                "503", "502", "429", "rate limit", "retry")):
        return ErrorSeverity.TRANSIENT

    # Auth
    if any(k in msg for k in ("401", "403", "unauthorized", "forbidden",
                                "token expired", "authentication", "unauthenticated")):
        return ErrorSeverity.AUTH

    # Permanent
    if any(k in msg for k in ("400", "404", "not found", "invalid",
                                "validation", "missing required")):
        return ErrorSeverity.PERMANENT

    return ErrorSeverity.UNKNOWN


# ── Circuit Breaker ───────────────────────────────────────────────────────────

class CircuitState(str, Enum):
    CLOSED = "closed"        # Normal operation
    OPEN = "open"            # Failing, block calls
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreaker:
    """Per-service circuit breaker."""
    service: str
    failure_threshold: int = 5
    recovery_timeout: float = 60.0  # seconds before trying half-open

    _failures: int = 0
    _state: CircuitState = CircuitState.CLOSED
    _last_failure_time: float = 0.0

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if time.time() - self._last_failure_time >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
        return self._state

    def record_success(self):
        self._failures = 0
        self._state = CircuitState.CLOSED

    def record_failure(self):
        self._failures += 1
        self._last_failure_time = time.time()
        if self._failures >= self.failure_threshold:
            self._state = CircuitState.OPEN
            logger.error(f"Circuit OPEN for {self.service} after {self._failures} failures")

    def allow_request(self) -> bool:
        s = self.state
        if s == CircuitState.CLOSED:
            return True
        if s == CircuitState.HALF_OPEN:
            return True  # Allow one probe
        return False


# ── Quarantine ────────────────────────────────────────────────────────────────

def quarantine_error(service: str, operation: str, exc: Exception, context: dict | None = None):
    """Write a persistent failure to the vault Quarantine folder."""
    qdir = Path(VAULT_PATH) / "Quarantine"
    qdir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc)
    entry = {
        "timestamp": ts.isoformat(),
        "service": service,
        "operation": operation,
        "error_type": type(exc).__name__,
        "error_message": str(exc),
        "severity": classify_error(exc).value,
        "traceback": traceback.format_exc(),
        "context": context or {},
    }

    filename = f"{ts.strftime('%Y-%m-%d')}_{service}.json"
    filepath = qdir / filename

    # Append to daily file
    existing = []
    if filepath.exists():
        try:
            existing = json.loads(filepath.read_text())
            if not isinstance(existing, list):
                existing = [existing]
        except (json.JSONDecodeError, ValueError):
            existing = []

    existing.append(entry)
    filepath.write_text(json.dumps(existing, indent=2, default=str))
    logger.warning(f"Quarantined: {service}/{operation} → {filepath}")
    return filepath


# ── Retry Budgets ─────────────────────────────────────────────────────────────

@dataclass
class RetryBudget:
    """Track retry budget per service to prevent retry storms."""
    max_retries_per_minute: int = 20
    _timestamps: list = field(default_factory=list)

    def acquire(self) -> bool:
        now = time.time()
        self._timestamps = [t for t in self._timestamps if now - t < 60]
        if len(self._timestamps) >= self.max_retries_per_minute:
            return False
        self._timestamps.append(now)
        return True


# ── Core Retry Engine ─────────────────────────────────────────────────────────

# Global registries
_circuit_breakers: dict[str, CircuitBreaker] = {}
_retry_budgets: dict[str, RetryBudget] = {}


def get_circuit_breaker(service: str) -> CircuitBreaker:
    if service not in _circuit_breakers:
        _circuit_breakers[service] = CircuitBreaker(service=service)
    return _circuit_breakers[service]


def get_retry_budget(service: str) -> RetryBudget:
    if service not in _retry_budgets:
        _retry_budgets[service] = RetryBudget()
    return _retry_budgets[service]


BACKOFF_SCHEDULE = [1, 5, 15, 30, 60]  # seconds


async def retry_with_recovery(
    func: Callable,
    *,
    service: str = "unknown",
    operation: str = "unknown",
    max_retries: int = 4,
    backoff_schedule: list[int] | None = None,
    retryable: tuple[Type[Exception], ...] = (Exception,),
    on_auth_failure: Callable | None = None,
    context: dict | None = None,
    **kwargs,
) -> Any:
    """
    Production retry with circuit breaker, backoff+jitter, error classification,
    retry budgets, and quarantine on exhaustion.
    """
    cb = get_circuit_breaker(service)
    budget = get_retry_budget(service)
    schedule = backoff_schedule or BACKOFF_SCHEDULE

    if not cb.allow_request():
        raise RuntimeError(f"Circuit open for {service} — service degraded")

    last_exc = None
    for attempt in range(max_retries + 1):
        try:
            result = await func(**kwargs)
            cb.record_success()
            return result
        except retryable as exc:
            last_exc = exc
            severity = classify_error(exc)

            # Permanent errors → don't retry
            if severity == ErrorSeverity.PERMANENT:
                logger.error(f"[{service}] Permanent error, no retry: {exc}")
                cb.record_failure()
                quarantine_error(service, operation, exc, context)
                raise

            # Auth errors → try re-auth once
            if severity == ErrorSeverity.AUTH and on_auth_failure and attempt == 0:
                logger.warning(f"[{service}] Auth failure, attempting re-auth")
                try:
                    await on_auth_failure()
                    continue  # Retry immediately after re-auth
                except Exception as auth_exc:
                    logger.error(f"[{service}] Re-auth failed: {auth_exc}")

            # Check budget
            if not budget.acquire():
                logger.error(f"[{service}] Retry budget exhausted")
                break

            cb.record_failure()

            if attempt < max_retries:
                base = schedule[min(attempt, len(schedule) - 1)]
                jitter = random.uniform(0, base * 0.3)
                wait = base + jitter
                logger.warning(
                    f"[{service}] Retry {attempt + 1}/{max_retries} "
                    f"in {wait:.1f}s ({severity.value}): {exc}"
                )
                await asyncio.sleep(wait)

    # Exhausted retries → quarantine
    quarantine_error(service, operation, last_exc, context)
    raise last_exc


def sync_retry_with_recovery(
    func: Callable,
    *,
    service: str = "unknown",
    operation: str = "unknown",
    max_retries: int = 4,
    backoff_schedule: list[int] | None = None,
    retryable: tuple[Type[Exception], ...] = (Exception,),
    on_auth_failure: Callable | None = None,
    context: dict | None = None,
    **kwargs,
) -> Any:
    """Synchronous version of retry_with_recovery."""
    cb = get_circuit_breaker(service)
    budget = get_retry_budget(service)
    schedule = backoff_schedule or BACKOFF_SCHEDULE

    if not cb.allow_request():
        raise RuntimeError(f"Circuit open for {service} — service degraded")

    last_exc = None
    for attempt in range(max_retries + 1):
        try:
            result = func(**kwargs)
            cb.record_success()
            return result
        except retryable as exc:
            last_exc = exc
            severity = classify_error(exc)

            if severity == ErrorSeverity.PERMANENT:
                logger.error(f"[{service}] Permanent error, no retry: {exc}")
                cb.record_failure()
                quarantine_error(service, operation, exc, context)
                raise

            if severity == ErrorSeverity.AUTH and on_auth_failure and attempt == 0:
                logger.warning(f"[{service}] Auth failure, attempting re-auth")
                try:
                    on_auth_failure()
                    continue
                except Exception:
                    pass

            if not budget.acquire():
                logger.error(f"[{service}] Retry budget exhausted")
                break

            cb.record_failure()

            if attempt < max_retries:
                base = schedule[min(attempt, len(schedule) - 1)]
                jitter = random.uniform(0, base * 0.3)
                wait = base + jitter
                logger.warning(
                    f"[{service}] Retry {attempt + 1}/{max_retries} "
                    f"in {wait:.1f}s ({severity.value}): {exc}"
                )
                time.sleep(wait)

    quarantine_error(service, operation, last_exc, context)
    raise last_exc


# ── Decorator ─────────────────────────────────────────────────────────────────

def retryable(
    service: str = "unknown",
    operation: str = "unknown",
    max_retries: int = 4,
    exceptions: tuple[Type[Exception], ...] = (Exception,),
):
    """Decorator for automatic retry on async functions."""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await retry_with_recovery(
                lambda **kw: func(*args, **kwargs),
                service=service,
                operation=operation,
                max_retries=max_retries,
                retryable=exceptions,
            )
        return wrapper
    return decorator


# ── Status ────────────────────────────────────────────────────────────────────

def get_health_status() -> dict:
    """Return circuit breaker and budget status for all services."""
    status = {}
    for svc, cb in _circuit_breakers.items():
        budget = _retry_budgets.get(svc)
        status[svc] = {
            "circuit_state": cb.state.value,
            "failures": cb._failures,
            "retries_last_minute": len(budget._timestamps) if budget else 0,
        }
    return status
