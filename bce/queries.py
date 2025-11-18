from __future__ import annotations

from functools import lru_cache
from typing import List

from .cache import CacheRegistry
from .models import Character, Event
from . import storage
from . import services


# Character API

@lru_cache(maxsize=128)
def get_character(char_id: str) -> Character:
    return storage.load_character(char_id)


def list_character_ids() -> List[str]:
    return storage.list_character_ids()


def list_all_characters() -> List[Character]:
    return list(storage.iter_characters())


# Delegate to services layer for backward compatibility
get_source_profile = services.get_source_profile


# Event API

@lru_cache(maxsize=128)
def get_event(event_id: str) -> Event:
    return storage.load_event(event_id)


def clear_cache() -> None:
    """Clear the cached character/event loads."""
    get_character.cache_clear()
    get_event.cache_clear()


# Register cache invalidator with CacheRegistry
CacheRegistry.register(clear_cache)


def list_event_ids() -> List[str]:
    return storage.list_event_ids()


def list_all_events() -> List[Event]:
    """Return all events as a list of Event objects."""
    return list(storage.iter_events())


def list_events_for_character(char_id: str) -> List[Event]:
    return [event for event in storage.iter_events() if char_id in event.participants]


def list_characters_with_tag(tag: str) -> List[str]:
    """Return IDs of characters whose tags include the given tag.

    Matching is case-insensitive; tags are compared by normalized lowercase
    value.
    """

    needle = tag.lower()
    result: List[str] = []
    for char in storage.iter_characters():
        tags = getattr(char, "tags", [])
        if any(isinstance(t, str) and t.lower() == needle for t in tags):
            result.append(char.id)
    return sorted(result)


def list_events_with_tag(tag: str) -> List[str]:
    """Return IDs of events whose tags include the given tag.

    Matching is case-insensitive; tags are compared by normalized lowercase
    value.
    """

    needle = tag.lower()
    result: List[str] = []
    for event in storage.iter_events():
        tags = getattr(event, "tags", [])
        if any(isinstance(t, str) and t.lower() == needle for t in tags):
            result.append(event.id)
    return sorted(result)
