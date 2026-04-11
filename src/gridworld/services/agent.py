"""Q-Learning agent — Q-table, ε-greedy selection, and Bellman update."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

from gridworld.constants import N_ACTIONS

logger = logging.getLogger(__name__)


class QLearningAgent:
    """Tabular Q-Learning agent.

    Maintains a Q-table of shape (n_states, n_actions) initialised to zeros.
    Action selection uses an ε-greedy policy; Q-values are updated via the
    Bellman optimality equation after every environment step.

    Input:  config dict (agent section), n_states (int)
    Output: action (int) from select_action(); Q-table updates in-place
    Setup:  alpha, gamma, epsilon, epsilon_decay, epsilon_min, seed
    """

    def __init__(self, config: dict[str, Any], n_states: int) -> None:
        """Initialise the agent with a zero Q-table.

        Args:
            config: Full parsed config (from ConfigManager.raw).
            n_states: Total number of discrete states in the environment.
        """
        agent_cfg = config["agent"]
        train_cfg = config["training"]

        self._alpha: float = agent_cfg["alpha"]
        self._gamma: float = agent_cfg["gamma"]
        self._epsilon: float = agent_cfg["epsilon"]
        self._epsilon_decay: float = agent_cfg["epsilon_decay"]
        self._epsilon_min: float = agent_cfg["epsilon_min"]

        self.n_states: int = n_states
        self.n_actions: int = N_ACTIONS

        # Q-table initialised to zeros (shape: states × actions)
        self.q_table: np.ndarray = np.zeros((n_states, N_ACTIONS), dtype=np.float64)
        self._rng = np.random.default_rng(train_cfg["seed"])

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def select_action(self, state: int) -> int:
        """Choose an action using the ε-greedy policy.

        Explores (random action) with probability ε;
        exploits (greedy action) with probability 1−ε.

        Args:
            state: Current state index.

        Returns:
            Integer action in [0, n_actions).
        """
        if self._rng.random() < self._epsilon:
            return int(self._rng.integers(0, self.n_actions))
        return int(np.argmax(self.q_table[state]))

    def get_greedy_action(self, state: int) -> int:
        """Return the greedy action (argmax Q) regardless of ε.

        Args:
            state: Current state index.

        Returns:
            Integer action with the highest Q-value.
        """
        return int(np.argmax(self.q_table[state]))

    def update(
        self,
        state: int,
        action: int,
        reward: float,
        next_state: int,
        done: bool,
    ) -> float:
        """Apply the Bellman update to Q(state, action).

        Q(s,a) ← Q(s,a) + α·[r + γ·max_a' Q(s',a') − Q(s,a)]

        The target is r when done=True (no future rewards after terminal state).

        Args:
            state: State in which the action was taken.
            action: Action that was executed.
            reward: Immediate reward received.
            next_state: State reached after the action.
            done: Whether the episode terminated.

        Returns:
            The TD error (δ) for this update.
        """
        current_q = self.q_table[state, action]
        future_q = 0.0 if done else float(np.max(self.q_table[next_state]))
        td_target = reward + self._gamma * future_q
        td_error = td_target - current_q
        self.q_table[state, action] += self._alpha * td_error
        return td_error

    def decay_epsilon(self) -> None:
        """Decay ε by the configured factor, clamped to epsilon_min.

        Called once per episode to shift from exploration to exploitation.
        """
        self._epsilon = max(self._epsilon_min, self._epsilon * self._epsilon_decay)

    @property
    def epsilon(self) -> float:
        """Current exploration rate."""
        return self._epsilon
