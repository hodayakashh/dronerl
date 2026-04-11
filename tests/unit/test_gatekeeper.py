"""Unit tests for ApiGatekeeper (FIFO queue, rate limiting, backpressure, retries)."""

from __future__ import annotations

import pytest

from dronerl.shared.gatekeeper import ApiGatekeeper, BackpressureError


@pytest.fixture()
def gk(tmp_path):
    """ApiGatekeeper backed by a temp rate_limits.json (high RPM for fast tests)."""
    cfg = tmp_path / "rate_limits.json"
    cfg.write_text(
        '{"version":"1.00","services":{"default":{'
        '"requests_per_minute":600,"concurrent_max":4,'
        '"retry_after_seconds":0.01,"max_retries":2,"max_queue_depth":5}}}'
    )
    return ApiGatekeeper(config_path=cfg)


def test_execute_returns_value(gk):
    assert gk.execute(lambda: 42) == 42


def test_execute_passes_args(gk):
    assert gk.execute(lambda a, b: a + b, 3, 7) == 10


def test_execute_passes_kwargs(gk):
    assert gk.execute(lambda x=0: x * 2, x=5) == 10


def test_queue_status_after_call(gk):
    gk.execute(lambda: None)
    s = gk.get_queue_status()
    assert s["total_calls"] == 1
    assert s["failed_calls"] == 0
    assert s["rpm_limit"] == 600
    assert "queue_depth" in s
    assert "available_slots" in s


def test_retries_on_transient_error(gk):
    calls = []

    def flaky():
        calls.append(1)
        if len(calls) < 2:
            msg = "transient"
            raise RuntimeError(msg)
        return "ok"

    assert gk.execute(flaky) == "ok"
    assert len(calls) == 2


def test_raises_after_max_retries(gk):
    with pytest.raises(RuntimeError, match="always"):
        gk.execute(lambda: (_ for _ in ()).throw(RuntimeError("always")))


def test_failed_calls_counted(gk):
    with pytest.raises(Exception):  # noqa: B017
        gk.execute(lambda: (_ for _ in ()).throw(ValueError("boom")))
    assert gk.get_queue_status()["failed_calls"] >= 1


def test_backpressure_when_queue_full(tmp_path):
    """Queue depth of 1 with a slow call should trigger BackpressureError."""
    import threading
    cfg = tmp_path / "rl.json"
    cfg.write_text(
        '{"version":"1.00","services":{"default":{'
        '"requests_per_minute":600,"concurrent_max":1,'
        '"retry_after_seconds":0,"max_retries":1,"max_queue_depth":1}}}'
    )
    gk = ApiGatekeeper(config_path=cfg)
    barrier = threading.Event()

    def slow():
        barrier.wait(timeout=5)
        return "done"

    # First call occupies the queue slot (drain thread picks it up immediately
    # but blocks on barrier). Second call should fill the queue. Third → error.
    t = threading.Thread(target=gk.execute, args=(slow,), daemon=True)
    t.start()
    import time; time.sleep(0.05)  # let drain thread pick first call

    # Queue a second call (fills depth=1 slot)
    t2 = threading.Thread(target=gk.execute, args=(lambda: None,), daemon=True)
    t2.start()
    time.sleep(0.02)

    with pytest.raises(BackpressureError):
        gk.execute(lambda: None)

    barrier.set()
    t.join(timeout=2)
    t2.join(timeout=2)


def test_config_uses_services_key(tmp_path):
    cfg = tmp_path / "rl.json"
    cfg.write_text(
        '{"version":"1.00","services":{"custom":{'
        '"requests_per_minute":30,"concurrent_max":2,'
        '"retry_after_seconds":0,"max_retries":1,"max_queue_depth":5}}}'
    )
    gk = ApiGatekeeper(config_path=cfg, profile="custom")
    assert gk.get_queue_status()["rpm_limit"] == 30
