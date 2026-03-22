import asyncio
import functools
import logging
from typing import Callable, Type

logger = logging.getLogger("gold_tier")

BACKOFF_SCHEDULE = [60, 300, 900]  # 1min, 5min, 15min


async def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    backoff_schedule: list[int] | None = None,
    retryable_exceptions: tuple[Type[Exception], ...] = (Exception,),
    **kwargs,
):
    schedule = backoff_schedule or BACKOFF_SCHEDULE
    last_exception = None
    for attempt in range(max_retries + 1):
        try:
            return await func(**kwargs)
        except retryable_exceptions as e:
            last_exception = e
            if attempt < max_retries:
                wait = schedule[min(attempt, len(schedule) - 1)]
                logger.warning(f"Retry {attempt + 1}/{max_retries} after {wait}s: {e}")
                await asyncio.sleep(wait)
    raise last_exception


def sync_retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    backoff_schedule: list[int] | None = None,
    retryable_exceptions: tuple[Type[Exception], ...] = (Exception,),
    **kwargs,
):
    import time
    schedule = backoff_schedule or BACKOFF_SCHEDULE
    last_exception = None
    for attempt in range(max_retries + 1):
        try:
            return func(**kwargs)
        except retryable_exceptions as e:
            last_exception = e
            if attempt < max_retries:
                wait = schedule[min(attempt, len(schedule) - 1)]
                logger.warning(f"Retry {attempt + 1}/{max_retries} after {wait}s: {e}")
                time.sleep(wait)
    raise last_exception
