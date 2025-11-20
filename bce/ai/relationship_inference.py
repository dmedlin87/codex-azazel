"""Relationship inference between characters based on co-occurrence and textual evidence.

This module suggests potential relationships between characters that may not
be explicitly recorded in the data.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set
from collections import defaultdict

from .. import queries
from ..exceptions import ConfigurationError
from .config import ensure_ai_enabled
from .embeddings import embed_text, cosine_similarity


def infer_relationships_for_character(
    character_id: str,
    confidence_threshold: float = 0.6,
) -> List[Dict[str, Any]]:
    """Infer potential relationships for a character.

    Analyzes co-occurrence in events, trait mentions, and existing
    relationship patterns to suggest new relationships.

    Parameters
    ----------
    character_id : str
        Character identifier
    confidence_threshold : float, optional
        Minimum confidence score (default: 0.6)

    Returns
    -------
    list of dict
        Suggested relationships with evidence

    Raises
    ------
    ConfigurationError
        If AI features are disabled

    Examples
    --------
    >>> from bce.ai import relationship_inference
    >>> suggestions = relationship_inference.infer_relationships_for_character("martha_of_bethany")
    >>> for sugg in suggestions:
    ...     print(f"{sugg['character_id']} -> {sugg['suggested_type']}: {sugg['confidence']}")
    """
    ensure_ai_enabled()

    char = queries.get_character(character_id)

    # Get existing relationships
    existing = {getattr(rel, "target_id", None) for rel in char.relationships}

    # Find potential relationships
    suggestions = []

    # 1. Co-occurrence in events
    event_cooccurrences = _find_event_cooccurrences(character_id)
    for other_char, events in event_cooccurrences.items():
        if other_char not in existing:
            sugg = _analyze_event_cooccurrence(
                character_id,
                other_char,
                events,
            )
            if sugg and sugg["confidence"] >= confidence_threshold:
                sugg["already_exists"] = False
                suggestions.append(sugg)

    # 2. Mentioned in same traits/contexts
    trait_associations = _find_trait_associations(character_id)
    for other_char, contexts in trait_associations.items():
        if other_char not in existing:
            sugg = _analyze_trait_association(
                character_id,
                other_char,
                contexts,
            )
            if sugg and sugg["confidence"] >= confidence_threshold:
                # Merge with existing suggestion if present
                existing_sugg = next((s for s in suggestions if s["character_id"] == other_char), None)
                if existing_sugg:
                    # Combine evidence
                    existing_sugg["evidence"].extend(sugg["evidence"])
                    existing_sugg["confidence"] = max(existing_sugg["confidence"], sugg["confidence"])
                else:
                    sugg["already_exists"] = False
                    suggestions.append(sugg)

    # 3. Check existing relationships (mark them as already_exists=True)
    for rel in char.relationships:
        other_id = getattr(rel, "target_id", None)
        if other_id:
            suggestions.append({
                "character_id": other_id,
                "suggested_type": getattr(rel, "type", None) or "unknown",
                "confidence": 1.0,
                "evidence": [getattr(rel, "description", None) or getattr(rel, "notes", "Existing relationship")],
                "already_exists": True,
            })

    # Sort by confidence
    suggestions.sort(key=lambda x: x["confidence"], reverse=True)

    return suggestions


def infer_all_relationships(
    confidence_threshold: float = 0.7,
) -> Dict[str, List[Dict[str, Any]]]:
    """Infer relationships for all characters.

    Parameters
    ----------
    confidence_threshold : float, optional
        Minimum confidence score (default: 0.7)

    Returns
    -------
    dict
        Mapping of character_id to list of relationship suggestions
    """
    ensure_ai_enabled()

    all_chars = queries.list_character_ids()
    results = {}

    for char_id in all_chars:
        suggestions = infer_relationships_for_character(
            char_id,
            confidence_threshold=confidence_threshold,
        )
        # Filter to only new relationships
        new_suggestions = [s for s in suggestions if not s["already_exists"]]
        if new_suggestions:
            results[char_id] = new_suggestions

    return results


def _find_event_cooccurrences(character_id: str) -> Dict[str, List[str]]:
    """Find characters that co-occur in events."""
    events = queries.list_events_for_character(character_id)

    cooccurrences = defaultdict(list)

    for event in events:
        for participant_id in event.participants:
            if participant_id != character_id:
                cooccurrences[participant_id].append(event.id)

    return dict(cooccurrences)


def _find_trait_associations(character_id: str) -> Dict[str, List[str]]:
    """Find characters mentioned in similar trait contexts."""
    char = queries.get_character(character_id)

    associations = defaultdict(list)

    # Extract all characters mentioned in trait values
    all_chars = {c.id: c.canonical_name for c in queries.list_all_characters()}

    for profile in char.source_profiles:
        for trait_key, trait_val in profile.traits.items():
            # Check if other character names appear in trait text
            trait_lower = trait_val.lower()
            for other_id, other_name in all_chars.items():
                if other_id != character_id:
                    if other_id.replace("_", " ") in trait_lower or other_name.lower() in trait_lower:
                        associations[other_id].append(f"{trait_key}: {trait_val}")

    return dict(associations)


def _analyze_event_cooccurrence(
    char_id: str,
    other_char_id: str,
    event_ids: List[str],
) -> Optional[Dict[str, Any]]:
    """Analyze co-occurrence in events to infer relationship type."""
    if not event_ids:
        return None

    # Get character details
    char = queries.get_character(char_id)
    other_char = queries.get_character(other_char_id)

    # Determine relationship type based on events and roles
    rel_type = _infer_relationship_type(char, other_char, event_ids)

    # Build evidence
    evidence = [
        f"Co-occur in {len(event_ids)} event(s): {', '.join(event_ids[:3])}{'...' if len(event_ids) > 3 else ''}"
    ]

    # Add specific event contexts
    for event_id in event_ids[:2]:
        event = queries.get_event(event_id)
        evidence.append(f"Event '{event.label}' involves both characters")

    # Calculate confidence
    confidence = _calculate_cooccurrence_confidence(len(event_ids), rel_type)

    return {
        "character_id": other_char_id,
        "suggested_type": rel_type,
        "confidence": confidence,
        "evidence": evidence,
    }


def _analyze_trait_association(
    char_id: str,
    other_char_id: str,
    contexts: List[str],
) -> Optional[Dict[str, Any]]:
    """Analyze trait associations to infer relationship."""
    if not contexts:
        return None

    # Infer type from context
    rel_type = "associated"
    confidence = 0.6

    # Check for family keywords
    family_keywords = ["brother", "sister", "mother", "father", "son", "daughter"]
    for context in contexts:
        context_lower = context.lower()
        for keyword in family_keywords:
            if keyword in context_lower:
                rel_type = "family"
                confidence = 0.9
                break

    # Check for disciple/teacher keywords
    if "disciple" in " ".join(contexts).lower():
        rel_type = "teacher_disciple"
        confidence = 0.85

    evidence = [f"Mentioned in trait context: {ctx[:100]}..." for ctx in contexts[:3]]

    return {
        "character_id": other_char_id,
        "suggested_type": rel_type,
        "confidence": confidence,
        "evidence": evidence,
    }


def _infer_relationship_type(
    char: Any,
    other_char: Any,
    event_ids: List[str],
) -> str:
    """Infer relationship type based on character roles and events."""
    # Check roles
    char_roles = set(char.roles)
    other_roles = set(other_char.roles)

    # Apostle/disciple relationships
    if "apostle" in char_roles or "disciple" in char_roles:
        if "apostle" in other_roles or "disciple" in other_roles:
            return "fellow_disciple"
        elif any(role in other_roles for role in ["teacher", "rabbi", "messiah"]):
            return "teacher_student"

    # Religious authority relationships
    if any(role in char_roles for role in ["priest", "pharisee", "sadducee"]):
        if any(role in other_roles for role in ["priest", "pharisee", "sadducee"]):
            return "religious_colleague"

    # Political relationships
    if any(role in char_roles for role in ["governor", "tetrarch", "ruler"]):
        if any(role in other_roles for role in ["governor", "tetrarch", "ruler"]):
            return "political_associate"

    # Default
    if len(event_ids) > 3:
        return "frequent_associate"
    else:
        return "associate"


def _calculate_cooccurrence_confidence(event_count: int, rel_type: str) -> float:
    """Calculate confidence based on co-occurrence frequency and type."""
    # Base confidence on event count
    base = min(0.5 + (event_count * 0.1), 0.95)

    # Adjust for relationship type specificity
    specific_types = ["teacher_student", "fellow_disciple", "family", "sibling"]
    if rel_type in specific_types:
        base += 0.1

    return min(base, 0.97)


def suggest_missing_relationships() -> List[Dict[str, Any]]:
    """Suggest characters that might be missing relationship data.

    Returns
    -------
    list of dict
        Characters with potential missing relationships
    """
    ensure_ai_enabled()

    all_chars = queries.list_all_characters()
    suggestions = []

    for char in all_chars:
        if len(char.relationships) == 0:
            # Character has no relationships - check if they should
            events = queries.list_events_for_character(char.id)
            if events:
                # Has events but no relationships - likely missing data
                participant_counts = defaultdict(int)
                for event in events:
                    for participant_id in event.participants:
                        if participant_id != char.id:
                            participant_counts[participant_id] += 1

                if participant_counts:
                    suggestions.append({
                        "character_id": char.id,
                        "canonical_name": char.canonical_name,
                        "reason": "Has event participation but no documented relationships",
                        "frequent_associates": [
                            {"character_id": k, "event_count": v}
                            for k, v in sorted(participant_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                        ],
                    })

    return suggestions
