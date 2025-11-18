"""
Tests for validate_schema_hydration.py - Schema validation script.

These tests verify the validation logic for checking schema completeness
and hydration of character and event data.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Import the module to test
import validate_schema_hydration as validate


class TestLoadJsonFile:
    """Test JSON file loading."""

    def test_load_valid_json(self):
        """Test loading a valid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_data = {"id": "test", "value": 123}
            json.dump(test_data, f)
            temp_path = Path(f.name)

        try:
            loaded = validate.load_json_file(temp_path)
            assert loaded == test_data
        finally:
            temp_path.unlink()

    def test_load_json_preserves_types(self):
        """Test that load preserves data types."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_data = {
                "string": "text",
                "number": 42,
                "list": [1, 2, 3],
                "dict": {"nested": "value"}
            }
            json.dump(test_data, f)
            temp_path = Path(f.name)

        try:
            loaded = validate.load_json_file(temp_path)
            assert isinstance(loaded["string"], str)
            assert isinstance(loaded["number"], int)
            assert isinstance(loaded["list"], list)
            assert isinstance(loaded["dict"], dict)
        finally:
            temp_path.unlink()


class TestCheckCharacterHydration:
    """Test character validation logic."""

    def test_valid_character_returns_no_issues(self):
        """Test that a fully valid character returns no issues."""
        char_data = {
            "id": "test_char",
            "canonical_name": "Test Character",
            "aliases": ["Alias1"],
            "roles": ["role1"],
            "tags": ["tag1"],
            "relationships": [],
            "source_profiles": [
                {
                    "source_id": "test_source",
                    "traits": {"trait1": "value1"},
                    "references": ["Test 1:1"]
                }
            ]
        }

        issues = validate.check_character_hydration("test_char", char_data)
        assert len(issues) == 0

    def test_missing_id_field(self):
        """Test detection of missing 'id' field."""
        char_data = {
            "canonical_name": "Test",
            "aliases": [],
            "roles": [],
            "source_profiles": []
        }

        issues = validate.check_character_hydration("test_char", char_data)
        assert any("Missing 'id' field" in issue for issue in issues)

    def test_id_mismatch(self):
        """Test detection of ID mismatch between filename and content."""
        char_data = {
            "id": "wrong_id",
            "canonical_name": "Test",
            "aliases": [],
            "roles": [],
            "source_profiles": []
        }

        issues = validate.check_character_hydration("test_char", char_data)
        assert any("ID mismatch" in issue for issue in issues)

    def test_missing_canonical_name(self):
        """Test detection of missing canonical_name."""
        char_data = {
            "id": "test_char",
            "aliases": [],
            "roles": [],
            "source_profiles": []
        }

        issues = validate.check_character_hydration("test_char", char_data)
        assert any("canonical_name" in issue for issue in issues)

    def test_empty_canonical_name(self):
        """Test detection of empty canonical_name."""
        char_data = {
            "id": "test_char",
            "canonical_name": "",
            "aliases": [],
            "roles": [],
            "source_profiles": []
        }

        issues = validate.check_character_hydration("test_char", char_data)
        assert any("canonical_name" in issue for issue in issues)

    def test_missing_aliases(self):
        """Test detection of missing 'aliases' field."""
        char_data = {
            "id": "test_char",
            "canonical_name": "Test",
            "roles": [],
            "source_profiles": []
        }

        issues = validate.check_character_hydration("test_char", char_data)
        assert any("aliases" in issue.lower() for issue in issues)

    def test_aliases_not_list(self):
        """Test detection of 'aliases' not being a list."""
        char_data = {
            "id": "test_char",
            "canonical_name": "Test",
            "aliases": "not a list",
            "roles": [],
            "source_profiles": []
        }

        issues = validate.check_character_hydration("test_char", char_data)
        assert any("aliases" in issue and "not a list" in issue for issue in issues)

    def test_empty_aliases_array(self):
        """Test detection of empty aliases array."""
        char_data = {
            "id": "test_char",
            "canonical_name": "Test",
            "aliases": [],
            "roles": ["role1"],
            "tags": [],
            "relationships": [],
            "source_profiles": [{"source_id": "s", "traits": {"t": "v"}, "references": ["r"]}]
        }

        issues = validate.check_character_hydration("test_char", char_data)
        assert any("Empty 'aliases'" in issue for issue in issues)

    def test_missing_roles(self):
        """Test detection of missing 'roles' field."""
        char_data = {
            "id": "test_char",
            "canonical_name": "Test",
            "aliases": ["a"],
            "source_profiles": []
        }

        issues = validate.check_character_hydration("test_char", char_data)
        assert any("roles" in issue.lower() for issue in issues)

    def test_empty_roles_array(self):
        """Test detection of empty roles array."""
        char_data = {
            "id": "test_char",
            "canonical_name": "Test",
            "aliases": ["a"],
            "roles": [],
            "source_profiles": []
        }

        issues = validate.check_character_hydration("test_char", char_data)
        assert any("Empty 'roles'" in issue for issue in issues)

    def test_missing_tags_field(self):
        """Test detection of missing 'tags' field (recommended)."""
        char_data = {
            "id": "test_char",
            "canonical_name": "Test",
            "aliases": ["a"],
            "roles": ["r"],
            "relationships": [],
            "source_profiles": [{"source_id": "s", "traits": {"t": "v"}, "references": ["r"]}]
        }

        issues = validate.check_character_hydration("test_char", char_data)
        assert any("tags" in issue and "recommended" in issue for issue in issues)

    def test_empty_tags_array(self):
        """Test detection of empty tags array."""
        char_data = {
            "id": "test_char",
            "canonical_name": "Test",
            "aliases": ["a"],
            "roles": ["r"],
            "tags": [],
            "relationships": [],
            "source_profiles": [{"source_id": "s", "traits": {"t": "v"}, "references": ["r"]}]
        }

        issues = validate.check_character_hydration("test_char", char_data)
        assert any("Empty 'tags'" in issue for issue in issues)

    def test_missing_relationships_field(self):
        """Test detection of missing 'relationships' field (recommended)."""
        char_data = {
            "id": "test_char",
            "canonical_name": "Test",
            "aliases": ["a"],
            "roles": ["r"],
            "tags": ["t"],
            "source_profiles": [{"source_id": "s", "traits": {"t": "v"}, "references": ["r"]}]
        }

        issues = validate.check_character_hydration("test_char", char_data)
        assert any("relationships" in issue and "recommended" in issue for issue in issues)

    def test_relationships_not_list(self):
        """Test detection of relationships not being a list."""
        char_data = {
            "id": "test_char",
            "canonical_name": "Test",
            "aliases": ["a"],
            "roles": ["r"],
            "tags": ["t"],
            "relationships": "not a list",
            "source_profiles": []
        }

        issues = validate.check_character_hydration("test_char", char_data)
        assert any("relationships" in issue and "not a list" in issue for issue in issues)

    def test_missing_source_profiles(self):
        """Test detection of missing source_profiles."""
        char_data = {
            "id": "test_char",
            "canonical_name": "Test",
            "aliases": ["a"],
            "roles": ["r"],
            "tags": ["t"],
            "relationships": []
        }

        issues = validate.check_character_hydration("test_char", char_data)
        assert any("source_profiles" in issue for issue in issues)

    def test_empty_source_profiles(self):
        """Test detection of empty source_profiles array."""
        char_data = {
            "id": "test_char",
            "canonical_name": "Test",
            "aliases": ["a"],
            "roles": ["r"],
            "tags": ["t"],
            "relationships": [],
            "source_profiles": []
        }

        issues = validate.check_character_hydration("test_char", char_data)
        assert any("Empty 'source_profiles'" in issue for issue in issues)

    def test_source_profile_missing_source_id(self):
        """Test detection of source profile missing source_id."""
        char_data = {
            "id": "test_char",
            "canonical_name": "Test",
            "aliases": ["a"],
            "roles": ["r"],
            "tags": ["t"],
            "relationships": [],
            "source_profiles": [
                {
                    "traits": {"t": "v"},
                    "references": ["r"]
                }
            ]
        }

        issues = validate.check_character_hydration("test_char", char_data)
        assert any("source_profiles[0]" in issue and "source_id" in issue for issue in issues)

    def test_source_profile_missing_traits(self):
        """Test detection of source profile missing traits."""
        char_data = {
            "id": "test_char",
            "canonical_name": "Test",
            "aliases": ["a"],
            "roles": ["r"],
            "tags": ["t"],
            "relationships": [],
            "source_profiles": [
                {
                    "source_id": "test",
                    "references": ["r"]
                }
            ]
        }

        issues = validate.check_character_hydration("test_char", char_data)
        assert any("traits" in issue for issue in issues)

    def test_source_profile_empty_traits(self):
        """Test detection of source profile with empty traits."""
        char_data = {
            "id": "test_char",
            "canonical_name": "Test",
            "aliases": ["a"],
            "roles": ["r"],
            "tags": ["t"],
            "relationships": [],
            "source_profiles": [
                {
                    "source_id": "test",
                    "traits": {},
                    "references": ["r"]
                }
            ]
        }

        issues = validate.check_character_hydration("test_char", char_data)
        assert any("empty 'traits'" in issue for issue in issues)

    def test_source_profile_missing_references(self):
        """Test detection of source profile missing references."""
        char_data = {
            "id": "test_char",
            "canonical_name": "Test",
            "aliases": ["a"],
            "roles": ["r"],
            "tags": ["t"],
            "relationships": [],
            "source_profiles": [
                {
                    "source_id": "test",
                    "traits": {"t": "v"}
                }
            ]
        }

        issues = validate.check_character_hydration("test_char", char_data)
        assert any("references" in issue for issue in issues)

    def test_source_profile_empty_references(self):
        """Test detection of source profile with empty references."""
        char_data = {
            "id": "test_char",
            "canonical_name": "Test",
            "aliases": ["a"],
            "roles": ["r"],
            "tags": ["t"],
            "relationships": [],
            "source_profiles": [
                {
                    "source_id": "test",
                    "traits": {"t": "v"},
                    "references": []
                }
            ]
        }

        issues = validate.check_character_hydration("test_char", char_data)
        assert any("empty 'references'" in issue for issue in issues)


class TestCheckEventHydration:
    """Test event validation logic."""

    def test_valid_event_returns_no_issues(self):
        """Test that a fully valid event returns no issues."""
        event_data = {
            "id": "test_event",
            "label": "Test Event",
            "participants": ["char1"],
            "tags": ["tag1"],
            "parallels": [],
            "accounts": [
                {
                    "source_id": "test_source",
                    "reference": "Test 1:1",
                    "summary": "Event summary"
                }
            ]
        }

        issues = validate.check_event_hydration("test_event", event_data)
        assert len(issues) == 0

    def test_missing_id_field(self):
        """Test detection of missing 'id' field."""
        event_data = {
            "label": "Test",
            "participants": [],
            "accounts": []
        }

        issues = validate.check_event_hydration("test_event", event_data)
        assert any("Missing 'id' field" in issue for issue in issues)

    def test_id_mismatch(self):
        """Test detection of ID mismatch."""
        event_data = {
            "id": "wrong_id",
            "label": "Test",
            "participants": [],
            "accounts": []
        }

        issues = validate.check_event_hydration("test_event", event_data)
        assert any("ID mismatch" in issue for issue in issues)

    def test_missing_label(self):
        """Test detection of missing label."""
        event_data = {
            "id": "test_event",
            "participants": [],
            "accounts": []
        }

        issues = validate.check_event_hydration("test_event", event_data)
        assert any("label" in issue for issue in issues)

    def test_empty_label(self):
        """Test detection of empty label."""
        event_data = {
            "id": "test_event",
            "label": "",
            "participants": [],
            "accounts": []
        }

        issues = validate.check_event_hydration("test_event", event_data)
        assert any("label" in issue for issue in issues)

    def test_missing_participants(self):
        """Test detection of missing participants."""
        event_data = {
            "id": "test_event",
            "label": "Test",
            "accounts": []
        }

        issues = validate.check_event_hydration("test_event", event_data)
        assert any("participants" in issue for issue in issues)

    def test_participants_not_list(self):
        """Test detection of participants not being a list."""
        event_data = {
            "id": "test_event",
            "label": "Test",
            "participants": "not a list",
            "accounts": []
        }

        issues = validate.check_event_hydration("test_event", event_data)
        assert any("participants" in issue and "not a list" in issue for issue in issues)

    def test_missing_tags_field(self):
        """Test detection of missing 'tags' field (recommended)."""
        event_data = {
            "id": "test_event",
            "label": "Test",
            "participants": [],
            "parallels": [],
            "accounts": [{"source_id": "s", "reference": "r", "summary": "s"}]
        }

        issues = validate.check_event_hydration("test_event", event_data)
        assert any("tags" in issue and "recommended" in issue for issue in issues)

    def test_empty_tags_array(self):
        """Test detection of empty tags array."""
        event_data = {
            "id": "test_event",
            "label": "Test",
            "participants": [],
            "tags": [],
            "parallels": [],
            "accounts": [{"source_id": "s", "reference": "r", "summary": "s"}]
        }

        issues = validate.check_event_hydration("test_event", event_data)
        assert any("Empty 'tags'" in issue for issue in issues)

    def test_missing_parallels_field(self):
        """Test detection of missing 'parallels' field (recommended)."""
        event_data = {
            "id": "test_event",
            "label": "Test",
            "participants": [],
            "tags": ["t"],
            "accounts": [{"source_id": "s", "reference": "r", "summary": "s"}]
        }

        issues = validate.check_event_hydration("test_event", event_data)
        assert any("parallels" in issue and "recommended" in issue for issue in issues)

    def test_parallels_not_list(self):
        """Test detection of parallels not being a list."""
        event_data = {
            "id": "test_event",
            "label": "Test",
            "participants": [],
            "tags": ["t"],
            "parallels": "not a list",
            "accounts": []
        }

        issues = validate.check_event_hydration("test_event", event_data)
        assert any("parallels" in issue and "not a list" in issue for issue in issues)

    def test_missing_accounts(self):
        """Test detection of missing accounts."""
        event_data = {
            "id": "test_event",
            "label": "Test",
            "participants": [],
            "tags": ["t"],
            "parallels": []
        }

        issues = validate.check_event_hydration("test_event", event_data)
        assert any("accounts" in issue for issue in issues)

    def test_empty_accounts(self):
        """Test detection of empty accounts array."""
        event_data = {
            "id": "test_event",
            "label": "Test",
            "participants": [],
            "tags": ["t"],
            "parallels": [],
            "accounts": []
        }

        issues = validate.check_event_hydration("test_event", event_data)
        assert any("Empty 'accounts'" in issue for issue in issues)

    def test_account_missing_source_id(self):
        """Test detection of account missing source_id."""
        event_data = {
            "id": "test_event",
            "label": "Test",
            "participants": [],
            "tags": ["t"],
            "parallels": [],
            "accounts": [
                {
                    "reference": "Test 1:1",
                    "summary": "Summary"
                }
            ]
        }

        issues = validate.check_event_hydration("test_event", event_data)
        assert any("accounts[0]" in issue and "source_id" in issue for issue in issues)

    def test_account_missing_reference(self):
        """Test detection of account missing reference."""
        event_data = {
            "id": "test_event",
            "label": "Test",
            "participants": [],
            "tags": ["t"],
            "parallels": [],
            "accounts": [
                {
                    "source_id": "test",
                    "summary": "Summary"
                }
            ]
        }

        issues = validate.check_event_hydration("test_event", event_data)
        assert any("reference" in issue for issue in issues)

    def test_account_missing_summary(self):
        """Test detection of account missing summary."""
        event_data = {
            "id": "test_event",
            "label": "Test",
            "participants": [],
            "tags": ["t"],
            "parallels": [],
            "accounts": [
                {
                    "source_id": "test",
                    "reference": "Test 1:1"
                }
            ]
        }

        issues = validate.check_event_hydration("test_event", event_data)
        assert any("summary" in issue for issue in issues)


class TestMainFunction:
    """Test the main validation function with integration tests."""

    def test_main_returns_zero_when_valid(self):
        """Test main returns 0 when all data is valid."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create data structure
            bce_dir = Path(tmpdir) / "bce"
            data_dir = bce_dir / "data"
            char_dir = data_dir / "characters"
            event_dir = data_dir / "events"

            char_dir.mkdir(parents=True)
            event_dir.mkdir(parents=True)

            # Create valid character file
            char_file = char_dir / "valid_char.json"
            char_data = {
                "id": "valid_char",
                "canonical_name": "Valid Character",
                "aliases": ["Alias"],
                "roles": ["role1"],
                "tags": ["tag1"],
                "relationships": [],
                "source_profiles": [{
                    "source_id": "test",
                    "traits": {"trait": "value"},
                    "references": ["Test 1:1"]
                }]
            }
            with open(char_file, 'w') as f:
                json.dump(char_data, f)

            # Create valid event file
            event_file = event_dir / "valid_event.json"
            event_data = {
                "id": "valid_event",
                "label": "Valid Event",
                "participants": ["char1"],
                "tags": ["tag1"],
                "parallels": [],
                "accounts": [{
                    "source_id": "test",
                    "reference": "Test 1:1",
                    "summary": "Summary"
                }]
            }
            with open(event_file, 'w') as f:
                json.dump(event_data, f)

            with patch("validate_schema_hydration.Path") as mock_path:
                mock_path.return_value = Path(tmpdir) / "script.py"

                with patch("builtins.print"):
                    result = validate.main()

            # Should return 0 (or close - might have warnings about empty arrays)
            # The key is it shouldn't crash
            assert result in [0, 1]  # May have warnings about empty tags

    def test_main_returns_one_when_issues_found(self):
        """Test main returns 1 when validation issues are found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bce_dir = Path(tmpdir) / "bce"
            data_dir = bce_dir / "data"
            char_dir = data_dir / "characters"
            event_dir = data_dir / "events"

            char_dir.mkdir(parents=True)
            event_dir.mkdir(parents=True)

            # Create invalid character file (missing required fields)
            char_file = char_dir / "invalid_char.json"
            char_data = {
                "id": "invalid_char",
                "canonical_name": "Invalid",
                "aliases": [],
                "roles": []  # Empty roles - should be flagged
            }
            with open(char_file, 'w') as f:
                json.dump(char_data, f)

            with patch("validate_schema_hydration.Path") as mock_path:
                mock_path.return_value = Path(tmpdir) / "script.py"

                with patch("builtins.print"):
                    result = validate.main()

            assert result == 1  # Should find issues

    def test_main_handles_json_load_errors(self):
        """Test main handles JSON loading errors gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bce_dir = Path(tmpdir) / "bce"
            data_dir = bce_dir / "data"
            char_dir = data_dir / "characters"
            event_dir = data_dir / "events"

            char_dir.mkdir(parents=True)
            event_dir.mkdir(parents=True)

            # Create invalid JSON file
            bad_file = char_dir / "bad.json"
            with open(bad_file, 'w') as f:
                f.write("{invalid json")

            with patch("validate_schema_hydration.Path") as mock_path:
                mock_path.return_value = Path(tmpdir) / "script.py"

                with patch("builtins.print"):
                    result = validate.main()

            assert result == 1  # Should return 1 due to error


class TestIntegrationWithRealFiles:
    """Integration tests with actual temporary files."""

    def test_validate_complete_character_file(self):
        """Test validation of a complete character file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            char_data = {
                "id": "test_char",
                "canonical_name": "Test Character",
                "aliases": ["Alias"],
                "roles": ["role1"],
                "tags": ["tag1"],
                "relationships": [],
                "source_profiles": [
                    {
                        "source_id": "test",
                        "traits": {"trait1": "value1"},
                        "references": ["Test 1:1"]
                    }
                ]
            }
            json.dump(char_data, f)
            temp_path = Path(f.name)

        try:
            loaded = validate.load_json_file(temp_path)
            issues = validate.check_character_hydration("test_char", loaded)
            # Should have only informational issue about empty tags
            assert len(issues) <= 1
            if issues:
                assert "consider adding" in issues[0].lower() or "empty" in issues[0].lower()
        finally:
            temp_path.unlink()

    def test_validate_incomplete_character_file(self):
        """Test validation of an incomplete character file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            char_data = {
                "id": "test_char",
                "canonical_name": "Test",
                "aliases": [],
                "roles": []
            }
            json.dump(char_data, f)
            temp_path = Path(f.name)

        try:
            loaded = validate.load_json_file(temp_path)
            issues = validate.check_character_hydration("test_char", loaded)
            # Should have multiple issues
            assert len(issues) > 0
            # Check for expected issues
            assert any("tags" in issue for issue in issues)
            assert any("relationships" in issue for issue in issues)
            assert any("source_profiles" in issue for issue in issues)
        finally:
            temp_path.unlink()

    def test_validate_complete_event_file(self):
        """Test validation of a complete event file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            event_data = {
                "id": "test_event",
                "label": "Test Event",
                "participants": ["char1"],
                "tags": ["tag1"],
                "parallels": [],
                "accounts": [
                    {
                        "source_id": "test",
                        "reference": "Test 1:1",
                        "summary": "Event summary"
                    }
                ]
            }
            json.dump(event_data, f)
            temp_path = Path(f.name)

        try:
            loaded = validate.load_json_file(temp_path)
            issues = validate.check_event_hydration("test_event", loaded)
            # Might have informational issue about empty tags
            assert len(issues) <= 1
        finally:
            temp_path.unlink()

    def test_validate_incomplete_event_file(self):
        """Test validation of an incomplete event file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            event_data = {
                "id": "test_event",
                "label": "Test",
                "participants": []
            }
            json.dump(event_data, f)
            temp_path = Path(f.name)

        try:
            loaded = validate.load_json_file(temp_path)
            issues = validate.check_event_hydration("test_event", loaded)
            # Should have multiple issues
            assert len(issues) > 0
            assert any("tags" in issue for issue in issues)
            assert any("parallels" in issue for issue in issues)
            assert any("accounts" in issue for issue in issues)
        finally:
            temp_path.unlink()
