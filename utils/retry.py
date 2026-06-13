"""Retry helpers with exponential backoff for external API calls."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def retry_with_backoff(
    func: Callable[[], T],
    *,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    retry_exceptions: tuple[type[Exception], ...] = (Exception,),
) -> T:
    """Run *func* with exponential backoff when retryable errors occur."""
    last_error: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            return func()
        except retry_exceptions as exc:
            last_error = exc
            if attempt >= max_attempts:
                break
            delay = base_delay * (2 ** (attempt - 1))
            logger.warning("Attempt %s/%s failed (%s). Retrying in %.1fs...", attempt, max_attempts, exc, delay)
            time.sleep(delay)

    assert last_error is not None
    raise last_error
