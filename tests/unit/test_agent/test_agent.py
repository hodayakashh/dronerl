"""Unit tests for QLearningAgent."""

from __future__ import annotations

import numpy as np
import pytest

from gridworld.services.agent import QLearningAgent

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

BASE_CONFIG: dict = {
    "agent": {
        "alpha": 0.1,
        "gamma": 0.99,
        "epsilon": 1.0,
        "epsilon_decay": 0.5,
        "epsilon_min": 0.01,
    },
    "training": {"seed": 0},
}

N_STATES = 16  # 4×4 grid


@pytest.fixture()
def agent() -> QLearningAgent:
    """Fresh QLearningAgent with ε=1 (pure exploration)."""
    return QLearningAgent(BASE_CONFIG, N_STATES)


@pytest.fixture()
def exploit_agent() -> QLearningAgent:
    """Agent with ε=0 (pure exploitation)."""
    cfg = {**BASE_CONFIG, "agent": {**BASE_CONFIG["agent"], "epsilon": 0.0}}
    return QLearningAgent(cfg, N_STATES)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_q_table_initialised_zeros(agent: QLearningAgent) -> None:
    """Q-table must start as an all-zero array of shape (n_states, n_actions)."""
    assert agent.q_table.shape == (N_STATES, 4)
    assert np.all(agent.q_table == 0.0)


def test_select_action_explores_when_epsilon_one(agent: QLearningAgent) -> None:
    """With ε=1 all actions must be sampled over many calls (uniform exploration)."""
    actions = {agent.select_action(0) for _ in range(200)}
    assert len(actions) == 4, "All 4 actions should be explored with ε=1"


def test_select_action_exploits_when_epsilon_zero(exploit_agent: QLearningAgent) -> None:
    """With ε=0 the agent must always choose the greedy action."""
    exploit_agent.q_table[5, 2] = 99.0  # make action 2 obviously best in state 5
    actions = {exploit_agent.select_action(5) for _ in range(50)}
    assert actions == {2}


def test_bellman_update_correct_value(agent: QLearningAgent) -> None:
    """Q(s,a) update must match the Bellman formula exactly.

    Setup: Q(0,0)=0, r=10, done=True → td_target=10, new Q=0+0.1*(10-0)=1.0
    """
    td_error = agent.update(state=0, action=0, reward=10.0, next_state=1, done=True)
    assert agent.q_table[0, 0] == pytest.approx(1.0)
    assert td_error == pytest.approx(10.0)


def test_bellman_update_uses_future_q_when_not_done(agent: QLearningAgent) -> None:
    """When done=False the update must incorporate γ·max Q(s')."""
    agent.q_table[1, :] = [0.0, 5.0, 0.0, 0.0]  # max Q(s'=1) = 5.0
    # td_target = -1 + 0.99*5 = 3.95; delta = 3.95; new Q = 0 + 0.1*3.95 = 0.395
    agent.update(state=0, action=0, reward=-1.0, next_state=1, done=False)
    assert agent.q_table[0, 0] == pytest.approx(0.395)


def test_epsilon_decay(agent: QLearningAgent) -> None:
    """decay_epsilon() must halve ε each call (decay=0.5) until epsilon_min."""
    initial = agent.epsilon  # 1.0
    agent.decay_epsilon()
    assert agent.epsilon == pytest.approx(initial * 0.5)
    # Force many decays — must not go below epsilon_min=0.01
    for _ in range(100):
        agent.decay_epsilon()
    assert agent.epsilon >= 0.01


def test_get_greedy_action_ignores_epsilon(exploit_agent: QLearningAgent) -> None:
    """get_greedy_action must return argmax Q regardless of epsilon."""
    exploit_agent.q_table[3, :] = [1.0, 2.0, 0.5, 3.5]
    assert exploit_agent.get_greedy_action(3) == 3
