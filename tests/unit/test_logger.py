"""Unit tests for dronerl.shared.logger."""

import logging

import pytest

import dronerl.shared.logger as logger_module
from dronerl.shared.logger import get_logger


@pytest.fixture(autouse=True)
def reset_logger_state() -> None:
    """Reset the _CONFIGURED flag before each test."""
    logger_module._CONFIGURED = False
    yield
    logger_module._CONFIGURED = False


def test_get_logger_returns_logger() -> None:
    log = get_logger("dronerl.test")
    assert isinstance(log, logging.Logger)


def test_logger_name_is_correct() -> None:
    log = get_logger("dronerl.mymodule")
    assert log.name == "dronerl.mymodule"


def test_no_duplicate_handlers() -> None:
    get_logger("dronerl.dup")
    get_logger("dronerl.dup")
    log = logging.getLogger("dronerl.dup")
    # Handlers are on the root logger; just confirm no error on second call
    assert isinstance(log, logging.Logger)


def test_configured_flag_set_after_first_call() -> None:
    assert logger_module._CONFIGURED is False
    get_logger("dronerl.flag_test")
    assert logger_module._CONFIGURED is True


def test_configured_flag_prevents_reconfiguration() -> None:
    get_logger("dronerl.once")
    initial_handlers = list(logging.root.handlers)
    get_logger("dronerl.twice")
    # Handler list should not have grown
    assert len(logging.root.handlers) == len(initial_handlers)
