from __future__ import annotations

from typing import Any, Dict, List

import re

from . import queries
from .exceptions import DataNotFoundError, StorageError, BceError


_REF_RE = re.compile(
    r"^\s*(?P<book>(?:[1-3]\s+)?[A-Za-z]+(?:\s+[A-Za-z]+)*)\s+"  # book name
    r"(?P<chapter>\d+):"  # chapter
    r"(?P<verse_start>\d+)"  # verse start
    r"(?:-(?P<verse_end>\d+))?\s*$"  # optional verse end
)


_BOOK_MAX_CHAPTER: Dict[str, int] = {
    "Matthew": 28,
    "Mark": 16,
    "Luke": 24,
    "John": 21,
}

_SUPPORTED_BOOKS_FOR_GLOBAL_VALIDATION = set(_BOOK_MAX_CHAPTER.keys())


def _normalize_book_name(raw: str) -> str:
    raw = " ".join(raw.split())
    parts = raw.split(" ")
    norm_parts = []
    for part in parts:
        if not part:
            continue
        if part[0].isdigit():
            norm_parts.append(part)
        else:
            norm_parts.append(part[0].upper() + part[1:].lower())
    return " ".join(norm_parts)


def validate_reference(ref: str) -> Dict[str, Any]:
    """Validate a scripture reference string.

    Returns a dictionary with keys:

    - ``valid`` (bool): overall validity flag.
    - ``error`` (str | None): human-readable error description, if any.
    - ``book`` (str | None): normalized book name when parseable.
    - ``chapter`` (int | None): chapter number when parseable.
    - ``verse_start`` / ``verse_end`` (int | None): verse bounds when parseable.
    - ``canonical`` (bool): True when the book is known in the internal table.
    """

    ref = ref.strip()
    result: Dict[str, Any] = {
        "valid": False,
        "error": None,
        "book": None,
        "chapter": None,
        "verse_start": None,
        "verse_end": None,
        "canonical": False,
    }

    if not ref:
        result["error"] = "Empty reference"
        return result

    match = _REF_RE.match(ref)
    if not match:
        result["error"] = "Unrecognized reference format"
        return result

    book_raw = match.group("book")
    chapter_str = match.group("chapter")
    verse_start_str = match.group("verse_start")
    verse_end_str = match.group("verse_end")

    try:
        chapter = int(chapter_str)
        verse_start = int(verse_start_str)
        verse_end = int(verse_end_str) if verse_end_str is not None else verse_start
    except ValueError:
        result["error"] = "Non-numeric chapter or verse"
        return result

    book = _normalize_book_name(book_raw)
    result["book"] = book
    result["chapter"] = chapter
    result["verse_start"] = verse_start
    result["verse_end"] = verse_end

    max_chapter = _BOOK_MAX_CHAPTER.get(book)
    if max_chapter is None:
        result["error"] = f"Unknown book '{book}'"
        return result

    result["canonical"] = True

    if chapter < 1 or chapter > max_chapter:
        result["error"] = f"Book '{book}' has only {max_chapter} chapters"
        return result

    if verse_start < 1 or verse_end < verse_start:
        result["error"] = "Invalid verse range"
        return result

    # We intentionally do not validate upper bounds on verses per chapter yet.
    result["valid"] = True
    result["error"] = None
    return result


def _validate_reference_in_context(ref: str, context: str, errors: List[str]) -> None:
    """Best-effort reference validation used by validate_all.

    Only applies strict checks for a limited set of books to avoid breaking
    existing free-form data. References that cannot be parsed or whose book
    is not in the supported set are ignored here.
    """

    result = validate_reference(ref)
    book = result.get("book")
    if not isinstance(book, str) or book not in _SUPPORTED_BOOKS_FOR_GLOBAL_VALIDATION:
        return

    if result.get("valid"):
        return

    error = result.get("error") or "invalid reference"
    errors.append(f"{context} has invalid reference '{ref}': {error}")


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
        except (DataNotFoundError, StorageError, BceError) as exc:
            errors.append(f"Failed to load character '{char_id}': {exc}")
            continue

        obj_id = getattr(character, "id", None)
        if not isinstance(obj_id, str) or not obj_id:
            errors.append(f"Character '{char_id}' has an empty or invalid id field")
        elif obj_id != char_id:
            errors.append(
                f"Character object id '{obj_id}' does not match key '{char_id}'"
            )

        # Best-effort validation of scripture references in source profiles.
        for profile in getattr(character, "source_profiles", []):
            for ref in getattr(profile, "references", []):
                if not isinstance(ref, str):
                    continue
                _validate_reference_in_context(
                    ref,
                    f"Character '{char_id}' profile '{getattr(profile, 'source_id', '?')}'",
                    errors,
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
        except (DataNotFoundError, StorageError, BceError) as exc:
            errors.append(f"Failed to load event '{event_id}': {exc}")
            continue

        obj_id = getattr(event, "id", None)
        if not isinstance(obj_id, str) or not obj_id:
            errors.append(f"Event '{event_id}' has an empty or invalid id field")
        elif obj_id != event_id:
            errors.append(
                f"Event object id '{obj_id}' does not match key '{event_id}'"
            )

        # Best-effort validation of scripture references in event accounts.
        for account in getattr(event, "accounts", []):
            ref = getattr(account, "reference", None)
            if not isinstance(ref, str):
                continue
            _validate_reference_in_context(
                ref,
                f"Event '{event_id}' account '{getattr(account, 'source_id', '?')}'",
                errors,
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


def validate_cross_references() -> List[str]:
    """Validate cross-references between events and characters.

    This helper focuses on relationships *between* core objects rather than on
    individual field formats. It checks that:

    - All event participants reference existing characters.
    - Each event account's source_id is present in at least one participant's
      source profile.

    Returns a list of human-readable error messages; an empty list means that
    all cross-reference checks passed.
    """

    errors: List[str] = []

    # Build a mapping of character_id -> set(source_ids) from source_profiles.
    character_ids = queries.list_character_ids()
    character_id_set = set(character_ids)
    character_sources: Dict[str, set[str]] = {}

    for char_id in character_ids:
        try:
            character = queries.get_character(char_id)
        except (DataNotFoundError, StorageError, BceError) as exc:
            errors.append(
                f"Failed to load character '{char_id}' for cross-reference validation: {exc}"
            )
            continue

        sources_for_char: set[str] = set()
        for profile in getattr(character, "source_profiles", []):
            source_id = getattr(profile, "source_id", None)
            if isinstance(source_id, str) and source_id:
                sources_for_char.add(source_id)
        character_sources[char_id] = sources_for_char

    # Now walk events and check participants + their account sources.
    for event_id in queries.list_event_ids():
        try:
            event = queries.get_event(event_id)
        except (DataNotFoundError, StorageError, BceError) as exc:
            errors.append(
                f"Failed to load event '{event_id}' for cross-reference validation: {exc}"
            )
            continue

        participants = [p for p in getattr(event, "participants", []) if isinstance(p, str)]

        # 1) Ensure all event participants exist as characters.
        for participant_id in participants:
            if participant_id not in character_id_set:
                errors.append(
                    f"Event '{event_id}' participant '{participant_id}' not found in characters"
                )

        # 2) Ensure event accounts' sources are present in at least one
        #    participant's source profiles. If there are no participants, skip
        #    this check for the event.
        if not participants:
            continue

        for account in getattr(event, "accounts", []):
            source_id = getattr(account, "source_id", None)
            if not isinstance(source_id, str) or not source_id:
                continue

            has_matching_profile = any(
                source_id in character_sources.get(participant_id, set())
                for participant_id in participants
                if participant_id in character_sources
            )

            if not has_matching_profile:
                errors.append(
                    f"Event '{event_id}' account from '{source_id}' has no participant "
                    "with matching source profile"
                )

    return errors
