"""API Gatekeeper — centralised rate-limiting façade for all external API calls."""

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


class BackpressureError(Exception):
    """Raised when the request queue is at maximum capacity."""


class _PendingCall:
    """Wraps a queued API call so the drain thread can signal completion."""

    __slots__ = ("fn", "args", "kwargs", "result", "error", "done")

    def __init__(self, fn: Callable, args: tuple, kwargs: dict) -> None:
        """Store the callable, its arguments, and a completion Event."""
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.result: Any = None
        self.error: BaseException | None = None
        self.done = threading.Event()


class ApiGatekeeper:
    """Centralised API call manager with FIFO queuing and rate limiting.

    All external calls must be routed through :meth:`execute`. Requests that
    arrive while the rate-limit window is saturated are placed in a FIFO queue
    and drained automatically when capacity becomes available.

    Args:
        config_path: Path to ``rate_limits.json``.
        profile: Key inside ``services`` to use (default ``"default"``).
    """

    def __init__(self, config_path: str | Path | None = None, profile: str = "default") -> None:
        """Load rate-limit config and start the background drain thread."""
        path = Path(config_path) if config_path else _DEFAULT_CONFIG
        raw = ConfigLoader().load_json(path, required_keys=["services"])
        services = raw["services"]
        cfg = services.get(profile) or services.get("default") or next(iter(services.values()))

        self._rpm: int = int(cfg.get("requests_per_minute", 60))
        self._concurrent_max: int = int(cfg.get("concurrent_max", 4))
        self._max_retries: int = int(cfg.get("max_retries", 3))
        self._retry_after: float = float(cfg.get("retry_after_seconds", 1))
        self._max_queue_depth: int = int(cfg.get("max_queue_depth", 10))

        self._lock = threading.Lock()
        self._semaphore = threading.Semaphore(self._concurrent_max)
        self._timestamps: deque[float] = deque()
        self._queue: deque[_PendingCall] = deque()
        self._total_calls: int = 0
        self._failed_calls: int = 0

        self._drain_thread = threading.Thread(target=self._drain_loop, daemon=True)
        self._drain_thread.start()
        logger.info("ApiGatekeeper ready: rpm=%d queue_depth=%d", self._rpm, self._max_queue_depth)

    def execute(self, api_call: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Enqueue *api_call*, block until processed. Raises BackpressureError if queue full."""
        with self._lock:
            if len(self._queue) >= self._max_queue_depth:
                logger.warning("Backpressure: queue full (%d)", self._max_queue_depth)
                raise BackpressureError(f"Queue full ({self._max_queue_depth} requests pending)")
            call = _PendingCall(api_call, args, kwargs)
            self._queue.append(call)

        call.done.wait()
        if call.error is not None:
            raise call.error
        return call.result

    def get_queue_status(self) -> dict[str, int]:
        """Return current gatekeeper statistics."""
        with self._lock:
            return {
                "total_calls": self._total_calls,
                "failed_calls": self._failed_calls,
                "queue_depth": len(self._queue),
                "available_slots": self._semaphore._value,  # noqa: SLF001
                "rpm_limit": self._rpm,
            }

    def _drain_loop(self) -> None:
        """Continuously drain the FIFO queue, honouring rate limits (daemon thread)."""
        while True:
            call = self._next_call()
            self._wait_for_rate_slot()
            self._run_with_retry(call)

    def _next_call(self) -> _PendingCall:
        """Block until there is a call in the queue, then pop it (FIFO)."""
        while True:
            with self._lock:
                if self._queue:
                    return self._queue.popleft()
            time.sleep(0.005)

    def _wait_for_rate_slot(self) -> None:
        """Block until the sliding-window rate limit allows the next call."""
        while True:
            with self._lock:
                now = time.monotonic()
                while self._timestamps and self._timestamps[0] < now - 60.0:
                    self._timestamps.popleft()
                if len(self._timestamps) < self._rpm:
                    self._timestamps.append(now)
                    return
                wait = 60.0 - (now - self._timestamps[0]) + 0.001
            time.sleep(wait)

    def _run_with_retry(self, call: _PendingCall) -> None:
        """Execute *call* with up to ``max_retries`` attempts."""
        for attempt in range(1, self._max_retries + 1):
            with self._semaphore:
                try:
                    call.result = call.fn(*call.args, **call.kwargs)
                    call.error = None
                    with self._lock:
                        self._total_calls += 1
                    break
                except Exception as exc:  # noqa: BLE001
                    call.error = exc
                    with self._lock:
                        self._failed_calls += 1
                    logger.warning("Attempt %d/%d failed: %s", attempt, self._max_retries, exc)
                    if attempt < self._max_retries:
                        time.sleep(self._retry_after * (2 ** (attempt - 1)))
        call.done.set()
