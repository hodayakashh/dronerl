"""Unit tests for dronerl.constants."""

from dronerl.constants import ACTION_DELTAS, N_ACTIONS, Action


def test_action_is_int_enum() -> None:
    assert issubclass(Action, int)


def test_action_enum_values() -> None:
    assert Action.UP == 0
    assert Action.DOWN == 1
    assert Action.LEFT == 2
    assert Action.RIGHT == 3


def test_n_actions_equals_4() -> None:
    assert N_ACTIONS == 4


def test_delta_keys_cover_all_actions() -> None:
    assert set(ACTION_DELTAS.keys()) == set(Action)


def test_delta_up_is_negative_row() -> None:
    dr, dc = ACTION_DELTAS[Action.UP]
    assert dr == -1 and dc == 0


def test_delta_down_is_positive_row() -> None:
    dr, dc = ACTION_DELTAS[Action.DOWN]
    assert dr == 1 and dc == 0


def test_delta_left_is_negative_col() -> None:
    dr, dc = ACTION_DELTAS[Action.LEFT]
    assert dr == 0 and dc == -1


def test_delta_right_is_positive_col() -> None:
    dr, dc = ACTION_DELTAS[Action.RIGHT]
    assert dr == 0 and dc == 1
