"""Trainer — orchestrates training and greedy evaluation loops."""

from __future__ import annotations

import logging
from typing import Any

from gridworld.services.agent import QLearningAgent
from gridworld.services.environment import GridWorldEnv

logger = logging.getLogger(__name__)


class Trainer:
    """Runs the Q-Learning training loop and evaluation.

    Training loop:
      For each episode → reset env → step until done →
      update agent → decay ε → log total reward.

    Evaluation loop:
      Fixed episodes with greedy policy; returns path of visited states.

    Input:  GridWorldEnv, QLearningAgent, config dict
    Output: List[float] from train(); List[int] path from evaluate()
    Setup:  episodes, max_steps_per_episode, eval_episodes (from config)
    """

    def __init__(
        self,
        env: GridWorldEnv,
        agent: QLearningAgent,
        config: dict[str, Any],
    ) -> None:
        """Wire up the environment, agent, and training config.

        Args:
            env: The GridWorld environment instance.
            agent: The Q-Learning agent instance.
            config: Full parsed config (from ConfigManager.raw).
        """
        self._env = env
        self._agent = agent
        self._episodes: int = config["training"]["episodes"]
        self._eval_episodes: int = config["training"]["eval_episodes"]

    def train(self) -> list[float]:
        """Run the full training loop.

        Returns:
            List of total rewards per episode (length == episodes).
        """
        episode_rewards: list[float] = []

        for ep in range(self._episodes):
            state = self._env.reset()
            total_reward = 0.0
            done = False

            while not done:
                action = self._agent.select_action(state)
                next_state, reward, done, _ = self._env.step(action)
                self._agent.update(state, action, reward, next_state, done)
                state = next_state
                total_reward += reward

            self._agent.decay_epsilon()
            episode_rewards.append(total_reward)

            if (ep + 1) % 100 == 0:
                avg = sum(episode_rewards[-100:]) / 100
                logger.info(
                    "Episode %4d | avg reward (last 100): %6.2f | ε=%.4f",
                    ep + 1,
                    avg,
                    self._agent.epsilon,
                )

        return episode_rewards

    def evaluate(self) -> list[int]:
        """Run one greedy evaluation episode and return the path taken.

        Uses argmax Q (no exploration) to demonstrate the learned policy.

        Returns:
            List of state indices visited from start to goal (or timeout).
        """
        state = self._env.reset()
        path = [state]
        done = False

        while not done:
            action = self._agent.get_greedy_action(state)
            state, _, done, _ = self._env.step(action)
            path.append(state)

        logger.info("Evaluation path (%d steps): %s", len(path) - 1, path)
        return path
