"""Unit tests for dronerl.environment.wind."""

import numpy as np
import pytest

from dronerl.constants import N_ACTIONS, Action
from dronerl.environment.wind import WindZone


def make_rng(seed: int = 42) -> np.random.Generator:
    return np.random.default_rng(seed)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_wind_drift_prob_property() -> None:
    wz = WindZone(0.3, make_rng())
    assert wz.drift_prob == pytest.approx(0.3)


def test_wind_invalid_drift_prob_above_1_raises() -> None:
    with pytest.raises(ValueError):
        WindZone(1.5, make_rng())


def test_wind_invalid_drift_prob_negative_raises() -> None:
    with pytest.raises(ValueError):
        WindZone(-0.1, make_rng())


def test_wind_drift_prob_zero_allowed() -> None:
    wz = WindZone(0.0, make_rng())
    assert wz.drift_prob == 0.0


def test_wind_drift_prob_one_allowed() -> None:
    wz = WindZone(1.0, make_rng())
    assert wz.drift_prob == 1.0


# ---------------------------------------------------------------------------
# apply — deterministic edges
# ---------------------------------------------------------------------------


def test_wind_zero_prob_always_returns_intended() -> None:
    wz = WindZone(0.0, make_rng())
    for action in Action:
        assert wz.apply(int(action)) == int(action)


def test_wind_one_prob_never_returns_intended() -> None:
    wz = WindZone(1.0, make_rng(0))
    for _ in range(50):
        result = wz.apply(int(Action.UP))
        assert result != int(Action.UP)


def test_wind_one_prob_returns_valid_action() -> None:
    wz = WindZone(1.0, make_rng(7))
    for _ in range(100):
        result = wz.apply(int(Action.RIGHT))
        assert 0 <= result < N_ACTIONS


# ---------------------------------------------------------------------------
# apply — stochastic behaviour
# ---------------------------------------------------------------------------


def test_wind_partial_prob_sometimes_deflects() -> None:
    wz = WindZone(0.5, make_rng(99))
    results = {wz.apply(int(Action.UP)) for _ in range(200)}
    # With p=0.5 over 200 trials, we should see both intended and deflected
    assert int(Action.UP) in results
    assert len(results) > 1


def test_wind_reproducible_with_seed() -> None:
    wz1 = WindZone(0.5, np.random.default_rng(123))
    wz2 = WindZone(0.5, np.random.default_rng(123))
    for action in [0, 1, 2, 3]:
        assert wz1.apply(action) == wz2.apply(action)
