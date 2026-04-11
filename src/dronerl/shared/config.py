"""Configuration loader — reads and validates YAML and JSON config files."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import yaml

from dronerl.shared.version import VERSION

logger = logging.getLogger(__name__)

SUPPORTED_VERSION: str = VERSION


class ConfigError(Exception):
    """Raised when a config file is invalid or incompatible."""


class ConfigLoader:
    """Load and validate YAML and JSON configuration files.

    All application parameters must be read through this class.
    Raises ConfigError on missing required fields or version mismatch.
    """

    def load_yaml(self, path: str | Path, required_keys: list[str] | None = None) -> SimpleNamespace:
        """Load a YAML config file and return a SimpleNamespace.

        Args:
            path: Path to the YAML file.
            required_keys: Top-level keys that must be present.

        Returns:
            SimpleNamespace with config values accessible via dot notation.

        Raises:
            ConfigError: If file not found, invalid YAML, or missing keys.
        """
        file_path = Path(path)
        if not file_path.exists():
            raise ConfigError(f"Config file not found: {file_path}")
        with file_path.open(encoding="utf-8") as fh:
            try:
                data: dict[str, Any] = yaml.safe_load(fh) or {}
            except yaml.YAMLError as exc:
                raise ConfigError(f"Invalid YAML in {file_path}: {exc}") from exc
        if required_keys:
            self._check_required(data, required_keys, file_path)
        logger.info("YAML config loaded from %s", file_path)
        return self._to_namespace(data)

    def load_json(self, path: str | Path, required_keys: list[str] | None = None) -> dict[str, Any]:
        """Load a JSON config file and return a dict.

        Args:
            path: Path to the JSON file.
            required_keys: Top-level keys that must be present.

        Returns:
            Parsed JSON as a plain dict.

        Raises:
            ConfigError: If file not found, invalid JSON, or missing keys.
        """
        file_path = Path(path)
        if not file_path.exists():
            raise ConfigError(f"Config file not found: {file_path}")
        with file_path.open(encoding="utf-8") as fh:
            try:
                data: dict[str, Any] = json.load(fh)
            except json.JSONDecodeError as exc:
                raise ConfigError(f"Invalid JSON in {file_path}: {exc}") from exc
        if required_keys:
            self._check_required(data, required_keys, file_path)
        logger.info("JSON config loaded from %s", file_path)
        return data

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _check_required(
        self, data: dict[str, Any], keys: list[str], path: Path
    ) -> None:
        """Raise ConfigError if any required key is absent."""
        for key in keys:
            if key not in data:
                raise ConfigError(f"Missing required key '{key}' in {path}")

    def _to_namespace(self, data: dict[str, Any]) -> SimpleNamespace:
        """Recursively convert a dict to a SimpleNamespace."""
        ns = SimpleNamespace()
        for key, value in data.items():
            if isinstance(value, dict):
                setattr(ns, key, self._to_namespace(value))
            else:
                setattr(ns, key, value)
        return ns
