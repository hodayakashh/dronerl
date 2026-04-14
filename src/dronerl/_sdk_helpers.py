"""Private helper functions for DroneRLSDK — keeps sdk.py within the 150-line limit."""

from __future__ import annotations

import logging
from types import SimpleNamespace

from dronerl.environment.env import SmartCityEnv  # noqa: F401 (re-exported for callers)
from dronerl.environment.grid import CellType, Grid

_SUPPORTED_CONFIG_VERSION = "1.00"


def build_grid(setup: dict, layout_ns: SimpleNamespace) -> Grid:
    """Construct a Grid from setup.json dimensions and settings.yaml layout.

    Why: centralises grid construction so sdk.py and tests can share the same logic.

    Args:
        setup: Parsed setup.json dict with a "grid" sub-dict (rows, cols).
        layout_ns: Namespace from settings.yaml containing cell-type lists.

    Returns:
        Fully populated Grid instance.
    """
    rows, cols = setup["grid"]["rows"], setup["grid"]["cols"]
    g = Grid(rows, cols)
    g.load_from_dict(vars(layout_ns))
    return g


def find_first(grid: Grid, cell_type: CellType) -> tuple[int, int] | None:
    """Return the first (row, col) containing *cell_type*, or None if absent.

    Why: scanning logic is shared between sdk.py and the anchor-restoration helper.

    Args:
        grid: Grid to search.
        cell_type: The CellType to locate.

    Returns:
        (row, col) of the first matching cell, or None.
    """
    for r in range(grid.rows):
        for c in range(grid.cols):
            if grid.get_cell(r, c) is cell_type:
                return (r, c)
    return None


def make_config_ns(setup: dict) -> SimpleNamespace:
    """Return a SimpleNamespace of gui/grid config for Renderer and Dashboard.

    Why: extracted to allow both sdk.py and gui_runner to share the same builder.

    Args:
        setup: Parsed setup.json dict.

    Returns:
        Namespace with .gui and .grid sub-namespaces.
    """
    ns = SimpleNamespace()
    ns.gui = SimpleNamespace(**setup["gui"])
    ns.grid = SimpleNamespace(**setup["grid"])
    return ns


def validate_config_version(
    version: str,
    path: str,
    supported: str,
    log: logging.Logger,
) -> None:
    """Warn if the config file version does not match the expected SDK version.

    Why: version mismatches can cause subtle runtime errors; early warning prevents them.

    Args:
        version: Version string read from the config file.
        path: Config file path (for the warning message).
        supported: The version string this SDK was built against.
        log: Logger to write the warning or debug message to.
    """
    from dronerl.shared.version import VERSION

    if str(version) != supported:
        log.warning(
            "Config version mismatch: '%s' in %s (SDK expects '%s'). "
            "Some settings may be ignored.",
            version,
            path,
            supported,
        )
    else:
        log.debug("Config version %s OK (SDK=%s)", version, VERSION)


def apply_grid_anchors(
    grid: Grid,
    default_start: tuple,
    default_goal: tuple,
    log: logging.Logger,
) -> tuple[tuple, tuple]:
    """Resolve START/GOAL positions from an edited grid; restore defaults if missing.

    Why: after the level editor runs, the grid may lack START or GOAL cells; this
    helper keeps sdk.py's launch_level_editor concise while guaranteeing valid state.

    Args:
        grid: The edited Grid (mutated in-place if anchors are missing).
        default_start: Fallback (row, col) for START if not found in grid.
        default_goal: Fallback (row, col) for GOAL if not found in grid.
        log: Logger for warning messages.

    Returns:
        (resolved_start, resolved_goal) tuples.
    """
    edited_start = find_first(grid, CellType.START)
    edited_goal = find_first(grid, CellType.GOAL)
    if edited_start is not None:
        start: tuple = edited_start
    else:
        start = default_start
        grid.set_cell(*default_start, CellType.START)
        log.warning("Editor grid had no START; restored default start=%s", default_start)
    if edited_goal is not None:
        goal: tuple = edited_goal
    else:
        goal = default_goal
        grid.set_cell(*default_goal, CellType.GOAL)
        log.warning("Editor grid had no GOAL; restored default goal=%s", default_goal)
    return start, goal
