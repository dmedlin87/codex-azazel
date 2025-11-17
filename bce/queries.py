from __future__ import annotations

import logging
from functools import lru_cache
from typing import List, Optional

from .models import Character, Event, SourceProfile
from . import storage

logger = logging.getLogger(__name__)


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
    logger.debug("Clearing query cache")
    get_character.cache_clear()
    get_event.cache_clear()
    logger.info("Query cache cleared")


def get_cache_stats() -> dict:
    """Return cache performance statistics for character and event queries.

    Returns:
        Dictionary with cache statistics including:
        - character_cache: CacheInfo for character lookups (hits, misses, maxsize, currsize)
        - event_cache: CacheInfo for event lookups (hits, misses, maxsize, currsize)

    Example:
        >>> stats = get_cache_stats()
        >>> print(f"Character cache hits: {stats['character_cache'].hits}")
        >>> print(f"Event cache misses: {stats['event_cache'].misses}")
    """
    return {
        "character_cache": get_character.cache_info(),
        "event_cache": get_event.cache_info(),
    }


def list_event_ids() -> List[str]:
    return storage.list_event_ids()


def list_events_for_character(char_id: str) -> List[Event]:
    return [event for event in storage.iter_events() if char_id in event.participants]
