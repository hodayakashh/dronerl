"""Integration tests — full training loop via DroneRLSDK."""

from pathlib import Path

import pytest

from dronerl.sdk import DroneRLSDK


@pytest.fixture()
def sdk() -> DroneRLSDK:
    return DroneRLSDK()


def test_headless_100_episodes_completes(sdk: DroneRLSDK) -> None:
    rewards = sdk.run_headless(100)
    assert len(rewards) == 100


def test_headless_returns_correct_episode_count(sdk: DroneRLSDK) -> None:
    sdk.run_headless(50)
    assert sdk.get_training_stats()["episodes"] == 50


def test_headless_rewards_are_finite(sdk: DroneRLSDK) -> None:
    import math
    rewards = sdk.run_headless(20)
    assert all(math.isfinite(r) for r in rewards)


def test_save_load_qtable_preserves_values(sdk: DroneRLSDK, tmp_path: Path) -> None:
    sdk.run_headless(30)
    p = str(tmp_path / "brain.npy")
    sdk.save_q_table(p)
    sdk2 = DroneRLSDK()
    sdk2.load_q_table(p)
    qt1 = sdk.get_q_table()
    qt2 = sdk2.get_q_table()
    for r in range(12):
        for c in range(12):
            assert qt1.max_value(r, c) == pytest.approx(qt2.max_value(r, c))


def test_policy_map_all_cells_covered(sdk: DroneRLSDK) -> None:
    pm = sdk.get_policy_map()
    assert len(pm) == 12 * 12
    assert all(0 <= a < 4 for a in pm.values())


def test_reset_restores_initial_state(sdk: DroneRLSDK) -> None:
    sdk.run_headless(20)
    eps_before = sdk._agent.epsilon
    sdk._agent.reset()
    assert sdk._agent.epsilon > eps_before
    assert sdk._agent.episode_count == 0
