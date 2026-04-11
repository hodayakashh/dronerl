"""API Gatekeeper — centralised rate-limiting façade for all external API calls.

All outbound API calls must go through ApiGatekeeper.execute() so that
rate limits, retry logic, and call logging are enforced in a single place.
"""

from __future__ import annotations

import logging
import threading
import time
from collections import deque
from collections.abc import Callable
from pathlib import Path
from typing import Any

from dronerl.shared.config import ConfigLoader

logger = logging.getLogger(__name__)

_DEFAULT_CONFIG = Path(__file__).parent.parent.parent.parent / "config" / "rate_limits.json"


class RateLimitExceededError(Exception):
    """Raised when the caller would exceed the configured rate limit."""


class ApiGatekeeper:
    """Centralised API call manager with rate limiting and retry logic.

    All external calls must be routed through :meth:`execute` so that
    requests-per-minute caps, concurrency limits, and retries are applied
    consistently across the application.

    Args:
        config_path: Path to ``rate_limits.json``.  Defaults to
            ``config/rate_limits.json`` relative to the project root.
        profile: Key inside ``rate_limits`` to use (default ``"default"``).
    """

    def __init__(
        self,
        config_path: str | Path | None = None,
        profile: str = "default",
    ) -> None:
        path = Path(config_path) if config_path else _DEFAULT_CONFIG
        raw = ConfigLoader().load_json(path, required_keys=["rate_limits"])
        cfg = raw["rate_limits"].get(profile, raw["rate_limits"]["default"])

        self._rpm: int = int(cfg.get("requests_per_minute", 60))
        self._concurrent_max: int = int(cfg.get("concurrent_max", 4))
        self._max_retries: int = int(cfg.get("max_retries", 3))

        self._lock = threading.Lock()
        self._semaphore = threading.Semaphore(self._concurrent_max)
        self._timestamps: deque[float] = deque()
        self._total_calls: int = 0
        self._failed_calls: int = 0

        logger.info(
            "ApiGatekeeper ready: profile=%s rpm=%d concurrent=%d retries=%d",
            profile, self._rpm, self._concurrent_max, self._max_retries,
        )

    def execute(self, api_call: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Execute *api_call* subject to rate and concurrency limits.

        Blocks until a slot is available, then calls ``api_call(*args, **kwargs)``
        with automatic retries on transient errors.

        Args:
            api_call: Callable representing the external API call.
            *args: Positional arguments forwarded to *api_call*.
            **kwargs: Keyword arguments forwarded to *api_call*.

        Returns:
            The return value of *api_call*.

        Raises:
            RateLimitExceededError: If the per-minute cap is already saturated.
            Exception: Re-raised from *api_call* after all retries are exhausted.
        """
        self._enforce_rate_limit()
        last_exc: Exception | None = None
        for attempt in range(1, self._max_retries + 1):
            with self._semaphore:
                try:
                    result = api_call(*args, **kwargs)
                    with self._lock:
                        self._total_calls += 1
                    logger.debug("API call succeeded on attempt %d", attempt)
                    return result
                except Exception as exc:  # noqa: BLE001
                    last_exc = exc
                    with self._lock:
                        self._failed_calls += 1
                    logger.warning("API call failed (attempt %d/%d): %s", attempt, self._max_retries, exc)
                    if attempt < self._max_retries:
                        time.sleep(2 ** (attempt - 1))
        raise last_exc  # type: ignore[misc]

    def get_queue_status(self) -> dict[str, int]:
        """Return current gatekeeper statistics.

        Returns:
            Dict with ``total_calls``, ``failed_calls``, ``available_slots``,
            and ``rpm_limit``.
        """
        with self._lock:
            return {
                "total_calls": self._total_calls,
                "failed_calls": self._failed_calls,
                "available_slots": self._semaphore._value,  # noqa: SLF001
                "rpm_limit": self._rpm,
            }

    def _enforce_rate_limit(self) -> None:
        """Block or raise if the per-minute call cap is reached."""
        with self._lock:
            now = time.monotonic()
            cutoff = now - 60.0
            while self._timestamps and self._timestamps[0] < cutoff:
                self._timestamps.popleft()
            if len(self._timestamps) >= self._rpm:
                raise RateLimitExceededError(
                    f"Rate limit of {self._rpm} requests/minute exceeded"
                )
            self._timestamps.append(now)
