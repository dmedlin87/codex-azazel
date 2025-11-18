"""
Data completeness auditor for identifying gaps and inconsistencies.

This module uses AI to analyze the dataset and suggest improvements.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..queries import get_character, get_event, list_all_characters, list_all_events
from ..sources import list_source_ids
from .cache import AIResultCache
from .config import ensure_ai_enabled


def audit_characters(use_cache: bool = True) -> Dict[str, Any]:
    """Audit all characters for completeness and consistency.

    Identifies:
    - Missing source profiles
    - Sparse trait coverage
    - Missing tags
    - Relationship gaps
    - Reference coverage

    Args:
        use_cache: Whether to use cached results (default: True)

    Returns:
        Dictionary mapping character_id -> audit report

    Raises:
        ConfigurationError: If AI features are disabled
    """
    ensure_ai_enabled()

    # Check cache first
    if use_cache:
        cache = AIResultCache("completeness_audit", max_age_seconds=86400)
        cached_result = cache.get("all_characters")
        if cached_result is not None:
            return cached_result

    characters = list_all_characters()
    all_source_ids = set(list_source_ids())
    audit_results = {}

    for char in characters:
        audit = audit_character(char.id, use_cache=False)
        audit_results[char.id] = audit

    result = {
        "audit_type": "characters",
        "total_characters": len(characters),
        "results": audit_results,
        "summary": _summarize_character_audits(audit_results),
    }

    # Cache the result
    if use_cache:
        cache.set("all_characters", result, model_name="completeness_audit")

    return result


def audit_character(char_id: str, use_cache: bool = True) -> Dict[str, Any]:
    """Audit a single character for completeness.

    Args:
        char_id: The character ID to audit
        use_cache: Whether to use cached results (default: True)

    Returns:
        Audit report for the character

    Raises:
        ConfigurationError: If AI features are disabled
    """
    ensure_ai_enabled()

    # Check cache first
    if use_cache:
        cache = AIResultCache("completeness_audit", max_age_seconds=86400)
        cached_result = cache.get(char_id)
        if cached_result is not None:
            return cached_result

    character = get_character(char_id)
    all_source_ids = set(list_source_ids())
    gaps = []
    inconsistencies = []

    # Check for missing source profiles
    character_sources = set(sp.source_id for sp in character.source_profiles)
    missing_sources = all_source_ids - character_sources

    for source_id in missing_sources:
        # Only flag as gap if the character might appear in that source
        # (This is a simple heuristic; could be enhanced with AI analysis)
        if _likely_appears_in_source(character, source_id):
            gaps.append({
                "type": "missing_source_profile",
                "source": source_id,
                "priority": "medium",
                "suggestion": (
                    f"{character.canonical_name} may appear in {source_id} "
                    f"but lacks a source profile. Consider adding one if applicable."
                ),
            })

    # Check for sparse trait coverage in existing profiles
    for profile in character.source_profiles:
        trait_count = len(profile.traits)
        if trait_count < 2:
            gaps.append({
                "type": "sparse_traits",
                "source": profile.source_id,
                "priority": "low",
                "suggestion": (
                    f"{profile.source_id} profile has only {trait_count} trait(s). "
                    f"Consider adding more detail if source material supports it."
                ),
            })

        # Check for missing references
        if not profile.references:
            gaps.append({
                "type": "missing_references",
                "source": profile.source_id,
                "priority": "high",
                "suggestion": (
                    f"{profile.source_id} profile lacks scripture references. "
                    f"Add references to support the trait claims."
                ),
            })

    # Check for missing tags
    if not character.tags:
        gaps.append({
            "type": "missing_tags",
            "priority": "medium",
            "suggestion": (
                f"{character.canonical_name} has no tags. "
                f"Add topical tags for better discovery and organization."
            ),
        })

    # Check for missing relationships
    if not character.relationships:
        gaps.append({
            "type": "missing_relationships",
            "priority": "low",
            "suggestion": (
                f"{character.canonical_name} has no documented relationships. "
                f"Consider adding relationship data if applicable."
            ),
        })

    # Check for tag/role consistency
    if character.roles:
        role_tags = set(r.lower().replace(" ", "_") for r in character.roles)
        char_tags = set(character.tags)
        missing_role_tags = role_tags - char_tags
        if missing_role_tags and len(missing_role_tags) <= 3:
            inconsistencies.append({
                "type": "tag_role_mismatch",
                "issue": (
                    f"Character has roles {character.roles} but missing related tags: "
                    f"{list(missing_role_tags)}"
                ),
                "priority": "low",
            })

    # Calculate completeness score (0.0 to 1.0)
    score_components = {
        "has_source_profiles": min(len(character.source_profiles) / 3, 1.0),
        "trait_coverage": min(
            sum(len(sp.traits) for sp in character.source_profiles) / 10, 1.0
        ),
        "has_references": (
            1.0 if any(sp.references for sp in character.source_profiles) else 0.0
        ),
        "has_tags": 1.0 if character.tags else 0.0,
        "has_relationships": 1.0 if character.relationships else 0.5,
    }

    completeness_score = sum(score_components.values()) / len(score_components)

    result = {
        "character_id": char_id,
        "canonical_name": character.canonical_name,
        "completeness_score": round(completeness_score, 2),
        "score_components": score_components,
        "gaps": gaps,
        "inconsistencies": inconsistencies,
        "gap_count": len(gaps),
        "inconsistency_count": len(inconsistencies),
    }

    # Cache the result
    if use_cache:
        cache = AIResultCache("completeness_audit", max_age_seconds=86400)
        cache.set(char_id, result, model_name="completeness_audit")

    return result


def _likely_appears_in_source(character, source_id: str) -> bool:
    """Simple heuristic to check if character likely appears in source.

    This is a placeholder for more sophisticated AI-based detection.
    Currently uses simple rules based on source and character properties.
    """
    # Major gospel sources
    gospel_sources = {"mark", "matthew", "luke", "john"}
    # Pauline sources
    pauline_sources = {"paul_undisputed", "paul_disputed"}

    # If character already has profiles in gospels, might appear in other gospels
    char_sources = {sp.source_id for sp in character.source_profiles}
    if source_id in gospel_sources and char_sources & gospel_sources:
        return True

    # If character has Paul profile, might appear in other Pauline sources
    if source_id in pauline_sources and char_sources & pauline_sources:
        return True

    # Otherwise, don't flag as likely missing (conservative approach)
    return False


def _summarize_character_audits(audits: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Summarize audit results across all characters."""
    total_gaps = sum(a["gap_count"] for a in audits.values())
    total_inconsistencies = sum(a["inconsistency_count"] for a in audits.values())
    avg_completeness = (
        sum(a["completeness_score"] for a in audits.values()) / len(audits)
        if audits
        else 0.0
    )

    characters_needing_attention = [
        char_id
        for char_id, audit in audits.items()
        if audit["completeness_score"] < 0.70
    ]

    return {
        "total_gaps": total_gaps,
        "total_inconsistencies": total_inconsistencies,
        "average_completeness": round(avg_completeness, 2),
        "characters_needing_attention": characters_needing_attention,
        "attention_count": len(characters_needing_attention),
    }


def audit_events(use_cache: bool = True) -> Dict[str, Any]:
    """Audit all events for completeness and consistency.

    Similar to character auditing but for events.

    Args:
        use_cache: Whether to use cached results (default: True)

    Returns:
        Dictionary mapping event_id -> audit report

    Raises:
        ConfigurationError: If AI features are disabled
    """
    ensure_ai_enabled()

    # Check cache first
    if use_cache:
        cache = AIResultCache("completeness_audit", max_age_seconds=86400)
        cached_result = cache.get("all_events")
        if cached_result is not None:
            return cached_result

    events = list_all_events()
    audit_results = {}

    for event in events:
        audit = audit_event(event.id, use_cache=False)
        audit_results[event.id] = audit

    result = {
        "audit_type": "events",
        "total_events": len(events),
        "results": audit_results,
        "summary": _summarize_event_audits(audit_results),
    }

    # Cache the result
    if use_cache:
        cache.set("all_events", result, model_name="completeness_audit")

    return result


def audit_event(event_id: str, use_cache: bool = True) -> Dict[str, Any]:
    """Audit a single event for completeness.

    Args:
        event_id: The event ID to audit
        use_cache: Whether to use cached results (default: True)

    Returns:
        Audit report for the event

    Raises:
        ConfigurationError: If AI features are disabled
    """
    ensure_ai_enabled()

    # Check cache first
    if use_cache:
        cache = AIResultCache("completeness_audit", max_age_seconds=86400)
        cache_key = f"event_{event_id}"
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return cached_result

    event = get_event(event_id)
    gaps = []
    inconsistencies = []

    # Check for missing accounts (at least should have 1-2 accounts)
    if len(event.accounts) < 1:
        gaps.append({
            "type": "no_accounts",
            "priority": "critical",
            "suggestion": f"Event '{event.label}' has no accounts. Add at least one account.",
        })
    elif len(event.accounts) < 2:
        gaps.append({
            "type": "single_account",
            "priority": "medium",
            "suggestion": (
                f"Event '{event.label}' has only one account. "
                f"Consider adding parallel accounts if they exist."
            ),
        })

    # Check for missing participants
    if not event.participants:
        gaps.append({
            "type": "missing_participants",
            "priority": "high",
            "suggestion": (
                f"Event '{event.label}' has no documented participants. "
                f"Add participant character IDs."
            ),
        })

    # Check for missing tags
    if not event.tags:
        gaps.append({
            "type": "missing_tags",
            "priority": "medium",
            "suggestion": (
                f"Event '{event.label}' has no tags. "
                f"Add topical tags for better discovery."
            ),
        })

    # Check for missing parallels
    if not event.parallels and len(event.accounts) > 1:
        gaps.append({
            "type": "missing_parallels",
            "priority": "low",
            "suggestion": (
                f"Event '{event.label}' has multiple accounts but no documented parallels. "
                f"Consider adding parallel pericope data."
            ),
        })

    # Check account quality
    for account in event.accounts:
        if not account.summary or len(account.summary) < 10:
            gaps.append({
                "type": "sparse_account_summary",
                "source": account.source_id,
                "priority": "medium",
                "suggestion": (
                    f"Account from {account.source_id} has very brief or missing summary. "
                    f"Expand the summary for better context."
                ),
            })

    # Calculate completeness score
    score_components = {
        "has_accounts": min(len(event.accounts) / 2, 1.0),
        "has_participants": 1.0 if event.participants else 0.0,
        "has_tags": 1.0 if event.tags else 0.0,
        "has_parallels": 1.0 if event.parallels else 0.5,
        "account_quality": (
            1.0 if all(len(a.summary) >= 20 for a in event.accounts) else 0.5
        ),
    }

    completeness_score = sum(score_components.values()) / len(score_components)

    result = {
        "event_id": event_id,
        "label": event.label,
        "completeness_score": round(completeness_score, 2),
        "score_components": score_components,
        "gaps": gaps,
        "inconsistencies": inconsistencies,
        "gap_count": len(gaps),
        "inconsistency_count": len(inconsistencies),
    }

    # Cache the result
    if use_cache:
        cache = AIResultCache("completeness_audit", max_age_seconds=86400)
        cache.set(cache_key, result, model_name="completeness_audit")

    return result


def _summarize_event_audits(audits: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Summarize audit results across all events."""
    total_gaps = sum(a["gap_count"] for a in audits.values())
    total_inconsistencies = sum(a["inconsistency_count"] for a in audits.values())
    avg_completeness = (
        sum(a["completeness_score"] for a in audits.values()) / len(audits)
        if audits
        else 0.0
    )

    events_needing_attention = [
        event_id
        for event_id, audit in audits.items()
        if audit["completeness_score"] < 0.70
    ]

    return {
        "total_gaps": total_gaps,
        "total_inconsistencies": total_inconsistencies,
        "average_completeness": round(avg_completeness, 2),
        "events_needing_attention": events_needing_attention,
        "attention_count": len(events_needing_attention),
    }


__all__ = [
    "audit_characters",
    "audit_character",
    "audit_events",
    "audit_event",
]
