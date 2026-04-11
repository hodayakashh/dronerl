"""Unit tests for dronerl.shared.version."""

import json
from pathlib import Path

from dronerl.shared.version import VERSION


def test_version_is_string() -> None:
    assert isinstance(VERSION, str)


def test_version_string_format() -> None:
    # Must be in "X.XX" format
    parts = VERSION.split(".")
    assert len(parts) == 2
    assert parts[0].isdigit()
    assert parts[1].isdigit()


def test_version_matches_setup_json() -> None:
    setup = json.loads(Path("config/setup.json").read_text(encoding="utf-8"))
    assert setup["version"] == VERSION


def test_version_matches_rate_limits_json() -> None:
    rl = json.loads(Path("config/rate_limits.json").read_text(encoding="utf-8"))
    assert rl["version"] == VERSION
