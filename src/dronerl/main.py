"""CLI entry point for DroneRL."""

from __future__ import annotations

import argparse
import sys


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Argument list (defaults to sys.argv[1:]).

    Returns:
        Parsed namespace with all flags.
    """
    parser = argparse.ArgumentParser(
        prog="dronerl",
        description="DroneRL — Smart City Drone Delivery via Q-Learning",
    )
    parser.add_argument(
        "--config", default="config/setup.json",
        metavar="PATH", help="Path to setup.json (default: config/setup.json)",
    )
    parser.add_argument(
        "--headless", action="store_true",
        help="Run training without GUI",
    )
    parser.add_argument(
        "--episodes", type=int, default=1000,
        metavar="N", help="Number of training episodes (headless mode)",
    )
    parser.add_argument(
        "--edit", action="store_true",
        help="Open the interactive level editor",
    )
    parser.add_argument(
        "--save-qt", metavar="PATH",
        help="Save Q-table to this .npy file after training",
    )
    parser.add_argument(
        "--load-qt", metavar="PATH",
        help="Load Q-table from this .npy file before running",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """DroneRL CLI entry point.

    Dispatches to headless training, GUI loop, or level editor
    depending on the supplied flags.

    Args:
        argv: Optional argument list (uses sys.argv when None).
    """
    args = parse_args(argv)

    from dronerl.sdk import DroneRLSDK

    sdk = DroneRLSDK(config_path=args.config)

    if args.load_qt:
        sdk.load_q_table(args.load_qt)

    try:
        if args.edit:
            sdk.launch_level_editor()
        elif args.headless:
            rewards = sdk.run_headless(args.episodes)
            stats = sdk.get_training_stats()
            print(f"Training complete: {stats['episodes']} episodes, "
                  f"goal rate {stats['goal_rate']:.1%}, "
                  f"last reward {rewards[-1]:.1f}")
        else:
            sdk.run_gui()
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        sys.exit(0)

    if args.save_qt:
        sdk.save_q_table(args.save_qt)

    stats = sdk.get_training_stats()
    print(f"Sessions stats: episodes={stats['episodes']}, "
          f"goals={stats['goals_reached']}, ε={stats['epsilon']:.4f}")


if __name__ == "__main__":
    main()
