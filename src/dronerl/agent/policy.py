"""Epsilon-greedy exploration policy."""

from __future__ import annotations

import numpy as np


class EpsilonGreedyPolicy:
    """ε-greedy policy: explore with probability ε, exploit otherwise.

    Epsilon decays multiplicatively after each episode via
    ``decay_epsilon()``, clamped at ``epsilon_min``.
    """

    def __init__(
        self,
        epsilon_start: float,
        epsilon_min: float,
        decay: float,
        n_actions: int,
        rng: np.random.Generator,
    ) -> None:
        """Initialise the policy.

        Args:
            epsilon_start: Initial exploration rate in [0, 1].
            epsilon_min:   Minimum exploration rate in [0, 1].
            decay:         Multiplicative decay factor in (0, 1).
            n_actions:     Number of discrete actions.
            rng:           NumPy random generator.

        Raises:
            ValueError: If any argument violates its constraints.
        """
        if not 0.0 <= epsilon_start <= 1.0:
            raise ValueError(f"epsilon_start must be in [0, 1], got {epsilon_start}")
        if not 0.0 <= epsilon_min <= 1.0:
            raise ValueError(f"epsilon_min must be in [0, 1], got {epsilon_min}")
        if epsilon_min > epsilon_start:
            raise ValueError("epsilon_min must be <= epsilon_start")
        if not 0.0 < decay < 1.0:
            raise ValueError(f"decay must be in (0, 1), got {decay}")
        if n_actions <= 0:
            raise ValueError(f"n_actions must be > 0, got {n_actions}")

        self._epsilon_start = epsilon_start
        self._epsilon_min = epsilon_min
        self._decay = decay
        self._n_actions = n_actions
        self._rng = rng
        self._epsilon = epsilon_start

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def epsilon(self) -> float:
        """Current exploration rate."""
        return self._epsilon

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def select(self, q_row: np.ndarray) -> int:
        """Choose an action using ε-greedy selection.

        Args:
            q_row: 1-D array of Q-values for the current state.

        Returns:
            Chosen action index.
        """
        if self._rng.random() < self._epsilon:
            return int(self._rng.integers(0, self._n_actions))
        return int(np.argmax(q_row))

    def decay_epsilon(self) -> None:
        """Multiply epsilon by decay, then clamp to epsilon_min."""
        self._epsilon = max(self._epsilon * self._decay, self._epsilon_min)

    def reset(self) -> None:
        """Restore epsilon to its initial value."""
        self._epsilon = self._epsilon_start
