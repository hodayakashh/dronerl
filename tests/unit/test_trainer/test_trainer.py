"""Unit tests for Trainer."""

from __future__ import annotations

import pytest

from gridworld.services.agent import QLearningAgent
from gridworld.services.environment import GridWorldEnv
from gridworld.services.trainer import Trainer

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SMALL_CONFIG: dict = {
    "grid": {
        "rows": 3,
        "cols": 3,
        "start": [0, 0],
        "goal": [2, 2],
        "obstacles": [],
    },
    "rewards": {"goal": 10.0, "step": -1.0, "obstacle": -5.0},
    "agent": {
        "alpha": 0.5,
        "gamma": 0.99,
        "epsilon": 1.0,
        "epsilon_decay": 0.99,
        "epsilon_min": 0.01,
    },
    "training": {
        "episodes": 50,
        "max_steps_per_episode": 100,
        "eval_episodes": 5,
        "seed": 42,
    },
    "output": {"results_dir": "results", "save_plots": False},
}


@pytest.fixture()
def trainer() -> Trainer:
    """A Trainer wired with a 3×3 env and default agent."""
    env = GridWorldEnv(SMALL_CONFIG)
    agent = QLearningAgent(SMALL_CONFIG, env.n_states)
    return Trainer(env, agent, SMALL_CONFIG)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_train_returns_correct_length(trainer: Trainer) -> None:
    """train() must return exactly one reward value per episode."""
    rewards = trainer.train()
    assert len(rewards) == SMALL_CONFIG["training"]["episodes"]


def test_train_rewards_are_floats(trainer: Trainer) -> None:
    """Every element in the reward list must be a float."""
    rewards = trainer.train()
    assert all(isinstance(r, float) for r in rewards)


def test_evaluate_reaches_goal(trainer: Trainer) -> None:
    """After training, greedy evaluation must end at the goal state."""
    trainer.train()
    env = trainer._env  # noqa: SLF001
    path = trainer.evaluate()
    assert path[-1] == env.goal


def test_evaluate_returns_nonempty_path(trainer: Trainer) -> None:
    """evaluate() must return a path with at least 2 states (start + goal)."""
    trainer.train()
    path = trainer.evaluate()
    assert len(path) >= 2
