"""Stochastic wind zone logic for the Smart City environment."""

from __future__ import annotations

import numpy as np

from dronerl.constants import N_ACTIONS


class WindZone:
    """Models stochastic wind that may deflect the drone's intended action.

    With probability ``drift_prob`` the wind picks one of the other
    (N_ACTIONS - 1) directions uniformly at random; otherwise the
    intended action is executed unchanged.
    """

    def __init__(self, drift_prob: float, rng: np.random.Generator) -> None:
        """Initialise the wind zone.

        Args:
            drift_prob: Probability in [0, 1] that the action is deflected.
            rng: NumPy random generator for reproducible stochasticity.

        Raises:
            ValueError: If drift_prob is outside [0, 1].
        """
        if not 0.0 <= drift_prob <= 1.0:
            raise ValueError(f"drift_prob must be in [0, 1], got {drift_prob}")
        self._drift_prob = drift_prob
        self._rng = rng

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def drift_prob(self) -> float:
        """Probability that wind deflects the intended action."""
        return self._drift_prob

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def apply(self, action: int) -> int:
        """Return the actual action after wind may have deflected it.

        Args:
            action: The intended action (0 … N_ACTIONS-1).

        Returns:
            The (possibly deflected) action index.
        """
        if self._rng.random() < self._drift_prob:
            other = [a for a in range(N_ACTIONS) if a != action]
            return int(self._rng.choice(other))
        return action
