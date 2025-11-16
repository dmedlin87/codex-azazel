from __future__ import annotations

from types import SimpleNamespace

from bce.validation import validate_all


def test_validate_all_has_no_errors() -> None:
    errors = validate_all()
    assert errors == [], f"Validation errors: {errors}"


def test_validate_all_reports_character_and_event_errors(monkeypatch) -> None:
    character_ids = [
        "primary",
        "duplicate",
        "duplicate",
        "mismatch",
        "empty",
        "broken",
    ]
    event_ids = [
        "primary_event",
        "duplicate_event",
        "duplicate_event",
        "mismatch_event",
        "empty_event",
        "bad_load",
    ]

    character_map = {
        "primary": SimpleNamespace(id="primary"),
        "duplicate": SimpleNamespace(id="duplicate"),
        "mismatch": SimpleNamespace(id="wrong_char"),
        "empty": SimpleNamespace(id=""),
    }
    event_map = {
        "primary_event": SimpleNamespace(id="primary_event"),
        "duplicate_event": SimpleNamespace(id="duplicate_event"),
        "mismatch_event": SimpleNamespace(id="wrong_event"),
        "empty_event": SimpleNamespace(id=""),
    }

    def fake_list_character_ids() -> list[str]:
        return list(character_ids)

    def fake_get_character(char_id: str) -> SimpleNamespace:
        if char_id == "broken":
            raise RuntimeError("boom")
        return character_map[char_id]

    def fake_list_event_ids() -> list[str]:
        return list(event_ids)

    def fake_get_event(event_id: str) -> SimpleNamespace:
        if event_id == "bad_load":
            raise RuntimeError("missing file")
        return event_map[event_id]

    monkeypatch.setattr("bce.validation.queries.list_character_ids", fake_list_character_ids)
    monkeypatch.setattr("bce.validation.queries.get_character", fake_get_character)
    monkeypatch.setattr("bce.validation.queries.list_event_ids", fake_list_event_ids)
    monkeypatch.setattr("bce.validation.queries.get_event", fake_get_event)

    errors = validate_all()

    expected_messages = [
        "Duplicate character IDs found: duplicate",
        "Failed to load character 'broken': boom",
        "Character 'empty' has an empty or invalid id field",
        "Character object id 'wrong_char' does not match key 'mismatch'",
        "Duplicate event IDs found: duplicate_event",
        "Failed to load event 'bad_load': missing file",
        "Event 'empty_event' has an empty or invalid id field",
        "Event object id 'wrong_event' does not match key 'mismatch_event'",
    ]

    for message in expected_messages:
        assert message in errors, f"Missing expected error: {message}"
