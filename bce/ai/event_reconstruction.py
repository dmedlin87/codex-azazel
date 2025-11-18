"""Event reconstruction - synthesize multi-source event accounts into comparative timelines.

This module builds comparative reconstructions of events showing how different
sources describe the same event with variations.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .. import queries, contradictions
from ..exceptions import ConfigurationError
from .config import ensure_ai_enabled
from .embeddings import embed_text, cosine_similarity


def build_event_timeline(
    event_id: str,
) -> Dict[str, Any]:
    """Build a comparative timeline reconstruction of an event.

    Analyzes multiple source accounts of the same event and creates a
    structured comparison showing agreements and conflicts.

    Parameters
    ----------
    event_id : str
        Event identifier

    Returns
    -------
    dict
        Timeline reconstruction with elements, conflicts, and synthesis

    Raises
    ------
    ConfigurationError
        If AI features are disabled

    Examples
    --------
    >>> from bce.ai import event_reconstruction
    >>> timeline = event_reconstruction.build_event_timeline("crucifixion")
    >>> for element in timeline["timeline_elements"]:
    ...     print(f"{element['element']}: conflict={element['conflict']}")
    """
    ensure_ai_enabled()

    event = queries.get_event(event_id)

    if not event.accounts or len(event.accounts) < 2:
        return {
            "event_id": event_id,
            "message": "Event requires at least 2 accounts for timeline reconstruction",
            "timeline_elements": [],
        }

    # Extract timeline elements from accounts
    timeline_elements = _extract_timeline_elements(event)

    # Build synthesis
    synthesis = _synthesize_event_narrative(event, timeline_elements)

    return {
        "event_id": event_id,
        "event_label": event.label,
        "timeline_elements": timeline_elements,
        "synthesis": synthesis,
        "source_count": len(event.accounts),
        "sources": [acc.source_id for acc in event.accounts],
    }


def compare_event_sequences(
    event_ids: List[str],
    source_id: str,
) -> Dict[str, Any]:
    """Compare the sequence of multiple events within a source.

    Analyzes how a source orders and connects multiple events.

    Parameters
    ----------
    event_ids : list of str
        Event identifiers in proposed sequence
    source_id : str
        Source to analyze

    Returns
    -------
    dict
        Sequence analysis
    """
    ensure_ai_enabled()

    events = [queries.get_event(eid) for eid in event_ids]

    # Check which events have accounts in this source
    sequence = []
    for event in events:
        account = next((acc for acc in event.accounts if acc.source_id == source_id), None)
        if account:
            sequence.append({
                "event_id": event.id,
                "event_label": event.label,
                "reference": account.reference,
                "summary": account.summary,
            })

    # Analyze sequence
    analysis = {
        "source_id": source_id,
        "requested_sequence": event_ids,
        "present_events": [s["event_id"] for s in sequence],
        "missing_events": [eid for eid in event_ids if eid not in [s["event_id"] for s in sequence]],
        "sequence": sequence,
    }

    return analysis


def _extract_timeline_elements(event: Any) -> List[Dict[str, Any]]:
    """Extract comparable timeline elements from event accounts."""
    elements = []

    # Common timeline elements to look for
    element_patterns = {
        "time_of_day": ["time", "hour", "day", "morning", "evening", "noon", "midnight"],
        "location": ["at", "in", "near", "place", "where"],
        "participants": ["who", "present", "with", "accompanied"],
        "sequence": ["first", "then", "after", "before", "next", "finally"],
        "duration": ["long", "days", "hours", "while", "until"],
        "final_words": ["said", "words", "spoke", "cried"],
        "actions": ["did", "performed", "took", "gave"],
    }

    # Extract elements from each account
    for elem_name, keywords in element_patterns.items():
        element = _extract_element_across_accounts(event, elem_name, keywords)
        if element and element.get("sources"):
            elements.append(element)

    return elements


def _extract_element_across_accounts(
    event: Any,
    element_name: str,
    keywords: List[str],
) -> Optional[Dict[str, Any]]:
    """Extract a specific element across all accounts."""
    sources_data = {}

    for account in event.accounts:
        # Search for element in summary
        summary_lower = account.summary.lower()

        # Look for keywords
        found_content = None
        for keyword in keywords:
            if keyword in summary_lower:
                # Extract context around keyword
                idx = summary_lower.find(keyword)
                start = max(0, idx - 30)
                end = min(len(account.summary), idx + 70)
                found_content = account.summary[start:end].strip()
                break

        if found_content:
            sources_data[account.source_id] = found_content

    if not sources_data:
        return None

    # Check for conflicts
    conflict = len(set(sources_data.values())) > 1

    # Perform AI analysis if conflict
    ai_analysis = None
    if conflict:
        ai_analysis = _analyze_element_conflict(element_name, sources_data)

    return {
        "element": element_name,
        "sources": sources_data,
        "conflict": conflict,
        "ai_analysis": ai_analysis,
    }


def _analyze_element_conflict(
    element_name: str,
    sources_data: Dict[str, str],
) -> str:
    """Analyze why an element conflicts across sources."""
    values = list(sources_data.values())

    # Use semantic similarity
    if len(values) >= 2:
        embeddings = [embed_text(v) for v in values]

        similarities = []
        for i in range(len(embeddings)):
            for j in range(i + 1, len(embeddings)):
                sim = cosine_similarity(embeddings[i], embeddings[j])
                similarities.append(sim)

        avg_sim = sum(similarities) / len(similarities) if similarities else 0.0

        # Generate analysis based on similarity
        if avg_sim > 0.75:
            return f"Minor variation in {element_name} - likely different wording of same detail"
        elif avg_sim > 0.5:
            return f"Moderate difference in {element_name} - different emphases or perspectives"
        else:
            return f"Significant discrepancy in {element_name} - genuinely conflicting accounts"

    return f"Variation in {element_name} across sources"


def _synthesize_event_narrative(
    event: Any,
    timeline_elements: List[Dict[str, Any]],
) -> str:
    """Synthesize a narrative explaining the multi-source comparison."""
    synthesis = f"Analysis of {event.label} across {len(event.accounts)} source(s).\n\n"

    # Count conflicts
    conflict_count = sum(1 for elem in timeline_elements if elem["conflict"])

    if conflict_count == 0:
        synthesis += "Sources show high agreement with no significant conflicts. "
        synthesis += "Accounts appear to derive from similar tradition or share common source."
    elif conflict_count <= 2:
        synthesis += f"Sources agree on most details but show {conflict_count} area(s) of variation. "
        synthesis += "Differences may reflect oral transmission variants or theological emphases."
    else:
        synthesis += f"Sources present {conflict_count} significant variations. "
        synthesis += "Each source preserves distinct tradition with different narrative priorities."

    # Highlight key conflicts
    if conflict_count > 0:
        synthesis += "\n\nKey variations:\n"
        for elem in timeline_elements:
            if elem["conflict"] and elem.get("ai_analysis"):
                synthesis += f"- {elem['element']}: {elem['ai_analysis']}\n"

    # Mention parallels if present
    if hasattr(event, 'parallels') and event.parallels:
        parallel_types = set(p.get("type", "") for p in event.parallels)
        if "synoptic_parallel" in parallel_types:
            synthesis += "\nSynoptic parallels indicate shared source material with independent redaction."

    return synthesis


def reconstruct_passion_narrative() -> Dict[str, Any]:
    """Reconstruct the passion narrative across all gospels.

    Special convenience function for the passion sequence.

    Returns
    -------
    dict
        Comprehensive passion narrative reconstruction
    """
    ensure_ai_enabled()

    # Common passion events
    passion_events = [
        "last_supper",
        "gethsemane",
        "arrest",
        "trial_before_sanhedrin",
        "trial_before_pilate",
        "crucifixion",
        "burial",
        "resurrection_appearance",
    ]

    # Build reconstruction for each event
    reconstructions = {}
    for event_id in passion_events:
        try:
            event = queries.get_event(event_id)
            timeline = build_event_timeline(event_id)
            reconstructions[event_id] = timeline
        except Exception:
            # Event might not exist in dataset
            reconstructions[event_id] = {
                "event_id": event_id,
                "message": "Event not found in dataset",
            }

    # Generate overall synthesis
    total_conflicts = sum(
        len([e for e in r.get("timeline_elements", []) if e.get("conflict")])
        for r in reconstructions.values()
    )

    synthesis = f"Passion narrative reconstruction across {len(passion_events)} events. "
    synthesis += f"Total conflicts detected: {total_conflicts}. "

    if total_conflicts > 10:
        synthesis += "Significant variation across gospel accounts suggests independent traditions "
        synthesis += "with different theological and narrative priorities."
    elif total_conflicts > 5:
        synthesis += "Moderate variation indicates shared tradition with source-specific emphases."
    else:
        synthesis += "High agreement suggests coordinated narrative or strong oral tradition."

    return {
        "narrative_type": "passion",
        "events": reconstructions,
        "synthesis": synthesis,
        "total_events": len(passion_events),
        "events_found": sum(1 for r in reconstructions.values() if "timeline_elements" in r),
    }


def reconstruct_ministry_sequence(
    source_id: str,
) -> Dict[str, Any]:
    """Reconstruct the ministry sequence as presented in a specific source.

    Parameters
    ----------
    source_id : str
        Source identifier

    Returns
    -------
    dict
        Ministry sequence reconstruction
    """
    ensure_ai_enabled()

    # Get all events
    all_events = queries.list_all_events()

    # Filter to events with this source
    source_events = []
    for event in all_events:
        account = next((acc for acc in event.accounts if acc.source_id == source_id), None)
        if account:
            source_events.append({
                "event_id": event.id,
                "event_label": event.label,
                "reference": account.reference,
                "summary": account.summary,
            })

    return {
        "source_id": source_id,
        "event_count": len(source_events),
        "events": source_events,
        "note": "Events listed but not ordered - chronological sequence requires reference parsing",
    }
