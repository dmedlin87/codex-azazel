from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from .cache import CacheRegistry
from .config import BceConfig, get_default_config
from .exceptions import DataNotFoundError, StorageError
from .models import Character, Event, EventAccount, SourceProfile


class StorageManager:
    """Manager for loading and saving BCE data from filesystem storage.

    This class encapsulates all storage operations for characters and events,
    replacing the previous global state pattern with instance-based management.

    Each StorageManager instance has its own configuration and can operate
    independently, making it thread-safe and testable.

    Examples:
        >>> # Use default storage
        >>> storage = StorageManager()
        >>> char = storage.load_character("jesus")
        >>>
        >>> # Use custom data root
        >>> config = BceConfig(data_root=Path("/custom/path"))
        >>> storage = StorageManager(config)
        >>> char = storage.load_character("custom_char")
    """

    def __init__(self, config: Optional[BceConfig] = None):
        """Initialize storage manager.

        Parameters:
            config: Configuration instance (default: global config)
        """
        self.config = config or get_default_config()
        self._char_dir = self.config.char_dir
        self._event_dir = self.config.event_dir

    @property
    def data_root(self) -> Path:
        """Return the data root path."""
        return self.config.data_root

    @property
    def char_dir(self) -> Path:
        """Return the characters directory path."""
        return self._char_dir

    @property
    def event_dir(self) -> Path:
        """Return the events directory path."""
        return self._event_dir

    def _read_json(self, path: Path) -> Dict[str, Any]:
        """Read and parse a JSON file.

        Parameters:
            path: Path to JSON file

        Returns:
            Parsed JSON data

        Raises:
            DataNotFoundError: If file doesn't exist
            StorageError: If file cannot be read or parsed
        """
        if not path.exists():
            raise DataNotFoundError(f"File not found: {path}")

        try:
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            # Preserve the original exception type for compatibility with
            # callers that expect JSONDecodeError.
            raise
        except (IOError, OSError) as e:
            raise StorageError(f"Failed to read {path}: {e}")

    def _write_json(self, path: Path, data: Any) -> None:
        """Write data to JSON file.

        Parameters:
            path: Path to JSON file
            data: Data to serialize

        Raises:
            StorageError: If file cannot be written
        """
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except (IOError, OSError) as e:
            raise StorageError(f"Failed to write {path}: {e}")
        except (TypeError, ValueError) as e:
            raise StorageError(f"Failed to serialize data for {path}: {e}")

    # Character operations

    def list_character_ids(self) -> List[str]:
        """List all character IDs in sorted order.

        Returns:
            Sorted list of character IDs (without .json extension)
        """
        if not self._char_dir.exists():
            return []
        return sorted(p.stem for p in self._char_dir.glob("*.json"))

    def load_character(self, char_id: str) -> Character:
        """Load a character by ID.

        Parameters:
            char_id: Character identifier

        Returns:
            Character instance

        Raises:
            DataNotFoundError: If character doesn't exist
            StorageError: If character cannot be loaded
        """
        path = self._char_dir / f"{char_id}.json"
        data = self._read_json(path)

        source_profiles = [SourceProfile(**sp) for sp in data.get("source_profiles", [])]
        relationships = self._normalize_relationships(data.get("relationships"))
        data = {
            **data,
            "source_profiles": source_profiles,
            "relationships": relationships,
        }

        try:
            return Character(**data)
        except TypeError:
            # Surface the original TypeError so existing tests that assert on
            # the specific error message continue to pass.
            raise
        except ValueError as e:
            raise StorageError(f"Invalid character data in {path}: {e}")

    def iter_characters(self) -> Iterator[Character]:
        """Iterate over all characters.

        Yields:
            Character instances in alphabetical order by ID
        """
        for char_id in self.list_character_ids():
            yield self.load_character(char_id)

    def save_character(self, character: Character) -> None:
        """Save a character to storage.

        Parameters:
            character: Character instance to save

        Raises:
            StorageError: If character cannot be saved
        """
        path = self._char_dir / f"{character.id}.json"
        self._write_json(path, asdict(character))
        CacheRegistry.invalidate_all()

    # Event operations

    def list_event_ids(self) -> List[str]:
        """List all event IDs in sorted order.

        Returns:
            Sorted list of event IDs (without .json extension)
        """
        if not self._event_dir.exists():
            return []
        return sorted(p.stem for p in self._event_dir.glob("*.json"))

    def load_event(self, event_id: str) -> Event:
        """Load an event by ID.

        Parameters:
            event_id: Event identifier

        Returns:
            Event instance

        Raises:
            DataNotFoundError: If event doesn't exist
            StorageError: If event cannot be loaded
        """
        path = self._event_dir / f"{event_id}.json"
        data = self._read_json(path)

        accounts = [EventAccount(**acc) for acc in data.get("accounts", [])]
        data = {**data, "accounts": accounts}

        try:
            return Event(**data)
        except TypeError:
            raise
        except ValueError as e:
            raise StorageError(f"Invalid event data in {path}: {e}")

    def _normalize_relationships(self, value: Any) -> List[dict]:
        """Convert relationships data to a list of dictionaries."""

        if value is None:
            return []
        if isinstance(value, list):
            return [
                rel
                for rel in value
                if isinstance(rel, dict) and rel.get("character_id")
            ]
        if isinstance(value, dict):
            flattened: List[dict] = []
            for group in value.values():
                if isinstance(group, list):
                    flattened.extend(
                        rel
                        for rel in group
                        if isinstance(rel, dict) and rel.get("character_id")
                    )
            return flattened
        return []

    def iter_events(self) -> Iterator[Event]:
        """Iterate over all events.

        Yields:
            Event instances in alphabetical order by ID
        """
        for event_id in self.list_event_ids():
            yield self.load_event(event_id)

    def save_event(self, event: Event) -> None:
        """Save an event to storage.

        Parameters:
            event: Event instance to save

        Raises:
            StorageError: If event cannot be saved
        """
        path = self._event_dir / f"{event.id}.json"
        self._write_json(path, asdict(event))
        CacheRegistry.invalidate_all()


# =============================================================================
# Module-level API for backward compatibility
# =============================================================================
# These functions delegate to a default StorageManager instance, maintaining
# the same API surface as the original implementation.

_default_storage: Optional[StorageManager] = None


def _get_default_storage() -> StorageManager:
    """Get or create the default storage manager instance."""
    global _default_storage
    if _default_storage is None:
        _default_storage = StorageManager()
    return _default_storage


def _reset_default_storage() -> None:
    """Reset the default storage manager (used after config changes)."""
    global _default_storage
    _default_storage = None


def configure_data_root(path: Path | str | None) -> None:
    """Point storage at a different data directory (use None to reset).

    This is a legacy function maintained for backward compatibility.
    New code should create a custom BceConfig and StorageManager instead.

    Parameters:
        path: Path to data directory, or None to reset to package default
    """
    from .config import BceConfig, set_default_config, reset_default_config

    if path is None:
        reset_default_config()
    else:
        target = Path(path)
        config = BceConfig(data_root=target)
        set_default_config(config)

    _reset_default_storage()
    CacheRegistry.invalidate_all()


def reset_data_root() -> None:
    """Restore the package's default data directory.

    This is a legacy function maintained for backward compatibility.
    """
    configure_data_root(None)


# Character operations (delegate to default storage)


def list_character_ids() -> List[str]:
    """List all character IDs in sorted order."""
    return _get_default_storage().list_character_ids()


def load_character(char_id: str) -> Character:
    """Load a character by ID."""
    return _get_default_storage().load_character(char_id)


def iter_characters() -> Iterator[Character]:
    """Iterate over all characters."""
    return _get_default_storage().iter_characters()


def save_character(character: Character) -> None:
    """Save a character to storage."""
    _get_default_storage().save_character(character)


# Event operations (delegate to default storage)


def list_event_ids() -> List[str]:
    """List all event IDs in sorted order."""
    return _get_default_storage().list_event_ids()


def load_event(event_id: str) -> Event:
    """Load an event by ID."""
    return _get_default_storage().load_event(event_id)


def iter_events() -> Iterator[Event]:
    """Iterate over all events."""
    return _get_default_storage().iter_events()


def save_event(event: Event) -> None:
    """Save an event to storage."""
    _get_default_storage().save_event(event)
