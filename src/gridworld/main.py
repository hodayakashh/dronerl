"""CLI entry point for the GridWorld Q-Learning experiment."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from gridworld.constants import DEFAULT_CONFIG_PATH
from gridworld.sdk.sdk import GridWorldSDK


def _parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="GridWorld Q-Learning Agent — BIU RL Assignment 01"
    )
    parser.add_argument(
        "--config",
        default=os.environ.get("GRIDWORLD_CONFIG_PATH", DEFAULT_CONFIG_PATH),
        help="Path to setup.json (default: config/setup.json)",
    )
    return parser.parse_args()


def main() -> None:
    """Run the GridWorld Q-Learning experiment from the command line."""
    args = _parse_args()
    config_path = Path(args.config)
    sdk = GridWorldSDK(config_path)
    sdk.run_experiment()


if __name__ == "__main__":
    main()
