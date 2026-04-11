"""Unit tests for dronerl.environment.rewards."""

from types import SimpleNamespace

import pytest

from dronerl.environment.grid import CellType
from dronerl.environment.rewards import RewardCalculator, RewardConfig


@pytest.fixture()
def cfg() -> RewardConfig:
    return RewardConfig(step=-1.0, goal=100.0, trap=-50.0, wind=-2.0, wall=-5.0)


@pytest.fixture()
def calc(cfg: RewardConfig) -> RewardCalculator:
    return RewardCalculator(cfg)


# ---------------------------------------------------------------------------
# RewardConfig
# ---------------------------------------------------------------------------


def test_reward_config_is_frozen(cfg: RewardConfig) -> None:
    with pytest.raises((AttributeError, TypeError)):
        cfg.step = 0.0  # type: ignore[misc]


def test_reward_config_from_namespace() -> None:
    ns = SimpleNamespace(step=-1, goal=100, trap=-50, wind=-2, wall=-5)
    rc = RewardConfig.from_namespace(ns)
    assert rc.step == pytest.approx(-1.0)
    assert rc.goal == pytest.approx(100.0)


def test_reward_config_values_stored(cfg: RewardConfig) -> None:
    assert cfg.trap == pytest.approx(-50.0)
    assert cfg.wind == pytest.approx(-2.0)
    assert cfg.wall == pytest.approx(-5.0)


# ---------------------------------------------------------------------------
# RewardCalculator — each cell type
# ---------------------------------------------------------------------------


def test_reward_goal(calc: RewardCalculator) -> None:
    assert calc.calculate(CellType.GOAL) == pytest.approx(100.0)


def test_reward_trap(calc: RewardCalculator) -> None:
    assert calc.calculate(CellType.TRAP) == pytest.approx(-50.0)


def test_reward_empty_step(calc: RewardCalculator) -> None:
    assert calc.calculate(CellType.EMPTY) == pytest.approx(-1.0)


def test_reward_start_step(calc: RewardCalculator) -> None:
    assert calc.calculate(CellType.START) == pytest.approx(-1.0)


def test_reward_wind_is_step_plus_wind(calc: RewardCalculator) -> None:
    # step(-1) + wind(-2) = -3
    assert calc.calculate(CellType.WIND) == pytest.approx(-3.0)


def test_reward_wall_bump(calc: RewardCalculator) -> None:
    assert calc.calculate(CellType.EMPTY, hit_wall=True) == pytest.approx(-5.0)


def test_reward_wall_bump_overrides_cell_type(calc: RewardCalculator) -> None:
    # Even if somehow the cell is GOAL, hit_wall takes priority
    assert calc.calculate(CellType.GOAL, hit_wall=True) == pytest.approx(-5.0)


# ---------------------------------------------------------------------------
# RewardCalculator — config property
# ---------------------------------------------------------------------------


def test_calc_config_property(calc: RewardCalculator, cfg: RewardConfig) -> None:
    assert calc.config is cfg
