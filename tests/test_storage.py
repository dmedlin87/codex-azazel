from __future__ import annotations

import json
from pathlib import Path

import pytest

from bce import queries, storage
from bce.models import Character, Event, EventAccount, SourceProfile


def test_configure_data_root(tmp_path: Path) -> None:
    custom_root = tmp_path / "custom_data"
    storage.configure_data_root(custom_root)
    try:
        assert storage.list_character_ids() == []
        character = Character(id="tmp", canonical_name="Temporary Character")
        storage.save_character(character)
        assert storage.list_character_ids() == ["tmp"]
    finally:
        storage.reset_data_root()

    ids = storage.list_character_ids()
    assert "jesus" in ids


def test_save_character_invalidates_query_cache(tmp_path: Path) -> None:
    custom_root = tmp_path / "custom_data_cache_char"
    storage.configure_data_root(custom_root)
    try:
        character = Character(id="cache_char", canonical_name="Original")
        storage.save_character(character)

        loaded = queries.get_character("cache_char")
        assert loaded.canonical_name == "Original"

        updated = Character(id="cache_char", canonical_name="Updated")
        storage.save_character(updated)

        refreshed = queries.get_character("cache_char")
        assert refreshed.canonical_name == "Updated"
    finally:
        storage.reset_data_root()


def test_save_event_invalidates_query_cache(tmp_path: Path) -> None:
    custom_root = tmp_path / "custom_data_cache_event"
    storage.configure_data_root(custom_root)
    try:
        event = Event(id="cache_event", label="Initial")
        storage.save_event(event)

        loaded = queries.get_event("cache_event")
        assert loaded.label == "Initial"

        updated = Event(id="cache_event", label="Changed")
        storage.save_event(updated)

        refreshed = queries.get_event("cache_event")
        assert refreshed.label == "Changed"
    finally:
        storage.reset_data_root()


# Error Handling Tests


class TestStorageErrorHandling:
    """Test error handling in storage module."""

    def test_load_character_nonexistent_file(self, tmp_path):
        """Loading nonexistent character should raise FileNotFoundError."""
        storage.configure_data_root(tmp_path)
        try:
            with pytest.raises(FileNotFoundError):
                storage.load_character("nonexistent")
        finally:
            storage.reset_data_root()

    def test_load_event_nonexistent_file(self, tmp_path):
        """Loading nonexistent event should raise FileNotFoundError."""
        storage.configure_data_root(tmp_path)
        try:
            with pytest.raises(FileNotFoundError):
                storage.load_event("nonexistent")
        finally:
            storage.reset_data_root()

    def test_load_character_malformed_json(self, tmp_path):
        """Loading malformed JSON should raise JSONDecodeError."""
        custom_root = tmp_path / "data"
        char_dir = custom_root / "characters"
        char_dir.mkdir(parents=True)

        # Write invalid JSON
        bad_file = char_dir / "bad.json"
        bad_file.write_text("{ this is not valid json }")

        storage.configure_data_root(custom_root)
        try:
            with pytest.raises(json.JSONDecodeError):
                storage.load_character("bad")
        finally:
            storage.reset_data_root()

    def test_load_event_malformed_json(self, tmp_path):
        """Loading malformed JSON should raise JSONDecodeError."""
        custom_root = tmp_path / "data"
        event_dir = custom_root / "events"
        event_dir.mkdir(parents=True)

        # Write invalid JSON
        bad_file = event_dir / "bad.json"
        bad_file.write_text("not json at all")

        storage.configure_data_root(custom_root)
        try:
            with pytest.raises(json.JSONDecodeError):
                storage.load_event("bad")
        finally:
            storage.reset_data_root()

    def test_load_character_missing_required_fields(self, tmp_path):
        """Loading character with missing required fields should raise ValueError."""
        custom_root = tmp_path / "data"
        char_dir = custom_root / "characters"
        char_dir.mkdir(parents=True)

        # Write JSON missing canonical_name
        incomplete_file = char_dir / "incomplete.json"
        incomplete_file.write_text('{"id": "incomplete"}')

        storage.configure_data_root(custom_root)
        try:
            with pytest.raises(ValueError):
                storage.load_character("incomplete")
        finally:
            storage.reset_data_root()

    def test_load_event_missing_required_fields(self, tmp_path):
        """Loading event with missing required fields should raise ValueError."""
        custom_root = tmp_path / "data"
        event_dir = custom_root / "events"
        event_dir.mkdir(parents=True)

        # Write JSON missing label
        incomplete_file = event_dir / "incomplete.json"
        incomplete_file.write_text('{"id": "incomplete"}')

        storage.configure_data_root(custom_root)
        try:
            with pytest.raises(ValueError):
                storage.load_event("incomplete")
        finally:
            storage.reset_data_root()

    def test_load_character_with_empty_source_profiles(self, tmp_path):
        """Character with empty source_profiles list should load successfully."""
        custom_root = tmp_path / "data"
        char_dir = custom_root / "characters"
        char_dir.mkdir(parents=True)

        # Character with no source profiles
        char_file = char_dir / "minimal.json"
        char_file.write_text(json.dumps({
            "id": "minimal",
            "canonical_name": "Minimal Character",
            "aliases": [],
            "roles": [],
            "source_profiles": []
        }))

        storage.configure_data_root(custom_root)
        try:
            char = storage.load_character("minimal")
            assert char.id == "minimal"
            assert char.source_profiles == []
        finally:
            storage.reset_data_root()

    def test_save_character_creates_directories(self, tmp_path):
        """Saving should create character directory if it doesn't exist."""
        custom_root = tmp_path / "new_data"
        storage.configure_data_root(custom_root)

        try:
            char = Character(id="test", canonical_name="Test")
            storage.save_character(char)

            # Directory should be created
            assert (custom_root / "characters").exists()
            assert (custom_root / "characters" / "test.json").exists()
        finally:
            storage.reset_data_root()

    def test_save_event_creates_directories(self, tmp_path):
        """Saving should create event directory if it doesn't exist."""
        custom_root = tmp_path / "new_data"
        storage.configure_data_root(custom_root)

        try:
            event = Event(id="test", label="Test")
            storage.save_event(event)

            # Directory should be created
            assert (custom_root / "events").exists()
            assert (custom_root / "events" / "test.json").exists()
        finally:
            storage.reset_data_root()


# Iterator Tests


class TestIterators:
    """Test iterator functions."""

    def test_iter_characters_yields_all(self):
        """iter_characters should yield same count as list_character_ids."""
        char_ids = storage.list_character_ids()
        chars_list = list(storage.iter_characters())

        assert len(chars_list) == len(char_ids)

    def test_iter_events_yields_all(self):
        """iter_events should yield same count as list_event_ids."""
        event_ids = storage.list_event_ids()
        events_list = list(storage.iter_events())

        assert len(events_list) == len(event_ids)

    def test_iter_characters_yields_character_objects(self):
        """iter_characters should yield Character objects."""
        for char in storage.iter_characters():
            assert isinstance(char, Character)
            assert char.id
            assert char.canonical_name
            break  # Just test first one

    def test_iter_events_yields_event_objects(self):
        """iter_events should yield Event objects."""
        for event in storage.iter_events():
            assert isinstance(event, Event)
            assert event.id
            assert event.label
            break  # Just test first one

    def test_iter_characters_with_empty_directory(self, tmp_path):
        """iter_characters with empty directory should yield nothing."""
        custom_root = tmp_path / "empty_data"
        storage.configure_data_root(custom_root)

        try:
            chars = list(storage.iter_characters())
            assert chars == []
        finally:
            storage.reset_data_root()

    def test_iter_events_with_empty_directory(self, tmp_path):
        """iter_events with empty directory should yield nothing."""
        custom_root = tmp_path / "empty_data"
        storage.configure_data_root(custom_root)

        try:
            events = list(storage.iter_events())
            assert events == []
        finally:
            storage.reset_data_root()

    def test_iter_characters_yields_correct_ids(self):
        """iter_characters should yield characters with correct IDs."""
        expected_ids = set(storage.list_character_ids())
        actual_ids = {char.id for char in storage.iter_characters()}

        assert actual_ids == expected_ids

    def test_iter_events_yields_correct_ids(self):
        """iter_events should yield events with correct IDs."""
        expected_ids = set(storage.list_event_ids())
        actual_ids = {event.id for event in storage.iter_events()}

        assert actual_ids == expected_ids

    def test_iter_characters_is_lazy(self, tmp_path):
        """iter_characters should be a generator (lazy)."""
        result = storage.iter_characters()

        # Should be a generator, not a list
        assert hasattr(result, "__next__")
        assert hasattr(result, "__iter__")

    def test_iter_events_is_lazy(self, tmp_path):
        """iter_events should be a generator (lazy)."""
        result = storage.iter_events()

        # Should be a generator, not a list
        assert hasattr(result, "__next__")
        assert hasattr(result, "__iter__")


# Additional Storage Tests


class TestListFunctions:
    """Test list_character_ids and list_event_ids functions."""

    def test_list_character_ids_returns_sorted_list(self):
        """list_character_ids should return sorted list."""
        ids = storage.list_character_ids()

        assert ids == sorted(ids)

    def test_list_event_ids_returns_sorted_list(self):
        """list_event_ids should return sorted list."""
        ids = storage.list_event_ids()

        assert ids == sorted(ids)

    def test_list_character_ids_no_duplicates(self):
        """list_character_ids should have no duplicates."""
        ids = storage.list_character_ids()

        assert len(ids) == len(set(ids))

    def test_list_event_ids_no_duplicates(self):
        """list_event_ids should have no duplicates."""
        ids = storage.list_event_ids()

        assert len(ids) == len(set(ids))

    def test_list_character_ids_nonexistent_directory(self, tmp_path):
        """list_character_ids with nonexistent dir should return empty list."""
        custom_root = tmp_path / "nonexistent"
        storage.configure_data_root(custom_root)

        try:
            ids = storage.list_character_ids()
            assert ids == []
        finally:
            storage.reset_data_root()

    def test_list_event_ids_nonexistent_directory(self, tmp_path):
        """list_event_ids with nonexistent dir should return empty list."""
        custom_root = tmp_path / "nonexistent"
        storage.configure_data_root(custom_root)

        try:
            ids = storage.list_event_ids()
            assert ids == []
        finally:
            storage.reset_data_root()


class TestSaveAndLoad:
    """Test save and load round-trips."""

    def test_save_and_load_character_preserves_data(self, tmp_path):
        """Character saved and loaded should be identical."""
        custom_root = tmp_path / "data"
        storage.configure_data_root(custom_root)

        try:
            original = Character(
                id="test_char",
                canonical_name="Test Character",
                aliases=["Testy", "TC"],
                roles=["tester", "validator"],
                source_profiles=[
                    SourceProfile(
                        source_id="test_source",
                        traits={"key": "value"},
                        references=["Test 1:1"]
                    )
                ]
            )

            storage.save_character(original)
            loaded = storage.load_character("test_char")

            assert loaded.id == original.id
            assert loaded.canonical_name == original.canonical_name
            assert loaded.aliases == original.aliases
            assert loaded.roles == original.roles
            assert len(loaded.source_profiles) == len(original.source_profiles)
            assert loaded.source_profiles[0].source_id == original.source_profiles[0].source_id
            assert loaded.source_profiles[0].traits == original.source_profiles[0].traits
            assert loaded.source_profiles[0].references == original.source_profiles[0].references

        finally:
            storage.reset_data_root()

    def test_save_and_load_event_preserves_data(self, tmp_path):
        """Event saved and loaded should be identical."""
        custom_root = tmp_path / "data"
        storage.configure_data_root(custom_root)

        try:
            original = Event(
                id="test_event",
                label="Test Event",
                participants=["char1", "char2"],
                accounts=[
                    EventAccount(
                        source_id="source1",
                        reference="Ref 1:1",
                        summary="Summary 1",
                        notes="Note 1"
                    ),
                    EventAccount(
                        source_id="source2",
                        reference="Ref 2:2",
                        summary="Summary 2"
                    )
                ]
            )

            storage.save_event(original)
            loaded = storage.load_event("test_event")

            assert loaded.id == original.id
            assert loaded.label == original.label
            assert loaded.participants == original.participants
            assert len(loaded.accounts) == len(original.accounts)
            assert loaded.accounts[0].source_id == original.accounts[0].source_id
            assert loaded.accounts[0].notes == original.accounts[0].notes
            assert loaded.accounts[1].notes is None  # Default value preserved

        finally:
            storage.reset_data_root()

    def test_save_character_overwrites_existing(self, tmp_path):
        """Saving character with same ID should overwrite."""
        custom_root = tmp_path / "data"
        storage.configure_data_root(custom_root)

        try:
            char1 = Character(id="test", canonical_name="First")
            storage.save_character(char1)

            char2 = Character(id="test", canonical_name="Second")
            storage.save_character(char2)

            loaded = storage.load_character("test")
            assert loaded.canonical_name == "Second"

        finally:
            storage.reset_data_root()

    def test_save_event_overwrites_existing(self, tmp_path):
        """Saving event with same ID should overwrite."""
        custom_root = tmp_path / "data"
        storage.configure_data_root(custom_root)

        try:
            event1 = Event(id="test", label="First")
            storage.save_event(event1)

            event2 = Event(id="test", label="Second")
            storage.save_event(event2)

            loaded = storage.load_event("test")
            assert loaded.label == "Second"

        finally:
            storage.reset_data_root()


class TestUnicodeHandling:
    """Test handling of Unicode and special characters."""

    def test_save_and_load_character_with_unicode(self, tmp_path):
        """Should handle Unicode in character fields."""
        custom_root = tmp_path / "data"
        storage.configure_data_root(custom_root)

        try:
            char = Character(
                id="unicode_test",
                canonical_name="Ἰησοῦς Χριστός",  # Greek
                aliases=["יֵשׁוּעַ", "耶稣"],  # Hebrew, Chinese
                roles=["Μεσσίας"]  # Greek
            )

            storage.save_character(char)
            loaded = storage.load_character("unicode_test")

            assert loaded.canonical_name == "Ἰησοῦς Χριστός"
            assert "יֵשׁוּעַ" in loaded.aliases
            assert "耶稣" in loaded.aliases

        finally:
            storage.reset_data_root()

    def test_save_and_load_event_with_unicode(self, tmp_path):
        """Should handle Unicode in event fields."""
        custom_root = tmp_path / "data"
        storage.configure_data_root(custom_root)

        try:
            event = Event(
                id="unicode_event",
                label="Σταύρωσις",  # Greek: Crucifixion
                participants=["test"]
            )

            storage.save_event(event)
            loaded = storage.load_event("unicode_event")

            assert loaded.label == "Σταύρωσις"

        finally:
            storage.reset_data_root()
