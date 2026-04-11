"""Immutable project-wide constants and enumerations."""

from enum import IntEnum


class Action(IntEnum):
    """Cardinal movement actions available to the agent."""

    UP = 0
    DOWN = 1
    LEFT = 2
    RIGHT = 3


# Mapping from Action to (delta_row, delta_col)
ACTION_DELTAS: dict[int, tuple[int, int]] = {
    Action.UP: (-1, 0),
    Action.DOWN: (1, 0),
    Action.LEFT: (0, -1),
    Action.RIGHT: (0, 1),
}

N_ACTIONS: int = len(Action)

# Config file default path (relative to project root)
DEFAULT_CONFIG_PATH: str = "config/setup.json"
