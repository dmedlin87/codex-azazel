from __future__ import annotations

from typing import List

from . import queries


def _validate_characters(errors: List[str]) -> None:
    ids = queries.list_character_ids()

    # Detect duplicate IDs.
    seen = set()
    duplicates = set()
    for char_id in ids:
        if char_id in seen:
            duplicates.add(char_id)
        seen.add(char_id)
    if duplicates:
        joined = ", ".join(sorted(duplicates))
        errors.append(f"Duplicate character IDs found: {joined}")

    # Validate that each character can be loaded and has a sane id field.
    for char_id in ids:
        try:
            character = queries.get_character(char_id)
        except Exception as exc:  # type: ignore[redundant-except]
            errors.append(f"Failed to load character '{char_id}': {exc}")
            continue

        obj_id = getattr(character, "id", None)
        if not isinstance(obj_id, str) or not obj_id:
            errors.append(f"Character '{char_id}' has an empty or invalid id field")
        elif obj_id != char_id:
            errors.append(
                f"Character object id '{obj_id}' does not match key '{char_id}'"
            )


def _validate_events(errors: List[str]) -> None:
    ids = queries.list_event_ids()

    # Detect duplicate IDs.
    seen = set()
    duplicates = set()
    for event_id in ids:
        if event_id in seen:
            duplicates.add(event_id)
        seen.add(event_id)
    if duplicates:
        joined = ", ".join(sorted(duplicates))
        errors.append(f"Duplicate event IDs found: {joined}")

    # Validate that each event can be loaded and has a sane id field.
    for event_id in ids:
        try:
            event = queries.get_event(event_id)
        except Exception as exc:  # type: ignore[redundant-except]
            errors.append(f"Failed to load event '{event_id}': {exc}")
            continue

        obj_id = getattr(event, "id", None)
        if not isinstance(obj_id, str) or not obj_id:
            errors.append(f"Event '{event_id}' has an empty or invalid id field")
        elif obj_id != event_id:
            errors.append(
                f"Event object id '{obj_id}' does not match key '{event_id}'"
            )


def validate_all() -> List[str]:
    """Run basic validation over all characters and events.

    Returns a list of human-readable error messages. An empty list means that
    all checks passed.
    """

    errors: List[str] = []
    _validate_characters(errors)
    _validate_events(errors)
    return errors
