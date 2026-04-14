"""Unit tests for dronerl._sdk_helpers module functions."""

from __future__ import annotations

import logging
from types import SimpleNamespace

import pytest

from dronerl._sdk_helpers import (
    apply_grid_anchors,
    build_grid,
    find_first,
    make_config_ns,
    validate_config_version,
)
from dronerl.environment.grid import CellType, Grid

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def empty_grid() -> Grid:
    g = Grid(4, 4)
    return g


@pytest.fixture()
def sample_setup() -> dict:
    return {
        "version": "1.00",
        "grid": {"rows": 4, "cols": 4},
        "gui": {"fps": 30, "cell_size": 40, "window_title": "Test", "dashboard_width": 200},
    }


@pytest.fixture()
def sample_layout_ns() -> SimpleNamespace:
    ns = SimpleNamespace()
    ns.walls = []
    ns.traps = []
    ns.wind = []
    ns.goals = [[1, 3]]
    ns.start = [0, 0]
    ns.goal = [1, 3]
    return ns


# ---------------------------------------------------------------------------
# find_first
# ---------------------------------------------------------------------------


def test_find_first_returns_position_when_present(empty_grid: Grid) -> None:
    empty_grid.set_cell(2, 3, CellType.GOAL)
    assert find_first(empty_grid, CellType.GOAL) == (2, 3)


def test_find_first_returns_none_when_absent(empty_grid: Grid) -> None:
    assert find_first(empty_grid, CellType.TRAP) is None


def test_find_first_returns_first_occurrence(empty_grid: Grid) -> None:
    empty_grid.set_cell(1, 1, CellType.WALL)
    empty_grid.set_cell(3, 3, CellType.WALL)
    assert find_first(empty_grid, CellType.WALL) == (1, 1)


def test_find_first_start_cell(empty_grid: Grid) -> None:
    empty_grid.set_cell(0, 0, CellType.START)
    assert find_first(empty_grid, CellType.START) == (0, 0)


# ---------------------------------------------------------------------------
# build_grid
# ---------------------------------------------------------------------------


def test_build_grid_returns_grid_with_correct_dimensions(
    sample_setup: dict, sample_layout_ns: SimpleNamespace
) -> None:
    grid = build_grid(sample_setup, sample_layout_ns)
    assert grid.rows == 4
    assert grid.cols == 4


def test_build_grid_places_goal(
    sample_setup: dict, sample_layout_ns: SimpleNamespace
) -> None:
    grid = build_grid(sample_setup, sample_layout_ns)
    assert find_first(grid, CellType.GOAL) is not None


# ---------------------------------------------------------------------------
# make_config_ns
# ---------------------------------------------------------------------------


def test_make_config_ns_has_gui_attribute(sample_setup: dict) -> None:
    ns = make_config_ns(sample_setup)
    assert hasattr(ns, "gui")


def test_make_config_ns_has_grid_attribute(sample_setup: dict) -> None:
    ns = make_config_ns(sample_setup)
    assert hasattr(ns, "grid")


def test_make_config_ns_gui_fps(sample_setup: dict) -> None:
    ns = make_config_ns(sample_setup)
    assert ns.gui.fps == 30


def test_make_config_ns_grid_rows(sample_setup: dict) -> None:
    ns = make_config_ns(sample_setup)
    assert ns.grid.rows == 4


# ---------------------------------------------------------------------------
# validate_config_version
# ---------------------------------------------------------------------------


def test_validate_config_version_no_warning_on_match(caplog: pytest.LogCaptureFixture) -> None:
    log = logging.getLogger("test")
    with caplog.at_level(logging.WARNING, logger="test"):
        validate_config_version("1.00", "config/setup.json", "1.00", log)
    assert not any(r.levelno == logging.WARNING for r in caplog.records)


def test_validate_config_version_warns_on_mismatch(caplog: pytest.LogCaptureFixture) -> None:
    log = logging.getLogger("test")
    with caplog.at_level(logging.WARNING, logger="test"):
        validate_config_version("0.99", "config/setup.json", "1.00", log)
    assert any("mismatch" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# apply_grid_anchors
# ---------------------------------------------------------------------------


def test_apply_grid_anchors_uses_existing_start_and_goal(empty_grid: Grid) -> None:
    log = logging.getLogger("test")
    empty_grid.set_cell(1, 0, CellType.START)
    empty_grid.set_cell(3, 3, CellType.GOAL)
    start, goal = apply_grid_anchors(empty_grid, (0, 0), (2, 2), log)
    assert start == (1, 0)
    assert goal == (3, 3)


def test_apply_grid_anchors_restores_default_start(empty_grid: Grid) -> None:
    log = logging.getLogger("test")
    empty_grid.set_cell(3, 3, CellType.GOAL)
    start, goal = apply_grid_anchors(empty_grid, (0, 0), (2, 2), log)
    assert start == (0, 0)
    assert empty_grid.get_cell(0, 0) is CellType.START


def test_apply_grid_anchors_restores_default_goal(empty_grid: Grid) -> None:
    log = logging.getLogger("test")
    empty_grid.set_cell(0, 0, CellType.START)
    start, goal = apply_grid_anchors(empty_grid, (0, 0), (2, 2), log)
    assert goal == (2, 2)
    assert empty_grid.get_cell(2, 2) is CellType.GOAL


def test_apply_grid_anchors_warns_on_missing_start(
    empty_grid: Grid, caplog: pytest.LogCaptureFixture
) -> None:
    log = logging.getLogger("test")
    empty_grid.set_cell(3, 3, CellType.GOAL)
    with caplog.at_level(logging.WARNING, logger="test"):
        apply_grid_anchors(empty_grid, (0, 0), (2, 2), log)
    assert any("START" in r.message for r in caplog.records)


def test_apply_grid_anchors_warns_on_missing_goal(
    empty_grid: Grid, caplog: pytest.LogCaptureFixture
) -> None:
    log = logging.getLogger("test")
    empty_grid.set_cell(0, 0, CellType.START)
    with caplog.at_level(logging.WARNING, logger="test"):
        apply_grid_anchors(empty_grid, (0, 0), (2, 2), log)
    assert any("GOAL" in r.message for r in caplog.records)
