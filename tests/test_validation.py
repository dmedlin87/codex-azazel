from __future__ import annotations

from types import SimpleNamespace

from bce.validation import (
    ValidationReport,
    run_validation,
    validate_all,
    validate_cross_references,
    validate_reference,
)


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


def test_validate_reference_valid_mark_range() -> None:
    result = validate_reference("Mark 16:1-8")

    assert result["valid"] is True
    assert result["book"] == "Mark"
    assert result["chapter"] == 16
    assert result["verse_start"] == 1
    assert result["verse_end"] == 8
    assert result["canonical"] is True
    assert result["error"] is None


def test_validate_reference_invalid_chapter_reports_error() -> None:
    result = validate_reference("Mark 99:1")

    assert result["valid"] is False
    assert result["canonical"] is True
    assert result["book"] == "Mark"
    assert isinstance(result["error"], str)
    assert "only" in result["error"].lower()


def test_validate_cross_references_reports_missing_participant_and_source(monkeypatch) -> None:
    """validate_cross_references should report missing participants and source mismatches."""

    character_ids = ["char_a"]
    event_ids = ["event_1"]

    character_map = {
        "char_a": SimpleNamespace(
            id="char_a",
            source_profiles=[SimpleNamespace(source_id="source1")],
        ),
    }

    event_map = {
        "event_1": SimpleNamespace(
            id="event_1",
            participants=["char_a", "missing_char"],
            accounts=[
                SimpleNamespace(source_id="source1"),
                SimpleNamespace(source_id="source2"),
            ],
        ),
    }

    def fake_list_character_ids() -> list[str]:
        return list(character_ids)

    def fake_get_character(char_id: str) -> SimpleNamespace:
        return character_map[char_id]

    def fake_list_event_ids() -> list[str]:
        return list(event_ids)

    def fake_get_event(event_id: str) -> SimpleNamespace:
        return event_map[event_id]

    monkeypatch.setattr("bce.validation.queries.list_character_ids", fake_list_character_ids)
    monkeypatch.setattr("bce.validation.queries.get_character", fake_get_character)
    monkeypatch.setattr("bce.validation.queries.list_event_ids", fake_list_event_ids)
    monkeypatch.setattr("bce.validation.queries.get_event", fake_get_event)

    errors = validate_cross_references()

    assert (
        "Event 'event_1' participant 'missing_char' not found in characters" in errors
    )
    assert (
        "Event 'event_1' account from 'source2' has no participant with matching source profile"
        in errors
    )


def test_validate_cross_references_no_errors_when_consistent(monkeypatch) -> None:
    """Consistent participants and sources should yield no cross-reference errors."""

    character_ids = ["char_a", "char_b"]
    event_ids = ["event_ok"]

    character_map = {
        "char_a": SimpleNamespace(
            id="char_a",
            source_profiles=[SimpleNamespace(source_id="source1")],
        ),
        "char_b": SimpleNamespace(
            id="char_b",
            source_profiles=[SimpleNamespace(source_id="source2")],
        ),
    }

    event_map = {
        "event_ok": SimpleNamespace(
            id="event_ok",
            participants=["char_a", "char_b"],
            accounts=[
                SimpleNamespace(source_id="source1"),
                SimpleNamespace(source_id="source2"),
            ],
        ),
    }

    def fake_list_character_ids() -> list[str]:
        return list(character_ids)

    def fake_get_character(char_id: str) -> SimpleNamespace:
        return character_map[char_id]

    def fake_list_event_ids() -> list[str]:
        return list(event_ids)

    def fake_get_event(event_id: str) -> SimpleNamespace:
        return event_map[event_id]

    monkeypatch.setattr("bce.validation.queries.list_character_ids", fake_list_character_ids)
    monkeypatch.setattr("bce.validation.queries.get_character", fake_get_character)
    monkeypatch.setattr("bce.validation.queries.list_event_ids", fake_list_event_ids)
    monkeypatch.setattr("bce.validation.queries.get_event", fake_get_event)

    errors = validate_cross_references()

    assert errors == []


def test_run_validation_skips_when_disabled(monkeypatch) -> None:
    """run_validation should skip when configuration disables validation."""

    fake_config = SimpleNamespace(enable_validation=False)
    monkeypatch.setattr("bce.validation.get_default_config", lambda: fake_config)

    called = {"collect": False}

    def boom():  # pragma: no cover - guard against execution when skipped
        called["collect"] = True
        return ValidationReport()

    monkeypatch.setattr("bce.validation._collect_validation_messages", lambda: boom())

    report = run_validation()

    assert report.skipped is True
    assert report.reason
    assert called["collect"] is False


def test_run_validation_force_true_runs_even_when_disabled(monkeypatch) -> None:
    """force=True should override configuration and execute validators."""

    fake_config = SimpleNamespace(enable_validation=False)
    monkeypatch.setattr("bce.validation.get_default_config", lambda: fake_config)

    expected = ValidationReport(errors=["boom"], warnings=["warn"])
    monkeypatch.setattr("bce.validation._collect_validation_messages", lambda: expected)

    report = run_validation(force=True)

    assert report.errors == ["boom"]
    assert report.warnings == ["warn"]
    assert report.skipped is False
