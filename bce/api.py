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


# AI-powered features (Phase 6+)
# These features require enable_ai_features=True in BceConfig


def analyze_semantic_contradictions(char_id: str, use_cache: bool = True) -> Dict[str, Any]:
    """Analyze character trait conflicts with semantic understanding.

    Uses sentence embeddings to distinguish genuine contradictions from
    complementary details or different emphases. Requires AI features enabled.

    Parameters
    ----------
    char_id : str
        Character identifier
    use_cache : bool, optional
        Whether to use cached results (default: True)

    Returns
    -------
    dict
        Semantic analysis with keys: character_id, canonical_name,
        has_conflicts, analyzed_conflicts, summary

    Raises
    ------
    ConfigurationError
        If AI features are disabled
    ImportError
        If required AI dependencies are missing

    Examples
    --------
    >>> from bce import api
    >>> from bce.config import BceConfig, set_default_config
    >>> config = BceConfig(enable_ai_features=True)
    >>> set_default_config(config)
    >>> analysis = api.analyze_semantic_contradictions("jesus")
    >>> for trait, details in analysis["analyzed_conflicts"].items():
    ...     if details["is_genuine_conflict"]:
    ...         print(f"Genuine conflict in {trait}")
    """
    from .ai import semantic_contradictions
    return semantic_contradictions.analyze_character_traits(char_id, use_cache=use_cache)


def audit_character_completeness(char_id: Optional[str] = None, use_cache: bool = True) -> Dict[str, Any]:
    """Audit character(s) for data completeness and identify gaps.

    Identifies missing source profiles, sparse traits, missing tags/references,
    and calculates completeness scores. Requires AI features enabled.

    Parameters
    ----------
    char_id : str, optional
        Character identifier. If None, audits all characters.
    use_cache : bool, optional
        Whether to use cached results (default: True)

    Returns
    -------
    dict
        Audit report with completeness scores, gaps, and inconsistencies

    Raises
    ------
    ConfigurationError
        If AI features are disabled

    Examples
    --------
    >>> from bce import api
    >>> audit = api.audit_character_completeness("thomas")
    >>> print(audit["completeness_score"])
    0.65
    >>> for gap in audit["gaps"]:
    ...     print(f"{gap['type']}: {gap['suggestion']}")
    """
    from .ai import completeness
    if char_id is None:
        return completeness.audit_characters(use_cache=use_cache)
    else:
        return completeness.audit_character(char_id, use_cache=use_cache)


def get_validation_suggestions(errors: Optional[List[str]] = None, use_cache: bool = True) -> List[Dict[str, Any]]:
    """Generate AI-powered suggestions for validation errors.

    Analyzes validation errors and suggests fixes using pattern matching
    and semantic similarity. Requires AI features enabled.

    Parameters
    ----------
    errors : list of str, optional
        Validation error messages. If None, runs validate_all() first.
    use_cache : bool, optional
        Whether to use cached results (default: True)

    Returns
    -------
    list of dict
        Suggestions with keys: error, suggestion, confidence, similar_items

    Raises
    ------
    ConfigurationError
        If AI features are disabled

    Examples
    --------
    >>> from bce import api
    >>> suggestions = api.get_validation_suggestions()
    >>> for sugg in suggestions:
    ...     print(f"{sugg['error']}")
    ...     print(f"  -> {sugg['suggestion']}")
    """
    from .ai import validation_assistant
    return validation_assistant.suggest_fixes(errors=errors, use_cache=use_cache)


def semantic_search(
    query: str,
    top_k: int = 10,
    scope: Optional[List[str]] = None,
    min_score: float = 0.3,
    use_cache: bool = True,
) -> List[Dict[str, Any]]:
    """Perform semantic search across characters and events.

    Unlike keyword search which matches exact strings, semantic search
    understands conceptual similarity. Requires AI features enabled.

    Parameters
    ----------
    query : str
        Natural language search query
    top_k : int, optional
        Maximum number of results to return (default: 10)
    scope : list of str, optional
        Fields to search in. Options: "traits", "relationships", "accounts".
        If None, searches all fields.
    min_score : float, optional
        Minimum similarity score 0.0-1.0 (default: 0.3)
    use_cache : bool, optional
        Whether to use cached search index (default: True)

    Returns
    -------
    list of dict
        Results with keys: type, id, relevance_score, matching_context,
        match_in, explanation

    Raises
    ------
    ConfigurationError
        If AI features are disabled
    ImportError
        If required AI dependencies are missing

    Examples
    --------
    >>> from bce import api
    >>> results = api.semantic_search("characters who doubted")
    >>> for result in results[:3]:
    ...     print(f"{result['id']}: {result['relevance_score']:.2f}")
    thomas: 0.89
    peter: 0.67
    """
    from .ai import semantic_search as ss
    return ss.query(query, top_k=top_k, scope=scope, min_score=min_score, use_cache=use_cache)


def find_similar_characters(
    char_id: str,
    top_k: int = 5,
    basis: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Find characters semantically similar to a given character.

    Uses embeddings of character traits to find conceptually similar
    characters. Requires AI features enabled.

    Parameters
    ----------
    char_id : str
        Reference character identifier
    top_k : int, optional
        Number of similar characters to return (default: 5)
    basis : list of str, optional
        Fields to use for similarity. Options: "traits", "roles", "tags".
        If None, uses ["traits"].

    Returns
    -------
    list of dict
        Similar characters with keys: character_id, canonical_name,
        similarity_score

    Raises
    ------
    ConfigurationError
        If AI features are disabled

    Examples
    --------
    >>> from bce import api
    >>> similar = api.find_similar_characters("paul", top_k=3)
    >>> for char in similar:
    ...     print(f"{char['canonical_name']}: {char['similarity_score']:.2f}")
    """
    from .ai import semantic_search as ss
    return ss.find_similar_characters(char_id, top_k=top_k, basis=basis)


def find_thematic_clusters(
    entity_type: str = "characters",
    num_clusters: int = 8,
    basis: Optional[List[str]] = None,
    use_cache: bool = True,
) -> List[Dict[str, Any]]:
    """Discover thematic clusters among characters or events.

    Uses K-means clustering on embeddings to automatically identify
    thematic groupings. Requires AI features enabled.

    Parameters
    ----------
    entity_type : str, optional
        "characters" or "events" (default: "characters")
    num_clusters : int, optional
        Target number of clusters (default: 8)
    basis : list of str, optional
        Fields to use for clustering. For characters: ["traits", "tags", "roles"].
        For events: uses accounts. If None, uses default.
    use_cache : bool, optional
        Whether to use cached results (default: True)

    Returns
    -------
    list of dict
        Clusters with keys: cluster_id, label, members, representative_traits,
        confidence, size

    Raises
    ------
    ConfigurationError
        If AI features are disabled
    ImportError
        If scikit-learn is not installed

    Examples
    --------
    >>> from bce import api
    >>> clusters = api.find_thematic_clusters(num_clusters=5)
    >>> for cluster in clusters:
    ...     print(f"{cluster['label']}: {cluster['members']}")
    Apostolic Leaders: ['peter', 'john', 'james_son_of_zebedee']
    Pauline Circle: ['paul', 'timothy', 'barnabas']
    """
    from .ai import clustering

    if entity_type == "characters":
        return clustering.find_character_clusters(
            num_clusters=num_clusters, basis=basis, use_cache=use_cache
        )
    elif entity_type == "events":
        return clustering.find_event_clusters(num_clusters=num_clusters, use_cache=use_cache)
    else:
        raise ValueError(f"entity_type must be 'characters' or 'events', got '{entity_type}'")
