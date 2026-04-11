"""Unit tests for GridWorldEnv."""

from __future__ import annotations

import pytest

from gridworld.constants import Action
from gridworld.services.environment import GridWorldEnv

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MINIMAL_CONFIG: dict = {
    "grid": {
        "rows": 4,
        "cols": 4,
        "start": [0, 0],
        "goal": [3, 3],
        "obstacles": [[1, 1]],
    },
    "rewards": {"goal": 10.0, "step": -1.0, "obstacle": -5.0},
    "training": {"max_steps_per_episode": 50, "seed": 0},
}


@pytest.fixture()
def env() -> GridWorldEnv:
    """A fresh 4×4 GridWorldEnv for each test."""
    return GridWorldEnv(MINIMAL_CONFIG)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_reset_returns_start_state(env: GridWorldEnv) -> None:
    """reset() must return the start state index (row=0, col=0 → state 0)."""
    state = env.reset()
    assert state == 0


def test_step_goal_gives_correct_reward(env: GridWorldEnv) -> None:
    """Moving into the goal cell must return reward=10 and done=True."""
    # Manually place agent adjacent to goal (row=3, col=2 → state 14)
    env.reset()
    env._state = 14  # noqa: SLF001  # test-only direct state injection
    next_state, reward, done, _ = env.step(Action.RIGHT)
    assert next_state == 15  # goal: row=3, col=3 → 3*4+3=15
    assert reward == pytest.approx(10.0)
    assert done is True


def test_step_obstacle_gives_penalty(env: GridWorldEnv) -> None:
    """Moving into an obstacle must return the obstacle penalty and done=False."""
    env.reset()
    env._state = 0  # row=0, col=0  noqa: SLF001
    # Move right then down → lands on (1,1) which is the obstacle
    env.step(Action.RIGHT)  # → (0,1)
    env._state = 4  # row=1, col=0  — set directly to control path  noqa: SLF001
    _, reward, done, _ = env.step(Action.RIGHT)  # → (1,1) obstacle
    assert reward == pytest.approx(-5.0)
    assert done is False


def test_step_wall_boundary_stays_in_place(env: GridWorldEnv) -> None:
    """Moving into a wall must keep the agent in the same cell."""
    env.reset()
    # Agent is at (0,0); moving UP or LEFT should stay at 0
    next_state, _, _, _ = env.step(Action.UP)
    assert next_state == 0
    next_state, _, _, _ = env.step(Action.LEFT)
    assert next_state == 0


def test_done_flag_on_goal(env: GridWorldEnv) -> None:
    """done must be True only when goal is reached, not on normal steps."""
    env.reset()
    _, _, done, _ = env.step(Action.RIGHT)
    assert done is False


def test_max_steps_terminates_episode() -> None:
    """Episode must terminate when max_steps_per_episode is reached."""
    cfg = {**MINIMAL_CONFIG, "training": {"max_steps_per_episode": 1, "seed": 0}}
    env = GridWorldEnv(cfg)
    env.reset()
    _, _, done, info = env.step(Action.RIGHT)
    assert done is True
    assert info["steps"] == 1


def test_render_does_not_raise(env: GridWorldEnv, capsys: pytest.CaptureFixture) -> None:
    """render() must produce output without raising an exception."""
    env.reset()
    env.render()
    captured = capsys.readouterr()
    # Agent at start renders as "A" (overwrites "S"); goal always shows "G"
    assert "A" in captured.out
    assert "G" in captured.out


def test_state_property(env: GridWorldEnv) -> None:
    """state property must reflect the current agent position."""
    env.reset()
    assert env.state == 0
    env.step(Action.RIGHT)
    assert env.state == 1
