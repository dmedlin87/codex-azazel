from __future__ import annotations

from dataclasses import asdict
from typing import Dict, List

from . import queries
from . import contradictions
from . import sources
from .models import Character, Event
from .dossier_types import (
    CharacterDossier,
    EventDossier,
    DOSSIER_KEY_ACCOUNTS,
    DOSSIER_KEY_ACCOUNT_CONFLICTS,
    DOSSIER_KEY_ALIASES,
    DOSSIER_KEY_CANONICAL_NAME,
    DOSSIER_KEY_ID,
    DOSSIER_KEY_LABEL,
    DOSSIER_KEY_PARTICIPANTS,
    DOSSIER_KEY_REFERENCES_BY_SOURCE,
    DOSSIER_KEY_ROLES,
    DOSSIER_KEY_SOURCE_IDS,
    DOSSIER_KEY_SOURCE_METADATA,
    DOSSIER_KEY_TRAIT_COMPARISON,
    DOSSIER_KEY_TRAIT_CONFLICTS,
    DOSSIER_KEY_TRAITS_BY_SOURCE,
    DOSSIER_KEY_RELATIONSHIPS,
    DOSSIER_KEY_PARALLELS,
)


def _build_source_ids(character: Character) -> List[str]:
    seen: Dict[str, None] = {}
    for profile in character.source_profiles:
        if profile.source_id not in seen:
            seen[profile.source_id] = None
    return list(seen.keys())


def build_character_dossier(char_id: str) -> CharacterDossier:
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

    source_metadata: Dict[str, Dict[str, str]] = {}
    for source_id in _build_source_ids(character):
        meta = sources.load_source_metadata(source_id)
        if meta is None:
            continue

        meta_dict: Dict[str, str] = {}
        if meta.date_range:
            meta_dict["date_range"] = meta.date_range
        if meta.provenance:
            meta_dict["provenance"] = meta.provenance
        if meta.audience:
            meta_dict["audience"] = meta.audience
        if meta.depends_on:
            meta_dict["depends_on"] = ", ".join(meta.depends_on)

        if meta_dict:
            source_metadata[source_id] = meta_dict

    dossier: CharacterDossier = {
        DOSSIER_KEY_ID: character.id,
        DOSSIER_KEY_CANONICAL_NAME: character.canonical_name,
        DOSSIER_KEY_ALIASES: list(character.aliases),
        DOSSIER_KEY_ROLES: list(character.roles),
        DOSSIER_KEY_SOURCE_IDS: _build_source_ids(character),
        DOSSIER_KEY_SOURCE_METADATA: source_metadata,
        DOSSIER_KEY_TRAITS_BY_SOURCE: traits_by_source,
        DOSSIER_KEY_REFERENCES_BY_SOURCE: references_by_source,
        DOSSIER_KEY_TRAIT_COMPARISON: trait_comparison,
        DOSSIER_KEY_TRAIT_CONFLICTS: trait_conflicts,
        DOSSIER_KEY_RELATIONSHIPS: list(character.relationships),
        DOSSIER_KEY_PARALLELS: [],
    }
    return dossier


def build_event_dossier(event_id: str) -> EventDossier:
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

    dossier: EventDossier = {
        DOSSIER_KEY_ID: event.id,
        DOSSIER_KEY_LABEL: event.label,
        DOSSIER_KEY_PARTICIPANTS: list(event.participants),
        DOSSIER_KEY_ACCOUNTS: accounts,
        DOSSIER_KEY_ACCOUNT_CONFLICTS: account_conflicts,
        DOSSIER_KEY_PARALLELS: list(event.parallels),
    }
    return dossier


def build_all_character_dossiers() -> list[CharacterDossier]:
    """Build dossiers for all characters defined in the data directory.

    Returns a list of JSON-serializable dicts, one per character, in the
    order returned by queries.list_character_ids().
    """
    dossiers: list[CharacterDossier] = []
    for char_id in queries.list_character_ids():
        dossiers.append(build_character_dossier(char_id))
    return dossiers


def build_all_event_dossiers() -> list[EventDossier]:
    """Build dossiers for all events defined in the data directory.

    Returns a list of JSON-serializable dicts, one per event, in the
    order returned by queries.list_event_ids().
    """
    dossiers = []
    for event_id in queries.list_event_ids():
        dossiers.append(build_event_dossier(event_id))
    return dossiers
