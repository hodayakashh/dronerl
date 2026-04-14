"""Unit tests for dronerl.sdk.DroneRLSDK."""

from pathlib import Path

import pytest

from dronerl._sdk_helpers import apply_grid_anchors, find_first
from dronerl.agent.q_table import QTable
from dronerl.environment.grid import CellType
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
    from dronerl.shared.config import ConfigError
    with pytest.raises(ConfigError):
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


def test_sdk_load_missing_file_returns_false(sdk: DroneRLSDK, tmp_path: Path) -> None:
    result = sdk.load_q_table(str(tmp_path / "missing.npy"))
    assert result is False


def test_sdk_load_success_returns_true(sdk: DroneRLSDK, tmp_path: Path) -> None:
    p = str(tmp_path / "brain.npy")
    sdk.save_q_table(p)
    assert sdk.load_q_table(p) is True


def test_sdk_load_wrong_shape_returns_false(sdk: DroneRLSDK, tmp_path: Path) -> None:
    import numpy as np
    p = tmp_path / "bad.npy"
    np.save(str(p), np.zeros((3, 3, 3), dtype=np.float32))
    assert sdk.load_q_table(str(p)) is False


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


# ---------------------------------------------------------------------------
# Editor anchor sync (START/GOAL)
# ---------------------------------------------------------------------------


def test_sdk_find_first_returns_position_when_present(sdk: DroneRLSDK) -> None:
    for r in range(sdk._grid.rows):
        for c in range(sdk._grid.cols):
            if sdk._grid.get_cell(r, c) is CellType.START:
                sdk._grid.set_cell(r, c, CellType.EMPTY)
    sdk._grid.set_cell(2, 3, CellType.START)
    assert find_first(sdk._grid, CellType.START) == (2, 3)


def test_sdk_find_first_returns_none_when_absent(sdk: DroneRLSDK) -> None:
    for r in range(sdk._grid.rows):
        for c in range(sdk._grid.cols):
            if sdk._grid.get_cell(r, c) is CellType.GOAL:
                sdk._grid.set_cell(r, c, CellType.EMPTY)
    assert find_first(sdk._grid, CellType.GOAL) is None


def test_sdk_apply_grid_anchors_updates_env_start_goal(sdk: DroneRLSDK) -> None:
    for r in range(sdk._grid.rows):
        for c in range(sdk._grid.cols):
            if sdk._grid.get_cell(r, c) in (CellType.START, CellType.GOAL):
                sdk._grid.set_cell(r, c, CellType.EMPTY)
    sdk._grid.set_cell(4, 5, CellType.START)
    sdk._grid.set_cell(7, 8, CellType.GOAL)

    start, goal = apply_grid_anchors(sdk._grid, sdk._default_start, sdk._default_goal, sdk._log)

    assert start == (4, 5)
    assert goal == (7, 8)


def test_sdk_apply_grid_anchors_restores_defaults_when_missing(sdk: DroneRLSDK) -> None:
    default_start = sdk._default_start
    default_goal = sdk._default_goal
    for r in range(sdk._grid.rows):
        for c in range(sdk._grid.cols):
            if sdk._grid.get_cell(r, c) in (CellType.START, CellType.GOAL):
                sdk._grid.set_cell(r, c, CellType.EMPTY)

    start, goal = apply_grid_anchors(sdk._grid, default_start, default_goal, sdk._log)

    assert start == default_start
    assert goal == default_goal
    assert sdk._grid.get_cell(*default_start) is CellType.START
    assert sdk._grid.get_cell(*default_goal) is CellType.GOAL
