from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from .exceptions import ConfigurationError


# Default data root is the package's bundled data directory
_PACKAGE_DIR = Path(__file__).resolve().parent
_DEFAULT_DATA_ROOT = _PACKAGE_DIR / "data"


class BceConfig:
    """Configuration for the Biblical Character Engine.

    Configuration is loaded from environment variables with sensible defaults.
    This class is designed to be instantiated once and reused throughout the
    application lifecycle.

    Environment Variables:
        BCE_DATA_ROOT: Path to the data directory (default: package bundled data)
        BCE_CACHE_SIZE: Maximum number of cached characters/events (default: 128)
        BCE_ENABLE_VALIDATION: Enable automatic validation on load (default: true)
        BCE_LOG_LEVEL: Logging level (default: WARNING)

    Examples:
        >>> config = BceConfig()
        >>> print(config.data_root)
        /path/to/bce/data

        >>> # Override with environment variable
        >>> os.environ['BCE_DATA_ROOT'] = '/custom/path'
        >>> config = BceConfig()
        >>> print(config.data_root)
        /custom/path

        >>> # Programmatic override
        >>> config = BceConfig(data_root=Path('/another/path'))
    """

    def __init__(
        self,
        data_root: Optional[Path] = None,
        cache_size: Optional[int] = None,
        enable_validation: Optional[bool] = None,
        log_level: Optional[str] = None,
    ):
        """Initialize configuration.

        Parameters:
            data_root: Override data root path (default: from env or package default)
            cache_size: Override cache size (default: from env or 128)
            enable_validation: Override validation setting (default: from env or True)
            log_level: Override log level (default: from env or WARNING)
        """
        self.data_root = self._resolve_data_root(data_root)
        self.cache_size = self._resolve_cache_size(cache_size)
        self.enable_validation = self._resolve_validation(enable_validation)
        self.log_level = self._resolve_log_level(log_level)

    def _resolve_data_root(self, override: Optional[Path]) -> Path:
        """Resolve data root from override, environment, or default."""
        if override is not None:
            return override

        env_root = os.getenv("BCE_DATA_ROOT")
        if env_root:
            path = Path(env_root).expanduser().resolve()
            if not path.exists():
                raise ConfigurationError(
                    f"BCE_DATA_ROOT '{path}' does not exist. "
                    "Please create it or update the environment variable."
                )
            return path

        return _DEFAULT_DATA_ROOT

    def _resolve_cache_size(self, override: Optional[int]) -> int:
        """Resolve cache size from override, environment, or default."""
        if override is not None:
            if override < 0:
                raise ConfigurationError(f"cache_size must be non-negative, got {override}")
            return override

        env_size = os.getenv("BCE_CACHE_SIZE")
        if env_size:
            try:
                size = int(env_size)
                if size < 0:
                    raise ConfigurationError(
                        f"BCE_CACHE_SIZE must be non-negative, got {size}"
                    )
                return size
            except ValueError:
                raise ConfigurationError(
                    f"BCE_CACHE_SIZE must be an integer, got '{env_size}'"
                )

        return 128  # Default: reasonable for current dataset (61 chars + 10 events)

    def _resolve_validation(self, override: Optional[bool]) -> bool:
        """Resolve validation setting from override, environment, or default."""
        if override is not None:
            return override

        env_validation = os.getenv("BCE_ENABLE_VALIDATION", "").lower()
        if env_validation in ("false", "0", "no", "off"):
            return False
        if env_validation in ("true", "1", "yes", "on"):
            return True

        return True  # Default: enable validation

    def _resolve_log_level(self, override: Optional[str]) -> str:
        """Resolve log level from override, environment, or default."""
        if override is not None:
            return override.upper()

        env_level = os.getenv("BCE_LOG_LEVEL", "WARNING").upper()
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if env_level not in valid_levels:
            raise ConfigurationError(
                f"Invalid log level '{env_level}'. Must be one of: {valid_levels}"
            )

        return env_level

    @property
    def char_dir(self) -> Path:
        """Return the path to the characters data directory."""
        return self.data_root / "characters"

    @property
    def event_dir(self) -> Path:
        """Return the path to the events data directory."""
        return self.data_root / "events"

    @property
    def sources_file(self) -> Path:
        """Return the path to the sources.json file."""
        return self.data_root / "sources.json"

    def validate_paths(self) -> list[str]:
        """Validate that required paths exist.

        Returns:
            List of error messages (empty if all checks pass)
        """
        errors: list[str] = []

        if not self.data_root.exists():
            errors.append(f"Data root does not exist: {self.data_root}")
        elif not self.data_root.is_dir():
            errors.append(f"Data root is not a directory: {self.data_root}")

        if not self.char_dir.exists():
            errors.append(f"Characters directory does not exist: {self.char_dir}")

        if not self.event_dir.exists():
            errors.append(f"Events directory does not exist: {self.event_dir}")

        return errors

    def __repr__(self) -> str:
        return (
            f"BceConfig("
            f"data_root={self.data_root}, "
            f"cache_size={self.cache_size}, "
            f"enable_validation={self.enable_validation}, "
            f"log_level={self.log_level})"
        )


# Global default configuration instance
_default_config: Optional[BceConfig] = None


def get_default_config() -> BceConfig:
    """Get or create the default global configuration instance.

    This singleton pattern allows configuration to be accessed throughout
    the package without passing config objects explicitly.

    Returns:
        The default BceConfig instance
    """
    global _default_config
    if _default_config is None:
        _default_config = BceConfig()
    return _default_config


def set_default_config(config: BceConfig) -> None:
    """Set the default global configuration instance.

    This allows programmatic reconfiguration of the entire package.

    Parameters:
        config: New configuration to use as default
    """
    global _default_config
    _default_config = config


def reset_default_config() -> None:
    """Reset the default configuration to environment-based defaults.

    This clears any programmatic configuration and reloads from environment.
    """
    global _default_config
    _default_config = None
