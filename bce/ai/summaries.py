"""Natural language summary generation from structured dossiers.

This module generates readable narrative summaries from character and event
dossiers for export and documentation purposes.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .. import dossiers
from ..exceptions import ConfigurationError
from .config import ensure_ai_enabled


def generate_character_summary(
    dossier: Dict[str, Any],
    style: str = "academic",
    max_words: int = 200,
) -> str:
    """Generate a natural language summary from a character dossier.

    Parameters
    ----------
    dossier : dict
        Character dossier (from build_character_dossier)
    style : str, optional
        Summary style: "academic", "accessible", or "technical" (default: "academic")
    max_words : int, optional
        Maximum word count (default: 200)

    Returns
    -------
    str
        Natural language summary

    Raises
    ------
    ConfigurationError
        If AI features are disabled

    Examples
    --------
    >>> from bce import api
    >>> from bce.ai import summaries
    >>> dossier = api.build_character_dossier("paul")
    >>> summary = summaries.generate_character_summary(dossier, style="academic")
    >>> print(summary)
    """
    ensure_ai_enabled()

    if style == "academic":
        return _generate_academic_character_summary(dossier, max_words)
    elif style == "accessible":
        return _generate_accessible_character_summary(dossier, max_words)
    elif style == "technical":
        return _generate_technical_character_summary(dossier, max_words)
    else:
        raise ValueError(f"Unknown style: {style}. Use 'academic', 'accessible', or 'technical'.")


def generate_event_summary(
    dossier: Dict[str, Any],
    style: str = "academic",
    max_words: int = 150,
) -> str:
    """Generate a natural language summary from an event dossier.

    Parameters
    ----------
    dossier : dict
        Event dossier (from build_event_dossier)
    style : str, optional
        Summary style (default: "academic")
    max_words : int, optional
        Maximum word count (default: 150)

    Returns
    -------
    str
        Natural language summary
    """
    ensure_ai_enabled()

    if style == "academic":
        return _generate_academic_event_summary(dossier, max_words)
    elif style == "accessible":
        return _generate_accessible_event_summary(dossier, max_words)
    elif style == "technical":
        return _generate_technical_event_summary(dossier, max_words)
    else:
        raise ValueError(f"Unknown style: {style}")


def _generate_academic_character_summary(dossier: Dict[str, Any], max_words: int) -> str:
    """Generate academic-style character summary."""
    identity = dossier["identity"]
    name = identity["canonical_name"]

    # Opening
    parts = [f"{name}"]

    # Sources
    sources = list(dossier["traits_by_source"].keys())
    if sources:
        source_list = _format_source_list(sources)
        parts.append(f"appears in {source_list} as")

    # Roles
    roles = identity.get("roles", [])
    if roles:
        role_list = _format_list(roles, "and")
        parts.append(f"{role_list}")
    else:
        parts.append("a significant figure")

    summary = " ".join(parts) + "."

    # Add source-specific highlights
    highlights = _extract_source_highlights(dossier)
    if highlights:
        summary += " " + " ".join(highlights[:2])

    # Add conflicts if present
    conflicts = dossier.get("conflicts", {})
    if conflicts:
        conflict_count = len(conflicts)
        summary += f" Sources present {conflict_count} significant contradiction{'s' if conflict_count > 1 else ''}"

        # Mention a key conflict
        if conflicts:
            first_conflict_key = list(conflicts.keys())[0]
            first_conflict = conflicts[first_conflict_key]
            values = first_conflict.get("values", {})
            if len(values) >= 2:
                conflict_sources = list(values.values())
                summary += f" regarding {first_conflict_key.replace('_', ' ')}"
                summary += f" ({', '.join(conflict_sources[0])} vs {', '.join(conflict_sources[1])})."

    # Relationships
    relationships = dossier.get("relationships", [])
    if relationships and len(relationships) > 0:
        rel_count = len(relationships)
        summary += f" Documented relationships include {rel_count} connection{'s' if rel_count > 1 else ''}"

        # Mention key relationships
        key_rels = [r for r in relationships[:2]]
        if key_rels:
            rel_names = [r.get("to", "unknown") for r in key_rels]
            summary += f" with {_format_list(rel_names, 'and')}."

    # Trim to max words
    return _trim_to_words(summary, max_words)


def _generate_accessible_character_summary(dossier: Dict[str, Any], max_words: int) -> str:
    """Generate accessible-style character summary."""
    identity = dossier["identity"]
    name = identity["canonical_name"]

    # Simpler opening
    summary = f"{name} is"

    # Roles in simple language
    roles = identity.get("roles", [])
    if roles:
        summary += f" known as {_format_list(roles, 'and')}"
    else:
        summary += " a significant figure in the New Testament"

    summary += ". "

    # Describe appearances
    sources = list(dossier["traits_by_source"].keys())
    if sources:
        summary += f"This character appears in {len(sources)} different source{'s' if len(sources) > 1 else ''}"

        # Mention which sources
        if len(sources) <= 3:
            summary += f": {_format_list(sources, 'and')}."
        else:
            summary += f", including {_format_list(sources[:3], 'and')} and others."

    # Highlight interesting traits
    all_traits = dossier.get("all_traits", {})
    if all_traits:
        interesting_traits = [k for k in list(all_traits.keys())[:2]]
        if interesting_traits:
            trait_list = [t.replace("_", " ") for t in interesting_traits]
            summary += f" Key characteristics include {_format_list(trait_list, 'and')}."

    return _trim_to_words(summary, max_words)


def _generate_technical_character_summary(dossier: Dict[str, Any], max_words: int) -> str:
    """Generate technical-style character summary."""
    identity = dossier["identity"]
    char_id = identity["id"]
    name = identity["canonical_name"]

    summary = f"Character ID: {char_id} ({name}). "

    # Source coverage
    sources = list(dossier["traits_by_source"].keys())
    summary += f"Source profiles: {len(sources)} ({', '.join(sources)}). "

    # Trait count
    all_traits = dossier.get("all_traits", {})
    summary += f"Total traits: {len(all_traits)}. "

    # Reference count
    all_refs = dossier.get("all_references", [])
    summary += f"Scripture references: {len(all_refs)}. "

    # Conflict count
    conflicts = dossier.get("conflicts", {})
    summary += f"Detected conflicts: {len(conflicts)}. "

    # Relationship count
    relationships = dossier.get("relationships", [])
    summary += f"Relationships: {len(relationships)}. "

    # Tags
    tags = identity.get("tags", [])
    if tags:
        summary += f"Tags: {', '.join(tags[:5])}."

    return _trim_to_words(summary, max_words)


def _generate_academic_event_summary(dossier: Dict[str, Any], max_words: int) -> str:
    """Generate academic-style event summary."""
    identity = dossier["identity"]
    label = identity["label"]

    summary = f"{label}"

    # Participants
    participants = dossier.get("participants", [])
    if participants:
        summary += f" involves {len(participants)} participant{'s' if len(participants) > 1 else ''}"
        if len(participants) <= 4:
            summary += f": {_format_list(participants, 'and')}"

    summary += ". "

    # Accounts
    accounts = dossier.get("accounts", [])
    if accounts:
        summary += f"Attested in {len(accounts)} source{'s' if len(accounts) > 1 else ''}"

        # List sources
        account_sources = [acc["source_id"] for acc in accounts]
        if len(account_sources) <= 4:
            summary += f" ({_format_list(account_sources, 'and')})"

        summary += ". "

        # Mention parallels if present
        parallels = dossier.get("parallels", [])
        if parallels:
            parallel_types = set(p.get("type", "unknown") for p in parallels)
            if "synoptic_parallel" in parallel_types or "triple_tradition" in parallel_types:
                summary += "Synoptic parallel accounts show narrative agreement with minor variations. "

    # Conflicts
    conflicts = dossier.get("conflicts", {})
    if conflicts:
        summary += f"Sources diverge on {len(conflicts)} aspect{'s' if len(conflicts) > 1 else ''}"

        # Mention key conflict
        if conflicts:
            first_key = list(conflicts.keys())[0]
            summary += f" including {first_key.replace('_', ' ')}."

    return _trim_to_words(summary, max_words)


def _generate_accessible_event_summary(dossier: Dict[str, Any], max_words: int) -> str:
    """Generate accessible-style event summary."""
    identity = dossier["identity"]
    label = identity["label"]

    summary = f"The {label.lower()}"

    # Use first account summary if available
    accounts = dossier.get("accounts", [])
    if accounts and accounts[0].get("summary"):
        summary += f" is described as: {accounts[0]['summary']}"
    else:
        summary += " is an important New Testament event"

    summary += ". "

    # Mention sources simply
    if accounts:
        account_sources = [acc["source_id"] for acc in accounts]
        summary += f"This event is recorded in {_format_list(account_sources, 'and')}. "

    # Participants
    participants = dossier.get("participants", [])
    if participants:
        summary += f"The people involved include {_format_list(participants[:4], 'and')}"
        if len(participants) > 4:
            summary += " and others"
        summary += ". "

    return _trim_to_words(summary, max_words)


def _generate_technical_event_summary(dossier: Dict[str, Any], max_words: int) -> str:
    """Generate technical-style event summary."""
    identity = dossier["identity"]
    event_id = identity["id"]
    label = identity["label"]

    summary = f"Event ID: {event_id} ({label}). "

    # Account count
    accounts = dossier.get("accounts", [])
    summary += f"Accounts: {len(accounts)}. "

    # Sources
    if accounts:
        account_sources = [acc["source_id"] for acc in accounts]
        summary += f"Sources: {', '.join(account_sources)}. "

    # Participants
    participants = dossier.get("participants", [])
    summary += f"Participants: {len(participants)} ({', '.join(participants[:5])}). "

    # Parallels
    parallels = dossier.get("parallels", [])
    summary += f"Parallel groups: {len(parallels)}. "

    # Conflicts
    conflicts = dossier.get("conflicts", {})
    summary += f"Conflicts: {len(conflicts)}. "

    # Tags
    tags = identity.get("tags", [])
    if tags:
        summary += f"Tags: {', '.join(tags)}."

    return _trim_to_words(summary, max_words)


def _format_source_list(sources: List[str]) -> str:
    """Format source list for narrative."""
    source_names = {
        "mark": "Mark",
        "matthew": "Matthew",
        "luke": "Luke",
        "john": "John",
        "acts": "Acts",
        "paul_undisputed": "the Pauline epistles",
    }

    formatted = [source_names.get(s, s) for s in sources]
    return _format_list(formatted, "and")


def _format_list(items: List[str], conjunction: str = "and") -> str:
    """Format a list with proper grammar."""
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} {conjunction} {items[1]}"
    return ", ".join(items[:-1]) + f", {conjunction} {items[-1]}"


def _extract_source_highlights(dossier: Dict[str, Any]) -> List[str]:
    """Extract interesting highlights from source profiles."""
    highlights = []
    traits_by_source = dossier.get("traits_by_source", {})

    for source, traits in traits_by_source.items():
        if not traits:
            continue

        # Look for distinctive traits
        distinctive_keys = [
            "messianic_self_understanding", "divine_claims", "authority_source",
            "death_method", "conversion_experience", "leadership_role"
        ]

        for key in distinctive_keys:
            if key in traits:
                trait_value = traits[key]
                highlight = f"{source.capitalize()} emphasizes {key.replace('_', ' ')}: {trait_value[:80]}."
                highlights.append(highlight)
                break

    return highlights


def _trim_to_words(text: str, max_words: int) -> str:
    """Trim text to maximum word count."""
    words = text.split()
    if len(words) <= max_words:
        return text

    trimmed = " ".join(words[:max_words])
    # Try to end at a sentence
    if "." in trimmed:
        last_period = trimmed.rfind(".")
        trimmed = trimmed[: last_period + 1]

    return trimmed
