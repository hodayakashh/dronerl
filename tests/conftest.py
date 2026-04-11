"""Shared pytest fixtures and headless Pygame setup."""

from __future__ import annotations

import os

import numpy as np
import pytest

# Headless Pygame — must be set before any pygame import
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

from dronerl.agent.agent import Agent  # noqa: E402
from dronerl.agent.policy import EpsilonGreedyPolicy  # noqa: E402
from dronerl.agent.q_table import QTable  # noqa: E402
from dronerl.environment.env import SmartCityEnv  # noqa: E402
from dronerl.environment.grid import CellType, Grid  # noqa: E402
from dronerl.environment.rewards import RewardCalculator, RewardConfig  # noqa: E402
from dronerl.environment.wind import WindZone  # noqa: E402


@pytest.fixture(scope="session")
def pygame_init():  # type: ignore[return]
    """Initialise a headless Pygame session for the whole test suite."""
    pygame.init()
    pygame.display.set_mode((800, 700))
    yield
    pygame.quit()


@pytest.fixture()
def minimal_grid() -> Grid:
    """4×4 grid: start=(0,0), goal=(3,3)."""
    g = Grid(4, 4)
    g.set_cell(0, 0, CellType.START)
    g.set_cell(3, 3, CellType.GOAL)
    return g


@pytest.fixture()
def default_rewards() -> RewardConfig:
    return RewardConfig(step=-1.0, goal=100.0, trap=-50.0, wind=-2.0, wall=-5.0)


@pytest.fixture()
def simple_env(minimal_grid: Grid, default_rewards: RewardConfig) -> SmartCityEnv:
    wind = WindZone(0.0, np.random.default_rng(0))
    return SmartCityEnv(
        minimal_grid,
        wind,
        RewardCalculator(default_rewards),
        start=(0, 0),
        goal=(3, 3),
    )


@pytest.fixture()
def simple_agent(minimal_grid: Grid) -> Agent:
    qt = QTable(minimal_grid.rows, minimal_grid.cols, 4)
    policy = EpsilonGreedyPolicy(1.0, 0.01, 0.995, 4, np.random.default_rng(42))
    return Agent(qt, policy, alpha=0.1, gamma=0.95)
