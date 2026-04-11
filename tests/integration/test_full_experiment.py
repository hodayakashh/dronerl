"""Integration tests — full experiment pipeline via GridWorldSDK."""

from __future__ import annotations

from pathlib import Path

from gridworld.sdk.sdk import GridWorldSDK


def test_experiment_runs_without_error(config_file: Path) -> None:
    """The full run_experiment() call must complete without raising."""
    sdk = GridWorldSDK(config_file)
    results = sdk.run_experiment()
    assert "episode_rewards" in results
    assert "eval_path" in results
    assert "q_table" in results


def test_episode_rewards_length(config_file: Path, sample_config: dict) -> None:
    """episode_rewards must contain exactly config.training.episodes entries."""
    sdk = GridWorldSDK(config_file)
    results = sdk.run_experiment()
    assert len(results["episode_rewards"]) == sample_config["training"]["episodes"]


def test_q_table_shape(config_file: Path, sample_config: dict) -> None:
    """Q-table shape must be (n_states, 4) = (rows*cols, 4)."""
    sdk = GridWorldSDK(config_file)
    results = sdk.run_experiment()
    rows = sample_config["grid"]["rows"]
    cols = sample_config["grid"]["cols"]
    assert results["q_table"].shape == (rows * cols, 4)


def test_eval_path_ends_at_goal(config_file: Path, sample_config: dict) -> None:
    """Greedy evaluation path must end at the goal state."""
    sdk = GridWorldSDK(config_file)
    results = sdk.run_experiment()
    goal_row, goal_col = sample_config["grid"]["goal"]
    cols = sample_config["grid"]["cols"]
    goal_state = goal_row * cols + goal_col
    assert results["eval_path"][-1] == goal_state


def test_result_files_created(tmp_path: Path, sample_config: dict) -> None:
    """Both PNG plots must be saved when save_plots=True."""
    import json

    sample_config["output"]["save_plots"] = True
    sample_config["output"]["results_dir"] = str(tmp_path)
    cfg_path = tmp_path / "setup.json"
    with cfg_path.open("w") as fh:
        json.dump(sample_config, fh)

    sdk = GridWorldSDK(cfg_path)
    sdk.run_experiment()

    assert (tmp_path / "reward_curve.png").exists()
    assert (tmp_path / "q_table_heatmap.png").exists()
