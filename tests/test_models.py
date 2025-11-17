"""Tests for bce.models dataclasses.

Tests the core data models and their validation.
"""

from __future__ import annotations

import pytest

from bce.models import Character, Event, EventAccount, SourceProfile


class TestSourceProfile:
    """Test SourceProfile dataclass."""

    def test_minimal_construction(self):
        """SourceProfile can be created with just source_id."""
        profile = SourceProfile(source_id="mark")

        assert profile.source_id == "mark"
        assert profile.traits == {}
        assert profile.references == []

    def test_construction_with_all_fields(self):
        """SourceProfile can be created with all fields."""
        profile = SourceProfile(
            source_id="matthew",
            traits={"role": "teacher", "origin": "Galilee"},
            references=["Matt 1:1", "Matt 2:1"]
        )

        assert profile.source_id == "matthew"
        assert profile.traits == {"role": "teacher", "origin": "Galilee"}
        assert profile.references == ["Matt 1:1", "Matt 2:1"]

    def test_default_factory_creates_independent_instances(self):
        """Default factories should create independent instances."""
        profile1 = SourceProfile(source_id="mark")
        profile2 = SourceProfile(source_id="luke")

        # Modify profile1's traits
        profile1.traits["test"] = "value"

        # profile2 should not be affected
        assert "test" not in profile2.traits
        assert profile1.traits != profile2.traits

    def test_references_default_is_independent(self):
        """References lists should be independent between instances."""
        profile1 = SourceProfile(source_id="mark")
        profile2 = SourceProfile(source_id="luke")

        profile1.references.append("Mark 1:1")

        assert "Mark 1:1" not in profile2.references
        assert len(profile2.references) == 0

    def test_required_field_source_id(self):
        """source_id is required."""
        with pytest.raises(TypeError):
            SourceProfile()  # Missing source_id

    def test_has_slots(self):
        """SourceProfile should use __slots__ for efficiency."""
        profile = SourceProfile(source_id="test")

        # With slots, __dict__ should not exist
        assert not hasattr(profile, "__dict__")
        # But we should be able to access __slots__
        assert hasattr(profile, "__slots__")


class TestCharacter:
    """Test Character dataclass."""

    def test_minimal_construction(self):
        """Character requires id and canonical_name."""
        char = Character(id="test", canonical_name="Test Character")

        assert char.id == "test"
        assert char.canonical_name == "Test Character"
        assert char.aliases == []
        assert char.roles == []
        assert char.source_profiles == []

    def test_construction_with_all_fields(self):
        """Character can be created with all fields."""
        profile = SourceProfile(source_id="mark", traits={"role": "apostle"})
        char = Character(
            id="peter",
            canonical_name="Simon Peter",
            aliases=["Simon", "Cephas"],
            roles=["apostle", "disciple"],
            source_profiles=[profile]
        )

        assert char.id == "peter"
        assert char.canonical_name == "Simon Peter"
        assert char.aliases == ["Simon", "Cephas"]
        assert char.roles == ["apostle", "disciple"]
        assert len(char.source_profiles) == 1
        assert char.source_profiles[0].source_id == "mark"

    def test_required_fields(self):
        """id and canonical_name are required."""
        with pytest.raises(TypeError):
            Character()  # Missing required fields

        with pytest.raises(TypeError):
            Character(id="test")  # Missing canonical_name

        with pytest.raises(TypeError):
            Character(canonical_name="Test")  # Missing id

    def test_default_factory_creates_independent_instances(self):
        """Default factories should create independent instances."""
        char1 = Character(id="test1", canonical_name="Test 1")
        char2 = Character(id="test2", canonical_name="Test 2")

        char1.aliases.append("Alias1")
        char1.roles.append("Role1")

        # char2 should not be affected
        assert "Alias1" not in char2.aliases
        assert "Role1" not in char2.roles

    def test_source_profiles_independent(self):
        """Source profiles list should be independent."""
        char1 = Character(id="test1", canonical_name="Test 1")
        char2 = Character(id="test2", canonical_name="Test 2")

        profile = SourceProfile(source_id="mark")
        char1.source_profiles.append(profile)

        assert len(char2.source_profiles) == 0

    def test_has_slots(self):
        """Character should use __slots__ for efficiency."""
        char = Character(id="test", canonical_name="Test")

        assert not hasattr(char, "__dict__")
        assert hasattr(char, "__slots__")

    def test_multiple_source_profiles(self):
        """Character can have multiple source profiles."""
        mark_profile = SourceProfile(source_id="mark")
        matthew_profile = SourceProfile(source_id="matthew")

        char = Character(
            id="jesus",
            canonical_name="Jesus",
            source_profiles=[mark_profile, matthew_profile]
        )

        assert len(char.source_profiles) == 2
        assert char.source_profiles[0].source_id == "mark"
        assert char.source_profiles[1].source_id == "matthew"


class TestEventAccount:
    """Test EventAccount dataclass."""

    def test_construction_with_required_fields(self):
        """EventAccount requires source_id, reference, and summary."""
        account = EventAccount(
            source_id="mark",
            reference="Mark 15:1-15",
            summary="Pilate questions Jesus"
        )

        assert account.source_id == "mark"
        assert account.reference == "Mark 15:1-15"
        assert account.summary == "Pilate questions Jesus"
        assert account.notes is None

    def test_construction_with_notes(self):
        """EventAccount can include optional notes."""
        account = EventAccount(
            source_id="john",
            reference="John 18:28-40",
            summary="Trial before Pilate",
            notes="John emphasizes the theological dialogue"
        )

        assert account.notes == "John emphasizes the theological dialogue"

    def test_required_fields(self):
        """source_id, reference, and summary are required."""
        with pytest.raises(TypeError):
            EventAccount()  # Missing all fields

        with pytest.raises(TypeError):
            EventAccount(source_id="mark")  # Missing reference and summary

        with pytest.raises(TypeError):
            EventAccount(
                source_id="mark",
                reference="Mark 1:1"
            )  # Missing summary

    def test_notes_defaults_to_none(self):
        """notes field should default to None."""
        account = EventAccount(
            source_id="luke",
            reference="Luke 23:1-25",
            summary="Trial"
        )

        assert account.notes is None

    def test_has_slots(self):
        """EventAccount should use __slots__ for efficiency."""
        account = EventAccount(
            source_id="test",
            reference="Test 1:1",
            summary="Test"
        )

        assert not hasattr(account, "__dict__")
        assert hasattr(account, "__slots__")


class TestEvent:
    """Test Event dataclass."""

    def test_minimal_construction(self):
        """Event requires id and label."""
        event = Event(id="test_event", label="Test Event")

        assert event.id == "test_event"
        assert event.label == "Test Event"
        assert event.participants == []
        assert event.accounts == []

    def test_construction_with_all_fields(self):
        """Event can be created with all fields."""
        account = EventAccount(
            source_id="mark",
            reference="Mark 14:43-50",
            summary="Judas betrays Jesus"
        )
        event = Event(
            id="betrayal",
            label="Betrayal of Jesus",
            participants=["jesus", "judas"],
            accounts=[account]
        )

        assert event.id == "betrayal"
        assert event.label == "Betrayal of Jesus"
        assert event.participants == ["jesus", "judas"]
        assert len(event.accounts) == 1
        assert event.accounts[0].source_id == "mark"

    def test_required_fields(self):
        """id and label are required."""
        with pytest.raises(TypeError):
            Event()  # Missing required fields

        with pytest.raises(TypeError):
            Event(id="test")  # Missing label

        with pytest.raises(TypeError):
            Event(label="Test")  # Missing id

    def test_default_factory_creates_independent_instances(self):
        """Default factories should create independent instances."""
        event1 = Event(id="event1", label="Event 1")
        event2 = Event(id="event2", label="Event 2")

        event1.participants.append("char1")

        # event2 should not be affected
        assert "char1" not in event2.participants

    def test_accounts_independent(self):
        """Accounts list should be independent."""
        event1 = Event(id="event1", label="Event 1")
        event2 = Event(id="event2", label="Event 2")

        account = EventAccount(
            source_id="mark",
            reference="Mark 1:1",
            summary="Test"
        )
        event1.accounts.append(account)

        assert len(event2.accounts) == 0

    def test_has_slots(self):
        """Event should use __slots__ for efficiency."""
        event = Event(id="test", label="Test")

        assert not hasattr(event, "__dict__")
        assert hasattr(event, "__slots__")

    def test_multiple_participants(self):
        """Event can have multiple participants."""
        event = Event(
            id="crucifixion",
            label="Crucifixion",
            participants=["jesus", "pilate", "peter"]
        )

        assert len(event.participants) == 3
        assert "jesus" in event.participants
        assert "pilate" in event.participants

    def test_multiple_accounts(self):
        """Event can have multiple accounts."""
        mark_account = EventAccount(
            source_id="mark",
            reference="Mark 15:1",
            summary="Mark's version"
        )
        john_account = EventAccount(
            source_id="john",
            reference="John 18:28",
            summary="John's version"
        )

        event = Event(
            id="trial",
            label="Trial",
            accounts=[mark_account, john_account]
        )

        assert len(event.accounts) == 2
        assert event.accounts[0].source_id == "mark"
        assert event.accounts[1].source_id == "john"


class TestDataclassInteraction:
    """Test interactions between dataclasses."""

    def test_character_with_nested_source_profile(self):
        """Character properly nests SourceProfile objects."""
        profile = SourceProfile(
            source_id="mark",
            traits={"role": "messiah"},
            references=["Mark 1:1"]
        )
        char = Character(
            id="jesus",
            canonical_name="Jesus",
            source_profiles=[profile]
        )

        # Should be able to access nested data
        assert char.source_profiles[0].source_id == "mark"
        assert char.source_profiles[0].traits["role"] == "messiah"
        assert "Mark 1:1" in char.source_profiles[0].references

    def test_event_with_nested_event_account(self):
        """Event properly nests EventAccount objects."""
        account = EventAccount(
            source_id="john",
            reference="John 13:21-30",
            summary="Jesus predicts betrayal",
            notes="Only John mentions Judas leaving immediately"
        )
        event = Event(
            id="prediction",
            label="Betrayal Prediction",
            participants=["jesus", "judas"],
            accounts=[account]
        )

        # Should be able to access nested data
        assert event.accounts[0].source_id == "john"
        assert event.accounts[0].summary == "Jesus predicts betrayal"
        assert event.accounts[0].notes is not None

    def test_modifying_nested_objects(self):
        """Modifying nested objects should affect parent."""
        profile = SourceProfile(source_id="mark")
        char = Character(
            id="test",
            canonical_name="Test",
            source_profiles=[profile]
        )

        # Modify the profile
        char.source_profiles[0].traits["new_trait"] = "value"

        # Should be reflected
        assert "new_trait" in char.source_profiles[0].traits

    def test_character_and_event_linking_by_id(self):
        """Event participants link to characters by ID."""
        char = Character(id="judas", canonical_name="Judas Iscariot")
        event = Event(
            id="betrayal",
            label="Betrayal",
            participants=["judas"]
        )

        # Participant ID should match character ID
        assert char.id in event.participants
