"""GridWorld environment — state transitions, rewards, and rendering."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

from gridworld.constants import ACTION_DELTAS, N_ACTIONS, Action

logger = logging.getLogger(__name__)


class GridWorldEnv:
    """A configurable N×M grid environment for tabular RL.

    States are encoded as integers: state = row * n_cols + col.
    Actions: UP=0, DOWN=1, LEFT=2, RIGHT=3 (see Action enum).

    Input:  config dict (grid, rewards, training sections from setup.json)
    Output: (next_state, reward, done, info) per step
    Setup:  rows, cols, start, goal, obstacles, reward values, max_steps, seed
    """

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialise the environment from the config dict.

        Args:
            config: Full parsed config (from ConfigManager.raw).
        """
        grid_cfg = config["grid"]
        reward_cfg = config["rewards"]
        train_cfg = config["training"]

        self.n_rows: int = grid_cfg["rows"]
        self.n_cols: int = grid_cfg["cols"]
        self.n_states: int = self.n_rows * self.n_cols
        self.n_actions: int = N_ACTIONS

        self._start: int = self._encode(grid_cfg["start"][0], grid_cfg["start"][1])
        self._goal: int = self._encode(grid_cfg["goal"][0], grid_cfg["goal"][1])
        self._obstacles: set[int] = {
            self._encode(r, c) for r, c in grid_cfg["obstacles"]
        }

        self._reward_goal: float = reward_cfg["goal"]
        self._reward_step: float = reward_cfg["step"]
        self._reward_obstacle: float = reward_cfg["obstacle"]
        self._max_steps: int = train_cfg["max_steps_per_episode"]

        self._rng = np.random.default_rng(train_cfg["seed"])
        self._state: int = self._start
        self._steps: int = 0

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def reset(self) -> int:
        """Reset the environment to the start state.

        Returns:
            The start state index.
        """
        self._state = self._start
        self._steps = 0
        return self._state

    def step(self, action: int) -> tuple[int, float, bool, dict[str, Any]]:
        """Apply action and return the transition tuple.

        Hitting a wall leaves the agent in place (state unchanged).
        Hitting an obstacle applies the obstacle penalty but does NOT terminate.

        Args:
            action: Integer in [0, N_ACTIONS).

        Returns:
            (next_state, reward, done, info)
        """
        dr, dc = ACTION_DELTAS[Action(action)]
        row, col = self._decode(self._state)
        new_row = row + dr
        new_col = col + dc

        # Clamp to grid boundaries — hitting a wall keeps the agent in place
        new_row = max(0, min(self.n_rows - 1, new_row))
        new_col = max(0, min(self.n_cols - 1, new_col))
        next_state = self._encode(new_row, new_col)

        self._steps += 1
        reward, done = self._compute_reward(next_state)
        self._state = next_state

        if self._steps >= self._max_steps:
            done = True

        return next_state, reward, done, {"steps": self._steps}

    def render(self) -> None:
        """Print an ASCII representation of the current grid to stdout."""
        symbols = {self._start: "S", self._goal: "G"}
        symbols.update(dict.fromkeys(self._obstacles, "X"))
        symbols[self._state] = "A"  # agent overwrites (except goal/start if coincide)

        lines = []
        for r in range(self.n_rows):
            row_chars = []
            for c in range(self.n_cols):
                s = self._encode(r, c)
                row_chars.append(symbols.get(s, "."))
            lines.append(" ".join(row_chars))
        print("\n".join(lines))

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def state(self) -> int:
        """Current agent state index."""
        return self._state

    @property
    def goal(self) -> int:
        """Goal state index."""
        return self._goal

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _encode(self, row: int, col: int) -> int:
        """Convert (row, col) to a flat state index."""
        return row * self.n_cols + col

    def _decode(self, state: int) -> tuple[int, int]:
        """Convert a flat state index to (row, col)."""
        return divmod(state, self.n_cols)

    def _compute_reward(self, next_state: int) -> tuple[float, bool]:
        """Return (reward, done) for transitioning into next_state."""
        if next_state == self._goal:
            return self._reward_goal, True
        if next_state in self._obstacles:
            return self._reward_obstacle, False
        return self._reward_step, False
