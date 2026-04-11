"""Reward configuration and calculator for the Smart City environment."""

from __future__ import annotations

from dataclasses import dataclass

from dronerl.environment.grid import CellType


@dataclass(frozen=True)
class RewardConfig:
    """Immutable reward values for each cell-type outcome.

    All values should be read from config — never hardcoded at call sites.
    """

    step: float
    goal: float
    trap: float
    wind: float
    wall: float

    @classmethod
    def from_namespace(cls, ns: object) -> RewardConfig:
        """Build a RewardConfig from a SimpleNamespace (loaded from YAML).

        Args:
            ns: Namespace with attributes: step, goal, trap, wind, wall.

        Returns:
            A new RewardConfig instance.
        """
        return cls(
            step=float(ns.step),  # type: ignore[attr-defined]
            goal=float(ns.goal),  # type: ignore[attr-defined]
            trap=float(ns.trap),  # type: ignore[attr-defined]
            wind=float(ns.wind),  # type: ignore[attr-defined]
            wall=float(ns.wall),  # type: ignore[attr-defined]
        )


class RewardCalculator:
    """Compute the scalar reward for a given transition outcome.

    Reward rules (in priority order):
    1. GOAL cell  → ``config.goal``
    2. TRAP cell  → ``config.trap``
    3. WALL bump  → ``config.wall``   (drone stayed in place)
    4. WIND cell  → ``config.wind``   (on top of step cost)
    5. Default    → ``config.step``
    """

    def __init__(self, config: RewardConfig) -> None:
        """Initialise with a frozen RewardConfig.

        Args:
            config: Reward values for each outcome.
        """
        self._cfg = config

    @property
    def config(self) -> RewardConfig:
        """The underlying RewardConfig (read-only)."""
        return self._cfg

    def calculate(self, cell_type: CellType, hit_wall: bool = False) -> float:
        """Return the reward for landing on ``cell_type``.

        Args:
            cell_type: The CellType of the cell the drone landed on.
            hit_wall:  True when the drone tried to move into a wall and
                       was bounced back to its previous position.

        Returns:
            Scalar reward value.
        """
        if hit_wall:
            return self._cfg.wall
        if cell_type is CellType.GOAL:
            return self._cfg.goal
        if cell_type is CellType.TRAP:
            return self._cfg.trap
        if cell_type is CellType.WIND:
            return self._cfg.step + self._cfg.wind
        return self._cfg.step
