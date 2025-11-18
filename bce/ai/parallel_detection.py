"""Parallel passage detection for synoptic and variant accounts.

This module automatically identifies parallel accounts of events across
different sources using semantic similarity and structural analysis.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from collections import defaultdict

from .. import queries
from ..exceptions import ConfigurationError
from .config import ensure_ai_enabled
from .embeddings import embed_text, cosine_similarity
from .cache import cached_analysis


def detect_event_parallels(
    event_id: str,
    similarity_threshold: float = 0.7,
    use_cache: bool = True,
) -> Dict[str, Any]:
    """Detect parallel accounts for an event across sources.

    Uses semantic similarity to identify parallel pericopes and variant
    accounts. Helps populate the 'parallels' field in event JSON.

    Parameters
    ----------
    event_id : str
        Event identifier
    similarity_threshold : float, optional
        Minimum similarity score to consider passages parallel (default: 0.7)
    use_cache : bool, optional
        Whether to use cached results (default: True)

    Returns
    -------
    dict
        Parallel detection results with keys: event_id, parallels

    Raises
    ------
    ConfigurationError
        If AI features are disabled

    Examples
    --------
    >>> from bce.ai import parallel_detection
    >>> parallels = parallel_detection.detect_event_parallels("crucifixion")
    >>> for parallel in parallels["parallels"]:
    ...     print(f"{parallel['sources']}: {parallel['similarity_score']}")
    """
    ensure_ai_enabled()

    if use_cache:
        return _cached_detect_parallels(event_id, similarity_threshold)
    else:
        return _detect_parallels_impl(event_id, similarity_threshold)


@cached_analysis(ttl_hours=48, namespace="parallel_detection")
def _cached_detect_parallels(event_id: str, similarity_threshold: float) -> Dict[str, Any]:
    """Cached wrapper for parallel detection."""
    return _detect_parallels_impl(event_id, similarity_threshold)


def _detect_parallels_impl(event_id: str, similarity_threshold: float) -> Dict[str, Any]:
    """Internal implementation of parallel detection."""
    event = queries.get_event(event_id)

    if not event.accounts or len(event.accounts) < 2:
        return {
            "event_id": event_id,
            "parallels": [],
            "message": "Event has fewer than 2 accounts; no parallels to detect."
        }

    # Compute embeddings for each account
    account_embeddings = []
    for account in event.accounts:
        # Combine summary and notes for embedding
        text = account.summary
        if account.notes:
            text += " " + account.notes

        embedding = embed_text(text)
        account_embeddings.append({
            "source_id": account.source_id,
            "reference": account.reference,
            "summary": account.summary,
            "embedding": embedding,
        })

    # Find parallel groups using similarity
    parallel_groups = _find_parallel_groups(account_embeddings, similarity_threshold)

    # Format parallels
    parallels = []
    for group in parallel_groups:
        sources = [acc["source_id"] for acc in group]
        references = {acc["source_id"]: acc["reference"] for acc in group}

        # Calculate average similarity within group
        similarities = []
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                sim = cosine_similarity(group[i]["embedding"], group[j]["embedding"])
                similarities.append(sim)

        avg_similarity = sum(similarities) / len(similarities) if similarities else 0.0

        # Determine parallel type
        parallel_type = _classify_parallel_type(sources, avg_similarity)

        # Generate narrative overlap assessment
        narrative_overlap = _assess_narrative_overlap(avg_similarity)

        # Generate suggested summary
        summaries = [acc["summary"] for acc in group]
        suggested_summary = _generate_combined_summary(summaries)

        parallels.append({
            "sources": sources,
            "type": parallel_type,
            "references": references,
            "similarity_score": round(avg_similarity, 2),
            "narrative_overlap": narrative_overlap,
            "suggested_summary": suggested_summary,
        })

    # Check for unique johannine accounts (if not already in parallels)
    if any(acc.source_id == "john" for acc in event.accounts):
        john_in_parallels = any("john" in p["sources"] for p in parallels)
        if not john_in_parallels:
            john_account = next(acc for acc in event.accounts if acc.source_id == "john")
            parallels.append({
                "sources": ["john"],
                "type": "johannine_unique",
                "references": {"john": john_account.reference},
                "similarity_score": 0.0,
                "narrative_overlap": "unique",
                "suggested_summary": john_account.summary,
                "notes": "Unique Johannine account with no synoptic parallel"
            })

    return {
        "event_id": event_id,
        "parallels": parallels,
    }


def find_parallel_events(
    reference: str,
    similarity_threshold: float = 0.65,
) -> List[Dict[str, Any]]:
    """Find events that parallel a given scripture reference.

    Parameters
    ----------
    reference : str
        Scripture reference (e.g., "Mark 6:30-44")
    similarity_threshold : float, optional
        Minimum similarity threshold (default: 0.65)

    Returns
    -------
    list of dict
        Events with parallel accounts
    """
    ensure_ai_enabled()

    # Parse reference to get source
    source_id = _parse_source_from_reference(reference)

    if not source_id:
        return []

    # Find all events with this source
    all_events = queries.list_all_events()
    matches = []

    for event in all_events:
        for account in event.accounts:
            if account.reference == reference or account.source_id == source_id:
                # Check if event has other accounts
                other_accounts = [acc for acc in event.accounts if acc.reference != reference]
                if other_accounts:
                    matches.append({
                        "event_id": event.id,
                        "event_label": event.label,
                        "reference": account.reference,
                        "parallel_references": [acc.reference for acc in other_accounts],
                        "parallel_sources": [acc.source_id for acc in other_accounts],
                    })

    return matches


def _find_parallel_groups(
    accounts: List[Dict[str, Any]],
    threshold: float,
) -> List[List[Dict[str, Any]]]:
    """Group accounts by similarity."""
    if len(accounts) < 2:
        return [[acc] for acc in accounts]

    # Calculate pairwise similarities
    n = len(accounts)
    similarity_matrix = []
    for i in range(n):
        row = []
        for j in range(n):
            if i == j:
                row.append(1.0)
            else:
                sim = cosine_similarity(accounts[i]["embedding"], accounts[j]["embedding"])
                row.append(sim)
        similarity_matrix.append(row)

    # Simple clustering: merge accounts above threshold
    groups = []
    assigned = [False] * n

    for i in range(n):
        if assigned[i]:
            continue

        # Start new group
        group = [accounts[i]]
        assigned[i] = True

        # Find similar accounts
        for j in range(i + 1, n):
            if assigned[j]:
                continue

            # Check if j is similar to any in group
            is_similar = any(
                similarity_matrix[group_idx][j] >= threshold
                for group_idx in range(len(accounts))
                if accounts[group_idx] in group
            )

            if is_similar:
                group.append(accounts[j])
                assigned[j] = True

        groups.append(group)

    return groups


def _classify_parallel_type(sources: List[str], similarity: float) -> str:
    """Classify the type of parallel based on sources and similarity."""
    # Check for synoptic sources
    synoptic = {"mark", "matthew", "luke"}
    source_set = set(sources)

    if source_set <= synoptic:
        # All synoptic
        if len(source_set) == 3:
            return "triple_tradition"
        elif len(source_set) == 2:
            if "mark" in source_set:
                return "synoptic_parallel"
            else:
                return "q_material_candidate"  # Matthew-Luke without Mark
        else:
            return "synoptic_unique"
    elif "john" in sources and len(sources) > 1:
        if source_set & synoptic:
            return "synoptic_johannine_parallel"
        else:
            return "johannine_variant"
    elif "john" in sources:
        return "johannine_unique"
    else:
        return "parallel"


def _assess_narrative_overlap(similarity: float) -> str:
    """Assess narrative overlap level based on similarity score."""
    if similarity >= 0.9:
        return "very_high"
    elif similarity >= 0.75:
        return "high"
    elif similarity >= 0.6:
        return "medium"
    elif similarity >= 0.4:
        return "low"
    else:
        return "minimal"


def _generate_combined_summary(summaries: List[str]) -> str:
    """Generate a combined summary from multiple account summaries."""
    if not summaries:
        return ""

    if len(summaries) == 1:
        return summaries[0]

    # For now, use the longest summary as base
    # Could be enhanced with actual text synthesis
    longest = max(summaries, key=len)

    # Add note about variations
    if len(summaries) > 1:
        return f"{longest} (with variations across {len(summaries)} accounts)"

    return longest


def _parse_source_from_reference(reference: str) -> Optional[str]:
    """Extract source ID from scripture reference."""
    # Common patterns
    gospels = ["Mark", "Matthew", "Luke", "John"]
    for gospel in gospels:
        if reference.startswith(gospel):
            return gospel.lower()

    if reference.startswith("Acts"):
        return "acts"

    # Pauline epistles
    pauline = [
        "Romans", "1 Corinthians", "2 Corinthians", "Galatians",
        "Ephesians", "Philippians", "Colossians", "1 Thessalonians",
        "2 Thessalonians", "1 Timothy", "2 Timothy", "Titus", "Philemon"
    ]
    for letter in pauline:
        if reference.startswith(letter):
            return "paul_undisputed"  # Simplified for now

    return None


def suggest_parallel_pericopes(
    min_similarity: float = 0.7,
) -> List[Dict[str, Any]]:
    """Suggest parallel pericopes across all events.

    Scans all events and identifies potential parallel groups that could
    be added to event JSON files.

    Parameters
    ----------
    min_similarity : float, optional
        Minimum similarity threshold (default: 0.7)

    Returns
    -------
    list of dict
        Suggested parallel groupings
    """
    ensure_ai_enabled()

    all_events = queries.list_all_events()
    suggestions = []

    for event in all_events:
        if len(event.accounts) >= 2:
            result = _detect_parallels_impl(event.id, min_similarity)
            if result["parallels"]:
                suggestions.append({
                    "event_id": event.id,
                    "event_label": event.label,
                    "suggested_parallels": result["parallels"],
                })

    return suggestions
