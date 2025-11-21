from __future__ import annotations

from typing import Dict, List

from . import queries
from . import contradictions
from . import sources
from . import claim_graph
from .models import Character, Event, Relationship
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
    DOSSIER_KEY_TRAIT_CONFLICT_SUMMARIES,
    DOSSIER_KEY_TRAITS_BY_SOURCE,
    DOSSIER_KEY_RELATIONSHIPS,
    DOSSIER_KEY_PARALLELS,
    DOSSIER_KEY_ACCOUNT_CONFLICT_SUMMARIES,
    DOSSIER_KEY_CLAIM_GRAPH,
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
    trait_conflict_summaries = contradictions.summarize_character_conflicts(char_id)

    traits_by_source: Dict[str, Dict[str, str]] = {}
    references_by_source: Dict[str, List[str]] = {}
    variants_by_source: Dict[str, List[Dict[str, str]]] = {}
    citations_by_source: Dict[str, List[str]] = {}

    for profile in character.source_profiles:
        traits_by_source[profile.source_id] = dict(profile.traits)
        references_by_source[profile.source_id] = list(profile.references)

        # Include variants if present
        if profile.variants:
            variants_by_source[profile.source_id] = [
                {
                    "manuscript_family": v.manuscript_family,
                    "reading": v.reading,
                    "significance": v.significance,
                }
                for v in profile.variants
            ]

        # Include citations if present
        if profile.citations:
            citations_by_source[profile.source_id] = list(profile.citations)

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

    # Enrich relationships with canonical names and group by type
    enriched_relationships = []
    relationships_by_type: Dict[str, List[Dict[str, object]]] = {}
    for rel in character.relationships:
        rel_dict = rel.to_dict() if isinstance(rel, Relationship) else dict(rel)
        target_id = rel_dict.get("target_id") or rel_dict.get("character_id") or rel_dict.get("to", "")
        if target_id and "character_id" not in rel_dict:
            rel_dict["character_id"] = target_id
        rel_dict.setdefault("sources", [])
        rel_dict.setdefault("references", [])

        # Try to get the canonical name of the related character
        try:
            related_char = queries.get_character(str(target_id))
            rel_dict["target_name"] = related_char.canonical_name
        except Exception:
            rel_dict["target_name"] = target_id

        # Flatten attestation for dossier readability
        attestation = rel_dict.get("attestation") or []
        if isinstance(attestation, list):
            rel_dict["attestation_sources"] = [
                att.get("source_id") for att in attestation if isinstance(att, dict)
            ]
            if not rel_dict.get("sources"):
                rel_dict["sources"] = [
                    att.get("source_id") for att in attestation if isinstance(att, dict) and att.get("source_id")
                ]
            if not rel_dict.get("references"):
                att_refs: list[str] = []
                for att in attestation:
                    if isinstance(att, dict):
                        att_refs.extend(att.get("references") or [])
                rel_dict["references"] = att_refs

        enriched_relationships.append(rel_dict)

        rel_type = rel_dict.get("type", "relationship")
        relationships_by_type.setdefault(rel_type, []).append(rel_dict)

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
        DOSSIER_KEY_TRAIT_CONFLICT_SUMMARIES: trait_conflict_summaries,
        DOSSIER_KEY_RELATIONSHIPS: enriched_relationships,
        "relationships_by_type": relationships_by_type,
        DOSSIER_KEY_PARALLELS: [],
        "variants_by_source": variants_by_source,  # NEW: Textual variants
        "citations_by_source": citations_by_source,  # NEW: Bibliography citations
        DOSSIER_KEY_CLAIM_GRAPH: claim_graph.build_claim_graph_for_character(character),
    }
    return dossier


def build_event_dossier(event_id: str) -> EventDossier:
    """Build a JSON-friendly dossier for an event.

    The returned dict includes core identity fields, per-source accounts,
    and nested differences between those accounts.
    """
    event: Event = queries.get_event(event_id)
    account_conflicts = contradictions.find_events_with_conflicting_accounts(event_id)
    account_conflict_summaries = contradictions.summarize_event_conflicts(event_id)

    accounts = [
        {
            "source_id": acc.source_id,
            "reference": acc.reference,
            "summary": acc.summary,
            "notes": acc.notes,
            "variants": [
                {
                    "manuscript_family": v.manuscript_family,
                    "reading": v.reading,
                    "significance": v.significance,
                }
                for v in acc.variants
            ] if acc.variants else [],  # NEW: Include variants from accounts
        }
        for acc in event.accounts
    ]

    dossier: EventDossier = {
        DOSSIER_KEY_ID: event.id,
        DOSSIER_KEY_LABEL: event.label,
        DOSSIER_KEY_PARTICIPANTS: list(event.participants),
        DOSSIER_KEY_ACCOUNTS: accounts,
        DOSSIER_KEY_ACCOUNT_CONFLICTS: account_conflicts,
        DOSSIER_KEY_ACCOUNT_CONFLICT_SUMMARIES: account_conflict_summaries,
        DOSSIER_KEY_PARALLELS: list(event.parallels),
        "citations": list(event.citations) if event.citations else [],  # NEW: Event citations
        "textual_variants": list(event.textual_variants) if event.textual_variants else [],  # NEW: Major textual variants
        DOSSIER_KEY_CLAIM_GRAPH: claim_graph.build_claim_graph_for_event(event),
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
