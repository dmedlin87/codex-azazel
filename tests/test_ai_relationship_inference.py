"""
Tests for bce.ai.relationship_inference module.

Tests relationship inference between characters based on co-occurrence and textual evidence.
"""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from bce.config import BceConfig, set_default_config, reset_default_config
from bce.exceptions import ConfigurationError
from bce.models import Character, SourceProfile, Event, EventAccount
from bce.ai import relationship_inference


class TestInferRelationshipsForCharacter:
    """Tests for infer_relationships_for_character function."""

    def setup_method(self):
        """Setup for each test."""
        reset_default_config()

    def teardown_method(self):
        """Cleanup after each test."""
        reset_default_config()

    def test_requires_ai_enabled(self):
        """Should raise ConfigurationError when AI is disabled."""
        config = BceConfig(enable_ai_features=False)
        set_default_config(config)

        with pytest.raises(ConfigurationError, match="AI features are disabled"):
            relationship_inference.infer_relationships_for_character("peter")

    @patch('bce.ai.relationship_inference.queries')
    def test_returns_existing_relationships(self, mock_queries):
        """Should include existing relationships with already_exists=True."""
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

        # Mock character with existing relationship
        char = Character(
            id="peter",
            canonical_name="Peter",
            aliases=[],
            roles=["apostle"],
            source_profiles=[],
            relationships=[
                {
                    "type": "teacher_student",
                    "to": "jesus",
                    "description": "Peter follows Jesus as teacher"
                }
            ],
            tags=[]
        )

        mock_queries.get_character.return_value = char
        mock_queries.list_events_for_character.return_value = []

        result = relationship_inference.infer_relationships_for_character("peter")

        # Should include the existing relationship
        existing = [r for r in result if r["already_exists"]]
        assert len(existing) == 1
        assert existing[0]["character_id"] == "jesus"
        assert existing[0]["confidence"] == 1.0

    @patch('bce.ai.relationship_inference.queries')
    def test_infers_from_event_cooccurrence(self, mock_queries):
        """Should infer relationships from event co-occurrence."""
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

        # Mock character
        char = Character(
            id="peter",
            canonical_name="Peter",
            aliases=[],
            roles=["apostle"],
            source_profiles=[],
            relationships=[],
            tags=[]
        )

        # Mock another character
        john = Character(
            id="john",
            canonical_name="John",
            aliases=[],
            roles=["apostle"],
            source_profiles=[],
            relationships=[],
            tags=[]
        )

        # Mock events where both participate
        event1 = Event(
            id="event1",
            label="Event 1",
            participants=["peter", "john", "jesus"],
            accounts=[],
            parallels=[],
            tags=[]
        )

        event2 = Event(
            id="event2",
            label="Event 2",
            participants=["peter", "john"],
            accounts=[],
            parallels=[],
            tags=[]
        )

        mock_queries.get_character.side_effect = lambda cid: char if cid == "peter" else john
        mock_queries.list_events_for_character.return_value = [event1, event2]
        mock_queries.get_event.side_effect = lambda eid: event1 if eid == "event1" else event2

        result = relationship_inference.infer_relationships_for_character("peter")

        # Should infer relationship with John based on co-occurrence
        new_suggestions = [r for r in result if not r["already_exists"]]
        john_suggestions = [r for r in new_suggestions if r["character_id"] == "john"]

        assert len(john_suggestions) > 0
        assert john_suggestions[0]["confidence"] > 0.0

    @patch('bce.ai.relationship_inference.queries')
    def test_respects_confidence_threshold(self, mock_queries):
        """Should filter by confidence threshold."""
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

        char = Character(
            id="peter",
            canonical_name="Peter",
            aliases=[],
            roles=["apostle"],
            source_profiles=[],
            relationships=[],
            tags=[]
        )

        mock_queries.get_character.return_value = char
        mock_queries.list_events_for_character.return_value = []

        # High threshold should return fewer results
        result_high = relationship_inference.infer_relationships_for_character(
            "peter",
            confidence_threshold=0.95
        )

        result_low = relationship_inference.infer_relationships_for_character(
            "peter",
            confidence_threshold=0.1
        )

        # High threshold should have equal or fewer results
        assert len(result_high) <= len(result_low)

    @patch('bce.ai.relationship_inference.queries')
    def test_sorts_by_confidence(self, mock_queries):
        """Should sort results by confidence descending."""
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

        char = Character(
            id="peter",
            canonical_name="Peter",
            aliases=[],
            roles=["apostle"],
            source_profiles=[],
            relationships=[
                {"type": "teacher_student", "to": "jesus", "description": "Follows Jesus"}
            ],
            tags=[]
        )

        mock_queries.get_character.return_value = char
        mock_queries.list_events_for_character.return_value = []

        result = relationship_inference.infer_relationships_for_character("peter")

        # Check that confidences are in descending order
        if len(result) > 1:
            confidences = [r["confidence"] for r in result]
            assert confidences == sorted(confidences, reverse=True)


class TestInferAllRelationships:
    """Tests for infer_all_relationships function."""

    def setup_method(self):
        """Setup for each test."""
        reset_default_config()

    def teardown_method(self):
        """Cleanup after each test."""
        reset_default_config()

    def test_requires_ai_enabled(self):
        """Should raise ConfigurationError when AI is disabled."""
        config = BceConfig(enable_ai_features=False)
        set_default_config(config)

        with pytest.raises(ConfigurationError, match="AI features are disabled"):
            relationship_inference.infer_all_relationships()

    @patch('bce.ai.relationship_inference.queries')
    def test_processes_all_characters(self, mock_queries):
        """Should process all characters."""
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

        mock_queries.list_character_ids.return_value = ["peter", "john"]

        # Mock minimal character data
        char = Character(
            id="test",
            canonical_name="Test",
            aliases=[],
            roles=[],
            source_profiles=[],
            relationships=[],
            tags=[]
        )

        mock_queries.get_character.return_value = char
        mock_queries.list_events_for_character.return_value = []

        result = relationship_inference.infer_all_relationships()

        # Should return dict with character IDs as keys
        assert isinstance(result, dict)

    @patch('bce.ai.relationship_inference.queries')
    def test_excludes_existing_relationships(self, mock_queries):
        """Should only return new relationship suggestions."""
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

        mock_queries.list_character_ids.return_value = ["peter"]

        char = Character(
            id="peter",
            canonical_name="Peter",
            aliases=[],
            roles=[],
            source_profiles=[],
            relationships=[
                {"type": "teacher_student", "to": "jesus", "description": "Follows Jesus"}
            ],
            tags=[]
        )

        mock_queries.get_character.return_value = char
        mock_queries.list_events_for_character.return_value = []

        result = relationship_inference.infer_all_relationships()

        # Should not include peter if only existing relationships found
        if "peter" in result:
            # All suggestions should be new
            for suggestion in result["peter"]:
                assert suggestion.get("already_exists", False) is False


class TestSuggestMissingRelationships:
    """Tests for suggest_missing_relationships function."""

    def setup_method(self):
        """Setup for each test."""
        reset_default_config()

    def teardown_method(self):
        """Cleanup after each test."""
        reset_default_config()

    def test_requires_ai_enabled(self):
        """Should raise ConfigurationError when AI is disabled."""
        config = BceConfig(enable_ai_features=False)
        set_default_config(config)

        with pytest.raises(ConfigurationError, match="AI features are disabled"):
            relationship_inference.suggest_missing_relationships()

    @patch('bce.ai.relationship_inference.queries')
    def test_identifies_characters_without_relationships(self, mock_queries):
        """Should identify characters with event participation but no relationships."""
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

        # Character with no relationships but has events
        char = Character(
            id="nicodemus",
            canonical_name="Nicodemus",
            aliases=[],
            roles=["pharisee"],
            source_profiles=[],
            relationships=[],  # No relationships
            tags=[]
        )

        event = Event(
            id="night_visit",
            label="Night Visit",
            participants=["nicodemus", "jesus"],
            accounts=[],
            parallels=[],
            tags=[]
        )

        mock_queries.list_all_characters.return_value = [char]
        mock_queries.list_events_for_character.return_value = [event]

        result = relationship_inference.suggest_missing_relationships()

        # Should suggest nicodemus as missing relationships
        assert len(result) > 0
        nicodemus_suggestions = [s for s in result if s["character_id"] == "nicodemus"]
        assert len(nicodemus_suggestions) > 0
        assert "frequent_associates" in nicodemus_suggestions[0]

    @patch('bce.ai.relationship_inference.queries')
    def test_skips_characters_with_relationships(self, mock_queries):
        """Should skip characters that already have relationships."""
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

        # Character with existing relationships
        char = Character(
            id="peter",
            canonical_name="Peter",
            aliases=[],
            roles=["apostle"],
            source_profiles=[],
            relationships=[
                {"type": "teacher_student", "to": "jesus", "description": "Follows Jesus"}
            ],
            tags=[]
        )

        mock_queries.list_all_characters.return_value = [char]
        mock_queries.list_events_for_character.return_value = []

        result = relationship_inference.suggest_missing_relationships()

        # Should not suggest peter
        peter_suggestions = [s for s in result if s["character_id"] == "peter"]
        assert len(peter_suggestions) == 0

    @patch('bce.ai.relationship_inference.queries')
    def test_skips_characters_with_no_events(self, mock_queries):
        """Should skip characters with no event participation."""
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

        # Character with no relationships and no events
        char = Character(
            id="obscure",
            canonical_name="Obscure Character",
            aliases=[],
            roles=[],
            source_profiles=[],
            relationships=[],
            tags=[]
        )

        mock_queries.list_all_characters.return_value = [char]
        mock_queries.list_events_for_character.return_value = []  # No events

        result = relationship_inference.suggest_missing_relationships()

        # Should not suggest characters with no events
        obscure_suggestions = [s for s in result if s["character_id"] == "obscure"]
        assert len(obscure_suggestions) == 0


class TestFindEventCooccurrences:
    """Tests for _find_event_cooccurrences helper function."""

    @patch('bce.ai.relationship_inference.queries')
    def test_finds_cooccurring_characters(self, mock_queries):
        """Should find characters that co-occur in events."""
        event1 = Event(
            id="event1",
            label="Event 1",
            participants=["peter", "john", "james"],
            accounts=[],
            parallels=[],
            tags=[]
        )

        event2 = Event(
            id="event2",
            label="Event 2",
            participants=["peter", "john"],
            accounts=[],
            parallels=[],
            tags=[]
        )

        mock_queries.list_events_for_character.return_value = [event1, event2]

        result = relationship_inference._find_event_cooccurrences("peter")

        assert "john" in result
        assert "james" in result
        assert len(result["john"]) == 2  # John in both events
        assert len(result["james"]) == 1  # James in one event

    @patch('bce.ai.relationship_inference.queries')
    def test_excludes_target_character(self, mock_queries):
        """Should exclude the target character from results."""
        event = Event(
            id="event1",
            label="Event 1",
            participants=["peter", "john"],
            accounts=[],
            parallels=[],
            tags=[]
        )

        mock_queries.list_events_for_character.return_value = [event]

        result = relationship_inference._find_event_cooccurrences("peter")

        assert "peter" not in result


class TestFindTraitAssociations:
    """Tests for _find_trait_associations helper function."""

    @patch('bce.ai.relationship_inference.queries')
    def test_finds_characters_mentioned_in_traits(self, mock_queries):
        """Should find characters mentioned in trait values."""
        peter = Character(
            id="peter",
            canonical_name="Simon Peter",
            aliases=[],
            roles=["apostle"],
            source_profiles=[
                SourceProfile(
                    source_id="mark",
                    traits={
                        "relationship": "Brother of Andrew, disciple with John"
                    },
                    references=[]
                )
            ],
            relationships=[],
            tags=[]
        )

        andrew = Character(id="andrew", canonical_name="Andrew", aliases=[], roles=[], source_profiles=[], relationships=[], tags=[])
        john = Character(id="john", canonical_name="John", aliases=[], roles=[], source_profiles=[], relationships=[], tags=[])

        mock_queries.get_character.return_value = peter
        mock_queries.list_all_characters.return_value = [peter, andrew, john]

        result = relationship_inference._find_trait_associations("peter")

        # Should find andrew and john mentioned in trait
        assert "andrew" in result or "john" in result

    @patch('bce.ai.relationship_inference.queries')
    def test_handles_character_with_no_trait_mentions(self, mock_queries):
        """Should handle characters with no mentions in traits."""
        char = Character(
            id="peter",
            canonical_name="Peter",
            aliases=[],
            roles=[],
            source_profiles=[
                SourceProfile(
                    source_id="mark",
                    traits={"role": "fisherman"},
                    references=[]
                )
            ],
            relationships=[],
            tags=[]
        )

        mock_queries.get_character.return_value = char
        mock_queries.list_all_characters.return_value = [char]

        result = relationship_inference._find_trait_associations("peter")

        # Should return empty dict
        assert result == {}


class TestAnalyzeEventCooccurrence:
    """Tests for _analyze_event_cooccurrence helper function."""

    @patch('bce.ai.relationship_inference.queries')
    def test_returns_relationship_suggestion(self, mock_queries):
        """Should return relationship suggestion dict."""
        peter = Character(id="peter", canonical_name="Peter", aliases=[], roles=["apostle"], source_profiles=[], relationships=[], tags=[])
        john = Character(id="john", canonical_name="John", aliases=[], roles=["apostle"], source_profiles=[], relationships=[], tags=[])

        event = Event(id="event1", label="Event 1", participants=["peter", "john"], accounts=[], parallels=[], tags=[])

        mock_queries.get_character.side_effect = lambda cid: peter if cid == "peter" else john
        mock_queries.get_event.return_value = event

        result = relationship_inference._analyze_event_cooccurrence(
            "peter",
            "john",
            ["event1"]
        )

        assert result is not None
        assert result["character_id"] == "john"
        assert "suggested_type" in result
        assert "confidence" in result
        assert "evidence" in result
        assert isinstance(result["evidence"], list)

    @patch('bce.ai.relationship_inference.queries')
    def test_returns_none_for_empty_event_list(self, mock_queries):
        """Should return None for empty event list."""
        result = relationship_inference._analyze_event_cooccurrence(
            "peter",
            "john",
            []
        )

        assert result is None


class TestAnalyzeTraitAssociation:
    """Tests for _analyze_trait_association helper function."""

    def test_returns_relationship_suggestion(self):
        """Should return relationship suggestion dict."""
        contexts = ["Peter is the brother of Andrew"]

        result = relationship_inference._analyze_trait_association(
            "peter",
            "andrew",
            contexts
        )

        assert result is not None
        assert result["character_id"] == "andrew"
        assert "suggested_type" in result
        assert "confidence" in result
        assert "evidence" in result

    def test_detects_family_relationships(self):
        """Should detect family relationship keywords."""
        contexts = ["Peter was the brother of Andrew"]

        result = relationship_inference._analyze_trait_association(
            "peter",
            "andrew",
            contexts
        )

        assert result["suggested_type"] == "family"
        assert result["confidence"] > 0.8

    def test_detects_disciple_relationships(self):
        """Should detect disciple relationships."""
        contexts = ["John was a disciple of Jesus"]

        result = relationship_inference._analyze_trait_association(
            "john",
            "jesus",
            contexts
        )

        assert result["suggested_type"] == "teacher_disciple"
        assert result["confidence"] > 0.8

    def test_returns_none_for_empty_contexts(self):
        """Should return None for empty contexts."""
        result = relationship_inference._analyze_trait_association(
            "peter",
            "john",
            []
        )

        assert result is None


class TestInferRelationshipType:
    """Tests for _infer_relationship_type helper function."""

    def test_infers_fellow_disciple(self):
        """Should infer fellow_disciple for apostles."""
        peter = Character(id="peter", canonical_name="Peter", aliases=[], roles=["apostle"], source_profiles=[], relationships=[], tags=[])
        john = Character(id="john", canonical_name="John", aliases=[], roles=["apostle"], source_profiles=[], relationships=[], tags=[])

        rel_type = relationship_inference._infer_relationship_type(
            peter,
            john,
            ["event1"]
        )

        assert rel_type == "fellow_disciple"

    def test_infers_teacher_student(self):
        """Should infer teacher_student for disciple-teacher pairs."""
        peter = Character(id="peter", canonical_name="Peter", aliases=[], roles=["disciple"], source_profiles=[], relationships=[], tags=[])
        jesus = Character(id="jesus", canonical_name="Jesus", aliases=[], roles=["teacher", "messiah"], source_profiles=[], relationships=[], tags=[])

        rel_type = relationship_inference._infer_relationship_type(
            peter,
            jesus,
            ["event1"]
        )

        assert rel_type == "teacher_student"

    def test_infers_religious_colleague(self):
        """Should infer religious_colleague for religious authorities."""
        nicodemus = Character(id="nicodemus", canonical_name="Nicodemus", aliases=[], roles=["pharisee"], source_profiles=[], relationships=[], tags=[])
        joseph = Character(id="joseph", canonical_name="Joseph", aliases=[], roles=["pharisee"], source_profiles=[], relationships=[], tags=[])

        rel_type = relationship_inference._infer_relationship_type(
            nicodemus,
            joseph,
            ["event1"]
        )

        assert rel_type == "religious_colleague"

    def test_infers_frequent_associate(self):
        """Should infer frequent_associate for many co-occurrences."""
        char1 = Character(id="char1", canonical_name="Char1", aliases=[], roles=[], source_profiles=[], relationships=[], tags=[])
        char2 = Character(id="char2", canonical_name="Char2", aliases=[], roles=[], source_profiles=[], relationships=[], tags=[])

        rel_type = relationship_inference._infer_relationship_type(
            char1,
            char2,
            ["event1", "event2", "event3", "event4"]
        )

        assert rel_type == "frequent_associate"

    def test_infers_associate_for_few_events(self):
        """Should infer associate for few co-occurrences."""
        char1 = Character(id="char1", canonical_name="Char1", aliases=[], roles=[], source_profiles=[], relationships=[], tags=[])
        char2 = Character(id="char2", canonical_name="Char2", aliases=[], roles=[], source_profiles=[], relationships=[], tags=[])

        rel_type = relationship_inference._infer_relationship_type(
            char1,
            char2,
            ["event1"]
        )

        assert rel_type == "associate"


class TestCalculateCooccurrenceConfidence:
    """Tests for _calculate_cooccurrence_confidence helper function."""

    def test_increases_with_event_count(self):
        """Should increase confidence with more events."""
        conf1 = relationship_inference._calculate_cooccurrence_confidence(1, "associate")
        conf2 = relationship_inference._calculate_cooccurrence_confidence(3, "associate")
        conf3 = relationship_inference._calculate_cooccurrence_confidence(5, "associate")

        assert conf2 > conf1
        assert conf3 > conf2

    def test_increases_for_specific_types(self):
        """Should increase confidence for specific relationship types."""
        conf_generic = relationship_inference._calculate_cooccurrence_confidence(2, "associate")
        conf_specific = relationship_inference._calculate_cooccurrence_confidence(2, "teacher_student")

        assert conf_specific > conf_generic

    def test_caps_at_max_confidence(self):
        """Should cap confidence at maximum value."""
        conf = relationship_inference._calculate_cooccurrence_confidence(100, "teacher_student")

        assert conf <= 0.97
