"""Agent: action selection and Q-Learning (Bellman) updates."""

from __future__ import annotations

from dronerl.agent.policy import EpsilonGreedyPolicy
from dronerl.agent.q_table import QTable

State = tuple[int, int]


class Agent:
    """Tabular Q-Learning agent.

    Applies the Bellman update rule::

        Q[s,a] += α * (r + γ * max Q[s'] − Q[s,a])

    For terminal transitions ``done=True`` the future term is omitted::

        Q[s,a] += α * (r − Q[s,a])
    """

    def __init__(
        self,
        q_table: QTable,
        policy: EpsilonGreedyPolicy,
        alpha: float,
        gamma: float,
    ) -> None:
        """Initialise the agent.

        Args:
            q_table: Pre-allocated QTable instance.
            policy:  EpsilonGreedyPolicy for action selection.
            alpha:   Learning rate in (0, 1].
            gamma:   Discount factor in (0, 1).

        Raises:
            ValueError: If alpha or gamma violate their constraints.
        """
        if not 0.0 < alpha <= 1.0:
            raise ValueError(f"alpha must be in (0, 1], got {alpha}")
        if not 0.0 < gamma < 1.0:
            raise ValueError(f"gamma must be in (0, 1), got {gamma}")

        self._q_table = q_table
        self._policy = policy
        self._alpha = alpha
        self._gamma = gamma
        self._episode_count = 0
        self._total_steps = 0

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def episode_count(self) -> int:
        """Number of completed episodes."""
        return self._episode_count

    @property
    def total_steps(self) -> int:
        """Total environment steps taken across all episodes."""
        return self._total_steps

    @property
    def epsilon(self) -> float:
        """Current exploration rate (delegated to policy)."""
        return self._policy.epsilon

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def select_action(self, state: State) -> int:
        """Choose an action for the given state using the policy.

        Args:
            state: Current (row, col) position of the drone.

        Returns:
            Chosen action index.
        """
        r, c = state
        return self._policy.select(self._q_table.get(r, c))

    def update(
        self,
        state: State,
        action: int,
        reward: float,
        next_state: State,
        done: bool,
    ) -> None:
        """Apply the Bellman update to Q[state, action].

        Args:
            state:      Current state (row, col).
            action:     Action taken.
            reward:     Scalar reward received.
            next_state: Resulting state (row, col).
            done:       True if the episode ended after this transition.
        """
        r, c = state
        nr, nc = next_state
        q_current = self._q_table.get_value(r, c, action)
        target = reward if done else reward + self._gamma * self._q_table.max_value(nr, nc)
        new_q = q_current + self._alpha * (target - q_current)
        self._q_table.set_value(r, c, action, new_q)
        self._total_steps += 1

    def end_episode(self) -> None:
        """Call at the end of each episode to decay epsilon and track count."""
        self._policy.decay_epsilon()
        self._episode_count += 1

    def reset(self) -> None:
        """Reset Q-table, policy epsilon, and counters to initial state."""
        self._q_table.reset()
        self._policy.reset()
        self._episode_count = 0
        self._total_steps = 0
