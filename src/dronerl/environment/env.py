"""SmartCityEnv — the drone delivery Markov Decision Process."""

from __future__ import annotations

from dronerl.constants import ACTION_DELTAS
from dronerl.environment.grid import CellType, Grid
from dronerl.environment.rewards import RewardCalculator
from dronerl.environment.wind import WindZone

State = tuple[int, int]


class SmartCityEnv:
    """Grid-world MDP for the drone delivery task.

    The agent controls a drone navigating a 2-D city grid.
    Episodes end when the drone reaches the GOAL or a TRAP cell,
    or when the step limit is exceeded (managed externally).

    Wind zones may stochastically deflect the drone's action.
    Walls block movement — the drone stays in place and receives a
    wall-bump penalty.
    """

    def __init__(
        self,
        grid: Grid,
        wind: WindZone,
        reward_calc: RewardCalculator,
        start: State,
        goal: State,
    ) -> None:
        """Initialise the environment.

        Args:
            grid: The Smart City grid.
            wind: WindZone used for stochastic deflection.
            reward_calc: Computes scalar rewards for transitions.
            start: Default (row, col) spawn position of the drone.
            goal: (row, col) of the delivery target cell.
        """
        self._grid = grid
        self._wind = wind
        self._reward_calc = reward_calc
        self._start = start
        self._goal = goal
        self._state: State = start

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def grid(self) -> Grid:
        """The underlying Grid (read-only reference)."""
        return self._grid

    @property
    def state(self) -> State:
        """Current drone position as (row, col)."""
        return self._state

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def reset(self) -> State:
        """Reset the drone to the start position.

        Returns:
            The initial state (row, col).
        """
        self._state = self._start
        return self._state

    def step(self, action: int) -> tuple[State, float, bool]:
        """Execute one step in the environment.

        Wind deflection is applied when the current cell is a WIND cell.
        If the intended move leads into a WALL the drone stays in place
        and receives the wall-bump reward.

        Args:
            action: Integer action index (see ``Action`` enum).

        Returns:
            (next_state, reward, done) where ``done`` is True on
            GOAL or TRAP termination.
        """
        r, c = self._state
        current_cell = self._grid.get_cell(r, c)

        # Apply wind deflection if on a wind cell
        if current_cell is CellType.WIND:
            action = self._wind.apply(action)

        next_state = self._apply_action((r, c), action)
        nr, nc = next_state

        next_cell = self._grid.get_cell(nr, nc)
        hit_wall = next_state == (r, c) and self._would_leave(r, c, action)

        reward = self._reward_calc.calculate(next_cell, hit_wall=hit_wall)
        done = next_cell in (CellType.GOAL, CellType.TRAP)

        self._state = next_state
        return next_state, reward, done

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _apply_action(self, state: State, action: int) -> State:
        """Return the next state after applying action (wall-clamped)."""
        r, c = state
        dr, dc = ACTION_DELTAS[action]
        nr, nc = r + dr, c + dc
        if self._grid.is_walkable(nr, nc):
            return (nr, nc)
        return (r, c)

    def _would_leave(self, r: int, c: int, action: int) -> bool:
        """Return True if the action would move off-grid or into a wall."""
        dr, dc = ACTION_DELTAS[action]
        nr, nc = r + dr, c + dc
        return not self._grid.is_walkable(nr, nc)
