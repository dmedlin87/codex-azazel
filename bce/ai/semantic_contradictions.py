"""
Semantic contradiction detection using AI.

This module enhances the basic string-matching contradiction detection
with semantic understanding to distinguish genuine conflicts from
complementary details.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..contradictions import compare_character_sources, find_trait_conflicts
from ..queries import get_character
from .cache import AIResultCache
from .config import ensure_ai_enabled
from .embeddings import cosine_similarity, embed_texts, EmbeddingCache


def analyze_character_traits(
    char_id: str,
    use_cache: bool = True,
) -> Dict[str, Any]:
    """Analyze character trait conflicts with semantic understanding.

    This function enhances basic contradiction detection by using
    semantic embeddings to determine if differing traits are:
    - Genuinely contradictory (low similarity)
    - Complementary details (high similarity)
    - Different emphases of the same concept (medium similarity)

    Args:
        char_id: The character ID to analyze
        use_cache: Whether to use cached results (default: True)

    Returns:
        Dictionary with semantic analysis of all trait conflicts

    Raises:
        ConfigurationError: If AI features are disabled
        ImportError: If required AI dependencies are missing

    Example:
        >>> result = analyze_character_traits("jesus")
        >>> for trait, analysis in result["analyzed_conflicts"].items():
        ...     if analysis["is_genuine_conflict"]:
        ...         print(f"Conflict in {trait}: {analysis['explanation']}")
    """
    ensure_ai_enabled()

    # Check cache first
    if use_cache:
        cache = AIResultCache("semantic_contradictions", max_age_seconds=86400)
        cached_result = cache.get(char_id)
        if cached_result is not None:
            return cached_result

    # Get character and basic conflicts
    character = get_character(char_id)
    basic_conflicts = find_trait_conflicts(char_id)

    # If no basic conflicts, no semantic conflicts either
    if not basic_conflicts:
        result = {
            "character_id": char_id,
            "canonical_name": character.canonical_name,
            "has_conflicts": False,
            "analyzed_conflicts": {},
            "summary": {
                "total_conflicts": 0,
                "genuine_conflicts": 0,
                "complementary_details": 0,
                "different_emphases": 0,
            },
        }
        if use_cache:
            cache.set(char_id, result, model_name="semantic_analysis")
        return result

    # Analyze each conflict semantically
    analyzed_conflicts = {}
    embedding_cache = EmbeddingCache("character_traits")

    for trait_key, source_values in basic_conflicts.items():
        analysis = _analyze_trait_conflict(
            trait_key, source_values, embedding_cache
        )
        analyzed_conflicts[trait_key] = analysis

    # Generate summary statistics
    genuine_count = sum(
        1 for a in analyzed_conflicts.values() if a["is_genuine_conflict"]
    )
    complementary_count = sum(
        1 for a in analyzed_conflicts.values()
        if a["conflict_type"] == "complementary_details"
    )
    emphasis_count = sum(
        1 for a in analyzed_conflicts.values()
        if a["conflict_type"] == "different_emphasis"
    )

    result = {
        "character_id": char_id,
        "canonical_name": character.canonical_name,
        "has_conflicts": True,
        "analyzed_conflicts": analyzed_conflicts,
        "summary": {
            "total_conflicts": len(analyzed_conflicts),
            "genuine_conflicts": genuine_count,
            "complementary_details": complementary_count,
            "different_emphases": emphasis_count,
        },
    }

    # Cache the result
    if use_cache:
        cache.set(char_id, result, model_name="semantic_analysis")

    return result


def _analyze_trait_conflict(
    trait_key: str,
    source_values: Dict[str, str],
    embedding_cache: EmbeddingCache,
) -> Dict[str, Any]:
    """Analyze a single trait conflict semantically.

    Args:
        trait_key: The trait being analyzed
        source_values: Dict mapping source_id -> trait value
        embedding_cache: Cache for embeddings

    Returns:
        Analysis dictionary with semantic understanding
    """
    # Get all unique values
    values = list(source_values.values())
    sources = list(source_values.keys())

    # Compute embeddings for all values
    embeddings = []
    for value in values:
        emb = embedding_cache.get_or_compute(value)
        embeddings.append(emb)

    # Compute pairwise similarities
    similarities = []
    for i in range(len(embeddings)):
        for j in range(i + 1, len(embeddings)):
            sim = cosine_similarity(embeddings[i], embeddings[j])
            similarities.append(sim)

    # Average similarity score
    avg_similarity = sum(similarities) / len(similarities) if similarities else 1.0

    # Classify conflict based on similarity
    if avg_similarity >= 0.80:
        conflict_type = "complementary_details"
        is_genuine_conflict = False
        severity = "low"
        explanation = (
            f"Sources provide similar information about '{trait_key}' with minor wording differences. "
            f"These appear to be complementary details rather than contradictory accounts."
        )
    elif avg_similarity >= 0.50:
        conflict_type = "different_emphasis"
        is_genuine_conflict = False
        severity = "medium"
        explanation = (
            f"Sources present '{trait_key}' with different emphases or perspectives. "
            f"While not identical, these accounts may reflect different theological or narrative priorities "
            f"rather than outright contradictions."
        )
    else:
        conflict_type = "genuine_contradiction"
        is_genuine_conflict = True
        severity = "high"
        explanation = (
            f"Sources present significantly different accounts of '{trait_key}'. "
            f"The low semantic similarity suggests these are genuinely contradictory claims "
            f"that cannot be easily reconciled."
        )

    return {
        "trait": trait_key,
        "sources": source_values,
        "semantic_analysis": {
            "is_genuine_conflict": is_genuine_conflict,
            "conflict_type": conflict_type,
            "similarity_score": round(avg_similarity, 3),
            "explanation": explanation,
            "severity": severity,
        },
    }


def analyze_event_conflicts(
    event_id: str,
    use_cache: bool = True,
) -> Dict[str, Any]:
    """Analyze event account conflicts with semantic understanding.

    Similar to character trait analysis, but for event accounts.

    Args:
        event_id: The event ID to analyze
        use_cache: Whether to use cached results (default: True)

    Returns:
        Dictionary with semantic analysis of event account conflicts

    Raises:
        ConfigurationError: If AI features are disabled
        ImportError: If required AI dependencies are missing
    """
    ensure_ai_enabled()

    from ..contradictions import find_events_with_conflicting_accounts
    from ..queries import get_event

    # Check cache first
    if use_cache:
        cache = AIResultCache("semantic_contradictions", max_age_seconds=86400)
        cache_key = f"event_{event_id}"
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return cached_result

    # Get event and basic conflicts
    event = get_event(event_id)
    basic_conflicts = find_events_with_conflicting_accounts(event_id)

    # If no basic conflicts, no semantic conflicts either
    if not basic_conflicts:
        result = {
            "event_id": event_id,
            "label": event.label,
            "has_conflicts": False,
            "analyzed_conflicts": {},
            "summary": {
                "total_conflicts": 0,
                "genuine_conflicts": 0,
                "complementary_details": 0,
                "different_emphases": 0,
            },
        }
        if use_cache:
            cache.set(cache_key, result, model_name="semantic_analysis")
        return result

    # Analyze each conflict semantically (same logic as character traits)
    analyzed_conflicts = {}
    embedding_cache = EmbeddingCache("event_accounts")

    for field_key, account_values in basic_conflicts.items():
        analysis = _analyze_trait_conflict(
            field_key, account_values, embedding_cache
        )
        analyzed_conflicts[field_key] = analysis

    # Generate summary statistics
    genuine_count = sum(
        1 for a in analyzed_conflicts.values() if a["is_genuine_conflict"]
    )
    complementary_count = sum(
        1 for a in analyzed_conflicts.values()
        if a["conflict_type"] == "complementary_details"
    )
    emphasis_count = sum(
        1 for a in analyzed_conflicts.values()
        if a["conflict_type"] == "different_emphasis"
    )

    result = {
        "event_id": event_id,
        "label": event.label,
        "has_conflicts": True,
        "analyzed_conflicts": analyzed_conflicts,
        "summary": {
            "total_conflicts": len(analyzed_conflicts),
            "genuine_conflicts": genuine_count,
            "complementary_details": complementary_count,
            "different_emphases": emphasis_count,
        },
    }

    # Cache the result
    if use_cache:
        cache.set(cache_key, result, model_name="semantic_analysis")

    return result


__all__ = [
    "analyze_character_traits",
    "analyze_event_conflicts",
]
