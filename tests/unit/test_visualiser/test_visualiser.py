"""Unit tests for Visualiser."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from gridworld.services.visualiser import Visualiser

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

VIS_CONFIG: dict = {
    "grid": {"rows": 3, "cols": 3},
    "output": {"results_dir": "", "save_plots": True},
}


@pytest.fixture()
def tmp_visualiser(tmp_path: Path) -> Visualiser:
    """Visualiser writing to a temporary directory."""
    cfg = {**VIS_CONFIG, "output": {"results_dir": str(tmp_path), "save_plots": True}}
    return Visualiser(cfg)


@pytest.fixture()
def no_save_visualiser(tmp_path: Path) -> Visualiser:
    """Visualiser with save_plots=False (should not write files)."""
    cfg = {**VIS_CONFIG, "output": {"results_dir": str(tmp_path), "save_plots": False}}
    return Visualiser(cfg)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_plot_reward_curve_saves_file(tmp_visualiser: Visualiser, tmp_path: Path) -> None:
    """plot_reward_curve() must save reward_curve.png to results_dir."""
    rewards = list(range(100))
    tmp_visualiser.plot_reward_curve(rewards)
    assert (tmp_path / "reward_curve.png").exists()


def test_plot_q_heatmap_saves_file(tmp_visualiser: Visualiser, tmp_path: Path) -> None:
    """plot_q_table_heatmap() must save q_table_heatmap.png to results_dir."""
    q_table = np.zeros((9, 4))
    tmp_visualiser.plot_q_table_heatmap(q_table)
    assert (tmp_path / "q_table_heatmap.png").exists()


def test_no_save_does_not_create_files(no_save_visualiser: Visualiser, tmp_path: Path) -> None:
    """When save_plots=False, no files must be written."""
    no_save_visualiser.plot_reward_curve(list(range(10)))
    no_save_visualiser.plot_q_table_heatmap(np.zeros((9, 4)))
    assert not list(tmp_path.glob("*.png"))


def test_reward_curve_short_rewards(tmp_visualiser: Visualiser, tmp_path: Path) -> None:
    """plot_reward_curve() with fewer rewards than the window must not crash."""
    tmp_visualiser.plot_reward_curve([1.0, 2.0, 3.0], window=50)
    assert (tmp_path / "reward_curve.png").exists()
