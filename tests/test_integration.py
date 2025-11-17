"""Integration tests for end-to-end workflows.

These tests verify that different modules work correctly together.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bce import contradictions, dossiers, queries, storage
from bce.export_json import export_all_characters, export_all_events
from bce.export_markdown import dossier_to_markdown
from bce.models import Character, Event, EventAccount, SourceProfile
from bce.validation import validate_all


class TestCompleteCharacterLifecycle:
    """Test complete lifecycle of a character from creation to export."""

    def test_create_save_load_query_export(self, tmp_path):
        """Complete workflow: create → save → load → query → export."""
        custom_root = tmp_path / "data"
        storage.configure_data_root(custom_root)

        try:
            # Step 1: Create a character
            char = Character(
                id="test_char",
                canonical_name="Test Character",
                aliases=["TC", "Testy"],
                roles=["tester", "validator"],
                source_profiles=[
                    SourceProfile(
                        source_id="source1",
                        traits={"role": "teacher", "origin": "Galilee"},
                        references=["Source1 1:1"]
                    ),
                    SourceProfile(
                        source_id="source2",
                        traits={"role": "prophet", "origin": "Galilee"},
                        references=["Source2 2:2"]
                    )
                ]
            )

            # Step 2: Save to storage
            storage.save_character(char)

            # Step 3: Load via storage
            loaded = storage.load_character("test_char")
            assert loaded.id == "test_char"

            # Step 4: Query via queries module (with caching)
            queried = queries.get_character("test_char")
            assert queried.id == "test_char"
            assert queried.canonical_name == "Test Character"

            # Step 5: Build dossier
            dossier = dossiers.build_character_dossier("test_char")
            assert dossier["id"] == "test_char"
            assert "trait_comparison" in dossier
            assert "trait_conflicts" in dossier

            # Step 6: Check for conflicts
            conflicts = contradictions.find_trait_conflicts("test_char")
            assert "role" in conflicts  # Different roles in different sources

            # Step 7: Export to JSON
            export_file = tmp_path / "export.json"
            export_all_characters(str(export_file))

            with export_file.open() as f:
                exported_data = json.load(f)

            assert len(exported_data) == 1
            assert exported_data[0]["id"] == "test_char"

            # Step 8: Export dossier to Markdown
            markdown = dossier_to_markdown(dossier)
            assert "# Test Character" in markdown
            assert "test_char" in markdown

        finally:
            storage.reset_data_root()

    def test_create_save_validate_workflow(self, tmp_path):
        """Create character → save → validate."""
        custom_root = tmp_path / "data"
        storage.configure_data_root(custom_root)

        try:
            # Create character
            char = Character(
                id="valid_char",
                canonical_name="Valid Character"
            )
            storage.save_character(char)

            # Validate all data
            errors = validate_all()
            assert errors == []  # No errors

        finally:
            storage.reset_data_root()


class TestCompleteEventLifecycle:
    """Test complete lifecycle of an event from creation to export."""

    def test_create_save_load_query_export(self, tmp_path):
        """Complete workflow: create → save → load → query → export."""
        custom_root = tmp_path / "data"
        storage.configure_data_root(custom_root)

        try:
            # Step 1: Create an event
            event = Event(
                id="test_event",
                label="Test Event",
                participants=["char1", "char2"],
                accounts=[
                    EventAccount(
                        source_id="source1",
                        reference="Source1 1:1",
                        summary="First account",
                        notes="From source 1"
                    ),
                    EventAccount(
                        source_id="source2",
                        reference="Source2 2:2",
                        summary="Second account",
                        notes="From source 2"
                    )
                ]
            )

            # Step 2: Save to storage
            storage.save_event(event)

            # Step 3: Load via storage
            loaded = storage.load_event("test_event")
            assert loaded.id == "test_event"

            # Step 4: Query via queries module
            queried = queries.get_event("test_event")
            assert queried.id == "test_event"
            assert queried.label == "Test Event"

            # Step 5: Build dossier
            dossier = dossiers.build_event_dossier("test_event")
            assert dossier["id"] == "test_event"
            assert "account_conflicts" in dossier

            # Step 6: Check for conflicts
            conflicts = contradictions.find_events_with_conflicting_accounts("test_event")
            # Should have conflicts in summary, reference, and notes
            assert len(conflicts) > 0

            # Step 7: Export to JSON
            export_file = tmp_path / "export.json"
            export_all_events(str(export_file))

            with export_file.open() as f:
                exported_data = json.load(f)

            assert len(exported_data) == 1
            assert exported_data[0]["id"] == "test_event"

            # Step 8: Export dossier to Markdown
            markdown = dossier_to_markdown(dossier)
            assert "# Test Event" in markdown
            assert "test_event" in markdown

        finally:
            storage.reset_data_root()


class TestCrossModuleCacheConsistency:
    """Test cache consistency across modules."""

    def test_cache_invalidation_across_modules(self, tmp_path):
        """Cache should be invalidated when data changes."""
        custom_root = tmp_path / "data"
        storage.configure_data_root(custom_root)

        try:
            # Create and save initial character
            char1 = Character(id="cache_test", canonical_name="Original")
            storage.save_character(char1)

            # Query via queries module (caches result)
            queried1 = queries.get_character("cache_test")
            assert queried1.canonical_name == "Original"

            # Build dossier (uses queries module)
            dossier1 = dossiers.build_character_dossier("cache_test")
            assert dossier1["canonical_name"] == "Original"

            # Update character
            char2 = Character(id="cache_test", canonical_name="Updated")
            storage.save_character(char2)  # Should clear cache

            # Query again - should get updated version
            queried2 = queries.get_character("cache_test")
            assert queried2.canonical_name == "Updated"

            # Build dossier again - should get updated version
            dossier2 = dossiers.build_character_dossier("cache_test")
            assert dossier2["canonical_name"] == "Updated"

        finally:
            storage.reset_data_root()

    def test_queries_dossiers_contradictions_integration(self, tmp_path):
        """Queries, dossiers, and contradictions should work together."""
        custom_root = tmp_path / "data"
        storage.configure_data_root(custom_root)

        try:
            # Create character with conflicting traits
            char = Character(
                id="conflict_test",
                canonical_name="Conflict Test",
                source_profiles=[
                    SourceProfile(
                        source_id="s1",
                        traits={"trait": "value1"}
                    ),
                    SourceProfile(
                        source_id="s2",
                        traits={"trait": "value2"}
                    )
                ]
            )
            storage.save_character(char)

            # Query the character
            queried = queries.get_character("conflict_test")
            assert len(queried.source_profiles) == 2

            # Find conflicts
            conflicts = contradictions.find_trait_conflicts("conflict_test")
            assert "trait" in conflicts

            # Build dossier (should include conflicts)
            dossier = dossiers.build_character_dossier("conflict_test")
            assert "trait_conflicts" in dossier
            assert "trait" in dossier["trait_conflicts"]

        finally:
            storage.reset_data_root()


class TestMultipleCharactersAndEvents:
    """Test workflows with multiple characters and events."""

    def test_create_multiple_characters_and_events(self, tmp_path):
        """Create multiple characters and events, then query and export."""
        custom_root = tmp_path / "data"
        storage.configure_data_root(custom_root)

        try:
            # Create multiple characters
            char1 = Character(id="char1", canonical_name="Character 1")
            char2 = Character(id="char2", canonical_name="Character 2")
            char3 = Character(id="char3", canonical_name="Character 3")

            storage.save_character(char1)
            storage.save_character(char2)
            storage.save_character(char3)

            # Create multiple events
            event1 = Event(
                id="event1",
                label="Event 1",
                participants=["char1", "char2"]
            )
            event2 = Event(
                id="event2",
                label="Event 2",
                participants=["char2", "char3"]
            )

            storage.save_event(event1)
            storage.save_event(event2)

            # List all characters and events
            char_ids = queries.list_character_ids()
            assert len(char_ids) == 3

            event_ids = queries.list_event_ids()
            assert len(event_ids) == 2

            # Query events for a character
            char2_events = queries.list_events_for_character("char2")
            assert len(char2_events) == 2  # char2 in both events

            # Build all dossiers
            all_char_dossiers = dossiers.build_all_character_dossiers()
            assert len(all_char_dossiers) == 3

            all_event_dossiers = dossiers.build_all_event_dossiers()
            assert len(all_event_dossiers) == 2

            # Export all
            char_export = tmp_path / "characters.json"
            event_export = tmp_path / "events.json"

            export_all_characters(str(char_export))
            export_all_events(str(event_export))

            assert char_export.exists()
            assert event_export.exists()

        finally:
            storage.reset_data_root()

    def test_validate_all_with_multiple_entities(self, tmp_path):
        """Validation should work with multiple characters and events."""
        custom_root = tmp_path / "data"
        storage.configure_data_root(custom_root)

        try:
            # Create valid data
            char = Character(id="char", canonical_name="Character")
            event = Event(
                id="event",
                label="Event",
                participants=["char"]  # References valid character
            )

            storage.save_character(char)
            storage.save_event(event)

            # Validate - should pass
            errors = validate_all()
            assert errors == []

        finally:
            storage.reset_data_root()


class TestRoundTripExportImport:
    """Test exporting and re-importing data."""

    def test_export_and_reimport_characters(self, tmp_path):
        """Export characters to JSON and verify they can be re-imported."""
        # Use actual data
        export_file = tmp_path / "characters.json"

        # Export all characters
        export_all_characters(str(export_file))

        # Load exported data
        with export_file.open() as f:
            exported = json.load(f)

        # Verify we can reconstruct Character objects
        for char_data in exported:
            profiles = [SourceProfile(**sp) for sp in char_data["source_profiles"]]
            char = Character(**{**char_data, "source_profiles": profiles})

            # Verify against original
            original = storage.load_character(char.id)
            assert char.id == original.id
            assert char.canonical_name == original.canonical_name

    def test_export_and_reimport_events(self, tmp_path):
        """Export events to JSON and verify they can be re-imported."""
        # Use actual data
        export_file = tmp_path / "events.json"

        # Export all events
        export_all_events(str(export_file))

        # Load exported data
        with export_file.open() as f:
            exported = json.load(f)

        # Verify we can reconstruct Event objects
        for event_data in exported:
            accounts = [EventAccount(**acc) for acc in event_data["accounts"]]
            event = Event(**{**event_data, "accounts": accounts})

            # Verify against original
            original = storage.load_event(event.id)
            assert event.id == original.id
            assert event.label == original.label


class TestConfigureDataRoot:
    """Test data root configuration integration."""

    def test_switch_data_roots_and_query(self, tmp_path):
        """Switch between data roots and verify queries work."""
        root1 = tmp_path / "root1"
        root2 = tmp_path / "root2"

        # Configure first root
        storage.configure_data_root(root1)
        char1 = Character(id="char1", canonical_name="Root 1 Character")
        storage.save_character(char1)

        # Verify in first root
        assert queries.get_character("char1").canonical_name == "Root 1 Character"

        # Switch to second root
        storage.configure_data_root(root2)
        char2 = Character(id="char2", canonical_name="Root 2 Character")
        storage.save_character(char2)

        # Verify in second root
        assert queries.get_character("char2").canonical_name == "Root 2 Character"

        # char1 should not exist in root2
        with pytest.raises(FileNotFoundError):
            queries.get_character("char1")

        # Switch back to first root
        storage.configure_data_root(root1)

        # char1 should exist again
        assert queries.get_character("char1").canonical_name == "Root 1 Character"

        # char2 should not exist in root1
        with pytest.raises(FileNotFoundError):
            queries.get_character("char2")

        # Reset
        storage.reset_data_root()


class TestExportToDossiersToMarkdown:
    """Test complete export pipeline to Markdown."""

    def test_full_export_pipeline(self, tmp_path):
        """Build dossiers and export to Markdown."""
        custom_root = tmp_path / "data"
        storage.configure_data_root(custom_root)

        try:
            # Create character
            char = Character(
                id="export_test",
                canonical_name="Export Test",
                aliases=["ET"],
                roles=["tester"],
                source_profiles=[
                    SourceProfile(
                        source_id="source1",
                        traits={"key": "value"},
                        references=["Ref 1:1"]
                    )
                ]
            )
            storage.save_character(char)

            # Build dossier
            dossier = dossiers.build_character_dossier("export_test")

            # Export to Markdown
            markdown = dossier_to_markdown(dossier)

            # Verify Markdown content
            assert "# Export Test" in markdown
            assert "ID: export_test" in markdown
            assert "ET" in markdown  # Alias
            assert "tester" in markdown  # Role
            assert "source1" in markdown  # Source

            # Save Markdown to file
            md_file = tmp_path / "export_test.md"
            md_file.write_text(markdown)

            # Verify file exists and has content
            assert md_file.exists()
            assert len(md_file.read_text()) > 100

        finally:
            storage.reset_data_root()
