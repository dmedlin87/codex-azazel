from __future__ import annotations

from functools import lru_cache
from typing import List, Optional

from .models import Character, Event, SourceProfile
from . import storage


# Character API

@lru_cache(maxsize=None)
def get_character(char_id: str) -> Character:
    return storage.load_character(char_id)


def list_character_ids() -> List[str]:
    return storage.list_character_ids()


def list_all_characters() -> List[Character]:
    return list(storage.iter_characters())


def get_source_profile(char: Character, source_id: str) -> Optional[SourceProfile]:
    for profile in char.source_profiles:
        if profile.source_id == source_id:
            return profile
    return None


# Event API

@lru_cache(maxsize=None)
def get_event(event_id: str) -> Event:
    return storage.load_event(event_id)


def clear_cache() -> None:
    """Clear the cached character/event loads."""
    get_character.cache_clear()
    get_event.cache_clear()


def list_event_ids() -> List[str]:
    return storage.list_event_ids()


def list_events_for_character(char_id: str) -> List[Event]:
    return [event for event in storage.iter_events() if char_id in event.participants]
