from __future__ import annotations

import json
import logging
import sys
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Iterator, List

from .models import Character, Event, EventAccount, SourceProfile

logger = logging.getLogger(__name__)


_PACKAGE_DIR = Path(__file__).resolve().parent
_DEFAULT_DATA_ROOT = _PACKAGE_DIR / "data"
_DATA_ROOT = _DEFAULT_DATA_ROOT
_CHAR_DIR = _DATA_ROOT / "characters"
_EVENT_DIR = _DATA_ROOT / "events"


def _update_dirs(root: Path) -> None:
    global _DATA_ROOT, _CHAR_DIR, _EVENT_DIR

    _DATA_ROOT = root
    _CHAR_DIR = root / "characters"
    _EVENT_DIR = root / "events"
    _clear_query_cache()


def _clear_query_cache() -> None:
    if "bce.queries" not in sys.modules:
        return
    from . import queries as _queries

    _queries.clear_cache()


def configure_data_root(path: Path | str | None) -> None:
    """Point storage at a different data directory (use ``None`` to reset)."""
    target = Path(path) if path is not None else _DEFAULT_DATA_ROOT
    logger.info(f"Configuring data root: {target}")
    _update_dirs(target)


def reset_data_root() -> None:
    """Restore the package's default data directory."""
    configure_data_root(None)


@contextmanager
def temporary_data_root(path: Path | str):
    """Temporarily use a different data root.

    This context manager is useful for testing with alternate data directories.

    Args:
        path: Path to the temporary data root directory.

    Example:
        >>> from pathlib import Path
        >>> with temporary_data_root(Path("/tmp/test_data")):
        ...     # All storage operations use /tmp/test_data
        ...     characters = list_character_ids()
        >>> # Original data root is restored
    """
    original = _DATA_ROOT
    configure_data_root(path)
    try:
        yield
    finally:
        _update_dirs(original)


def _read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def list_character_ids() -> List[str]:
    if not _CHAR_DIR.exists():
        return []
    return sorted(p.stem for p in _CHAR_DIR.glob("*.json"))


def load_character(char_id: str) -> Character:
    path = _CHAR_DIR / f"{char_id}.json"
    logger.debug(f"Loading character: {char_id} from {path}")
    try:
        data = _read_json(path)
        source_profiles = [SourceProfile(**sp) for sp in data.get("source_profiles", [])]
        data = {**data, "source_profiles": source_profiles}
        character = Character(**data)
        logger.info(f"Successfully loaded character: {char_id}")
        return character
    except (TypeError, KeyError) as e:
        logger.error(f"Failed to load character {char_id}: {e}")
        raise ValueError(
            f"Invalid character data in {path}: {e}. "
            f"Check that all required fields are present and correctly typed."
        ) from e


def iter_characters() -> Iterator[Character]:
    for char_id in list_character_ids():
        yield load_character(char_id)


def save_character(character: Character) -> None:
    path = _CHAR_DIR / f"{character.id}.json"
    logger.debug(f"Saving character: {character.id} to {path}")
    _write_json(path, asdict(character))
    _clear_query_cache()
    logger.info(f"Successfully saved character: {character.id}")


def list_event_ids() -> List[str]:
    if not _EVENT_DIR.exists():
        return []
    return sorted(p.stem for p in _EVENT_DIR.glob("*.json"))


def load_event(event_id: str) -> Event:
    path = _EVENT_DIR / f"{event_id}.json"
    logger.debug(f"Loading event: {event_id} from {path}")
    try:
        data = _read_json(path)
        accounts = [EventAccount(**acc) for acc in data.get("accounts", [])]
        data = {**data, "accounts": accounts}
        event = Event(**data)
        logger.info(f"Successfully loaded event: {event_id}")
        return event
    except (TypeError, KeyError) as e:
        logger.error(f"Failed to load event {event_id}: {e}")
        raise ValueError(
            f"Invalid event data in {path}: {e}. "
            f"Check that all required fields are present and correctly typed."
        ) from e


def iter_events() -> Iterator[Event]:
    for event_id in list_event_ids():
        yield load_event(event_id)


def save_event(event: Event) -> None:
    path = _EVENT_DIR / f"{event.id}.json"
    logger.debug(f"Saving event: {event.id} to {path}")
    _write_json(path, asdict(event))
    _clear_query_cache()
    logger.info(f"Successfully saved event: {event.id}")
