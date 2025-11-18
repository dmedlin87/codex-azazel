"""Tests for error handling and error message quality.

These tests verify that error messages are helpful and informative.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bce import queries, storage
from bce.exceptions import StorageError
from bce.models import Character, Event


class TestCharacterErrorMessages:
    """Test error message quality for character operations."""

    def test_character_not_found_error_message(self, tmp_path):
        """Character not found error should mention the character ID."""
        storage.configure_data_root(tmp_path)

        try:
            with pytest.raises(FileNotFoundError) as exc_info:
                queries.get_character("nonexistent_char")

            error_message = str(exc_info.value)
            # Should mention it's about a character
            # FileNotFoundError will contain the path which includes "characters"
            assert "characters" in error_message or "nonexistent_char" in error_message

        finally:
            storage.reset_data_root()

    def test_load_character_missing_file_helpful_message(self, tmp_path):
        """Missing character file should provide helpful error."""
        custom_root = tmp_path / "data"
        storage.configure_data_root(custom_root)

        try:
            with pytest.raises(FileNotFoundError) as exc_info:
                storage.load_character("missing")

            # Error should indicate file path
            error_message = str(exc_info.value)
            assert "missing.json" in error_message

        finally:
            storage.reset_data_root()

    def test_load_character_malformed_json_helpful_message(self, tmp_path):
        """Malformed JSON should provide clear error."""
        custom_root = tmp_path / "data"
        char_dir = custom_root / "characters"
        char_dir.mkdir(parents=True)

        bad_file = char_dir / "bad.json"
        bad_file.write_text("{ this is not valid json }")

        storage.configure_data_root(custom_root)

        try:
            with pytest.raises(json.JSONDecodeError) as exc_info:
                storage.load_character("bad")

            # JSONDecodeError should have details
            error_message = str(exc_info.value)
            # Should indicate position of error
            assert "line" in error_message.lower() or "column" in error_message.lower()

        finally:
            storage.reset_data_root()

    def test_load_character_missing_required_field_helpful_message(self, tmp_path):
        """Missing required field should indicate which field and file."""
        custom_root = tmp_path / "data"
        char_dir = custom_root / "characters"
        char_dir.mkdir(parents=True)

        incomplete_file = char_dir / "incomplete.json"
        incomplete_file.write_text('{"id": "incomplete"}')

        storage.configure_data_root(custom_root)

        try:
            with pytest.raises(StorageError) as exc_info:
                storage.load_character("incomplete")

            error_message = str(exc_info.value)
            # Should mention the missing parameter and the file
            assert "canonical_name" in error_message
            assert "incomplete.json" in error_message

        finally:
            storage.reset_data_root()


class TestEventErrorMessages:
    """Test error message quality for event operations."""

    def test_event_not_found_error_message(self, tmp_path):
        """Event not found error should mention the event ID."""
        storage.configure_data_root(tmp_path)

        try:
            with pytest.raises(FileNotFoundError) as exc_info:
                queries.get_event("nonexistent_event")

            error_message = str(exc_info.value)
            # Should mention it's about an event
            assert "events" in error_message or "nonexistent_event" in error_message

        finally:
            storage.reset_data_root()

    def test_load_event_missing_file_helpful_message(self, tmp_path):
        """Missing event file should provide helpful error."""
        custom_root = tmp_path / "data"
        storage.configure_data_root(custom_root)

        try:
            with pytest.raises(FileNotFoundError) as exc_info:
                storage.load_event("missing")

            error_message = str(exc_info.value)
            assert "missing.json" in error_message

        finally:
            storage.reset_data_root()

    def test_load_event_malformed_json_helpful_message(self, tmp_path):
        """Malformed JSON should provide clear error."""
        custom_root = tmp_path / "data"
        event_dir = custom_root / "events"
        event_dir.mkdir(parents=True)

        bad_file = event_dir / "bad.json"
        bad_file.write_text("not json at all")

        storage.configure_data_root(custom_root)

        try:
            with pytest.raises(json.JSONDecodeError) as exc_info:
                storage.load_event("bad")

            error_message = str(exc_info.value)
            # Should have error details
            assert len(error_message) > 0

        finally:
            storage.reset_data_root()

    def test_load_event_missing_required_field_helpful_message(self, tmp_path):
        """Missing required field should indicate which field and file."""
        custom_root = tmp_path / "data"
        event_dir = custom_root / "events"
        event_dir.mkdir(parents=True)

        incomplete_file = event_dir / "incomplete.json"
        incomplete_file.write_text('{"id": "incomplete"}')

        storage.configure_data_root(custom_root)

        try:
            with pytest.raises(StorageError) as exc_info:
                storage.load_event("incomplete")

            error_message = str(exc_info.value)
            # Should mention the missing parameter and the file
            assert "label" in error_message
            assert "incomplete.json" in error_message

        finally:
            storage.reset_data_root()


class TestValidationErrorMessages:
    """Test validation error message quality."""

    def test_validation_reports_duplicate_character_ids(self, tmp_path, monkeypatch):
        """Validation should clearly report duplicate character IDs."""
        def fake_list_character_ids():
            return ["duplicate", "duplicate", "unique"]

        def fake_get_character(char_id):
            from types import SimpleNamespace
            return SimpleNamespace(id=char_id)

        monkeypatch.setattr("bce.validation.queries.list_character_ids", fake_list_character_ids)
        monkeypatch.setattr("bce.validation.queries.get_character", fake_get_character)
        monkeypatch.setattr("bce.validation.queries.list_event_ids", lambda: [])

        from bce.validation import validate_all

        errors = validate_all()

        # Should have error about duplicate
        duplicate_errors = [e for e in errors if "duplicate" in e.lower() and "character" in e.lower()]
        assert len(duplicate_errors) > 0

        # Error should mention "duplicate"
        assert any("duplicate" in error for error in errors)

    def test_validation_reports_id_mismatch(self, tmp_path, monkeypatch):
        """Validation should report when object ID doesn't match filename."""
        def fake_list_character_ids():
            return ["mismatch"]

        def fake_get_character(char_id):
            from types import SimpleNamespace
            return SimpleNamespace(id="wrong_id")  # ID doesn't match

        monkeypatch.setattr("bce.validation.queries.list_character_ids", fake_list_character_ids)
        monkeypatch.setattr("bce.validation.queries.get_character", fake_get_character)
        monkeypatch.setattr("bce.validation.queries.list_event_ids", lambda: [])

        from bce.validation import validate_all

        errors = validate_all()

        # Should report ID mismatch
        mismatch_errors = [e for e in errors if "mismatch" in e]
        assert len(mismatch_errors) > 0

        # Error should mention both IDs
        error_text = " ".join(errors)
        assert "wrong_id" in error_text
        assert "mismatch" in error_text

    def test_validation_reports_load_failures(self, tmp_path, monkeypatch):
        """Validation should report load failures with error details."""
        def fake_list_character_ids():
            return ["broken"]

        def fake_get_character(char_id):
            raise RuntimeError("Simulated load error")

        monkeypatch.setattr("bce.validation.queries.list_character_ids", fake_list_character_ids)
        monkeypatch.setattr("bce.validation.queries.get_character", fake_get_character)
        monkeypatch.setattr("bce.validation.queries.list_event_ids", lambda: [])

        from bce.validation import validate_all

        errors = validate_all()

        # Should report load failure
        load_errors = [e for e in errors if "broken" in e]
        assert len(load_errors) > 0

        # Error should mention the character ID and the error
        error_text = " ".join(errors)
        assert "broken" in error_text
        assert "Simulated load error" in error_text or "load" in error_text.lower()


class TestContradictionErrorMessages:
    """Test contradiction detection error messages."""

    def test_nonexistent_character_in_contradictions(self, tmp_path):
        """Querying contradictions for nonexistent character should fail clearly."""
        storage.configure_data_root(tmp_path)

        try:
            from bce import contradictions

            with pytest.raises(FileNotFoundError) as exc_info:
                contradictions.compare_character_sources("nonexistent")

            # Should provide helpful error
            error_message = str(exc_info.value)
            assert len(error_message) > 0

        finally:
            storage.reset_data_root()

    def test_nonexistent_event_in_contradictions(self, tmp_path):
        """Querying conflicts for nonexistent event should fail clearly."""
        storage.configure_data_root(tmp_path)

        try:
            from bce import contradictions

            with pytest.raises(FileNotFoundError) as exc_info:
                contradictions.find_events_with_conflicting_accounts("nonexistent")

            # Should provide helpful error
            error_message = str(exc_info.value)
            assert len(error_message) > 0

        finally:
            storage.reset_data_root()


class TestDossierErrorMessages:
    """Test dossier building error messages."""

    def test_nonexistent_character_dossier(self, tmp_path):
        """Building dossier for nonexistent character should fail clearly."""
        storage.configure_data_root(tmp_path)

        try:
            from bce import dossiers

            with pytest.raises(FileNotFoundError) as exc_info:
                dossiers.build_character_dossier("nonexistent")

            # Should provide helpful error
            error_message = str(exc_info.value)
            assert len(error_message) > 0

        finally:
            storage.reset_data_root()

    def test_nonexistent_event_dossier(self, tmp_path):
        """Building dossier for nonexistent event should fail clearly."""
        storage.configure_data_root(tmp_path)

        try:
            from bce import dossiers

            with pytest.raises(FileNotFoundError) as exc_info:
                dossiers.build_event_dossier("nonexistent")

            # Should provide helpful error
            error_message = str(exc_info.value)
            assert len(error_message) > 0

        finally:
            storage.reset_data_root()


class TestModelConstructionErrors:
    """Test error messages when constructing models incorrectly."""

    def test_character_missing_id_error_message(self):
        """Creating Character without ID should have clear error."""
        with pytest.raises(TypeError) as exc_info:
            Character(canonical_name="Test")  # Missing id

        error_message = str(exc_info.value)
        assert "id" in error_message.lower()

    def test_character_missing_canonical_name_error_message(self):
        """Creating Character without canonical_name should have clear error."""
        with pytest.raises(TypeError) as exc_info:
            Character(id="test")  # Missing canonical_name

        error_message = str(exc_info.value)
        assert "canonical_name" in error_message

    def test_event_missing_id_error_message(self):
        """Creating Event without ID should have clear error."""
        with pytest.raises(TypeError) as exc_info:
            Event(label="Test")  # Missing id

        error_message = str(exc_info.value)
        assert "id" in error_message.lower()

    def test_event_missing_label_error_message(self):
        """Creating Event without label should have clear error."""
        with pytest.raises(TypeError) as exc_info:
            Event(id="test")  # Missing label

        error_message = str(exc_info.value)
        assert "label" in error_message

    def test_event_account_missing_fields_error_message(self):
        """Creating EventAccount without required fields should have clear error."""
        from bce.models import EventAccount

        with pytest.raises(TypeError) as exc_info:
            EventAccount(source_id="test")  # Missing reference and summary

        error_message = str(exc_info.value)
        # Should mention at least one missing field
        assert "reference" in error_message or "summary" in error_message


class TestQueryErrorMessages:
    """Test query module error messages."""

    def test_get_source_profile_returns_none_for_missing(self):
        """get_source_profile should return None (not error) for missing source."""
        char = Character(
            id="test",
            canonical_name="Test",
            source_profiles=[]
        )

        profile = queries.get_source_profile(char, "nonexistent")

        # Should return None, not raise error
        assert profile is None

    def test_list_events_for_nonexistent_character(self, tmp_path):
        """Listing events for nonexistent character should return empty list."""
        storage.configure_data_root(tmp_path)

        try:
            # Should not raise error, just return empty list
            events = queries.list_events_for_character("nonexistent")
            assert events == []

        finally:
            storage.reset_data_root()
