from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from . import queries
from . import storage


def _iter_characters() -> Iterable[Dict[str, Any]]:
    for char in queries.list_all_characters():
        yield {
            "type": "character",
            "id": char.id,
            "character": char,
        }


def _iter_events() -> Iterable[Dict[str, Any]]:
    for event in storage.iter_events():
        yield {
            "type": "event",
            "id": event.id,
            "event": event,
        }


def _contains(haystack: Optional[str], needle: str) -> bool:
    if not haystack:
        return False
    return needle in haystack.lower()


def search_all(query: str, scope: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Search across characters and events for a simple text query.

    Parameters
    ----------
    query:
        Text to search for (case-insensitive substring match).
    scope:
        Optional list of search domains. Supported values include:

        - "traits": character traits by source
        - "references": character references by source
        - "accounts": event account summaries and references
        - "notes": event account notes
        - "tags": character and event tags

        When omitted or empty, all supported scopes are searched.

    Returns
    -------
    list of dict
        Each result is a JSON-serializable dict with at least:

        - "type": "character" or "event"
        - "id": the character or event id
        - "match_in": a string describing where the match was found

        Additional fields provide useful context for the match, such as
        "source_id", "field", "value", and "reference".
    """

    scopes = set(scope or ["traits", "references", "accounts", "notes", "tags"])
    needle = query.lower()
    results: List[Dict[str, Any]] = []

    # Character search
    if scopes & {"traits", "references", "tags"}:
        for entry in _iter_characters():
            char = entry["character"]
            for profile in getattr(char, "source_profiles", []):
                source_id = getattr(profile, "source_id", None)

                if "traits" in scopes:
                    for trait_name, trait_value in getattr(profile, "traits", {}).items():
                        # Search both trait key and value
                        if _contains(trait_name, needle) or _contains(trait_value, needle):
                            results.append(
                                {
                                    "type": "character",
                                    "id": char.id,
                                    "match_in": "traits",
                                    "source_id": source_id,
                                    "field": trait_name,
                                    "value": trait_value,
                                }
                            )

                if "references" in scopes:
                    for ref in getattr(profile, "references", []):
                        if not isinstance(ref, str):
                            continue
                        if _contains(ref, needle):
                            results.append(
                                {
                                    "type": "character",
                                    "id": char.id,
                                    "match_in": "references",
                                    "source_id": source_id,
                                    "reference": ref,
                                }
                            )

                if "tags" in scopes:
                    for tag in getattr(char, "tags", []):
                        if _contains(tag, needle):
                            results.append(
                                {
                                    "type": "character",
                                    "id": char.id,
                                    "match_in": "tags",
                                    "tag": tag,
                                }
                            )

    # Event search
    if scopes & {"accounts", "notes", "tags"}:
        for entry in _iter_events():
            event = entry["event"]
            for account in getattr(event, "accounts", []):
                source_id = getattr(account, "source_id", None)
                reference = getattr(account, "reference", None)

                if "accounts" in scopes:
                    summary = getattr(account, "summary", None)
                    if _contains(summary, needle) or _contains(reference, needle):
                        results.append(
                            {
                                "type": "event",
                                "id": event.id,
                                "match_in": "accounts",
                                "source_id": source_id,
                                "reference": reference,
                                "summary": summary,
                            }
                        )

                if "notes" in scopes:
                    notes = getattr(account, "notes", None)
                    if _contains(notes, needle):
                        results.append(
                            {
                                "type": "event",
                                "id": event.id,
                                "match_in": "notes",
                                "source_id": source_id,
                                "reference": reference,
                                "notes": notes,
                            }
                        )

    return results
