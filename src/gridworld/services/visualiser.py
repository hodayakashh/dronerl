"""Visualiser — reward curve and Q-table heatmap plots."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

from gridworld.constants import Action

logger = logging.getLogger(__name__)

_ACTION_NAMES = [a.name for a in Action]


class Visualiser:
    """Generates and saves training visualisations.

    Produces:
    1. Reward-per-episode learning curve (with rolling average).
    2. Q-table heatmaps — one subplot per action.

    Input:  episode rewards (List[float]), Q-table (np.ndarray)
    Output: PNG files saved to config["output"]["results_dir"]
    Setup:  results_dir, save_plots, grid rows/cols (from config)
    """

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialise paths from config.

        Args:
            config: Full parsed config (from ConfigManager.raw).
        """
        output_cfg = config["output"]
        self._results_dir = Path(output_cfg["results_dir"])
        self._save = bool(output_cfg["save_plots"])
        self._n_rows: int = config["grid"]["rows"]
        self._n_cols: int = config["grid"]["cols"]
        self._results_dir.mkdir(parents=True, exist_ok=True)

    def plot_reward_curve(self, rewards: list[float], window: int = 50) -> None:
        """Plot total reward per episode with a rolling-average overlay.

        Args:
            rewards: List of per-episode total rewards from training.
            window: Rolling-average window size.
        """
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(rewards, alpha=0.4, label="Per-episode reward")

        if len(rewards) >= window:
            rolling = np.convolve(rewards, np.ones(window) / window, mode="valid")
            ax.plot(range(window - 1, len(rewards)), rolling, label=f"Rolling avg ({window})")

        ax.set_xlabel("Episode")
        ax.set_ylabel("Total reward")
        ax.set_title("Q-Learning — Reward per Episode")
        ax.legend()
        fig.tight_layout()
        self._save_fig(fig, "reward_curve.png")
        plt.close(fig)

    def plot_q_table_heatmap(self, q_table: np.ndarray) -> None:
        """Plot Q-values as a 2D heatmap for each of the 4 actions.

        Args:
            q_table: Array of shape (n_states, n_actions).
        """
        fig, axes = plt.subplots(1, 4, figsize=(16, 4))
        n_actions = q_table.shape[1]

        for idx in range(n_actions):
            grid = q_table[:, idx].reshape(self._n_rows, self._n_cols)
            im = axes[idx].imshow(grid, cmap="RdYlGn", aspect="auto")
            axes[idx].set_title(f"Q — {_ACTION_NAMES[idx]}")
            axes[idx].set_xlabel("col")
            axes[idx].set_ylabel("row")
            fig.colorbar(im, ax=axes[idx], fraction=0.046, pad=0.04)

        fig.suptitle("Q-Table Heatmaps (after training)")
        fig.tight_layout()
        self._save_fig(fig, "q_table_heatmap.png")
        plt.close(fig)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _save_fig(self, fig: plt.Figure, filename: str) -> None:
        """Save figure to results_dir if save_plots is enabled."""
        if not self._save:
            return
        out_path = self._results_dir / filename
        fig.savefig(out_path, dpi=150, bbox_inches="tight")
        logger.info("Saved plot: %s", out_path)
