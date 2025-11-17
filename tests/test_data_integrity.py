"""Tests for data integrity and cross-reference validation.

These tests verify that the JSON data files maintain referential integrity
and follow expected conventions.
"""

from __future__ import annotations

import pytest
from bce import queries, storage


class TestCharacterEventCrossReferences:
    """Test cross-references between characters and events."""

    def test_all_event_participants_reference_valid_characters(self):
        """All participants in events should reference existing characters."""
        character_ids = set(queries.list_character_ids())
        events = queries.list_all_characters()  # Will load all events via iteration

        for event_id in queries.list_event_ids():
            event = queries.get_event(event_id)
            for participant_id in event.participants:
                assert participant_id in character_ids, (
                    f"Event '{event_id}' references non-existent "
                    f"character '{participant_id}'"
                )

    def test_character_ids_match_filenames(self):
        """Character IDs should match their JSON filenames."""
        for char_id in queries.list_character_ids():
            char = queries.get_character(char_id)
            assert char.id == char_id, (
                f"Character file '{char_id}.json' contains object with "
                f"id='{char.id}'"
            )

    def test_event_ids_match_filenames(self):
        """Event IDs should match their JSON filenames."""
        for event_id in queries.list_event_ids():
            event = queries.get_event(event_id)
            assert event.id == event_id, (
                f"Event file '{event_id}.json' contains object with "
                f"id='{event.id}'"
            )


class TestCharacterDataQuality:
    """Test quality and consistency of character data."""

    def test_all_characters_have_canonical_name(self):
        """Every character should have a non-empty canonical name."""
        for char_id in queries.list_character_ids():
            char = queries.get_character(char_id)
            assert char.canonical_name, (
                f"Character '{char_id}' has empty canonical_name"
            )
            assert char.canonical_name.strip(), (
                f"Character '{char_id}' has whitespace-only canonical_name"
            )

    def test_all_characters_have_valid_id(self):
        """Every character should have a valid ID."""
        for char_id in queries.list_character_ids():
            char = queries.get_character(char_id)
            assert char.id, f"Character '{char_id}' has empty id field"
            assert isinstance(char.id, str), (
                f"Character '{char_id}' has non-string id"
            )

    def test_characters_have_source_profiles_list(self):
        """Characters should have source_profiles as a list."""
        for char_id in queries.list_character_ids():
            char = queries.get_character(char_id)
            assert isinstance(char.source_profiles, list), (
                f"Character '{char_id}' source_profiles is not a list"
            )
            # Note: Not all characters have source profiles yet (data in progress)

    def test_source_profiles_have_valid_structure(self):
        """Source profiles should have required fields."""
        for char_id in queries.list_character_ids():
            char = queries.get_character(char_id)
            for profile in char.source_profiles:
                assert profile.source_id, (
                    f"Character '{char_id}' has profile with empty source_id"
                )
                assert isinstance(profile.traits, dict), (
                    f"Character '{char_id}' profile '{profile.source_id}' "
                    f"has non-dict traits"
                )
                assert isinstance(profile.references, list), (
                    f"Character '{char_id}' profile '{profile.source_id}' "
                    f"has non-list references"
                )

    def test_no_duplicate_source_ids_per_character(self):
        """Each character should not have duplicate source IDs."""
        for char_id in queries.list_character_ids():
            char = queries.get_character(char_id)
            source_ids = [p.source_id for p in char.source_profiles]
            unique_source_ids = set(source_ids)

            assert len(source_ids) == len(unique_source_ids), (
                f"Character '{char_id}' has duplicate source_ids: "
                f"{source_ids}"
            )

    def test_aliases_are_strings(self):
        """Character aliases should all be strings."""
        for char_id in queries.list_character_ids():
            char = queries.get_character(char_id)
            assert isinstance(char.aliases, list), (
                f"Character '{char_id}' aliases is not a list"
            )
            for alias in char.aliases:
                assert isinstance(alias, str), (
                    f"Character '{char_id}' has non-string alias: {alias}"
                )

    def test_roles_are_strings(self):
        """Character roles should all be strings."""
        for char_id in queries.list_character_ids():
            char = queries.get_character(char_id)
            assert isinstance(char.roles, list), (
                f"Character '{char_id}' roles is not a list"
            )
            for role in char.roles:
                assert isinstance(role, str), (
                    f"Character '{char_id}' has non-string role: {role}"
                )


class TestEventDataQuality:
    """Test quality and consistency of event data."""

    def test_all_events_have_label(self):
        """Every event should have a non-empty label."""
        for event_id in queries.list_event_ids():
            event = queries.get_event(event_id)
            assert event.label, f"Event '{event_id}' has empty label"
            assert event.label.strip(), (
                f"Event '{event_id}' has whitespace-only label"
            )

    def test_all_events_have_valid_id(self):
        """Every event should have a valid ID."""
        for event_id in queries.list_event_ids():
            event = queries.get_event(event_id)
            assert event.id, f"Event '{event_id}' has empty id field"
            assert isinstance(event.id, str), (
                f"Event '{event_id}' has non-string id"
            )

    def test_events_have_participants(self):
        """Events should have at least one participant."""
        for event_id in queries.list_event_ids():
            event = queries.get_event(event_id)
            assert isinstance(event.participants, list), (
                f"Event '{event_id}' participants is not a list"
            )
            assert len(event.participants) > 0, (
                f"Event '{event_id}' has no participants"
            )

    def test_events_have_accounts(self):
        """Events should have at least one account."""
        for event_id in queries.list_event_ids():
            event = queries.get_event(event_id)
            assert isinstance(event.accounts, list), (
                f"Event '{event_id}' accounts is not a list"
            )
            assert len(event.accounts) > 0, (
                f"Event '{event_id}' has no accounts"
            )

    def test_event_accounts_have_valid_structure(self):
        """Event accounts should have required fields."""
        for event_id in queries.list_event_ids():
            event = queries.get_event(event_id)
            for account in event.accounts:
                assert account.source_id, (
                    f"Event '{event_id}' has account with empty source_id"
                )
                assert account.reference, (
                    f"Event '{event_id}' account '{account.source_id}' "
                    f"has empty reference"
                )
                assert account.summary, (
                    f"Event '{event_id}' account '{account.source_id}' "
                    f"has empty summary"
                )
                # notes is optional, so we don't assert it

    def test_participants_are_strings(self):
        """Event participants should all be strings."""
        for event_id in queries.list_event_ids():
            event = queries.get_event(event_id)
            for participant in event.participants:
                assert isinstance(participant, str), (
                    f"Event '{event_id}' has non-string participant: "
                    f"{participant}"
                )

    def test_no_duplicate_participants_per_event(self):
        """Events should not list the same participant multiple times."""
        for event_id in queries.list_event_ids():
            event = queries.get_event(event_id)
            unique_participants = set(event.participants)

            assert len(event.participants) == len(unique_participants), (
                f"Event '{event_id}' has duplicate participants: "
                f"{event.participants}"
            )


class TestSourceConsistency:
    """Test consistency of source IDs across characters and events."""

    def test_common_sources_used_across_data(self):
        """Verify common biblical sources appear in the data."""
        all_character_sources = set()
        all_event_sources = set()

        for char_id in queries.list_character_ids():
            char = queries.get_character(char_id)
            for profile in char.source_profiles:
                all_character_sources.add(profile.source_id)

        for event_id in queries.list_event_ids():
            event = queries.get_event(event_id)
            for account in event.accounts:
                all_event_sources.add(account.source_id)

        # Should have at least some overlap between character and event sources
        common_sources = all_character_sources.intersection(all_event_sources)
        assert len(common_sources) > 0, (
            "No common sources found between characters and events"
        )

        # Verify known biblical sources are present
        known_sources = {"mark", "matthew", "luke", "john"}
        found_sources = all_character_sources.union(all_event_sources)

        # At least some known sources should be present
        assert len(known_sources.intersection(found_sources)) > 0, (
            "No known biblical sources (mark, matthew, luke, john) found in data"
        )


class TestDataCompleteness:
    """Test that data files contain expected minimum content."""

    def test_minimum_characters_present(self):
        """Should have at least the core NT characters."""
        character_ids = queries.list_character_ids()

        # Core characters that should always be present
        core_characters = {"jesus", "paul", "peter"}

        for char_id in core_characters:
            assert char_id in character_ids, (
                f"Core character '{char_id}' is missing from data"
            )

    def test_minimum_events_present(self):
        """Should have at least some core NT events."""
        event_ids = queries.list_event_ids()

        # Core events that should always be present
        core_events = {"crucifixion"}

        for event_id in core_events:
            assert event_id in event_ids, (
                f"Core event '{event_id}' is missing from data"
            )

    def test_jesus_has_multiple_sources(self):
        """Jesus should have data from multiple gospel sources."""
        jesus = queries.get_character("jesus")
        source_ids = {p.source_id for p in jesus.source_profiles}

        # Jesus should appear in multiple gospels
        assert len(source_ids) >= 2, (
            f"Jesus only has {len(source_ids)} source(s), expected at least 2"
        )

    def test_crucifixion_has_multiple_accounts(self):
        """Crucifixion should have accounts from multiple sources."""
        crucifixion = queries.get_event("crucifixion")
        source_ids = {a.source_id for a in crucifixion.accounts}

        # Crucifixion is in all four gospels
        assert len(source_ids) >= 2, (
            f"Crucifixion only has {len(source_ids)} account(s), "
            f"expected at least 2"
        )
