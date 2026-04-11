"""Centralised logging setup for the dronerl package."""

from __future__ import annotations

import json
import logging
import logging.config
from pathlib import Path

_CONFIG_PATH = Path("config/logging_config.json")
_CONFIGURED: bool = False


def get_logger(name: str) -> logging.Logger:
    """Return a logger configured from config/logging_config.json.

    Reads level and handlers from the JSON config on first call.
    Subsequent calls reuse the already-configured logging system.
    Ensures the log directory exists before attaching a FileHandler.

    Args:
        name: Logger name, typically __name__ of the calling module.

    Returns:
        A standard :class:`logging.Logger` instance.
    """
    global _CONFIGURED  # noqa: PLW0603
    if not _CONFIGURED:
        _apply_config()
        _CONFIGURED = True
    return logging.getLogger(name)


def _apply_config() -> None:
    """Load logging_config.json and apply it via dictConfig."""
    if not _CONFIG_PATH.exists():
        logging.basicConfig(level=logging.INFO)
        return
    with _CONFIG_PATH.open(encoding="utf-8") as fh:
        cfg = json.load(fh)
    _ensure_log_dirs(cfg)
    logging.config.dictConfig(cfg)


def _ensure_log_dirs(cfg: dict) -> None:
    """Create parent directories for any FileHandler filenames."""
    handlers = cfg.get("handlers", {})
    for handler in handlers.values():
        filename = handler.get("filename")
        if filename:
            Path(filename).parent.mkdir(parents=True, exist_ok=True)
