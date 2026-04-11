"""Unit tests for dronerl.environment.grid."""

import pytest

from dronerl.environment.grid import CellType, Grid

# ---------------------------------------------------------------------------
# Grid construction
# ---------------------------------------------------------------------------


def test_grid_init_all_empty() -> None:
    g = Grid(3, 4)
    for r in range(3):
        for c in range(4):
            assert g.get_cell(r, c) is CellType.EMPTY


def test_grid_rows_cols_properties() -> None:
    g = Grid(5, 7)
    assert g.rows == 5
    assert g.cols == 7


def test_grid_invalid_rows_raises() -> None:
    with pytest.raises(ValueError):
        Grid(0, 5)


def test_grid_invalid_cols_raises() -> None:
    with pytest.raises(ValueError):
        Grid(5, 0)


def test_grid_negative_dims_raises() -> None:
    with pytest.raises(ValueError):
        Grid(-1, -1)


# ---------------------------------------------------------------------------
# set_cell / get_cell
# ---------------------------------------------------------------------------


def test_set_and_get_cell() -> None:
    g = Grid(4, 4)
    g.set_cell(1, 2, CellType.WALL)
    assert g.get_cell(1, 2) is CellType.WALL


def test_set_cell_all_types() -> None:
    g = Grid(6, 1)
    for i, ct in enumerate(CellType):
        g.set_cell(i, 0, ct)
        assert g.get_cell(i, 0) is ct


def test_get_cell_out_of_bounds_raises() -> None:
    g = Grid(3, 3)
    with pytest.raises(IndexError):
        g.get_cell(5, 0)


def test_set_cell_out_of_bounds_raises() -> None:
    g = Grid(3, 3)
    with pytest.raises(IndexError):
        g.set_cell(3, 3, CellType.WALL)


# ---------------------------------------------------------------------------
# in_bounds
# ---------------------------------------------------------------------------


def test_in_bounds_valid() -> None:
    g = Grid(5, 5)
    assert g.in_bounds(0, 0) is True
    assert g.in_bounds(4, 4) is True


def test_in_bounds_negative() -> None:
    g = Grid(5, 5)
    assert g.in_bounds(-1, 0) is False


def test_in_bounds_exceeds_dims() -> None:
    g = Grid(5, 5)
    assert g.in_bounds(5, 0) is False
    assert g.in_bounds(0, 5) is False


# ---------------------------------------------------------------------------
# is_walkable
# ---------------------------------------------------------------------------


def test_empty_cell_is_walkable() -> None:
    g = Grid(3, 3)
    assert g.is_walkable(1, 1) is True


def test_wall_cell_not_walkable() -> None:
    g = Grid(3, 3)
    g.set_cell(1, 1, CellType.WALL)
    assert g.is_walkable(1, 1) is False


def test_trap_cell_is_walkable() -> None:
    g = Grid(3, 3)
    g.set_cell(0, 0, CellType.TRAP)
    assert g.is_walkable(0, 0) is True


def test_out_of_bounds_not_walkable() -> None:
    g = Grid(3, 3)
    assert g.is_walkable(10, 10) is False


# ---------------------------------------------------------------------------
# load_from_dict
# ---------------------------------------------------------------------------


def test_load_from_dict_walls() -> None:
    g = Grid(5, 5)
    g.load_from_dict({"walls": [[1, 1], [2, 2]]})
    assert g.get_cell(1, 1) is CellType.WALL
    assert g.get_cell(2, 2) is CellType.WALL


def test_load_from_dict_goal_and_start() -> None:
    g = Grid(5, 5)
    g.load_from_dict({"goal": [4, 4], "start": [0, 0]})
    assert g.get_cell(4, 4) is CellType.GOAL
    assert g.get_cell(0, 0) is CellType.START


def test_load_from_dict_traps_and_winds() -> None:
    g = Grid(5, 5)
    g.load_from_dict({"traps": [[1, 0]], "winds": [[2, 0]]})
    assert g.get_cell(1, 0) is CellType.TRAP
    assert g.get_cell(2, 0) is CellType.WIND


def test_load_from_dict_empty_dict_leaves_empty() -> None:
    g = Grid(3, 3)
    g.load_from_dict({})
    assert g.get_cell(1, 1) is CellType.EMPTY
