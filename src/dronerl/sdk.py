"""DroneRLSDK — single entry point for all business logic."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import numpy as np

from dronerl._sdk_helpers import (
    _SUPPORTED_CONFIG_VERSION,
    apply_grid_anchors,
    build_grid,
    make_config_ns,
    validate_config_version,
)
from dronerl.agent.agent import Agent
from dronerl.agent.policy import EpsilonGreedyPolicy
from dronerl.agent.q_table import QTable
from dronerl.constants import N_ACTIONS
from dronerl.environment.env import SmartCityEnv
from dronerl.environment.grid import Grid
from dronerl.environment.rewards import RewardCalculator, RewardConfig
from dronerl.environment.wind import WindZone
from dronerl.shared.config import ConfigLoader
from dronerl.shared.logger import get_logger

_DEFAULT_QT_PATH = Path(__file__).parent.parent.parent / "data" / "q_tables" / "brain.npy"


class DroneRLSDK:
    """Facade that wires together all DroneRL components.

    GUI and CLI layers must use only this class — no business logic outside.
    """

    def __init__(self, config_path: str = "config/setup.json") -> None:
        """Load configs and instantiate all components."""
        self._log = get_logger(__name__)
        loader = ConfigLoader()
        self._setup = loader.load_json(config_path, required_keys=["version", "grid", "gui"])
        validate_config_version(
            self._setup.get("version", ""), config_path, _SUPPORTED_CONFIG_VERSION, self._log
        )
        self._cfg = loader.load_yaml("config/settings.yaml", required_keys=["agent", "rewards"])
        self._grid: Grid = build_grid(self._setup, self._cfg.layout)  # type: ignore[attr-defined]
        a = self._cfg.agent  # type: ignore[attr-defined]
        rng = np.random.default_rng(int(a.seed))
        self._wind = WindZone(float(a.wind_drift_prob), rng)
        self._reward_calc = RewardCalculator(RewardConfig.from_namespace(self._cfg.rewards))
        layout = self._cfg.layout  # type: ignore[attr-defined]
        self._default_start: tuple = tuple(layout.start)
        self._default_goal: tuple = tuple(layout.goal)
        self._start: tuple = tuple(layout.start)
        self._goal: tuple = tuple(layout.goal)
        self._env = SmartCityEnv(
            self._grid, self._wind, self._reward_calc, self._start, self._goal
        )
        rows, cols = self._setup["grid"]["rows"], self._setup["grid"]["cols"]
        self._q_table = QTable(rows, cols, N_ACTIONS)
        policy = EpsilonGreedyPolicy(
            float(a.epsilon_start), float(a.epsilon_min),
            float(a.epsilon_decay), N_ACTIONS,
            np.random.default_rng(int(a.seed)),
        )
        self._agent = Agent(self._q_table, policy, float(a.alpha), float(a.gamma))
        self._max_steps = int(a.max_steps)
        self._episode_rewards: list[float] = []
        self._goals_reached: int = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_headless(self, n_episodes: int) -> list[float]:
        """Train without rendering. Returns list of per-episode rewards."""
        for ep in range(n_episodes):
            state = self._env.reset()
            total = 0.0
            for _ in range(self._max_steps):
                action = self._agent.select_action(state)
                ns, reward, done = self._env.step(action)
                self._agent.update(state, action, reward, ns, done)
                state, total = ns, total + reward
                if done:
                    if self._env.grid.get_cell(*state).name == "GOAL":
                        self._goals_reached += 1
                    break
            self._agent.end_episode()
            self._episode_rewards.append(total)
            if (ep + 1) % 100 == 0:
                self._log.info("Ep %d/%d  r=%.1f  ε=%.3f",
                               ep + 1, n_episodes, total, self._agent.epsilon)
        return list(self._episode_rewards)

    def run_gui(self) -> None:
        """Run the interactive Pygame training loop."""
        from dronerl._gui_runner import run_gui_loop
        run_gui_loop(self)

    def get_q_table(self) -> QTable:
        """Return the current Q-table."""
        return self._q_table

    def get_policy_map(self) -> dict[tuple, int]:
        """Return greedy action per (row, col) state."""
        return {(r, c): self._q_table.best_action(r, c)
                for r in range(self._grid.rows) for c in range(self._grid.cols)}

    def save_q_table(self, path: str | None = None) -> None:
        """Save Q-table to .npy file."""
        p = Path(path) if path else _DEFAULT_QT_PATH
        p.parent.mkdir(parents=True, exist_ok=True)
        self._q_table.save(p)

    def load_q_table(self, path: str | None = None) -> bool:
        """Load Q-table from .npy file. Returns True on success, False otherwise."""
        p = Path(path) if path else _DEFAULT_QT_PATH
        if not p.exists():
            self._log.warning("No saved brain at %s", p)
            return False
        try:
            self._q_table.load(p)
            self._log.info("Brain loaded from %s", p)
            return True
        except (ValueError, OSError) as exc:
            self._log.error("Failed to load brain: %s", exc)
            return False

    def launch_level_editor(self) -> None:
        """Open the interactive level editor (blocks until closed)."""
        import pygame

        from dronerl.gui.level_editor import LevelEditor

        cell = self._setup["gui"]["cell_size"]
        screen = pygame.display.set_mode(
            (self._grid.cols * cell + 240, self._grid.rows * cell + 28)
        )
        self._grid = LevelEditor(screen, self._grid, cell_size=cell).run()
        self._start, self._goal = apply_grid_anchors(
            self._grid, self._default_start, self._default_goal, self._log
        )
        self._env = SmartCityEnv(
            self._grid, self._wind, self._reward_calc, self._start, self._goal
        )
        self._log.info("Editor applied: start=%s goal=%s", self._start, self._goal)

    def get_training_stats(self) -> dict:
        """Return a snapshot of current training statistics."""
        rw = self._episode_rewards
        return {
            "episodes": len(rw),
            "goals_reached": self._goals_reached,
            "goal_rate": self._goals_reached / max(1, len(rw)),
            "last_reward": rw[-1] if rw else 0.0,
            "epsilon": self._agent.epsilon,
            "total_steps": self._agent.total_steps,
        }

    def get_config_ns(self) -> SimpleNamespace:
        """Return config namespace for Renderer and Dashboard."""
        return make_config_ns(self._setup)
