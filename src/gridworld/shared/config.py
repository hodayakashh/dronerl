"""Configuration manager — loads and validates config/setup.json."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from gridworld.shared.version import VERSION

logger = logging.getLogger(__name__)

SUPPORTED_CONFIG_VERSION = VERSION


class ConfigManager:
    """Load, validate, and expose configuration from a JSON file.

    All application parameters must be read through this class.
    Raises ValueError if the config version is incompatible.
    """

    def __init__(self, config_path: str | Path) -> None:
        """Load and validate the config file.

        Args:
            config_path: Path to setup.json (absolute or relative to CWD).
        """
        self._path = Path(config_path)
        self._data: dict[str, Any] = self._load()
        self._validate_version()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, key: str, default: Any = None) -> Any:
        """Return a top-level config value by key.

        Args:
            key: Top-level JSON key.
            default: Fallback if key is absent.
        """
        return self._data.get(key, default)

    @property
    def raw(self) -> dict[str, Any]:
        """Return the full config dict (read-only view)."""
        return dict(self._data)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load(self) -> dict[str, Any]:
        """Read and parse the JSON config file."""
        if not self._path.exists():
            raise FileNotFoundError(f"Config file not found: {self._path}")
        with self._path.open(encoding="utf-8") as fh:
            data = json.load(fh)
        logger.info("Config loaded from %s", self._path)
        return data

    def _validate_version(self) -> None:
        """Ensure the config file version matches the supported version."""
        cfg_version = self._data.get("version", "")
        if cfg_version != SUPPORTED_CONFIG_VERSION:
            raise ValueError(
                f"Config version mismatch: file='{cfg_version}', "
                f"supported='{SUPPORTED_CONFIG_VERSION}'"
            )
