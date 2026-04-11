"""Unit tests for dronerl.agent.policy."""

import numpy as np
import pytest

from dronerl.agent.policy import EpsilonGreedyPolicy


def make_policy(
    epsilon_start: float = 0.5,
    epsilon_min: float = 0.01,
    decay: float = 0.99,
    n_actions: int = 4,
    seed: int = 42,
) -> EpsilonGreedyPolicy:
    return EpsilonGreedyPolicy(
        epsilon_start=epsilon_start,
        epsilon_min=epsilon_min,
        decay=decay,
        n_actions=n_actions,
        rng=np.random.default_rng(seed),
    )


Q_ROW = np.array([1.0, 5.0, 2.0, 3.0], dtype=np.float32)  # best action = 1


# ---------------------------------------------------------------------------
# Construction validation
# ---------------------------------------------------------------------------


def test_policy_invalid_epsilon_start_raises() -> None:
    with pytest.raises(ValueError):
        make_policy(epsilon_start=1.5)


def test_policy_invalid_epsilon_min_raises() -> None:
    with pytest.raises(ValueError):
        make_policy(epsilon_min=-0.1)


def test_policy_epsilon_min_gt_start_raises() -> None:
    with pytest.raises(ValueError):
        make_policy(epsilon_start=0.1, epsilon_min=0.5)


def test_policy_invalid_decay_raises() -> None:
    with pytest.raises(ValueError):
        make_policy(decay=1.0)


def test_policy_invalid_decay_zero_raises() -> None:
    with pytest.raises(ValueError):
        make_policy(decay=0.0)


def test_policy_invalid_n_actions_raises() -> None:
    with pytest.raises(ValueError):
        make_policy(n_actions=0)


# ---------------------------------------------------------------------------
# epsilon property
# ---------------------------------------------------------------------------


def test_policy_epsilon_property_readable() -> None:
    p = make_policy(epsilon_start=0.9)
    assert p.epsilon == pytest.approx(0.9)


# ---------------------------------------------------------------------------
# select — exploitation
# ---------------------------------------------------------------------------


def test_policy_epsilon_zero_always_exploits() -> None:
    p = make_policy(epsilon_start=0.0, epsilon_min=0.0)
    for _ in range(50):
        assert p.select(Q_ROW) == 1  # argmax of Q_ROW


# ---------------------------------------------------------------------------
# select — exploration
# ---------------------------------------------------------------------------


def test_policy_epsilon_one_always_explores() -> None:
    p = make_policy(epsilon_start=1.0, epsilon_min=0.0, seed=0)
    results = {p.select(Q_ROW) for _ in range(200)}
    assert len(results) > 1


def test_policy_select_returns_valid_action() -> None:
    p = make_policy(seed=7)
    for _ in range(100):
        a = p.select(Q_ROW)
        assert 0 <= a < 4


# ---------------------------------------------------------------------------
# decay_epsilon
# ---------------------------------------------------------------------------


def test_policy_decay_reduces_epsilon() -> None:
    p = make_policy(epsilon_start=1.0, decay=0.9)
    p.decay_epsilon()
    assert p.epsilon < 1.0


def test_policy_decay_clamps_at_min() -> None:
    p = make_policy(epsilon_start=0.011, epsilon_min=0.01, decay=0.5)
    for _ in range(20):
        p.decay_epsilon()
    assert p.epsilon == pytest.approx(0.01)


# ---------------------------------------------------------------------------
# reset
# ---------------------------------------------------------------------------


def test_policy_reset_restores_epsilon() -> None:
    p = make_policy(epsilon_start=0.8)
    for _ in range(10):
        p.decay_epsilon()
    p.reset()
    assert p.epsilon == pytest.approx(0.8)


# ---------------------------------------------------------------------------
# reproducibility
# ---------------------------------------------------------------------------


def test_policy_reproducible_with_seed() -> None:
    p1 = make_policy(epsilon_start=0.5, seed=99)
    p2 = make_policy(epsilon_start=0.5, seed=99)
    results1 = [p1.select(Q_ROW) for _ in range(20)]
    results2 = [p2.select(Q_ROW) for _ in range(20)]
    assert results1 == results2
