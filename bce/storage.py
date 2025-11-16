from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Iterator, List

from .models import Character, Event, EventAccount, SourceProfile


_BASE_DIR = Path(__file__).resolve().parent
_CHAR_DIR = _BASE_DIR / "data" / "characters"
_EVENT_DIR = _BASE_DIR / "data" / "events"


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
