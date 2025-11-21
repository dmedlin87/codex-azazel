"""
Data completeness auditor for identifying gaps and inconsistencies.

This module uses AI to analyze the dataset and suggest improvements.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from typing import Any, Dict, List, Optional, Sequence

from .. import contradictions
from ..queries import get_character, get_event, list_all_characters, list_all_events
from ..sources import list_source_ids
from .cache import AIResultCache
from .config import ensure_ai_enabled
from . import clustering, semantic_contradictions


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


def build_curation_review_queue(
    entity_type: str = "character",
    limit: Optional[int] = None,
    use_cache: bool = True,
) -> Dict[str, Any]:
    """Rank review tasks by combining completeness, conflict density, and uncertainty.

    The resulting queue prioritizes items that most need human curation by
    blending: (1) completeness gaps, (2) structural conflict density, and
    (3) semantic uncertainty signals.
    """
    ensure_ai_enabled()
    entity_type = entity_type.lower()
    if entity_type not in {"character", "event"}:
        raise ValueError("entity_type must be 'character' or 'event'")

    cache_key = f"{entity_type}_{limit or 'all'}"
    cache = AIResultCache("curation_review_queue", max_age_seconds=1800)
    if use_cache:
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

    items: List[Dict[str, Any]] = []
    if entity_type == "character":
        for char in list_all_characters():
            items.append(_score_character_review_task(char.id, use_cache=use_cache))
    else:
        for event in list_all_events():
            items.append(_score_event_review_task(event.id, use_cache=use_cache))

    # Sort by priority and trim if requested
    items.sort(key=lambda item: item["priority_score"], reverse=True)
    if limit is not None:
        items = items[:limit]

    summary = {
        "entity_type": entity_type,
        "items_scored": len(items),
        "average_priority": round(
            sum(item["priority_score"] for item in items) / len(items), 3
        ) if items else 0.0,
        "high_priority": len([i for i in items if i["priority_score"] >= 0.66]),
        "medium_priority": len([i for i in items if 0.33 <= i["priority_score"] < 0.66]),
        "low_priority": len([i for i in items if i["priority_score"] < 0.33]),
    }

    result = {"entity_type": entity_type, "items": items, "summary": summary}
    if use_cache:
        cache.set(cache_key, result, model_name="curation_queue")
    return result


def _score_character_review_task(
    char_id: str,
    use_cache: bool = True,
) -> Dict[str, Any]:
    """Score a single character for curation priority."""
    char = get_character(char_id)
    completeness_report = audit_character(char_id, use_cache=use_cache)
    conflict_summary = contradictions.summarize_character_conflicts(char_id)
    conflict_density = len(conflict_summary)
    high_conflict_fields = sum(
        1 for meta in conflict_summary.values() if meta["severity"] == "high"
    )
    uncertainty = _estimate_uncertainty_from_semantics(
        char_id, conflict_density, use_cache=use_cache
    )

    priority_score = _combine_priority_scores(
        completeness_report["completeness_score"],
        conflict_density,
        uncertainty,
        high_conflict_fields,
    )

    reasons = []
    if completeness_report["gap_count"]:
        reasons.append(f"{completeness_report['gap_count']} completeness gap(s)")
    if conflict_density:
        reasons.append(f"{conflict_density} conflicting trait(s)")
    if uncertainty >= 0.4:
        reasons.append("semantic conflicts need human judgment")

    recommended_actions = []
    if completeness_report["gap_count"]:
        recommended_actions.append("Fill missing references/tags in sparse source profiles.")
    if high_conflict_fields:
        recommended_actions.append("Resolve high-severity conflicts first.")
    if uncertainty >= 0.4:
        recommended_actions.append("Add notes clarifying ambiguous or divergent portrayals.")

    return {
        "id": char_id,
        "type": "character",
        "canonical_name": char.canonical_name,
        "priority_score": round(priority_score, 3),
        "metrics": {
            "completeness_score": completeness_report["completeness_score"],
            "gap_count": completeness_report["gap_count"],
            "conflict_density": conflict_density,
            "high_conflict_fields": high_conflict_fields,
            "uncertainty": round(uncertainty, 3),
        },
        "drivers": reasons,
        "recommended_actions": recommended_actions or ["Quick review for final polish."],
    }


def _score_event_review_task(
    event_id: str,
    use_cache: bool = True,
) -> Dict[str, Any]:
    """Score a single event for curation priority."""
    event = get_event(event_id)
    completeness_report = audit_event(event_id, use_cache=use_cache)
    conflict_summary = contradictions.summarize_event_conflicts(event_id)
    conflict_density = len(conflict_summary)
    high_conflict_fields = sum(
        1 for meta in conflict_summary.values() if meta["severity"] == "high"
    )
    uncertainty = min(1.0, conflict_density * 0.15 + high_conflict_fields * 0.1)

    priority_score = _combine_priority_scores(
        completeness_report["completeness_score"],
        conflict_density,
        uncertainty,
        high_conflict_fields,
    )

    reasons = []
    if completeness_report["gap_count"]:
        reasons.append(f"{completeness_report['gap_count']} completeness gap(s)")
    if conflict_density:
        reasons.append(f"{conflict_density} divergent account field(s)")
    if uncertainty >= 0.4:
        reasons.append("account conflicts need human reconciliation")

    recommended_actions = []
    if completeness_report["gap_count"]:
        recommended_actions.append("Add participant lists, tags, and parallels where missing.")
    if high_conflict_fields:
        recommended_actions.append("Clarify account summaries that conflict across sources.")
    if uncertainty >= 0.4:
        recommended_actions.append("Note plausible harmonizations or mark as disputed.")

    return {
        "id": event_id,
        "type": "event",
        "label": event.label,
        "priority_score": round(priority_score, 3),
        "metrics": {
            "completeness_score": completeness_report["completeness_score"],
            "gap_count": completeness_report["gap_count"],
            "conflict_density": conflict_density,
            "high_conflict_fields": high_conflict_fields,
            "uncertainty": round(uncertainty, 3),
        },
        "drivers": reasons,
        "recommended_actions": recommended_actions or ["Quick review for final polish."],
    }


def _combine_priority_scores(
    completeness_score: float,
    conflict_density: int,
    uncertainty: float,
    high_conflict_fields: int,
) -> float:
    """Blend completeness, conflict, and uncertainty into a single priority score."""
    gap_pressure = 1.0 - completeness_score
    conflict_pressure = min(1.0, (conflict_density * 0.12) + (high_conflict_fields * 0.08))
    uncertainty_pressure = min(1.0, uncertainty)

    score = (
        0.45 * gap_pressure
        + 0.35 * conflict_pressure
        + 0.20 * uncertainty_pressure
    )
    return max(0.0, min(1.0, score))


def _estimate_uncertainty_from_semantics(
    char_id: str,
    conflict_density: int,
    use_cache: bool = True,
) -> float:
    """Estimate uncertainty using semantic conflict analysis when available."""
    try:
        semantic = semantic_contradictions.analyze_character_traits(
            char_id, use_cache=use_cache
        )
    except ImportError:
        return min(0.6, conflict_density * 0.12)

    summary = semantic.get("summary", {})
    emphasis = summary.get("different_emphases", 0)
    complementary = summary.get("complementary_details", 0)
    genuine = summary.get("genuine_conflicts", 0)

    # Uncertainty rises with ambiguous/differing emphases, and is tempered when
    # genuine contradictions dominate (they are clearer, not ambiguous).
    raw = (emphasis * 0.2) + (complementary * 0.1) + (genuine * 0.05)
    return min(1.0, raw + (conflict_density * 0.05))


def run_cluster_guardian(
    num_clusters: int = 6,
    support_threshold: float = 0.6,
    use_cache: bool = True,
) -> Dict[str, Any]:
    """Detect cluster-level tag/role inconsistencies and alignment gaps."""
    ensure_ai_enabled()
    cache = AIResultCache("cluster_guardian", max_age_seconds=7200)
    cache_key = f"{num_clusters}_{support_threshold}"
    if use_cache:
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

    try:
        clusters = clustering.find_character_clusters(
            num_clusters=num_clusters,
            use_cache=use_cache,
        )
    except ImportError as exc:
        raise ImportError(
            "Cluster guardian requires scikit-learn. Install with "
            "'pip install codex-azazel[ai]' to enable clustering."
        ) from exc

    reports: List[Dict[str, Any]] = []
    flagged = 0

    for cluster in clusters:
        members = cluster.get("members", [])
        char_objects = [get_character(mid) for mid in members]
        tag_counts = Counter()
        role_counts = Counter()

        for char in char_objects:
            tag_counts.update(char.tags)
            role_counts.update(_normalize_roles(char.roles))

        dominant_tags = _dominant_items(tag_counts, len(char_objects), support_threshold)
        dominant_roles = _dominant_items(role_counts, len(char_objects), support_threshold)

        member_reports = []
        for char in char_objects:
            missing_cluster_tags = [t for t in dominant_tags if t not in char.tags]
            missing_role_tags = [
                tag for tag in _normalize_roles(char.roles)
                if tag not in char.tags
            ]
            outlier_tags = [t for t in char.tags if tag_counts.get(t, 0) == 1 and len(tag_counts) > 3]

            issues = missing_cluster_tags + missing_role_tags + outlier_tags
            alignment_score = 1.0
            if tag_counts or role_counts:
                alignment_score = max(
                    0.0,
                    1.0 - (len(issues) / (len(dominant_tags) + len(char.tags) + 1)),
                )

            suggestions = []
            if missing_cluster_tags:
                suggestions.append(f"Consider adding cluster tags: {missing_cluster_tags}")
            if missing_role_tags:
                suggestions.append(f"Add tags to mirror roles: {missing_role_tags}")
            if outlier_tags:
                suggestions.append(f"Verify outlier tags: {outlier_tags}")

            if issues:
                flagged += 1

            member_reports.append({
                "character_id": char.id,
                "canonical_name": char.canonical_name,
                "alignment_score": round(alignment_score, 3),
                "missing_cluster_tags": missing_cluster_tags,
                "missing_role_tags": missing_role_tags,
                "outlier_tags": outlier_tags,
                "suggestions": suggestions or ["Cluster alignment looks healthy."],
            })

        reports.append({
            "cluster_id": cluster.get("cluster_id"),
            "label": cluster.get("label"),
            "size": cluster.get("size", len(members)),
            "dominant_tags": dominant_tags,
            "dominant_roles": dominant_roles,
            "members": member_reports,
        })

    result = {
        "audit_type": "cluster_alignment_guardian",
        "clusters_checked": len(reports),
        "flags": flagged,
        "clusters": reports,
    }
    if use_cache:
        cache.set(cache_key, result, model_name="cluster_guardian")
    return result


def describe_json_edit_impact(
    before: Dict[str, Any],
    after: Dict[str, Any],
    entity_type: str = "character",
    use_cache: bool = True,
) -> Dict[str, Any]:
    """Summarize how JSON edits change completeness/conflict metrics."""
    ensure_ai_enabled()
    entity_type = entity_type.lower()
    if entity_type not in {"character", "event"}:
        raise ValueError("entity_type must be 'character' or 'event'")

    cache = AIResultCache("semantic_diff", max_age_seconds=3600)
    cache_key = _hash_diff_inputs(before, after, entity_type)
    if use_cache:
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

    before_metrics = _snapshot_metrics(before, entity_type)
    after_metrics = _snapshot_metrics(after, entity_type)

    deltas = {
        "completeness_delta": round(
            after_metrics["completeness_score"] - before_metrics["completeness_score"], 3
        ),
        "gap_delta": after_metrics["gap_count"] - before_metrics["gap_count"],
        "conflict_delta": after_metrics["conflict_density"] - before_metrics["conflict_density"],
    }

    narrative = _render_impact_narrative(before_metrics, after_metrics, deltas)

    result = {
        "entity_type": entity_type,
        "id": after.get("id") or before.get("id"),
        "before": before_metrics,
        "after": after_metrics,
        "deltas": deltas,
        "summary": narrative,
    }
    if use_cache:
        cache.set(cache_key, result, model_name="semantic_diff")
    return result


def _snapshot_metrics(data: Dict[str, Any], entity_type: str) -> Dict[str, Any]:
    """Compute lightweight completeness/conflict metrics from raw JSON dict."""
    if entity_type == "character":
        return _character_snapshot_metrics(data)
    return _event_snapshot_metrics(data)


def _character_snapshot_metrics(data: Dict[str, Any]) -> Dict[str, Any]:
    profiles: Sequence[Dict[str, Any]] = data.get("source_profiles", []) or []
    tags = data.get("tags", []) or []
    relationships = data.get("relationships", []) or []

    trait_map: Dict[str, Dict[str, str]] = {}
    for profile in profiles:
        source_id = profile.get("source_id")
        for trait, value in (profile.get("traits") or {}).items():
            if not value:
                continue
            trait_map.setdefault(trait, {})[source_id] = value

    conflicts = {
        trait: per_source
        for trait, per_source in trait_map.items()
        if len(set(per_source.values())) > 1
    }

    score_components = {
        "has_source_profiles": min(len(profiles) / 3, 1.0),
        "trait_coverage": min(
            sum(len((p.get("traits") or {})) for p in profiles) / 10, 1.0
        ),
        "has_references": 1.0 if any(p.get("references") for p in profiles) else 0.0,
        "has_tags": 1.0 if tags else 0.0,
        "has_relationships": 1.0 if relationships else 0.5,
    }

    completeness_score = sum(score_components.values()) / len(score_components)
    gaps = 0
    if not tags:
        gaps += 1
    if not relationships:
        gaps += 1
    if not profiles:
        gaps += 1
    if any(not (p.get("references") or []) for p in profiles):
        gaps += 1

    return {
        "character_id": data.get("id"),
        "completeness_score": round(completeness_score, 2),
        "gap_count": gaps,
        "conflict_density": len(conflicts),
    }


def _event_snapshot_metrics(data: Dict[str, Any]) -> Dict[str, Any]:
    accounts: Sequence[Dict[str, Any]] = data.get("accounts", []) or []
    tags = data.get("tags", []) or []
    participants = data.get("participants", []) or []
    parallels = data.get("parallels", []) or []

    field_map: Dict[str, Dict[str, str]] = {}
    for account in accounts:
        source_id = account.get("source_id")
        for field in ("summary", "notes", "reference"):
            value = account.get(field)
            if not value:
                continue
            field_map.setdefault(field, {})[source_id] = value

    conflicts = {
        field: per_source
        for field, per_source in field_map.items()
        if len(set(per_source.values())) > 1
    }

    score_components = {
        "has_accounts": min(len(accounts) / 2, 1.0),
        "has_participants": 1.0 if participants else 0.0,
        "has_tags": 1.0 if tags else 0.0,
        "has_parallels": 1.0 if parallels else 0.5,
        "account_quality": (
            1.0 if all(len((a.get("summary") or "")) >= 20 for a in accounts) else 0.5
        ),
    }
    completeness_score = sum(score_components.values()) / len(score_components)
    gaps = 0
    if not participants:
        gaps += 1
    if not tags:
        gaps += 1
    if len(accounts) < 1:
        gaps += 1
    elif len(accounts) < 2:
        gaps += 1

    return {
        "event_id": data.get("id") or data.get("event_id"),
        "completeness_score": round(completeness_score, 2),
        "gap_count": gaps,
        "conflict_density": len(conflicts),
    }


def _render_impact_narrative(
    before: Dict[str, Any],
    after: Dict[str, Any],
    deltas: Dict[str, Any],
) -> List[str]:
    """Create human-readable summary lines for diff impact."""
    lines = []
    comp_delta = deltas["completeness_delta"]
    if comp_delta > 0:
        lines.append(f"Completeness improved by +{comp_delta:.2f}.")
    elif comp_delta < 0:
        lines.append(f"Completeness dropped by {comp_delta:.2f}.")

    gap_delta = deltas["gap_delta"]
    if gap_delta < 0:
        lines.append(f"Closed {-gap_delta} gap(s).")
    elif gap_delta > 0:
        lines.append(f"Introduced {gap_delta} new gap(s).")

    conflict_delta = deltas["conflict_delta"]
    if conflict_delta < 0:
        lines.append(f"Reduced conflicts by {-conflict_delta}.")
    elif conflict_delta > 0:
        lines.append(f"Conflict density increased by {conflict_delta}.")

    if not lines:
        lines.append("No material change detected in completeness or conflicts.")
    return lines


def _dominant_items(
    counts: Counter,
    population: int,
    threshold: float,
) -> List[str]:
    """Return items that meet the support threshold within a cluster."""
    if population <= 0:
        return []
    return [
        item
        for item, count in counts.items()
        if population and (count / population) >= threshold and count >= 2
    ]


def _normalize_roles(roles: Sequence[str]) -> List[str]:
    """Normalize role labels into tag-like tokens."""
    normalized = []
    for role in roles:
        token = role.lower().replace(" ", "_")
        if token:
            normalized.append(token)
    return normalized


def _hash_diff_inputs(
    before: Dict[str, Any],
    after: Dict[str, Any],
    entity_type: str,
) -> str:
    """Generate a repeatable hash for diff cache keys."""
    payload = json.dumps(
        {"before": before, "after": after, "entity_type": entity_type},
        sort_keys=True,
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


__all__ = [
    "audit_characters",
    "audit_character",
    "audit_events",
    "audit_event",
    "build_curation_review_queue",
    "run_cluster_guardian",
    "describe_json_edit_impact",
]
