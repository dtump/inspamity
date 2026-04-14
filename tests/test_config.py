import pytest

from email_utils import config as config_module
from email_utils.config import load_config


def test_load_config_from_local(tmp_path, monkeypatch):
    """Config loads from local path when system path doesn't exist."""
    config_file = tmp_path / "config.ini"
    config_file.write_text(
        "[anthropic]\napi_key = test-key-123\nmodel = claude-haiku-4-5-latest\ntimeout = 15.0\n"
    )

    monkeypatch.setattr(config_module, "SYSTEM_CONFIG_PATH", tmp_path / "nonexistent.ini")
    monkeypatch.setattr(config_module, "LOCAL_CONFIG_PATH", config_file)

    cfg = load_config()
    assert cfg.get("anthropic", "api_key") == "test-key-123"
    assert cfg.get("anthropic", "model") == "claude-haiku-4-5-latest"
    assert cfg.getfloat("anthropic", "timeout") == 15.0


def test_load_config_system_takes_priority(tmp_path, monkeypatch):
    """System config is preferred over local config."""
    system_file = tmp_path / "system.ini"
    system_file.write_text("[anthropic]\napi_key = system-key\n")

    local_file = tmp_path / "local.ini"
    local_file.write_text("[anthropic]\napi_key = local-key\n")

    monkeypatch.setattr(config_module, "SYSTEM_CONFIG_PATH", system_file)
    monkeypatch.setattr(config_module, "LOCAL_CONFIG_PATH", local_file)

    cfg = load_config()
    assert cfg.get("anthropic", "api_key") == "system-key"


def test_load_config_missing(tmp_path, monkeypatch):
    """FileNotFoundError when no config exists."""
    monkeypatch.setattr(config_module, "SYSTEM_CONFIG_PATH", tmp_path / "nope1.ini")
    monkeypatch.setattr(config_module, "LOCAL_CONFIG_PATH", tmp_path / "nope2.ini")

    with pytest.raises(FileNotFoundError):
        load_config()


def test_load_config_temperature_optional(tmp_path, monkeypatch):
    """Config without temperature should not have the option."""
    config_file = tmp_path / "config.ini"
    config_file.write_text("[anthropic]\napi_key = key\n")

    monkeypatch.setattr(config_module, "SYSTEM_CONFIG_PATH", tmp_path / "nonexistent.ini")
    monkeypatch.setattr(config_module, "LOCAL_CONFIG_PATH", config_file)

    cfg = load_config()
    assert not cfg.has_option("anthropic", "temperature")


def test_load_config_temperature_present(tmp_path, monkeypatch):
    """Config with temperature should have the option."""
    config_file = tmp_path / "config.ini"
    config_file.write_text("[anthropic]\napi_key = key\ntemperature = 0.0\n")

    monkeypatch.setattr(config_module, "SYSTEM_CONFIG_PATH", tmp_path / "nonexistent.ini")
    monkeypatch.setattr(config_module, "LOCAL_CONFIG_PATH", config_file)

    cfg = load_config()
    assert cfg.has_option("anthropic", "temperature")
    assert cfg.getfloat("anthropic", "temperature") == 0.0
