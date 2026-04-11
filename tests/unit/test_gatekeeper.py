"""Unit tests for ApiGatekeeper."""

from __future__ import annotations

import pytest

from dronerl.shared.gatekeeper import ApiGatekeeper, RateLimitExceededError


@pytest.fixture()
def gatekeeper(tmp_path):
    """ApiGatekeeper backed by a temp rate_limits.json."""
    cfg = tmp_path / "rate_limits.json"
    cfg.write_text(
        '{"version":"1.00","rate_limits":{"default":{"requests_per_minute":5,"concurrent_max":2,"max_retries":2}}}'
    )
    return ApiGatekeeper(config_path=cfg)


def test_execute_success(gatekeeper):
    result = gatekeeper.execute(lambda: 42)
    assert result == 42


def test_execute_passes_args(gatekeeper):
    result = gatekeeper.execute(lambda a, b: a + b, 3, 7)
    assert result == 10


def test_execute_passes_kwargs(gatekeeper):
    result = gatekeeper.execute(lambda x=0: x * 2, x=5)
    assert result == 10


def test_get_queue_status(gatekeeper):
    gatekeeper.execute(lambda: None)
    status = gatekeeper.get_queue_status()
    assert status["total_calls"] == 1
    assert status["failed_calls"] == 0
    assert status["rpm_limit"] == 5
    assert "available_slots" in status


def test_retries_on_transient_error(gatekeeper):
    calls = []

    def flaky():
        calls.append(1)
        if len(calls) < 2:
            msg = "transient"
            raise RuntimeError(msg)
        return "ok"

    result = gatekeeper.execute(flaky)
    assert result == "ok"
    assert len(calls) == 2


def test_raises_after_max_retries(gatekeeper):
    with pytest.raises(RuntimeError, match="always fails"):
        gatekeeper.execute(lambda: (_ for _ in ()).throw(RuntimeError("always fails")))


def test_rate_limit_exceeded(tmp_path):
    cfg = tmp_path / "rate_limits.json"
    cfg.write_text(
        '{"version":"1.00","rate_limits":{"default":{"requests_per_minute":2,"concurrent_max":4,"max_retries":1}}}'
    )
    gk = ApiGatekeeper(config_path=cfg)
    gk.execute(lambda: None)
    gk.execute(lambda: None)
    with pytest.raises(RateLimitExceededError):
        gk.execute(lambda: None)


def test_failed_calls_counted(gatekeeper):
    with pytest.raises(Exception):  # noqa: B017
        gatekeeper.execute(lambda: (_ for _ in ()).throw(ValueError("boom")))
    status = gatekeeper.get_queue_status()
    assert status["failed_calls"] >= 1
