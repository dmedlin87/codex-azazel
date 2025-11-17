from __future__ import annotations

from typing import Dict

from . import queries


def _find_conflicts(field_map: Dict[str, Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    conflicts: Dict[str, Dict[str, str]] = {}
    for field_name, per_source in field_map.items():
        values = {v for v in per_source.values() if v}
        if len(values) > 1:
            conflicts[field_name] = per_source
    return conflicts


def compare_character_sources(char_id: str) -> Dict[str, Dict[str, str]]:
    """Compare a character's traits across sources.

    Returns a nested mapping of ``trait -> source_id -> trait_value`` for the
    character identified by ``char_id``.
    """
    char = queries.get_character(char_id)
    trait_map: Dict[str, Dict[str, str]] = {}
    for profile in char.source_profiles:
        for trait, value in profile.traits.items():
            trait_map.setdefault(trait, {})[profile.source_id] = value
    return trait_map


def find_trait_conflicts(char_id: str) -> Dict[str, Dict[str, str]]:
    """Find character traits that differ between sources.

    Returns a nested mapping of ``trait -> source_id -> trait_value`` including
    only those traits whose values are not the same across sources.
    """
    comparison = compare_character_sources(char_id)
    return _find_conflicts(comparison)


def find_events_with_conflicting_accounts(event_id: str) -> Dict[str, Dict[str, str]]:
    """Summarize differing fields across event accounts.

    Returns a nested mapping of ``field_name -> source_id -> value`` for the
    event identified by ``event_id``, including only fields whose non-empty
    values differ between sources.
    """
    event = queries.get_event(event_id)
    field_map: Dict[str, Dict[str, str]] = {}

    for account in event.accounts:
        for field_name in ("summary", "notes", "reference"):
            value = getattr(account, field_name)
            if not value:
                continue
            field_map.setdefault(field_name, {})[account.source_id] = value

    return _find_conflicts(field_map)
