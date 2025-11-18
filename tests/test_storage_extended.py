"""Extended storage tests to improve coverage of bce/storage.py."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bce import storage
from bce.exceptions import StorageError
from bce.models import Character, Event, EventAccount, SourceProfile
from bce.storage import StorageManager
from bce.config import BceConfig


class TestStorageManagerProperties:
    """Test StorageManager property methods."""

    def test_storage_manager_data_root_property(self, tmp_path: Path):
        """StorageManager.data_root should return the configured data root."""
        config = BceConfig(data_root=tmp_path)
        manager = StorageManager(config)

        assert manager.data_root == tmp_path

    def test_storage_manager_char_dir_property(self, tmp_path: Path):
        """StorageManager.char_dir should return characters directory."""
        config = BceConfig(data_root=tmp_path)
        manager = StorageManager(config)

        expected = tmp_path / "characters"
        assert manager.char_dir == expected

    def test_storage_manager_event_dir_property(self, tmp_path: Path):
        """StorageManager.event_dir should return events directory."""
        config = BceConfig(data_root=tmp_path)
        manager = StorageManager(config)

        expected = tmp_path / "events"
        assert manager.event_dir == expected


class TestStorageErrorHandlingExtended:
    """Additional error handling tests for storage module."""

    # Note: IOError and ValueError error paths in storage are difficult to trigger
    # with the current implementation because:
    # 1. Path.open() handles most I/O errors internally
    # 2. dataclasses.asdict() is very permissive and rarely raises errors
    # 3. Character and Event constructors accept most values
    # These error paths exist for defensive programming and are tested implicitly
    # by the comprehensive error handling tests in test_storage.py

    pass


class TestRelationshipValidation:
    """Test relationship field validation in storage."""

    def test_load_character_with_legacy_nested_relationships_raises_error(self, tmp_path: Path):
        """Loading character with nested dict relationships should raise StorageError."""
        custom_root = tmp_path / "data"
        char_dir = custom_root / "characters"
        char_dir.mkdir(parents=True)

        # Create character with legacy nested dict format (Format A)
        char_file = char_dir / "legacy.json"
        char_data = {
            "id": "legacy",
            "canonical_name": "Legacy Character",
            "aliases": [],
            "roles": [],
            "source_profiles": [],
            "relationships": {
                "peter": [{"type": "teacher", "sources": ["mark"]}]
            }
        }
        char_file.write_text(json.dumps(char_data))

        config = BceConfig(data_root=custom_root)
        manager = StorageManager(config)

        with pytest.raises(StorageError, match="deprecated nested dict format"):
            manager.load_character("legacy")

    def test_load_character_with_non_dict_relationship_raises_error(self, tmp_path: Path):
        """Relationship that is not a dict should raise StorageError."""
        custom_root = tmp_path / "data"
        char_dir = custom_root / "characters"
        char_dir.mkdir(parents=True)

        # Create character with non-dict relationship
        char_file = char_dir / "bad_rel.json"
        char_data = {
            "id": "bad_rel",
            "canonical_name": "Bad Relationship",
            "aliases": [],
            "roles": [],
            "source_profiles": [],
            "relationships": ["not_a_dict"]
        }
        char_file.write_text(json.dumps(char_data))

        config = BceConfig(data_root=custom_root)
        manager = StorageManager(config)

        with pytest.raises(StorageError, match="is not a dict"):
            manager.load_character("bad_rel")

    def test_load_character_with_missing_character_id_in_relationship(self, tmp_path: Path):
        """Relationship missing character_id should raise StorageError."""
        custom_root = tmp_path / "data"
        char_dir = custom_root / "characters"
        char_dir.mkdir(parents=True)

        # Create character with relationship missing character_id
        char_file = char_dir / "missing_id.json"
        char_data = {
            "id": "missing_id",
            "canonical_name": "Missing ID",
            "aliases": [],
            "roles": [],
            "source_profiles": [],
            "relationships": [
                {"type": "teacher", "sources": ["mark"]}  # Missing character_id
            ]
        }
        char_file.write_text(json.dumps(char_data))

        config = BceConfig(data_root=custom_root)
        manager = StorageManager(config)

        with pytest.raises(StorageError, match="missing required 'character_id' field"):
            manager.load_character("missing_id")

    def test_load_character_with_non_list_relationships_raises_error(self, tmp_path: Path):
        """Relationships that is not a list or dict should raise StorageError."""
        custom_root = tmp_path / "data"
        char_dir = custom_root / "characters"
        char_dir.mkdir(parents=True)

        # Create character with string relationships
        char_file = char_dir / "wrong_type.json"
        char_data = {
            "id": "wrong_type",
            "canonical_name": "Wrong Type",
            "aliases": [],
            "roles": [],
            "source_profiles": [],
            "relationships": "not a list"
        }
        char_file.write_text(json.dumps(char_data))

        config = BceConfig(data_root=custom_root)
        manager = StorageManager(config)

        with pytest.raises(StorageError, match="must be a list"):
            manager.load_character("wrong_type")

    def test_load_character_with_null_relationships_succeeds(self, tmp_path: Path):
        """Character with null relationships should load as empty list."""
        custom_root = tmp_path / "data"
        char_dir = custom_root / "characters"
        char_dir.mkdir(parents=True)

        # Create character with null relationships
        char_file = char_dir / "null_rels.json"
        char_data = {
            "id": "null_rels",
            "canonical_name": "Null Relationships",
            "aliases": [],
            "roles": [],
            "source_profiles": [],
            "relationships": None
        }
        char_file.write_text(json.dumps(char_data))

        config = BceConfig(data_root=custom_root)
        manager = StorageManager(config)

        char = manager.load_character("null_rels")
        assert char.relationships == []

    def test_load_character_with_valid_flat_relationships_succeeds(self, tmp_path: Path):
        """Character with valid flat list relationships should load successfully."""
        custom_root = tmp_path / "data"
        char_dir = custom_root / "characters"
        char_dir.mkdir(parents=True)

        # Create character with valid flat list format
        char_file = char_dir / "valid.json"
        char_data = {
            "id": "valid",
            "canonical_name": "Valid Character",
            "aliases": [],
            "roles": [],
            "source_profiles": [],
            "relationships": [
                {
                    "character_id": "peter",
                    "type": "teacher",
                    "sources": ["mark"],
                    "references": ["Mark 1:16-20"]
                }
            ]
        }
        char_file.write_text(json.dumps(char_data))

        config = BceConfig(data_root=custom_root)
        manager = StorageManager(config)

        char = manager.load_character("valid")
        assert len(char.relationships) == 1
        assert char.relationships[0]["character_id"] == "peter"
        assert char.relationships[0]["type"] == "teacher"
