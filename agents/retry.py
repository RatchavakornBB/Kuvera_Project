"""Bounded retry for node work — AGENT.md Section 10: max 2 attempts on
failure (timeout, malformed structured output, provider error), then fail
loud via NodeFailure rather than retrying forever or returning a silent
default."""

import logging
from typing import Callable, TypeVar

from agents.errors import NodeFailure

logger = logging.getLogger("agents")
T = TypeVar("T")


def with_retry(node_name: str, fn: Callable[[], T], max_attempts: int = 2) -> T:
    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001 - deliberately broad, converted to NodeFailure below
            last_error = e
            logger.warning("%s attempt %d/%d failed: %s", node_name, attempt, max_attempts, e)

    raise NodeFailure(
        node=node_name,
        attempts=max_attempts,
        reason="exhausted retries",
        raw_error=str(last_error),
    )
