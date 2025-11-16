from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Iterator, List

from .models import Character, Event, EventAccount, SourceProfile


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
    _update_dirs(target)


def reset_data_root() -> None:
    """Restore the package's default data directory."""
    configure_data_root(None)


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
    data = _read_json(path)
    source_profiles = [SourceProfile(**sp) for sp in data.get("source_profiles", [])]
    data = {**data, "source_profiles": source_profiles}
    return Character(**data)


def iter_characters() -> Iterator[Character]:
    for char_id in list_character_ids():
        yield load_character(char_id)


def save_character(character: Character) -> None:
    path = _CHAR_DIR / f"{character.id}.json"
    _write_json(path, asdict(character))
    _clear_query_cache()


def list_event_ids() -> List[str]:
    if not _EVENT_DIR.exists():
        return []
    return sorted(p.stem for p in _EVENT_DIR.glob("*.json"))


def load_event(event_id: str) -> Event:
    path = _EVENT_DIR / f"{event_id}.json"
    data = _read_json(path)
    accounts = [EventAccount(**acc) for acc in data.get("accounts", [])]
    data = {**data, "accounts": accounts}
    return Event(**data)


def iter_events() -> Iterator[Event]:
    for event_id in list_event_ids():
        yield load_event(event_id)


def save_event(event: Event) -> None:
    path = _EVENT_DIR / f"{event.id}.json"
    _write_json(path, asdict(event))
    _clear_query_cache()
