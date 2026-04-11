"""Unit tests for dronerl.shared.config.ConfigLoader."""

import json
import textwrap
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from dronerl.shared.config import ConfigError, ConfigLoader


@pytest.fixture()
def loader() -> ConfigLoader:
    return ConfigLoader()


@pytest.fixture()
def tmp_yaml(tmp_path: Path) -> Path:
    data = {"agent": {"alpha": 0.1, "gamma": 0.95}, "rewards": {"step": -1}}
    p = tmp_path / "settings.yaml"
    p.write_text(yaml.dump(data), encoding="utf-8")
    return p


@pytest.fixture()
def tmp_json(tmp_path: Path) -> Path:
    data = {"version": "1.00", "app_name": "DroneRL"}
    p = tmp_path / "setup.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


def test_load_yaml_returns_namespace(loader: ConfigLoader, tmp_yaml: Path) -> None:
    result = loader.load_yaml(tmp_yaml)
    assert isinstance(result, SimpleNamespace)


def test_load_yaml_nested_accessible_via_dot(loader: ConfigLoader, tmp_yaml: Path) -> None:
    result = loader.load_yaml(tmp_yaml)
    assert result.agent.alpha == pytest.approx(0.1)


def test_load_yaml_missing_key_raises(loader: ConfigLoader, tmp_yaml: Path) -> None:
    with pytest.raises(ConfigError, match="Missing required key"):
        loader.load_yaml(tmp_yaml, required_keys=["nonexistent"])


def test_load_yaml_invalid_path_raises(loader: ConfigLoader) -> None:
    with pytest.raises(ConfigError, match="not found"):
        loader.load_yaml("nonexistent/path/settings.yaml")


def test_load_yaml_invalid_content_raises(loader: ConfigLoader, tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text("key: [unclosed", encoding="utf-8")
    with pytest.raises(ConfigError, match="Invalid YAML"):
        loader.load_yaml(bad)


def test_load_json_returns_dict(loader: ConfigLoader, tmp_json: Path) -> None:
    result = loader.load_json(tmp_json)
    assert isinstance(result, dict)


def test_load_json_value_correct(loader: ConfigLoader, tmp_json: Path) -> None:
    result = loader.load_json(tmp_json)
    assert result["app_name"] == "DroneRL"


def test_load_json_missing_key_raises(loader: ConfigLoader, tmp_json: Path) -> None:
    with pytest.raises(ConfigError, match="Missing required key"):
        loader.load_json(tmp_json, required_keys=["missing_key"])


def test_load_json_invalid_path_raises(loader: ConfigLoader) -> None:
    with pytest.raises(ConfigError, match="not found"):
        loader.load_json("nonexistent/setup.json")


def test_load_json_invalid_content_raises(loader: ConfigLoader, tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(ConfigError, match="Invalid JSON"):
        loader.load_json(bad)


def test_load_real_settings_yaml(loader: ConfigLoader) -> None:
    result = loader.load_yaml("config/settings.yaml", required_keys=["agent", "rewards"])
    assert hasattr(result, "agent")
    assert hasattr(result, "rewards")


def test_load_real_setup_json(loader: ConfigLoader) -> None:
    result = loader.load_json("config/setup.json", required_keys=["version"])
    assert result["version"] == "1.00"
