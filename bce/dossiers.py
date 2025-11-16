from __future__ import annotations

from dataclasses import asdict
from typing import Dict, List

from . import queries
from . import contradictions
from .models import Character, Event


def _build_source_ids(character: Character) -> List[str]:
    seen: Dict[str, None] = {}
    for profile in character.source_profiles:
        if profile.source_id not in seen:
            seen[profile.source_id] = None
    return list(seen.keys())


def build_character_dossier(char_id: str) -> dict:
    """Build a JSON-friendly dossier for a character.

    The returned dict includes core identity fields, per-source traits,
    and nested comparisons/conflicts for traits across sources.
    """
    character = queries.get_character(char_id)
    trait_comparison = contradictions.compare_character_sources(char_id)
    trait_conflicts = contradictions.find_trait_conflicts(char_id)

    traits_by_source: Dict[str, Dict[str, str]] = {}
    references_by_source: Dict[str, List[str]] = {}
    for profile in character.source_profiles:
        traits_by_source[profile.source_id] = dict(profile.traits)
        references_by_source[profile.source_id] = list(profile.references)

    dossier = {
        "id": character.id,
        "canonical_name": character.canonical_name,
        "aliases": list(character.aliases),
        "roles": list(character.roles),
        "source_ids": _build_source_ids(character),
        "traits_by_source": traits_by_source,
        "references_by_source": references_by_source,
        "trait_comparison": trait_comparison,
        "trait_conflicts": trait_conflicts,
    }
    return dossier


def build_event_dossier(event_id: str) -> dict:
    """Build a JSON-friendly dossier for an event.

    The returned dict includes core identity fields, per-source accounts,
    and nested differences between those accounts.
    """
    event: Event = queries.get_event(event_id)
    account_conflicts = contradictions.find_events_with_conflicting_accounts(event_id)

    accounts = [
        {
            "source_id": acc.source_id,
            "reference": acc.reference,
            "summary": acc.summary,
            "notes": acc.notes,
        }
        for acc in event.accounts
    ]

    dossier = {
        "id": event.id,
        "label": event.label,
        "participants": list(event.participants),
        "accounts": accounts,
        "account_conflicts": account_conflicts,
    }
    return dossier


def build_all_character_dossiers() -> list[dict]:
    """Build dossiers for all characters defined in the data directory.

    Returns a list of JSON-serializable dicts, one per character, in the
    order returned by queries.list_character_ids().
    """
    dossiers = []
    for char_id in queries.list_character_ids():
        dossiers.append(build_character_dossier(char_id))
    return dossiers


def build_all_event_dossiers() -> list[dict]:
    """Build dossiers for all events defined in the data directory.

    Returns a list of JSON-serializable dicts, one per event, in the
    order returned by queries.list_event_ids().
    """
    dossiers = []
    for event_id in queries.list_event_ids():
        dossiers.append(build_event_dossier(event_id))
    return dossiers
