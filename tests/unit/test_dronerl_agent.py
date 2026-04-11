"""Unit tests for dronerl.agent.agent."""

import numpy as np
import pytest

from dronerl.agent.agent import Agent
from dronerl.agent.policy import EpsilonGreedyPolicy
from dronerl.agent.q_table import QTable


def make_agent(
    rows: int = 4, cols: int = 4, n_actions: int = 4,
    alpha: float = 0.5, gamma: float = 0.9, epsilon: float = 0.0, seed: int = 0,
) -> Agent:
    qt = QTable(rows, cols, n_actions)
    policy = EpsilonGreedyPolicy(epsilon, 0.0, 0.99, n_actions, np.random.default_rng(seed))
    return Agent(qt, policy, alpha=alpha, gamma=gamma)


def test_agent_invalid_alpha_raises() -> None:
    with pytest.raises(ValueError):
        make_agent(alpha=0.0)


def test_agent_invalid_alpha_above_one_raises() -> None:
    with pytest.raises(ValueError):
        make_agent(alpha=1.5)


def test_agent_invalid_gamma_raises() -> None:
    with pytest.raises(ValueError):
        make_agent(gamma=0.0)


def test_agent_invalid_gamma_one_raises() -> None:
    with pytest.raises(ValueError):
        make_agent(gamma=1.0)


def test_agent_select_action_valid() -> None:
    assert 0 <= make_agent().select_action((0, 0)) < 4


def test_agent_update_bellman_non_terminal() -> None:
    agent = make_agent(alpha=0.5, gamma=0.9)
    agent.update((0, 0), 0, reward=10.0, next_state=(0, 1), done=False)
    assert agent._q_table.get_value(0, 0, 0) == pytest.approx(5.0)


def test_agent_update_bellman_terminal() -> None:
    agent = make_agent(alpha=1.0, gamma=0.9)
    agent.update((1, 1), 2, reward=-50.0, next_state=(1, 1), done=True)
    assert agent._q_table.get_value(1, 1, 2) == pytest.approx(-50.0)


def test_agent_update_alpha_zero_no_change() -> None:
    agent = make_agent(alpha=1e-9)
    agent.update((0, 0), 1, reward=100.0, next_state=(0, 1), done=False)
    assert abs(agent._q_table.get_value(0, 0, 1)) < 1e-6


def test_agent_target_terminal_no_future() -> None:
    agent = make_agent(alpha=1.0, gamma=0.9)
    agent._q_table.set_value(1, 0, 0, 999.0)
    agent.update((0, 0), 0, reward=5.0, next_state=(1, 0), done=True)
    assert agent._q_table.get_value(0, 0, 0) == pytest.approx(5.0)


def test_agent_total_steps_increments() -> None:
    agent = make_agent()
    agent.update((0, 0), 0, 1.0, (0, 1), False)
    agent.update((0, 1), 1, 1.0, (0, 2), False)
    assert agent.total_steps == 2


def test_agent_episode_count_increments() -> None:
    agent = make_agent()
    agent.end_episode()
    agent.end_episode()
    assert agent.episode_count == 2


def test_agent_end_episode_decays_epsilon() -> None:
    qt = QTable(4, 4, 4)
    policy = EpsilonGreedyPolicy(1.0, 0.0, 0.5, 4, np.random.default_rng(0))
    agent = Agent(qt, policy, alpha=0.1, gamma=0.9)
    agent.end_episode()
    assert agent.epsilon == pytest.approx(0.5)


def test_agent_reset_zeros_qtable() -> None:
    agent = make_agent()
    agent.update((0, 0), 0, 10.0, (0, 1), False)
    agent.reset()
    assert agent._q_table.get_value(0, 0, 0) == pytest.approx(0.0)


def test_agent_reset_resets_counters() -> None:
    agent = make_agent()
    agent.end_episode()
    agent.update((0, 0), 0, 1.0, (0, 1), False)
    agent.reset()
    assert agent.episode_count == 0
    assert agent.total_steps == 0


def test_agent_reset_restores_epsilon() -> None:
    qt = QTable(4, 4, 4)
    policy = EpsilonGreedyPolicy(0.9, 0.0, 0.5, 4, np.random.default_rng(0))
    agent = Agent(qt, policy, alpha=0.1, gamma=0.9)
    agent.end_episode()
    agent.reset()
    assert agent.epsilon == pytest.approx(0.9)


def test_agent_update_zero_reward() -> None:
    agent = make_agent(alpha=1.0)
    agent.update((0, 0), 0, 0.0, (0, 1), False)
    assert agent._q_table.get_value(0, 0, 0) == pytest.approx(0.0)


def test_agent_update_negative_reward() -> None:
    agent = make_agent(alpha=1.0, gamma=0.9)
    agent.update((0, 0), 1, -10.0, (0, 1), True)
    assert agent._q_table.get_value(0, 0, 1) == pytest.approx(-10.0)
