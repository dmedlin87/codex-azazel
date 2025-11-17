from __future__ import annotations

from typing import Any, Dict, List, Optional

from . import dossiers, queries, contradictions, search, export, export_graph


# Core data access

def get_character(char_id: str):
    """Return a Character object by ID.

    Thin wrapper around ``bce.queries.get_character``.
    """

    return queries.get_character(char_id)


def get_event(event_id: str):
    """Return an Event object by ID.

    Thin wrapper around ``bce.queries.get_event``.
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
    """Build a JSON-friendly dossier for a character."""

    return dossiers.build_character_dossier(char_id)


def build_event_dossier(event_id: str) -> Dict[str, Any]:
    """Build a JSON-friendly dossier for an event."""

    return dossiers.build_event_dossier(event_id)


def build_all_character_dossiers() -> List[Dict[str, Any]]:
    """Build dossiers for all characters."""

    return dossiers.build_all_character_dossiers()


def build_all_event_dossiers() -> List[Dict[str, Any]]:
    """Build dossiers for all events."""

    return dossiers.build_all_event_dossiers()


# Conflicts


def summarize_character_conflicts(char_id: str) -> Dict[str, Dict[str, Any]]:
    """Return normalized conflict summaries for a character's traits."""

    return contradictions.summarize_character_conflicts(char_id)


def summarize_event_conflicts(event_id: str) -> Dict[str, Dict[str, Any]]:
    """Return normalized conflict summaries for an event's accounts."""

    return contradictions.summarize_event_conflicts(event_id)


# Tags and search


def list_characters_with_tag(tag: str) -> List[str]:
    """Return IDs of characters tagged with the given tag (case-insensitive)."""

    return queries.list_characters_with_tag(tag)


def list_events_with_tag(tag: str) -> List[str]:
    """Return IDs of events tagged with the given tag (case-insensitive)."""

    return queries.list_events_with_tag(tag)


def search_all(query: str, scope: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Search across characters and events.

    Thin wrapper around ``bce.search.search_all``.
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
