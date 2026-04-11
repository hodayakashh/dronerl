"""Extended tests for Milestone 5 quality requirements (5.1–5.8)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from dronerl.agent.agent import Agent
from dronerl.agent.policy import EpsilonGreedyPolicy
from dronerl.agent.q_table import QTable
from dronerl.constants import Action
from dronerl.environment.grid import CellType, Grid
from dronerl.environment.rewards import RewardCalculator, RewardConfig
from dronerl.environment.wind import WindZone
from dronerl.sdk import DroneRLSDK


# ---------------------------------------------------------------------------
# 5.1 Extended — grid.py
# ---------------------------------------------------------------------------


def test_grid_large_100x100() -> None:
    g = Grid(100, 100)
    assert g.rows == 100 and g.cols == 100


def test_grid_single_cell() -> None:
    g = Grid(1, 1)
    assert g.get_cell(0, 0) is CellType.EMPTY


def test_grid_all_celltypes_accessible() -> None:
    assert len(list(CellType)) == 6


def test_grid_all_walls_except_corners() -> None:
    g = Grid(3, 3)
    for r in range(3):
        for c in range(3):
            if (r, c) not in ((0, 0), (2, 2)):
                g.set_cell(r, c, CellType.WALL)
    assert not g.is_walkable(1, 1)
    assert g.is_walkable(0, 0)


# ---------------------------------------------------------------------------
# 5.2 Extended — wind.py
# ---------------------------------------------------------------------------


def test_wind_statistical_distribution() -> None:
    wz = WindZone(0.5, np.random.default_rng(0))
    deflected = sum(1 for _ in range(1000) if wz.apply(0) != 0)
    assert 400 < deflected < 600


def test_wind_deflection_never_same_action() -> None:
    wz = WindZone(1.0, np.random.default_rng(42))
    for action in Action:
        for _ in range(30):
            assert wz.apply(int(action)) != int(action)


def test_wind_all_4_actions_as_input() -> None:
    wz = WindZone(0.0, np.random.default_rng(0))
    for action in Action:
        assert wz.apply(int(action)) == int(action)


# ---------------------------------------------------------------------------
# 5.3 Extended — rewards.py
# ---------------------------------------------------------------------------


def test_reward_custom_values() -> None:
    cfg = RewardConfig(step=-2.0, goal=200.0, trap=-100.0, wind=-5.0, wall=-10.0)
    calc = RewardCalculator(cfg)
    assert calc.calculate(CellType.GOAL) == pytest.approx(200.0)
    assert calc.calculate(CellType.TRAP) == pytest.approx(-100.0)


def test_reward_all_values_are_floats() -> None:
    cfg = RewardConfig(step=-1.0, goal=100.0, trap=-50.0, wind=-2.0, wall=-5.0)
    assert all(isinstance(v, float) for v in (cfg.step, cfg.goal, cfg.trap, cfg.wind, cfg.wall))


def test_reward_wind_cell_no_hit_wall() -> None:
    cfg = RewardConfig(step=-1.0, goal=100.0, trap=-50.0, wind=-2.0, wall=-5.0)
    calc = RewardCalculator(cfg)
    assert calc.calculate(CellType.WIND, hit_wall=False) == pytest.approx(-3.0)


# ---------------------------------------------------------------------------
# 5.4 Extended — env.py
# ---------------------------------------------------------------------------


def test_env_full_episode_start_to_goal() -> None:
    g = Grid(1, 3)
    g.set_cell(0, 2, CellType.GOAL)
    env = _make_env(g, start=(0, 0), goal=(0, 2))
    env.reset()
    _, _, d1 = env.step(int(Action.RIGHT))
    _, _, d2 = env.step(int(Action.RIGHT))
    assert d2 is True


def test_env_full_episode_start_to_trap() -> None:
    g = Grid(1, 2)
    g.set_cell(0, 1, CellType.TRAP)
    env = _make_env(g, start=(0, 0), goal=(0, 0))
    env.reset()
    _, _, done = env.step(int(Action.RIGHT))
    assert done is True


def test_env_consecutive_wall_penalties() -> None:
    g = Grid(2, 2)
    g.set_cell(0, 1, CellType.WALL)
    env = _make_env(g, start=(0, 0), goal=(1, 1))
    env.reset()
    _, r1, _ = env.step(int(Action.RIGHT))
    _, r2, _ = env.step(int(Action.RIGHT))
    assert r1 == pytest.approx(-5.0)
    assert r2 == pytest.approx(-5.0)


# ---------------------------------------------------------------------------
# 5.5 Extended — q_table.py
# ---------------------------------------------------------------------------


def test_qtable_negative_values() -> None:
    qt = QTable(2, 2, 4)
    qt.set_value(0, 0, 0, -99.0)
    assert qt.get_value(0, 0, 0) == pytest.approx(-99.0)


def test_qtable_large_positive_values() -> None:
    qt = QTable(2, 2, 4)
    qt.set_value(1, 1, 3, 1e6)
    assert qt.max_value(1, 1) == pytest.approx(1e6)


def test_qtable_n_actions_one() -> None:
    qt = QTable(2, 2, 1)
    assert qt.best_action(0, 0) == 0


def test_qtable_load_nonexistent_raises() -> None:
    qt = QTable(2, 2, 4)
    with pytest.raises(Exception):
        qt.load("nonexistent_file.npy")


# ---------------------------------------------------------------------------
# 5.6 Extended — policy.py
# ---------------------------------------------------------------------------


def test_policy_equal_q_values_returns_valid() -> None:
    p = EpsilonGreedyPolicy(0.0, 0.0, 0.99, 4, np.random.default_rng(0))
    q = np.zeros(4, dtype=np.float32)
    assert 0 <= p.select(q) < 4


def test_policy_all_negative_q_values() -> None:
    p = EpsilonGreedyPolicy(0.0, 0.0, 0.99, 4, np.random.default_rng(0))
    q = np.array([-5.0, -1.0, -3.0, -2.0], dtype=np.float32)
    assert p.select(q) == 1  # argmax = index 1 (-1.0 is largest)


def test_policy_1000_decays_approaches_min() -> None:
    p = EpsilonGreedyPolicy(1.0, 0.01, 0.99, 4, np.random.default_rng(0))
    for _ in range(1000):
        p.decay_epsilon()
    assert p.epsilon == pytest.approx(0.01)


def test_policy_epsilon_never_below_min() -> None:
    p = EpsilonGreedyPolicy(0.5, 0.1, 0.5, 4, np.random.default_rng(0))
    for _ in range(100):
        p.decay_epsilon()
        assert p.epsilon >= 0.1


# ---------------------------------------------------------------------------
# 5.7 Extended — agent.py  (additional covered by test_dronerl_agent.py)
# ---------------------------------------------------------------------------


def test_agent_multiple_updates_same_state() -> None:
    qt = QTable(4, 4, 4)
    policy = EpsilonGreedyPolicy(0.0, 0.0, 0.99, 4, np.random.default_rng(0))
    agent = Agent(qt, policy, alpha=0.5, gamma=0.9)
    for _ in range(5):
        agent.update((0, 0), 0, 10.0, (0, 1), False)
    assert agent._q_table.get_value(0, 0, 0) > 0


def test_agent_total_steps_accumulates() -> None:
    qt = QTable(4, 4, 4)
    policy = EpsilonGreedyPolicy(0.0, 0.0, 0.99, 4, np.random.default_rng(0))
    agent = Agent(qt, policy, alpha=0.1, gamma=0.9)
    for _ in range(10):
        agent.update((0, 0), 0, 1.0, (0, 1), False)
    assert agent.total_steps == 10


# ---------------------------------------------------------------------------
# 5.8 Extended — sdk.py
# ---------------------------------------------------------------------------


def test_sdk_run_headless_1_episode() -> None:
    sdk = DroneRLSDK()
    result = sdk.run_headless(1)
    assert len(result) == 1


def test_sdk_run_headless_0_episodes() -> None:
    sdk = DroneRLSDK()
    result = sdk.run_headless(0)
    assert result == []


def test_sdk_policy_map_valid_actions() -> None:
    sdk = DroneRLSDK()
    pm = sdk.get_policy_map()
    assert all(0 <= a < 4 for a in pm.values())


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_env(grid: Grid, start: tuple, goal: tuple):
    cfg = RewardConfig(step=-1.0, goal=100.0, trap=-50.0, wind=-2.0, wall=-5.0)
    wind = WindZone(0.0, np.random.default_rng(0))
    from dronerl.environment.env import SmartCityEnv
    return SmartCityEnv(grid, wind, RewardCalculator(cfg), start, goal)
