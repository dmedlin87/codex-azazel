from __future__ import annotations

from typing import Any, Dict

from . import queries
from . import claim_graph


def _find_conflicts(field_map: Dict[str, Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    conflicts: Dict[str, Dict[str, str]] = {}
    for field_name, per_source in field_map.items():
        values = {v for v in per_source.values() if v}
        if len(values) > 1:
            conflicts[field_name] = per_source
    return conflicts


def _index_claim_conflicts(conflict_block: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Index serialized claim conflicts by predicate for quick lookups."""

    conflicts = conflict_block.get("conflicts") if isinstance(conflict_block, dict) else None
    if not isinstance(conflicts, list):
        return {}

    result: Dict[str, Dict[str, Any]] = {}
    for entry in conflicts:
        if isinstance(entry, dict) and isinstance(entry.get("predicate"), str):
            result[entry["predicate"]] = entry
    return result


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


def _classify_trait_category(trait_name: str) -> str:
    """Best-effort classification of a character trait into a conflict category.

    This is intentionally heuristic and conservative; categories are designed
    to be stable, human-readable labels rather than a strict taxonomy.
    """

    name = trait_name.lower()
    if "birth" in name or "narrative" in name or "story" in name:
        return "narrative"
    if "chronolog" in name or "date" in name or "timeline" in name or "order" in name:
        return "chronology"
    if "christolog" in name or "theolog" in name or "resurrect" in name or "salvation" in name:
        return "theology"
    if "location" in name or "place" in name or "region" in name or "city" in name:
        return "geography"
    return "other"


def _classify_event_field_category(field_name: str) -> str:
    """Classify an event account field into a conflict category."""

    if field_name == "reference":
        return "chronology"
    if field_name in {"summary", "notes"}:
        return "narrative"
    return "other"


def _estimate_severity(num_sources: int, num_distinct: int) -> str:
    """Estimate conflict severity from how many sources and values disagree."""

    if num_distinct >= 3 or num_sources >= 4:
        return "high"
    if num_distinct == 2 and num_sources >= 3:
        return "medium"
    return "low"


def summarize_character_conflicts(char_id: str) -> Dict[str, Dict[str, Any]]:
    """Summarize character trait conflicts with basic severity metadata.

    Returns
    -------
    dict
        Mapping ``trait -> info`` where ``info`` includes:

        - ``field``: the trait name
        - ``severity``: "low", "medium", or "high"
        - ``category``: coarse category such as "narrative" or "theology"
        - ``sources``: the original ``source_id -> value`` mapping
        - ``distinct_values``: list of distinct non-empty values
        - ``notes``: short human-readable summary string
    """

    character = queries.get_character(char_id)
    conflicts = find_trait_conflicts(char_id)
    claim_conflicts = _index_claim_conflicts(claim_graph.build_claim_graph_for_character(character))
    summary: Dict[str, Dict[str, Any]] = {}

    for trait, per_source in conflicts.items():
        values = {v for v in per_source.values() if v}
        num_sources = len(per_source)
        num_distinct = len(values)
        severity = _estimate_severity(num_sources, num_distinct)
        claim_conflict = claim_conflicts.get(trait, {})
        category = claim_conflict.get("claim_type") or _classify_trait_category(trait)
        conflict_type = claim_conflict.get("conflict_type") or category
        harmonization_moves = claim_conflict.get("harmonization_moves") or []

        summary[trait] = {
            "field": trait,
            "severity": severity,
            "category": category,
            "conflict_type": conflict_type,
            "claim_type": category,
            "aspect": claim_conflict.get("aspect"),
            "sources": per_source,
            "distinct_values": sorted(values),
            "harmonization_moves": harmonization_moves,
            "dominant_value": claim_conflict.get("dominant_value"),
            "notes": f"{num_distinct} distinct value(s) across {num_sources} source(s)",
            "rationale": claim_conflict.get("rationale"),
        }

    return summary


def summarize_event_conflicts(event_id: str) -> Dict[str, Dict[str, Any]]:
    """Summarize event account conflicts with basic severity metadata.

    Returns
    -------
    dict
        Mapping ``field_name -> info`` where ``info`` includes:

        - ``field``: the account field name (e.g. "summary")
        - ``severity``: "low", "medium", or "high"
        - ``category``: coarse category such as "narrative" or "chronology"
        - ``sources``: the original ``source_id -> value`` mapping
        - ``distinct_values``: list of distinct non-empty values
        - ``notes``: short human-readable summary string
    """

    event = queries.get_event(event_id)
    conflicts = find_events_with_conflicting_accounts(event_id)
    claim_conflicts = _index_claim_conflicts(claim_graph.build_claim_graph_for_event(event))
    summary: Dict[str, Dict[str, Any]] = {}

    for field_name, per_source in conflicts.items():
        values = {v for v in per_source.values() if v}
        num_sources = len(per_source)
        num_distinct = len(values)
        severity = _estimate_severity(num_sources, num_distinct)
        claim_conflict = claim_conflicts.get(field_name, {})
        category = claim_conflict.get("claim_type") or _classify_event_field_category(field_name)
        conflict_type = claim_conflict.get("conflict_type") or category
        harmonization_moves = claim_conflict.get("harmonization_moves") or []

        summary[field_name] = {
            "field": field_name,
            "severity": severity,
            "category": category,
            "conflict_type": conflict_type,
            "claim_type": category,
            "aspect": claim_conflict.get("aspect"),
            "sources": per_source,
            "distinct_values": sorted(values),
            "harmonization_moves": harmonization_moves,
            "dominant_value": claim_conflict.get("dominant_value"),
            "notes": f"{num_distinct} distinct value(s) across {num_sources} source(s)",
            "rationale": claim_conflict.get("rationale"),
        }

    return summary
