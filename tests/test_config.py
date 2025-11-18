from __future__ import annotations

import os
from pathlib import Path

import pytest

from bce.config import BceConfig, ConfigurationError, get_default_config, reset_default_config, set_default_config


class TestBceConfigDataRoot:
    def test_env_data_root_nonexistent_raises_configuration_error(self, monkeypatch, tmp_path: Path) -> None:
        bogus = tmp_path / "does_not_exist"
        # Do not create the directory so it truly does not exist
        monkeypatch.setenv("BCE_DATA_ROOT", str(bogus))

        with pytest.raises(ConfigurationError) as exc:
            BceConfig()

        msg = str(exc.value)
        assert "does not exist" in msg
        assert "BCE_DATA_ROOT" in msg

    def test_programmatic_data_root_override_wins_over_env(self, monkeypatch, tmp_path: Path) -> None:
        env_root = tmp_path / "env_root"
        env_root.mkdir()
        monkeypatch.setenv("BCE_DATA_ROOT", str(env_root))

        override_root = tmp_path / "override_root"
        override_root.mkdir()

        cfg = BceConfig(data_root=override_root)

        assert cfg.data_root == override_root


class TestBceConfigCacheSize:
    def test_env_cache_size_valid_and_invalid_values(self, monkeypatch) -> None:
        monkeypatch.delenv("BCE_CACHE_SIZE", raising=False)

        # Valid integer value
        monkeypatch.setenv("BCE_CACHE_SIZE", "256")
        cfg = BceConfig()
        assert cfg.cache_size == 256

        # Negative value should raise
        monkeypatch.setenv("BCE_CACHE_SIZE", "-1")
        with pytest.raises(ConfigurationError) as exc_neg:
            BceConfig()
        assert "non-negative" in str(exc_neg.value)

        # Non-integer value should raise
        monkeypatch.setenv("BCE_CACHE_SIZE", "not-an-int")
        with pytest.raises(ConfigurationError) as exc_type:
            BceConfig()
        assert "must be an integer" in str(exc_type.value)

    def test_programmatic_cache_size_override_wins_over_env(self, monkeypatch) -> None:
        monkeypatch.setenv("BCE_CACHE_SIZE", "999")

        cfg = BceConfig(cache_size=10)

        assert cfg.cache_size == 10


class TestBceConfigValidationFlag:
    @pytest.mark.parametrize("env_value, expected", [
        ("false", False),
        ("0", False),
        ("no", False),
        ("off", False),
        ("true", True),
        ("1", True),
        ("yes", True),
        ("on", True),
        ("", True),  # default when unset/empty
    ])
    def test_enable_validation_from_env(self, monkeypatch, env_value: str, expected: bool) -> None:
        monkeypatch.delenv("BCE_ENABLE_VALIDATION", raising=False)
        if env_value:
            monkeypatch.setenv("BCE_ENABLE_VALIDATION", env_value)

        cfg = BceConfig()

        assert cfg.enable_validation is expected

    def test_programmatic_validation_override_wins_over_env(self, monkeypatch) -> None:
        monkeypatch.setenv("BCE_ENABLE_VALIDATION", "false")

        cfg = BceConfig(enable_validation=True)

        assert cfg.enable_validation is True


class TestBceConfigLogLevel:
    def test_log_level_default_and_env(self, monkeypatch) -> None:
        monkeypatch.delenv("BCE_LOG_LEVEL", raising=False)
        cfg_default = BceConfig()
        assert cfg_default.log_level == "WARNING"

        monkeypatch.setenv("BCE_LOG_LEVEL", "debug")
        cfg_env = BceConfig()
        assert cfg_env.log_level == "DEBUG"

    def test_invalid_log_level_raises_configuration_error(self, monkeypatch) -> None:
        monkeypatch.setenv("BCE_LOG_LEVEL", "INVALID")

        with pytest.raises(ConfigurationError) as exc:
            BceConfig()

        msg = str(exc.value)
        assert "Invalid log level" in msg
        assert "INVALID" in msg

    def test_programmatic_log_level_override_wins_over_env(self, monkeypatch) -> None:
        monkeypatch.setenv("BCE_LOG_LEVEL", "ERROR")

        cfg = BceConfig(log_level="info")

        assert cfg.log_level == "INFO"


class TestBceConfigPathsAndSingleton:
    def test_validate_paths_reports_missing_directories(self, tmp_path: Path) -> None:
        root = tmp_path / "data_root"
        root.mkdir()
        cfg = BceConfig(data_root=root)

        errors = cfg.validate_paths()

        # The root exists and is a directory, but characters/events do not yet
        assert any("Characters directory does not exist" in e for e in errors)
        assert any("Events directory does not exist" in e for e in errors)

    def test_default_config_singleton_and_reset(self, monkeypatch, tmp_path: Path) -> None:
        reset_default_config()

        # First call constructs new instance
        cfg1 = get_default_config()
        cfg2 = get_default_config()
        assert cfg1 is cfg2

        # set_default_config should replace singleton
        new_root = tmp_path / "override"
        new_root.mkdir()
        custom = BceConfig(data_root=new_root)
        set_default_config(custom)

        cfg3 = get_default_config()
        assert cfg3 is custom
        assert cfg3.data_root == new_root

        # reset_default_config should drop the override and recreate from env/defaults
        reset_default_config()
        cfg4 = get_default_config()
        assert cfg4 is not custom

    def test_repr_includes_key_fields(self, tmp_path: Path) -> None:
        root = tmp_path / "data_root"
        root.mkdir()
        cfg = BceConfig(data_root=root, cache_size=42, enable_validation=False, log_level="info")

        text = repr(cfg)
        assert "BceConfig(" in text
        assert "cache_size=42" in text
        assert "enable_validation=False" in text
        assert "log_level=INFO" in text
