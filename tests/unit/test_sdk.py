"""Unit tests for dronerl.sdk.DroneRLSDK."""

from pathlib import Path

import pytest

from dronerl.agent.q_table import QTable
from dronerl.sdk import DroneRLSDK


@pytest.fixture()
def sdk() -> DroneRLSDK:
    return DroneRLSDK()


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------


def test_sdk_init_valid_config(sdk: DroneRLSDK) -> None:
    assert sdk is not None


def test_sdk_invalid_config_raises() -> None:
    with pytest.raises(Exception):
        DroneRLSDK(config_path="nonexistent/setup.json")


def test_sdk_grid_has_correct_dimensions(sdk: DroneRLSDK) -> None:
    assert sdk._grid.rows == 12
    assert sdk._grid.cols == 12


# ---------------------------------------------------------------------------
# run_headless
# ---------------------------------------------------------------------------


def test_sdk_run_headless_returns_list(sdk: DroneRLSDK) -> None:
    result = sdk.run_headless(5)
    assert isinstance(result, list)


def test_sdk_run_headless_correct_length(sdk: DroneRLSDK) -> None:
    result = sdk.run_headless(10)
    assert len(result) == 10


def test_sdk_run_headless_rewards_are_floats(sdk: DroneRLSDK) -> None:
    result = sdk.run_headless(5)
    assert all(isinstance(r, float) for r in result)


def test_sdk_run_headless_epsilon_decays(sdk: DroneRLSDK) -> None:
    eps_before = sdk._agent.epsilon
    sdk.run_headless(20)
    assert sdk._agent.epsilon < eps_before


# ---------------------------------------------------------------------------
# Q-table API
# ---------------------------------------------------------------------------


def test_sdk_get_qtable_returns_qtable(sdk: DroneRLSDK) -> None:
    assert isinstance(sdk.get_q_table(), QTable)


def test_sdk_get_policy_map_returns_dict(sdk: DroneRLSDK) -> None:
    pm = sdk.get_policy_map()
    assert isinstance(pm, dict)
    assert len(pm) == 12 * 12


def test_sdk_get_policy_map_keys_are_tuples(sdk: DroneRLSDK) -> None:
    pm = sdk.get_policy_map()
    assert all(isinstance(k, tuple) for k in pm)


def test_sdk_save_load_qtable_round_trip(sdk: DroneRLSDK, tmp_path: Path) -> None:
    sdk.run_headless(5)
    p = str(tmp_path / "brain.npy")
    sdk.save_q_table(p)
    sdk2 = DroneRLSDK()
    sdk2.load_q_table(p)
    for r in range(12):
        for c in range(12):
            for a in range(4):
                assert sdk.get_q_table().get_value(r, c, a) == pytest.approx(
                    sdk2.get_q_table().get_value(r, c, a)
                )


def test_sdk_save_creates_file(sdk: DroneRLSDK, tmp_path: Path) -> None:
    p = str(tmp_path / "qt.npy")
    sdk.save_q_table(p)
    assert Path(p).exists()


# ---------------------------------------------------------------------------
# Training stats
# ---------------------------------------------------------------------------


def test_sdk_get_training_stats_keys(sdk: DroneRLSDK) -> None:
    stats = sdk.get_training_stats()
    assert "episodes" in stats
    assert "goal_rate" in stats
    assert "epsilon" in stats
    assert "total_steps" in stats


def test_sdk_stats_episodes_count(sdk: DroneRLSDK) -> None:
    sdk.run_headless(7)
    assert sdk.get_training_stats()["episodes"] == 7
