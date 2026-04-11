"""GridWorldSDK — façade that wires all components for external consumers.

External code (CLI, notebooks, tests) must only import this module.
It never exposes internal service classes directly.
"""

from __future__ import annotations

import json
import logging
import logging.config
from pathlib import Path
from typing import Any

import numpy as np

from gridworld.services.agent import QLearningAgent
from gridworld.services.environment import GridWorldEnv
from gridworld.services.trainer import Trainer
from gridworld.services.visualiser import Visualiser
from gridworld.shared.config import ConfigManager
from gridworld.shared.gatekeeper import ApiGatekeeper

logger = logging.getLogger(__name__)

_LOG_CONFIG_PATH = Path("config/logging_config.json")


def _setup_logging() -> None:
    """Configure logging from logging_config.json if it exists."""
    if _LOG_CONFIG_PATH.exists():
        with _LOG_CONFIG_PATH.open() as fh:
            logging.config.dictConfig(json.load(fh))


class GridWorldSDK:
    """Public façade for the GridWorld Q-Learning experiment.

    Usage::

        sdk = GridWorldSDK("config/setup.json")
        results = sdk.run_experiment()

    All business logic is delegated to internal service classes.
    The gatekeeper wraps any future external calls.
    """

    def __init__(self, config_path: str | Path = "config/setup.json") -> None:
        """Initialise SDK by loading config and wiring components.

        Args:
            config_path: Path to setup.json.
        """
        _setup_logging()
        self._gatekeeper = ApiGatekeeper()
        self._cfg_manager = ConfigManager(config_path)
        self._config: dict[str, Any] = self._cfg_manager.raw

        self._env = GridWorldEnv(self._config)
        self._agent = QLearningAgent(self._config, self._env.n_states)
        self._trainer = Trainer(self._env, self._agent, self._config)
        self._visualiser = Visualiser(self._config)

    def run_experiment(self) -> dict[str, Any]:
        """Execute the full experiment: train → evaluate → visualise.

        Returns:
            Dict with keys: 'episode_rewards', 'eval_path', 'q_table'.
        """
        logger.info("Starting Q-Learning experiment")

        episode_rewards = self._trainer.train()
        eval_path = self._trainer.evaluate()

        self._visualiser.plot_reward_curve(episode_rewards)
        self._visualiser.plot_q_table_heatmap(self._agent.q_table)

        self._print_summary(episode_rewards, eval_path)

        return {
            "episode_rewards": episode_rewards,
            "eval_path": eval_path,
            "q_table": self._agent.q_table,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _print_summary(self, rewards: list[float], path: list[int]) -> None:
        """Print a human-readable summary to stdout."""
        print("\n" + "=" * 60)
        print("TRAINING COMPLETE")
        print("=" * 60)
        print(f"Episodes:          {len(rewards)}")
        print(f"Final ε:           {self._agent.epsilon:.4f}")
        print(f"Avg reward (last 100): {sum(rewards[-100:]) / 100:.2f}")
        print(f"\nGreedy eval path ({len(path) - 1} steps): {path}")
        print("\nQ-Table (rows=states, cols=actions [U,D,L,R]):")
        print(np.round(self._agent.q_table, 2))
        print("=" * 60)
