"""Unit tests for dronerl.environment.env."""

import numpy as np
import pytest

from dronerl.constants import Action
from dronerl.environment.env import SmartCityEnv
from dronerl.environment.grid import CellType, Grid
from dronerl.environment.rewards import RewardCalculator, RewardConfig
from dronerl.environment.wind import WindZone


@pytest.fixture()
def cfg() -> RewardConfig:
    return RewardConfig(step=-1.0, goal=100.0, trap=-50.0, wind=-2.0, wall=-5.0)


@pytest.fixture()
def no_wind() -> WindZone:
    return WindZone(0.0, np.random.default_rng(0))


@pytest.fixture()
def simple_env(cfg: RewardConfig, no_wind: WindZone) -> SmartCityEnv:
    """4×4 grid: start=(0,0), goal=(3,3), wall=(1,1)."""
    g = Grid(4, 4)
    g.set_cell(1, 1, CellType.WALL)
    g.set_cell(3, 3, CellType.GOAL)
    g.set_cell(0, 0, CellType.START)
    return SmartCityEnv(g, no_wind, RewardCalculator(cfg), start=(0, 0), goal=(3, 3))


def test_reset_returns_start(simple_env: SmartCityEnv) -> None:
    assert simple_env.reset() == (0, 0)


def test_reset_after_move_returns_start(simple_env: SmartCityEnv) -> None:
    simple_env.step(int(Action.DOWN))
    assert simple_env.reset() == (0, 0)


def test_state_property_matches_reset(simple_env: SmartCityEnv) -> None:
    simple_env.reset()
    assert simple_env.state == (0, 0)




def test_step_moves_right(simple_env: SmartCityEnv) -> None:
    simple_env.reset()
    ns, _, _ = simple_env.step(int(Action.RIGHT))
    assert ns == (0, 1)


def test_step_moves_down(simple_env: SmartCityEnv) -> None:
    simple_env.reset()
    ns, _, _ = simple_env.step(int(Action.DOWN))
    assert ns == (1, 0)


def test_step_updates_internal_state(simple_env: SmartCityEnv) -> None:
    simple_env.reset()
    simple_env.step(int(Action.RIGHT))
    assert simple_env.state == (0, 1)




def test_step_into_wall_stays(simple_env: SmartCityEnv) -> None:
    """Moving from (0,0) DOWN then RIGHT into wall (1,1) stays at (1,0)."""
    simple_env.reset()
    simple_env.step(int(Action.DOWN))  # → (1,0)
    ns, reward, _ = simple_env.step(int(Action.RIGHT))  # wall at (1,1)
    assert ns == (1, 0)
    assert reward == pytest.approx(-5.0)


def test_step_into_grid_boundary_stays(simple_env: SmartCityEnv) -> None:
    simple_env.reset()
    ns, reward, _ = simple_env.step(int(Action.UP))  # already at row 0
    assert ns == (0, 0)
    assert reward == pytest.approx(-5.0)




def test_step_to_goal_returns_done(cfg: RewardConfig, no_wind: WindZone) -> None:
    g = Grid(2, 2)
    g.set_cell(0, 1, CellType.GOAL)
    env = SmartCityEnv(g, no_wind, RewardCalculator(cfg), start=(0, 0), goal=(0, 1))
    env.reset()
    _, reward, done = env.step(int(Action.RIGHT))
    assert done is True
    assert reward == pytest.approx(100.0)


def test_step_to_trap_returns_done(cfg: RewardConfig, no_wind: WindZone) -> None:
    g = Grid(2, 2)
    g.set_cell(0, 1, CellType.TRAP)
    env = SmartCityEnv(g, no_wind, RewardCalculator(cfg), start=(0, 0), goal=(1, 1))
    env.reset()
    _, reward, done = env.step(int(Action.RIGHT))
    assert done is True
    assert reward == pytest.approx(-50.0)


def test_step_empty_cell_not_done(simple_env: SmartCityEnv) -> None:
    simple_env.reset()
    _, _, done = simple_env.step(int(Action.RIGHT))
    assert done is False


# ---------------------------------------------------------------------------
# step — wind deflection
# ---------------------------------------------------------------------------


def test_wind_cell_may_deflect(cfg: RewardConfig) -> None:
    """Drone on a WIND cell with drift_prob=1 always gets deflected."""
    g = Grid(3, 3)
    g.set_cell(1, 1, CellType.WIND)
    wind = WindZone(1.0, np.random.default_rng(5))
    env = SmartCityEnv(g, wind, RewardCalculator(cfg), start=(1, 1), goal=(2, 2))
    results = set()
    for _ in range(20):
        env.reset()
        ns, _, _ = env.step(int(Action.UP))
        results.add(ns)
    assert (0, 1) not in results or len(results) > 1


def test_no_wind_cell_no_deflection(cfg: RewardConfig) -> None:
    """Drone on EMPTY cell is never deflected even with high drift_prob."""
    g = Grid(3, 3)
    wind = WindZone(1.0, np.random.default_rng(5))
    env = SmartCityEnv(g, wind, RewardCalculator(cfg), start=(1, 1), goal=(2, 2))
    for _ in range(20):
        env.reset()
        ns, _, _ = env.step(int(Action.UP))
        assert ns == (0, 1)


def test_env_grid_property(simple_env: SmartCityEnv) -> None:
    assert isinstance(simple_env.grid, Grid)
