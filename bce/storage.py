from __future__ import annotations

import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from .cache import CacheRegistry
from .config import BceConfig, get_default_config
from .exceptions import DataNotFoundError, StorageError
from .models import Character, Event, EventAccount, SourceProfile, TextualVariant

logger = logging.getLogger(__name__)


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

    @staticmethod
    def _deserialize_variants(variants_data: Any) -> List[TextualVariant]:
        """Deserialize textual variants from JSON data.

        Parameters:
            variants_data: Raw variants data from JSON (list of dicts or None)

        Returns:
            List of TextualVariant instances
        """
        if not variants_data:
            return []

        result: List[TextualVariant] = []
        for variant_dict in variants_data:
            if isinstance(variant_dict, dict):
                try:
                    result.append(TextualVariant(**variant_dict))
                except (TypeError, ValueError) as e:
                    # Log warning but continue - don't fail entire load for bad variant
                    logger.warning(f"Failed to deserialize variant: {e}. Data: {variant_dict}")
                    continue
        return result

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

        # Deserialize source profiles with variants and citations
        source_profiles: List[SourceProfile] = []
        for sp_data in data.get("source_profiles", []):
            sp_dict = dict(sp_data)  # Make a copy to avoid mutating original
            # Deserialize variants if present
            variants = self._deserialize_variants(sp_dict.get("variants"))
            sp_dict["variants"] = variants
            # Ensure citations is a list
            if "citations" not in sp_dict:
                sp_dict["citations"] = []
            source_profiles.append(SourceProfile(**sp_dict))

        relationships = self._normalize_relationships(data.get("relationships"), char_id)
        data = {
            **data,
            "source_profiles": source_profiles,
            "relationships": relationships,
        }

        try:
            return Character(**data)
        except TypeError as e:
            # Wrap TypeError with context about which file failed
            raise StorageError(
                f"Failed to load character from {path}: {e}. "
                f"The JSON data may be missing required fields (id, canonical_name) "
                f"or have incorrect field types."
            ) from e
        except ValueError as e:
            raise StorageError(f"Invalid character data in {path}: {e}") from e

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

        # Deserialize event accounts with variants
        accounts: List[EventAccount] = []
        for acc_data in data.get("accounts", []):
            acc_dict = dict(acc_data)  # Make a copy to avoid mutating original
            # Deserialize variants if present
            variants = self._deserialize_variants(acc_dict.get("variants"))
            acc_dict["variants"] = variants
            accounts.append(EventAccount(**acc_dict))

        # Ensure citations is present
        if "citations" not in data:
            data["citations"] = []

        data = {**data, "accounts": accounts}

        try:
            return Event(**data)
        except TypeError as e:
            # Wrap TypeError with context about which file failed
            raise StorageError(
                f"Failed to load event from {path}: {e}. "
                f"The JSON data may be missing required fields (id, label) "
                f"or have incorrect field types."
            ) from e
        except ValueError as e:
            raise StorageError(f"Invalid event data in {path}: {e}") from e

    def _normalize_relationships(self, value: Any, char_id: str) -> List[dict]:
        """Convert relationships data to a list of dictionaries.

        Only accepts the flat list format with character_id references.
        Raises StorageError for legacy nested dict format to prevent silent data loss.

        Args:
            value: Raw relationships data from JSON
            char_id: Character ID for error messages

        Returns:
            List of relationship dictionaries

        Raises:
            StorageError: If legacy nested format is detected
        """

        if value is None:
            return []

        # Reject legacy nested dict format (Format A)
        if isinstance(value, dict):
            raise StorageError(
                f"Character '{char_id}': relationships use deprecated nested dict format. "
                f"Please migrate to flat list format with 'character_id' field. "
                f"See docs/SCHEMA.md for the correct structure."
            )

        # Only accept flat list format (Format B)
        if isinstance(value, list):
            result: List[dict] = []
            for i, rel in enumerate(value):
                if not isinstance(rel, dict):
                    raise StorageError(
                        f"Character '{char_id}': relationship at index {i} is not a dict"
                    )
                if "character_id" not in rel:
                    raise StorageError(
                        f"Character '{char_id}': relationship at index {i} missing required 'character_id' field"
                    )
                result.append(rel)
            return result

        raise StorageError(
            f"Character '{char_id}': relationships must be a list, got {type(value).__name__}"
        )

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
_default_storage_config_root: Optional[Path] = None


def _get_default_storage() -> StorageManager:
    """Get or create the default storage manager instance."""
    global _default_storage, _default_storage_config_root

    current_config = get_default_config()
    current_root = current_config.data_root

    # Recreate the storage manager if it doesn't exist or if the data root
    # has changed since the last creation (e.g., in tests that swap configs).
    if _default_storage is None or _default_storage_config_root != current_root:
        _default_storage = StorageManager(current_config)
        _default_storage_config_root = current_root

    return _default_storage


def _reset_default_storage() -> None:
    """Reset the default storage manager (used after config changes)."""
    global _default_storage, _default_storage_config_root
    _default_storage = None
    _default_storage_config_root = None


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
