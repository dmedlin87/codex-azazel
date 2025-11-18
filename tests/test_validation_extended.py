"""Extended validation tests to improve coverage of bce/validation.py."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from bce.validation import validate_reference, validate_all, validate_cross_references


class TestValidateReferenceEdgeCases:
    """Test edge cases in validate_reference function."""

    def test_validate_reference_empty_string(self):
        """Empty reference should be invalid with appropriate error."""
        result = validate_reference("")

        assert result["valid"] is False
        assert result["error"] == "Empty reference"
        assert result["book"] is None
        assert result["chapter"] is None

    def test_validate_reference_whitespace_only(self):
        """Whitespace-only reference should be invalid."""
        result = validate_reference("   ")

        assert result["valid"] is False
        assert result["error"] == "Empty reference"

    def test_validate_reference_unrecognized_format(self):
        """Unrecognized format should be invalid."""
        result = validate_reference("NotAValidReference")

        assert result["valid"] is False
        assert result["error"] == "Unrecognized reference format"

    def test_validate_reference_non_numeric_chapter(self):
        """Non-numeric chapter should be invalid."""
        # This is hard to trigger due to regex, but let's test boundary
        result = validate_reference("Mark abc:1")

        assert result["valid"] is False
        assert "Unrecognized reference format" in result["error"]

    def test_validate_reference_unknown_book(self):
        """Unknown book should be invalid."""
        result = validate_reference("Nonexistent 1:1")

        assert result["valid"] is False
        assert result["canonical"] is False
        assert "Unknown book" in result["error"]

    def test_validate_reference_chapter_too_high(self):
        """Chapter number exceeding book's chapter count should be invalid."""
        result = validate_reference("Mark 99:1")

        assert result["valid"] is False
        assert result["canonical"] is True
        assert "only" in result["error"].lower()

    def test_validate_reference_chapter_zero(self):
        """Chapter 0 should be invalid."""
        result = validate_reference("Mark 0:1")

        assert result["valid"] is False
        assert "only" in result["error"].lower()

    def test_validate_reference_verse_zero(self):
        """Verse 0 should be invalid."""
        result = validate_reference("Mark 1:0")

        assert result["valid"] is False
        assert result["error"] == "Invalid verse range"

    def test_validate_reference_verse_range_reversed(self):
        """Verse range where end < start should be invalid."""
        result = validate_reference("Mark 1:10-5")

        assert result["valid"] is False
        assert result["error"] == "Invalid verse range"

    def test_validate_reference_valid_single_verse(self):
        """Valid single verse reference should succeed."""
        result = validate_reference("John 3:16")

        assert result["valid"] is True
        assert result["book"] == "John"
        assert result["chapter"] == 3
        assert result["verse_start"] == 16
        assert result["verse_end"] == 16
        assert result["canonical"] is True
        assert result["error"] is None

    def test_validate_reference_valid_verse_range(self):
        """Valid verse range should succeed."""
        result = validate_reference("Matthew 5:3-12")

        assert result["valid"] is True
        assert result["book"] == "Matthew"
        assert result["chapter"] == 5
        assert result["verse_start"] == 3
        assert result["verse_end"] == 12

    def test_validate_reference_book_name_normalization(self):
        """Book name should be normalized to title case."""
        result = validate_reference("mark 1:1")

        assert result["book"] == "Mark"

    def test_validate_reference_luke_max_chapters(self):
        """Luke has 24 chapters."""
        result = validate_reference("Luke 24:53")

        assert result["valid"] is True
        assert result["chapter"] == 24

        result_invalid = validate_reference("Luke 25:1")
        assert result_invalid["valid"] is False


class TestValidateAllRelationships:
    """Test relationship validation in validate_all."""

    def test_validate_all_detects_missing_relationship_type(self, monkeypatch):
        """validate_all should detect relationship missing 'type' field."""
        character_ids = ["test_char"]
        event_ids = []

        character_map = {
            "test_char": SimpleNamespace(
                id="test_char",
                source_profiles=[],
                relationships=[
                    {
                        "character_id": "other_char",
                        "sources": ["mark"],
                        "references": ["Mark 1:1"]
                        # Missing 'type' field
                    }
                ]
            )
        }

        monkeypatch.setattr("bce.validation.queries.list_character_ids", lambda: character_ids)
        monkeypatch.setattr("bce.validation.queries.get_character", lambda cid: character_map[cid])
        monkeypatch.setattr("bce.validation.queries.list_event_ids", lambda: event_ids)

        errors = validate_all()

        assert any("missing 'type' field" in error for error in errors)

    def test_validate_all_detects_missing_relationship_sources(self, monkeypatch):
        """validate_all should detect relationship missing 'sources' field."""
        character_ids = ["test_char"]
        event_ids = []

        character_map = {
            "test_char": SimpleNamespace(
                id="test_char",
                source_profiles=[],
                relationships=[
                    {
                        "character_id": "other_char",
                        "type": "teacher",
                        "references": ["Mark 1:1"]
                        # Missing 'sources' field
                    }
                ]
            )
        }

        monkeypatch.setattr("bce.validation.queries.list_character_ids", lambda: character_ids)
        monkeypatch.setattr("bce.validation.queries.get_character", lambda cid: character_map[cid])
        monkeypatch.setattr("bce.validation.queries.list_event_ids", lambda: event_ids)

        errors = validate_all()

        assert any("missing 'sources' field" in error for error in errors)

    def test_validate_all_detects_missing_relationship_references(self, monkeypatch):
        """validate_all should detect relationship missing 'references' field."""
        character_ids = ["test_char"]
        event_ids = []

        character_map = {
            "test_char": SimpleNamespace(
                id="test_char",
                source_profiles=[],
                relationships=[
                    {
                        "character_id": "other_char",
                        "type": "teacher",
                        "sources": ["mark"]
                        # Missing 'references' field
                    }
                ]
            )
        }

        monkeypatch.setattr("bce.validation.queries.list_character_ids", lambda: character_ids)
        monkeypatch.setattr("bce.validation.queries.get_character", lambda cid: character_map[cid])
        monkeypatch.setattr("bce.validation.queries.list_event_ids", lambda: event_ids)

        errors = validate_all()

        assert any("missing 'references' field" in error for error in errors)

    def test_validate_all_detects_missing_relationship_character_id(self, monkeypatch):
        """validate_all should detect relationship missing 'character_id'."""
        character_ids = ["test_char"]
        event_ids = []

        character_map = {
            "test_char": SimpleNamespace(
                id="test_char",
                source_profiles=[],
                relationships=[
                    {
                        # Missing 'character_id' field
                        "type": "teacher",
                        "sources": ["mark"],
                        "references": ["Mark 1:1"]
                    }
                ]
            )
        }

        monkeypatch.setattr("bce.validation.queries.list_character_ids", lambda: character_ids)
        monkeypatch.setattr("bce.validation.queries.get_character", lambda cid: character_map[cid])
        monkeypatch.setattr("bce.validation.queries.list_event_ids", lambda: event_ids)

        errors = validate_all()

        assert any("missing 'character_id'" in error for error in errors)

    def test_validate_all_detects_unknown_relationship_target(self, monkeypatch):
        """validate_all should detect relationship referencing unknown character."""
        character_ids = ["test_char"]
        event_ids = []

        character_map = {
            "test_char": SimpleNamespace(
                id="test_char",
                source_profiles=[],
                relationships=[
                    {
                        "character_id": "nonexistent_char",
                        "type": "teacher",
                        "sources": ["mark"],
                        "references": ["Mark 1:1"]
                    }
                ]
            )
        }

        monkeypatch.setattr("bce.validation.queries.list_character_ids", lambda: character_ids)
        monkeypatch.setattr("bce.validation.queries.get_character", lambda cid: character_map[cid])
        monkeypatch.setattr("bce.validation.queries.list_event_ids", lambda: event_ids)

        errors = validate_all()

        assert any("references unknown character 'nonexistent_char'" in error for error in errors)

    def test_validate_all_detects_non_dict_relationship(self, monkeypatch):
        """validate_all should detect non-dict relationship."""
        character_ids = ["test_char"]
        event_ids = []

        character_map = {
            "test_char": SimpleNamespace(
                id="test_char",
                source_profiles=[],
                relationships=["not_a_dict"]
            )
        }

        monkeypatch.setattr("bce.validation.queries.list_character_ids", lambda: character_ids)
        monkeypatch.setattr("bce.validation.queries.get_character", lambda cid: character_map[cid])
        monkeypatch.setattr("bce.validation.queries.list_event_ids", lambda: event_ids)

        errors = validate_all()

        assert any("is not a dict" in error for error in errors)


class TestValidateCrossReferencesExtended:
    """Extended tests for validate_cross_references."""

    def test_validate_cross_references_handles_character_load_failure(self, monkeypatch):
        """validate_cross_references should handle character load failures."""
        character_ids = ["char_a", "char_b"]
        event_ids = []

        def fake_get_character(char_id: str):
            if char_id == "char_b":
                raise RuntimeError("Load failed")
            return SimpleNamespace(id="char_a", source_profiles=[])

        monkeypatch.setattr("bce.validation.queries.list_character_ids", lambda: character_ids)
        monkeypatch.setattr("bce.validation.queries.get_character", fake_get_character)
        monkeypatch.setattr("bce.validation.queries.list_event_ids", lambda: event_ids)

        errors = validate_cross_references()

        assert any("Failed to load character 'char_b'" in error for error in errors)

    def test_validate_cross_references_handles_event_load_failure(self, monkeypatch):
        """validate_cross_references should handle event load failures."""
        character_ids = ["char_a"]
        event_ids = ["event_a", "event_b"]

        character_map = {
            "char_a": SimpleNamespace(id="char_a", source_profiles=[])
        }

        def fake_get_event(event_id: str):
            if event_id == "event_b":
                raise RuntimeError("Event load failed")
            return SimpleNamespace(id="event_a", participants=[], accounts=[])

        monkeypatch.setattr("bce.validation.queries.list_character_ids", lambda: character_ids)
        monkeypatch.setattr("bce.validation.queries.get_character", lambda cid: character_map[cid])
        monkeypatch.setattr("bce.validation.queries.list_event_ids", lambda: event_ids)
        monkeypatch.setattr("bce.validation.queries.get_event", fake_get_event)

        errors = validate_cross_references()

        assert any("Failed to load event 'event_b'" in error for error in errors)

    def test_validate_cross_references_skips_events_without_participants(self, monkeypatch):
        """Events without participants should skip account-source validation."""
        character_ids = ["char_a"]
        event_ids = ["event_no_participants"]

        character_map = {
            "char_a": SimpleNamespace(
                id="char_a",
                source_profiles=[SimpleNamespace(source_id="source1")]
            )
        }

        event_map = {
            "event_no_participants": SimpleNamespace(
                id="event_no_participants",
                participants=[],  # No participants
                accounts=[SimpleNamespace(source_id="source_missing")]
            )
        }

        monkeypatch.setattr("bce.validation.queries.list_character_ids", lambda: character_ids)
        monkeypatch.setattr("bce.validation.queries.get_character", lambda cid: character_map[cid])
        monkeypatch.setattr("bce.validation.queries.list_event_ids", lambda: event_ids)
        monkeypatch.setattr("bce.validation.queries.get_event", lambda eid: event_map[eid])

        errors = validate_cross_references()

        # Should not report source mismatch for events without participants
        assert not any("source_missing" in error for error in errors)

    def test_validate_cross_references_skips_non_string_source_ids(self, monkeypatch):
        """Non-string or empty source_ids should be skipped."""
        character_ids = ["char_a"]
        event_ids = ["event_test"]

        character_map = {
            "char_a": SimpleNamespace(
                id="char_a",
                source_profiles=[SimpleNamespace(source_id="source1")]
            )
        }

        event_map = {
            "event_test": SimpleNamespace(
                id="event_test",
                participants=["char_a"],
                accounts=[
                    SimpleNamespace(source_id=None),  # None source_id
                    SimpleNamespace(source_id=""),     # Empty source_id
                ]
            )
        }

        monkeypatch.setattr("bce.validation.queries.list_character_ids", lambda: character_ids)
        monkeypatch.setattr("bce.validation.queries.get_character", lambda cid: character_map[cid])
        monkeypatch.setattr("bce.validation.queries.list_event_ids", lambda: event_ids)
        monkeypatch.setattr("bce.validation.queries.get_event", lambda eid: event_map[eid])

        errors = validate_cross_references()

        # Should not report errors for None or empty source_ids
        assert len(errors) == 0


class TestValidateReferenceInContext:
    """Test scripture reference validation in context."""

    def test_validate_all_skips_non_string_references_in_characters(self, monkeypatch):
        """Non-string references should be skipped during validation."""
        character_ids = ["test_char"]
        event_ids = []

        character_map = {
            "test_char": SimpleNamespace(
                id="test_char",
                source_profiles=[
                    SimpleNamespace(
                        source_id="mark",
                        references=[123, None, "Mark 1:1"]  # Non-string values
                    )
                ],
                relationships=[]
            )
        }

        monkeypatch.setattr("bce.validation.queries.list_character_ids", lambda: character_ids)
        monkeypatch.setattr("bce.validation.queries.get_character", lambda cid: character_map[cid])
        monkeypatch.setattr("bce.validation.queries.list_event_ids", lambda: event_ids)

        errors = validate_all()

        # Should not crash on non-string references, should skip them
        # Only valid reference should be processed
        assert len(errors) == 0 or not any("123" in error for error in errors)

    def test_validate_all_skips_non_string_references_in_events(self, monkeypatch):
        """Non-string references in event accounts should be skipped."""
        character_ids = []
        event_ids = ["test_event"]

        event_map = {
            "test_event": SimpleNamespace(
                id="test_event",
                participants=[],
                accounts=[
                    SimpleNamespace(
                        source_id="mark",
                        reference=None  # Non-string reference
                    )
                ]
            )
        }

        monkeypatch.setattr("bce.validation.queries.list_character_ids", lambda: character_ids)
        monkeypatch.setattr("bce.validation.queries.list_event_ids", lambda: event_ids)
        monkeypatch.setattr("bce.validation.queries.get_event", lambda eid: event_map[eid])

        errors = validate_all()

        # Should not crash on None reference
        # No errors should be reported for non-string references
        assert len(errors) == 0 or not any("None" in error for error in errors)
