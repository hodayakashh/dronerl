"""Unit tests for dronerl.agent.q_table."""

from pathlib import Path

import numpy as np
import pytest

from dronerl.agent.q_table import QTable


@pytest.fixture()
def qt() -> QTable:
    return QTable(rows=4, cols=4, n_actions=4)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_qtable_init_all_zeros(qt: QTable) -> None:
    for r in range(4):
        for c in range(4):
            assert np.all(qt.get(r, c) == 0.0)


def test_qtable_shape_correct(qt: QTable) -> None:
    assert qt.shape == (4, 4, 4)


def test_qtable_invalid_rows_raises() -> None:
    with pytest.raises(ValueError):
        QTable(0, 4, 4)


def test_qtable_invalid_cols_raises() -> None:
    with pytest.raises(ValueError):
        QTable(4, 0, 4)


def test_qtable_invalid_actions_raises() -> None:
    with pytest.raises(ValueError):
        QTable(4, 4, 0)


# ---------------------------------------------------------------------------
# get / set_value
# ---------------------------------------------------------------------------


def test_qtable_set_and_get_value(qt: QTable) -> None:
    qt.set_value(1, 2, 3, 7.5)
    assert qt.get_value(1, 2, 3) == pytest.approx(7.5)


def test_qtable_get_returns_slice(qt: QTable) -> None:
    qt.set_value(0, 0, 2, 3.14)
    arr = qt.get(0, 0)
    assert arr[2] == pytest.approx(3.14)
    assert len(arr) == 4


def test_qtable_set_value_does_not_affect_other_cells(qt: QTable) -> None:
    qt.set_value(2, 2, 1, 9.9)
    assert qt.get_value(0, 0, 1) == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# best_action / max_value
# ---------------------------------------------------------------------------


def test_qtable_best_action_argmax(qt: QTable) -> None:
    qt.set_value(1, 1, 2, 5.0)
    assert qt.best_action(1, 1) == 2


def test_qtable_max_value_correct(qt: QTable) -> None:
    qt.set_value(3, 3, 0, 10.0)
    qt.set_value(3, 3, 1, 5.0)
    assert qt.max_value(3, 3) == pytest.approx(10.0)


def test_qtable_max_value_all_zeros(qt: QTable) -> None:
    assert qt.max_value(0, 0) == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# reset
# ---------------------------------------------------------------------------


def test_qtable_reset_zeros_all(qt: QTable) -> None:
    qt.set_value(0, 0, 0, 99.0)
    qt.reset()
    assert qt.get_value(0, 0, 0) == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# save / load
# ---------------------------------------------------------------------------


def test_qtable_save_creates_file(qt: QTable, tmp_path: Path) -> None:
    p = tmp_path / "qt.npy"
    qt.save(p)
    assert p.exists()


def test_qtable_load_round_trip(qt: QTable, tmp_path: Path) -> None:
    qt.set_value(2, 3, 1, 42.0)
    p = tmp_path / "qt.npy"
    qt.save(p)
    qt2 = QTable(4, 4, 4)
    qt2.load(p)
    assert qt2.get_value(2, 3, 1) == pytest.approx(42.0)


def test_qtable_load_wrong_shape_raises(qt: QTable, tmp_path: Path) -> None:
    wrong = QTable(3, 3, 4)
    p = tmp_path / "wrong.npy"
    wrong.save(p)
    with pytest.raises(ValueError, match="Shape mismatch"):
        qt.load(p)


# ---------------------------------------------------------------------------
# __repr__
# ---------------------------------------------------------------------------


def test_qtable_repr(qt: QTable) -> None:
    r = repr(qt)
    assert "QTable" in r
    assert "rows=4" in r
