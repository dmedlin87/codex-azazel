"""Tests for bce.queries module.

These tests verify the high-level query API and caching behavior.
"""

from __future__ import annotations

import pytest
from bce import queries
from bce.models import Character, SourceProfile


class TestGetCharacter:
    """Test get_character function."""

    def test_get_character_returns_character_object(self):
        """get_character should return a Character object."""
        char = queries.get_character("jesus")

        assert isinstance(char, Character)
        assert char.id == "jesus"
        assert char.canonical_name == "Jesus of Nazareth"

    def test_get_character_nonexistent_raises_error(self):
        """get_character with invalid ID should raise an error."""
        with pytest.raises(FileNotFoundError):
            queries.get_character("nonexistent")

    def test_get_character_caches_result(self):
        """get_character should cache results."""
        # Clear cache first
        queries.clear_cache()

        # First call
        char1 = queries.get_character("paul")
        # Second call should return cached result (same object)
        char2 = queries.get_character("paul")

        assert char1 is char2  # Should be the exact same object due to caching


class TestGetEvent:
    """Test get_event function."""

    def test_get_event_returns_event_object(self):
        """get_event should return an Event object."""
        event = queries.get_event("crucifixion")

        assert event.id == "crucifixion"
        assert event.label == "Crucifixion of Jesus"

    def test_get_event_nonexistent_raises_error(self):
        """get_event with invalid ID should raise an error."""
        with pytest.raises(FileNotFoundError):
            queries.get_event("nonexistent")

    def test_get_event_caches_result(self):
        """get_event should cache results."""
        # Clear cache first
        queries.clear_cache()

        # First call
        event1 = queries.get_event("betrayal")
        # Second call should return cached result (same object)
        event2 = queries.get_event("betrayal")

        assert event1 is event2  # Should be the exact same object due to caching


class TestListCharacterIds:
    """Test list_character_ids function."""

    def test_list_character_ids_returns_list(self):
        """list_character_ids should return a list of strings."""
        ids = queries.list_character_ids()

        assert isinstance(ids, list)
        assert len(ids) > 0
        assert all(isinstance(id, str) for id in ids)

    def test_list_character_ids_contains_known_characters(self):
        """list_character_ids should contain known characters."""
        ids = queries.list_character_ids()

        assert "jesus" in ids
        assert "paul" in ids
        assert "peter" in ids

    def test_list_character_ids_is_sorted(self):
        """list_character_ids should return sorted IDs."""
        ids = queries.list_character_ids()

        assert ids == sorted(ids)


class TestListEventIds:
    """Test list_event_ids function."""

    def test_list_event_ids_returns_list(self):
        """list_event_ids should return a list of strings."""
        ids = queries.list_event_ids()

        assert isinstance(ids, list)
        assert len(ids) > 0
        assert all(isinstance(id, str) for id in ids)

    def test_list_event_ids_contains_known_events(self):
        """list_event_ids should contain known events."""
        ids = queries.list_event_ids()

        assert "crucifixion" in ids
        assert "betrayal" in ids

    def test_list_event_ids_is_sorted(self):
        """list_event_ids should return sorted IDs."""
        ids = queries.list_event_ids()

        assert ids == sorted(ids)


class TestListAllCharacters:
    """Test list_all_characters function."""

    def test_list_all_characters_returns_list(self):
        """list_all_characters should return a list of Character objects."""
        chars = queries.list_all_characters()

        assert isinstance(chars, list)
        assert len(chars) > 0
        assert all(isinstance(c, Character) for c in chars)

    def test_list_all_characters_returns_all_known_chars(self):
        """list_all_characters should return all characters."""
        chars = queries.list_all_characters()
        char_ids = {c.id for c in chars}

        known_ids = {"jesus", "paul", "peter", "judas", "pilate"}
        assert known_ids.issubset(char_ids)

    def test_list_all_characters_returns_complete_objects(self):
        """Each character should have complete data."""
        chars = queries.list_all_characters()

        for char in chars:
            assert char.id
            assert char.canonical_name
            assert isinstance(char.source_profiles, list)


class TestGetSourceProfile:
    """Test get_source_profile function."""

    def test_get_source_profile_existing_source(self):
        """get_source_profile should return profile for existing source."""
        jesus = queries.get_character("jesus")
        profile = queries.get_source_profile(jesus, "mark")

        assert profile is not None
        assert isinstance(profile, SourceProfile)
        assert profile.source_id == "mark"
        assert isinstance(profile.traits, dict)
        assert isinstance(profile.references, list)

    def test_get_source_profile_nonexistent_returns_none(self):
        """get_source_profile should return None for non-existent source."""
        jesus = queries.get_character("jesus")
        profile = queries.get_source_profile(jesus, "nonexistent_source")

        assert profile is None

    def test_get_source_profile_with_multiple_sources(self):
        """get_source_profile should distinguish between sources."""
        jesus = queries.get_character("jesus")

        mark_profile = queries.get_source_profile(jesus, "mark")
        matthew_profile = queries.get_source_profile(jesus, "matthew")

        assert mark_profile is not None
        assert matthew_profile is not None
        assert mark_profile.source_id != matthew_profile.source_id

    def test_get_source_profile_returns_first_match(self):
        """get_source_profile should return first matching profile."""
        paul = queries.get_character("paul")
        profile = queries.get_source_profile(paul, "paul_undisputed")

        assert profile is not None
        assert profile.source_id == "paul_undisputed"


class TestListEventsForCharacter:
    """Test list_events_for_character function."""

    def test_list_events_for_character_returns_list(self):
        """list_events_for_character should return a list of events."""
        events = queries.list_events_for_character("jesus")

        assert isinstance(events, list)
        assert len(events) > 0

    def test_list_events_for_character_filters_correctly(self):
        """list_events_for_character should only return events with that character."""
        events = queries.list_events_for_character("jesus")

        for event in events:
            assert "jesus" in event.participants

    def test_list_events_for_character_includes_known_events(self):
        """list_events_for_character should include known events."""
        events = queries.list_events_for_character("jesus")
        event_ids = {e.id for e in events}

        assert "crucifixion" in event_ids

    def test_list_events_for_character_no_events(self):
        """list_events_for_character should return empty list if no events."""
        # Paul has events, but test a character that might not
        events = queries.list_events_for_character("paul")

        # Even if empty, should return a list
        assert isinstance(events, list)

    def test_list_events_for_character_multiple_participants(self):
        """Events with multiple participants should be found."""
        # Betrayal involves both jesus and judas
        jesus_events = queries.list_events_for_character("jesus")
        judas_events = queries.list_events_for_character("judas")

        jesus_event_ids = {e.id for e in jesus_events}
        judas_event_ids = {e.id for e in judas_events}

        # Both should include betrayal
        assert "betrayal" in jesus_event_ids
        assert "betrayal" in judas_event_ids


class TestClearCache:
    """Test cache clearing functionality."""

    def test_clear_cache_invalidates_character_cache(self):
        """clear_cache should invalidate character cache."""
        # Load and cache
        char1 = queries.get_character("peter")

        # Clear cache
        queries.clear_cache()

        # Load again - should be different object
        char2 = queries.get_character("peter")

        # Content should be the same
        assert char1.id == char2.id
        # But objects should be different (new load)
        assert char1 is not char2

    def test_clear_cache_invalidates_event_cache(self):
        """clear_cache should invalidate event cache."""
        # Load and cache
        event1 = queries.get_event("crucifixion")

        # Clear cache
        queries.clear_cache()

        # Load again - should be different object
        event2 = queries.get_event("crucifixion")

        # Content should be the same
        assert event1.id == event2.id
        # But objects should be different (new load)
        assert event1 is not event2

    def test_clear_cache_can_be_called_multiple_times(self):
        """clear_cache should be safe to call multiple times."""
        queries.clear_cache()
        queries.clear_cache()
        queries.clear_cache()

        # Should still work after multiple clears
        char = queries.get_character("jesus")
        assert char.id == "jesus"
