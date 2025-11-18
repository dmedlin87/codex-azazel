from __future__ import annotations

from typing import Any, Dict, List, Optional

from . import dossiers, queries, contradictions, search, export, export_graph, bibles


# Core data access

def get_character(char_id: str):
    """Return a Character object by ID.

    Loads and returns a complete Character object with all source profiles,
    relationships, tags, and metadata.

    Parameters
    ----------
    char_id : str
        Character identifier (e.g., "jesus", "paul", "peter")

    Returns
    -------
    Character
        Complete character object with all fields populated

    Raises
    ------
    DataNotFoundError
        If the character ID does not exist
    StorageError
        If the character file cannot be read or parsed

    Examples
    --------
    >>> from bce import api
    >>> jesus = api.get_character("jesus")
    >>> print(jesus.canonical_name)
    Jesus of Nazareth
    >>> print(jesus.list_sources())
    ['mark', 'matthew', 'luke', 'john', 'paul_undisputed']
    """

    return queries.get_character(char_id)


def get_event(event_id: str):
    """Return an Event object by ID.

    Loads and returns a complete Event object with all accounts, participants,
    parallels, and tags.

    Parameters
    ----------
    event_id : str
        Event identifier (e.g., "crucifixion", "resurrection_appearance")

    Returns
    -------
    Event
        Complete event object with all fields populated

    Raises
    ------
    DataNotFoundError
        If the event ID does not exist
    StorageError
        If the event file cannot be read or parsed

    Examples
    --------
    >>> from bce import api
    >>> crucifixion = api.get_event("crucifixion")
    >>> print(crucifixion.label)
    Crucifixion of Jesus
    >>> print([acc.source_id for acc in crucifixion.accounts])
    ['mark', 'john']
    """

    return queries.get_event(event_id)


def list_character_ids() -> List[str]:
    """List all character IDs in sorted order."""

    return queries.list_character_ids()


def list_event_ids() -> List[str]:
    """List all event IDs in sorted order."""

    return queries.list_event_ids()


def list_characters() -> List[str]:
    """Alias for ``list_character_ids`` for ergonomic API usage."""

    return list_character_ids()


def list_events() -> List[str]:
    """Alias for ``list_event_ids`` for ergonomic API usage."""

    return list_event_ids()


# Dossiers


def build_character_dossier(char_id: str) -> Dict[str, Any]:
    """Build a comprehensive JSON-friendly dossier for a character.

    A dossier includes the character's identity (name, aliases, roles, tags),
    per-source traits organized by source ID, all scripture references,
    relationships with other characters, and detected conflicts between sources.

    Parameters
    ----------
    char_id : str
        Character identifier

    Returns
    -------
    dict
        Character dossier with keys: identity, traits_by_source, all_traits,
        references_by_source, all_references, relationships, conflicts

    Raises
    ------
    DataNotFoundError
        If the character does not exist

    Examples
    --------
    >>> from bce import api
    >>> dossier = api.build_character_dossier("paul")
    >>> print(dossier["identity"]["canonical_name"])
    Paul (Saul of Tarsus)
    >>> print(dossier["conflicts"].keys())
    dict_keys(['conversion_timeline', 'authority_source'])
    """

    return dossiers.build_character_dossier(char_id)


def build_event_dossier(event_id: str) -> Dict[str, Any]:
    """Build a comprehensive JSON-friendly dossier for an event.

    An event dossier includes the event's identity (label, tags), all
    participating characters, per-source accounts with references and
    summaries, parallel pericope information, and detected conflicts
    between different accounts.

    Parameters
    ----------
    event_id : str
        Event identifier

    Returns
    -------
    dict
        Event dossier with keys: identity, participants, accounts,
        parallels, conflicts

    Raises
    ------
    DataNotFoundError
        If the event does not exist

    Examples
    --------
    >>> from bce import api
    >>> dossier = api.build_event_dossier("crucifixion")
    >>> print(dossier["identity"]["label"])
    Crucifixion of Jesus
    >>> print(len(dossier["accounts"]))
    2
    """

    return dossiers.build_event_dossier(event_id)


def build_all_character_dossiers() -> List[Dict[str, Any]]:
    """Build dossiers for all characters."""

    return dossiers.build_all_character_dossiers()


def build_all_event_dossiers() -> List[Dict[str, Any]]:
    """Build dossiers for all events."""

    return dossiers.build_all_event_dossiers()


# Conflicts


def summarize_character_conflicts(char_id: str) -> Dict[str, Dict[str, Any]]:
    """Return normalized conflict summaries for a character's traits.

    Analyzes a character's source profiles and identifies traits where
    different sources provide conflicting information. The summary groups
    sources by their reported value for each conflicting trait.

    Parameters
    ----------
    char_id : str
        Character identifier

    Returns
    -------
    dict
        Mapping of trait name to conflict summary. Each conflict summary
        has a "values" key mapping trait values to lists of sources.
        Empty dict if no conflicts exist.

    Raises
    ------
    DataNotFoundError
        If the character does not exist

    Examples
    --------
    >>> from bce import api
    >>> conflicts = api.summarize_character_conflicts("judas")
    >>> print(conflicts["death_method"]["values"])
    {'hanging': ['matthew'], 'falling_headlong': ['acts']}
    """

    return contradictions.summarize_character_conflicts(char_id)


def summarize_event_conflicts(event_id: str) -> Dict[str, Dict[str, Any]]:
    """Return normalized conflict summaries for an event's accounts.

    Analyzes an event's accounts across different sources and identifies
    fields where sources provide conflicting information. The summary
    groups sources by their reported value for each conflicting field.

    Parameters
    ----------
    event_id : str
        Event identifier

    Returns
    -------
    dict
        Mapping of field name to conflict summary. Each conflict summary
        has a "values" key mapping field values to lists of sources.
        Empty dict if no conflicts exist.

    Raises
    ------
    DataNotFoundError
        If the event does not exist

    Examples
    --------
    >>> from bce import api
    >>> conflicts = api.summarize_event_conflicts("crucifixion")
    >>> print(conflicts.keys())
    dict_keys(['summary', 'notes'])
    """

    return contradictions.summarize_event_conflicts(event_id)


# Tags and search


def list_characters_with_tag(tag: str) -> List[str]:
    """Return IDs of characters tagged with the given tag (case-insensitive)."""

    return queries.list_characters_with_tag(tag)


def list_events_with_tag(tag: str) -> List[str]:
    """Return IDs of events tagged with the given tag (case-insensitive)."""

    return queries.list_events_with_tag(tag)


def search_all(query: str, scope: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Search across characters and events using full-text search.

    Searches through character traits, tags, roles, event accounts, notes,
    parallels, and scripture references. Results include match context
    showing where and how the query matched.

    Parameters
    ----------
    query : str
        Search query (case-insensitive)
    scope : list of str, optional
        Limit search to specific fields. Options: "traits", "references",
        "accounts", "notes", "tags", "roles". If None, searches all fields.

    Returns
    -------
    list of dict
        Search results with keys: type (character/event), id, match_in
        (field that matched), snippet (matching text context)

    Examples
    --------
    >>> from bce import api
    >>> results = api.search_all("resurrection")
    >>> print(len(results))
    15
    >>> print(results[0]["type"])
    character
    >>> results = api.search_all("John 3:16", scope=["references"])
    >>> print(results[0]["match_in"])
    references
    """

    return search.search_all(query, scope=scope)


# Export helpers


def export_all_characters() -> List[Dict[str, Any]]:
    """Export all characters as a list of JSON-serializable dicts.

    This builds on top of ``bce.dossiers.build_all_character_dossiers`` so
    callers receive the enriched dossier shape rather than raw dataclasses
    or file paths.
    """

    return dossiers.build_all_character_dossiers()


def export_all_events() -> List[Dict[str, Any]]:
    """Export all events as a list of JSON-serializable dicts.

    This builds on top of ``bce.dossiers.build_all_event_dossiers`` so
    callers receive the enriched dossier shape rather than raw dataclasses
    or file paths.
    """

    return dossiers.build_all_event_dossiers()


def export_characters_csv(output_path: str, include_fields: Optional[List[str]] = None) -> None:
    """Write a CSV of characters to ``output_path``.

    Thin wrapper around ``bce.export.export_characters_csv``.
    """

    export.export_characters_csv(output_path, include_fields=include_fields)


def export_events_csv(output_path: str, include_fields: Optional[List[str]] = None) -> None:
    """Write a CSV of events to ``output_path``.

    Thin wrapper around ``bce.export.export_events_csv``.
    """

    export.export_events_csv(output_path, include_fields=include_fields)


def export_citations(format: str = "bibtex") -> List[str]:
    """Export citations for sources, characters, and events.

    Thin wrapper around ``bce.export.export_citations``.
    """

    return export.export_citations(format=format)


# Graph snapshot


def build_graph_snapshot() -> export_graph.GraphSnapshot:
    """Build a property-graph snapshot of the BCE data.

    Thin wrapper around ``bce.export_graph.build_graph_snapshot``.
    """

    return export_graph.build_graph_snapshot()


# Bible text helpers


def list_bible_translations() -> List[str]:
    """List available Bible translations (by code)."""

    return bibles.list_translations()


def get_verse_text(book: str, chapter: int, verse: int, translation: str = "web") -> str:
    """Return Bible verse text for the given reference and translation."""

    return bibles.get_verse(book, chapter, verse, translation=translation)


def get_parallel_verse_text(
    book: str,
    chapter: int,
    verse: int,
    translations: List[str],
) -> Dict[str, str]:
    """Return a mapping of translation code to verse text for the given reference."""

    return bibles.get_parallel(book, chapter, verse, translations=translations)
