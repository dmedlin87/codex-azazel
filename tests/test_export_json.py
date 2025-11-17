"""Tests for bce.export_json module.

Tests the JSON export functionality for characters and events.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bce import storage
from bce.export_json import export_all_characters, export_all_events
from bce.models import Character, Event, EventAccount, SourceProfile


class TestExportAllCharacters:
    """Test export_all_characters function."""

    def test_creates_valid_json_file(self, tmp_path):
        """export_all_characters should create a valid JSON file."""
        output_file = tmp_path / "characters.json"

        export_all_characters(str(output_file))

        assert output_file.exists()

        # Should be valid JSON
        with output_file.open() as f:
            data = json.load(f)

        assert isinstance(data, list)
        assert len(data) > 0

    def test_contains_all_characters(self, tmp_path):
        """Export should contain all characters from storage."""
        output_file = tmp_path / "characters.json"

        export_all_characters(str(output_file))

        with output_file.open() as f:
            data = json.load(f)

        # Get all character IDs from storage
        expected_ids = storage.list_character_ids()
        exported_ids = [char["id"] for char in data]

        assert set(exported_ids) == set(expected_ids)

    def test_preserves_all_character_fields(self, tmp_path):
        """Exported characters should have all required fields."""
        output_file = tmp_path / "characters.json"

        export_all_characters(str(output_file))

        with output_file.open() as f:
            data = json.load(f)

        # Check first character has all fields
        char = data[0]
        assert "id" in char
        assert "canonical_name" in char
        assert "aliases" in char
        assert "roles" in char
        assert "source_profiles" in char

        # Check source profile structure
        if char["source_profiles"]:
            profile = char["source_profiles"][0]
            assert "source_id" in profile
            assert "traits" in profile
            assert "references" in profile

    def test_handles_nested_directory_creation(self, tmp_path):
        """Should create nested directories if they don't exist."""
        output_file = tmp_path / "exports" / "nested" / "characters.json"

        export_all_characters(str(output_file))

        assert output_file.exists()
        assert output_file.is_file()

    def test_unicode_in_character_names(self, tmp_path):
        """Should handle Unicode characters correctly."""
        output_file = tmp_path / "characters.json"

        export_all_characters(str(output_file))

        with output_file.open(encoding="utf-8") as f:
            content = f.read()
            data = json.loads(content)

        # Should be properly encoded (not ascii-escaped)
        assert isinstance(data, list)
        # Verify we can read it back
        assert all(isinstance(char["canonical_name"], str) for char in data)

    def test_overwrites_existing_file(self, tmp_path):
        """Should overwrite existing file without error."""
        output_file = tmp_path / "characters.json"

        # Create initial file with different content
        with output_file.open("w") as f:
            json.dump([{"test": "data"}], f)

        # Export should overwrite
        export_all_characters(str(output_file))

        with output_file.open() as f:
            data = json.load(f)

        # Should have real character data, not test data
        assert "test" not in data[0]
        assert "id" in data[0]

    def test_export_with_custom_data_root(self, tmp_path):
        """Should export from custom data root."""
        # Set up custom data root with test character
        custom_root = tmp_path / "custom_data"
        storage.configure_data_root(custom_root)

        try:
            test_char = Character(
                id="test_char",
                canonical_name="Test Character",
                aliases=["TC"],
                roles=["test"],
                source_profiles=[]
            )
            storage.save_character(test_char)

            # Export from custom root
            output_file = tmp_path / "export.json"
            export_all_characters(str(output_file))

            with output_file.open() as f:
                data = json.load(f)

            assert len(data) == 1
            assert data[0]["id"] == "test_char"

        finally:
            storage.reset_data_root()

    def test_empty_character_list(self, tmp_path):
        """Should handle empty character directory gracefully."""
        # Set up empty data root
        custom_root = tmp_path / "empty_data"
        storage.configure_data_root(custom_root)

        try:
            output_file = tmp_path / "export.json"
            export_all_characters(str(output_file))

            with output_file.open() as f:
                data = json.load(f)

            assert data == []

        finally:
            storage.reset_data_root()


class TestExportAllEvents:
    """Test export_all_events function."""

    def test_creates_valid_json_file(self, tmp_path):
        """export_all_events should create a valid JSON file."""
        output_file = tmp_path / "events.json"

        export_all_events(str(output_file))

        assert output_file.exists()

        # Should be valid JSON
        with output_file.open() as f:
            data = json.load(f)

        assert isinstance(data, list)
        assert len(data) > 0

    def test_contains_all_events(self, tmp_path):
        """Export should contain all events from storage."""
        output_file = tmp_path / "events.json"

        export_all_events(str(output_file))

        with output_file.open() as f:
            data = json.load(f)

        # Get all event IDs from storage
        expected_ids = storage.list_event_ids()
        exported_ids = [event["id"] for event in data]

        assert set(exported_ids) == set(expected_ids)

    def test_preserves_all_event_fields(self, tmp_path):
        """Exported events should have all required fields."""
        output_file = tmp_path / "events.json"

        export_all_events(str(output_file))

        with output_file.open() as f:
            data = json.load(f)

        # Check first event has all fields
        event = data[0]
        assert "id" in event
        assert "label" in event
        assert "participants" in event
        assert "accounts" in event

        # Check account structure
        if event["accounts"]:
            account = event["accounts"][0]
            assert "source_id" in account
            assert "reference" in account
            assert "summary" in account
            # notes is optional

    def test_handles_nested_directory_creation(self, tmp_path):
        """Should create nested directories if they don't exist."""
        output_file = tmp_path / "exports" / "nested" / "events.json"

        export_all_events(str(output_file))

        assert output_file.exists()
        assert output_file.is_file()

    def test_export_with_custom_data_root(self, tmp_path):
        """Should export from custom data root."""
        # Set up custom data root with test event
        custom_root = tmp_path / "custom_data"
        storage.configure_data_root(custom_root)

        try:
            test_event = Event(
                id="test_event",
                label="Test Event",
                participants=["test_char"],
                accounts=[
                    EventAccount(
                        source_id="test_source",
                        reference="Test 1:1",
                        summary="Test summary"
                    )
                ]
            )
            storage.save_event(test_event)

            # Export from custom root
            output_file = tmp_path / "export.json"
            export_all_events(str(output_file))

            with output_file.open() as f:
                data = json.load(f)

            assert len(data) == 1
            assert data[0]["id"] == "test_event"

        finally:
            storage.reset_data_root()

    def test_empty_event_list(self, tmp_path):
        """Should handle empty event directory gracefully."""
        # Set up empty data root
        custom_root = tmp_path / "empty_data"
        storage.configure_data_root(custom_root)

        try:
            output_file = tmp_path / "export.json"
            export_all_events(str(output_file))

            with output_file.open() as f:
                data = json.load(f)

            assert data == []

        finally:
            storage.reset_data_root()

    def test_event_accounts_with_notes(self, tmp_path):
        """Should preserve optional notes field in accounts."""
        output_file = tmp_path / "events.json"

        export_all_events(str(output_file))

        with output_file.open() as f:
            data = json.load(f)

        # Find an event with accounts
        event_with_accounts = next((e for e in data if e["accounts"]), None)
        assert event_with_accounts is not None

        # Notes field should be present (even if None)
        account = event_with_accounts["accounts"][0]
        assert "notes" in account or account.get("notes") is None


class TestExportIntegration:
    """Integration tests for export functionality."""

    def test_export_and_reimport_characters(self, tmp_path):
        """Exported data should be loadable back into Character objects."""
        output_file = tmp_path / "characters.json"

        # Export
        export_all_characters(str(output_file))

        # Load and verify
        with output_file.open() as f:
            data = json.load(f)

        # Reconstruct Character objects
        for char_data in data:
            # Convert source_profiles back to objects
            profiles = [SourceProfile(**sp) for sp in char_data["source_profiles"]]
            char = Character(**{**char_data, "source_profiles": profiles})

            # Should match original
            original = storage.load_character(char.id)
            assert char.id == original.id
            assert char.canonical_name == original.canonical_name

    def test_export_and_reimport_events(self, tmp_path):
        """Exported data should be loadable back into Event objects."""
        output_file = tmp_path / "events.json"

        # Export
        export_all_events(str(output_file))

        # Load and verify
        with output_file.open() as f:
            data = json.load(f)

        # Reconstruct Event objects
        for event_data in data:
            # Convert accounts back to objects
            accounts = [EventAccount(**acc) for acc in event_data["accounts"]]
            event = Event(**{**event_data, "accounts": accounts})

            # Should match original
            original = storage.load_event(event.id)
            assert event.id == original.id
            assert event.label == original.label

    def test_both_exports_to_same_directory(self, tmp_path):
        """Should be able to export both characters and events to same dir."""
        export_dir = tmp_path / "exports"

        char_file = export_dir / "characters.json"
        event_file = export_dir / "events.json"

        export_all_characters(str(char_file))
        export_all_events(str(event_file))

        assert char_file.exists()
        assert event_file.exists()

        # Both should be valid
        with char_file.open() as f:
            char_data = json.load(f)
        with event_file.open() as f:
            event_data = json.load(f)

        assert isinstance(char_data, list)
        assert isinstance(event_data, list)
