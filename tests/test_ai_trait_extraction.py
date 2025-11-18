"""
Tests for bce.ai.trait_extraction module.

Tests character trait extraction and event detail extraction from scripture passages.
"""

from __future__ import annotations

import pytest

from bce.config import BceConfig, set_default_config, reset_default_config
from bce.exceptions import ConfigurationError
from bce.ai import trait_extraction


class TestExtractCharacterTraits:
    """Tests for extract_character_traits function."""

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
            trait_extraction.extract_character_traits(
                "nicodemus",
                "john",
                "John 3:1-21",
                "Some text"
            )

    def test_basic_extraction_with_social_status(self):
        """Should extract social status traits from text."""
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

        bible_text = "There was a man named Nicodemus, a Pharisee and a member of the Sanhedrin."

        result = trait_extraction.extract_character_traits(
            "nicodemus",
            "john",
            "John 3:1",
            bible_text
        )

        assert result["character_id"] == "nicodemus"
        assert result["source"] == "john"
        assert result["reference"] == "John 3:1"
        assert result["needs_review"] is True
        assert len(result["suggested_traits"]) > 0

        # Should find Pharisee trait
        trait_keys = [t["trait_key"] for t in result["suggested_traits"]]
        assert "social_status" in trait_keys

        # Should have confidence scores
        for trait in result["suggested_traits"]:
            assert "confidence" in trait
            assert 0.0 <= trait["confidence"] <= 1.0

    def test_extraction_with_occupation(self):
        """Should extract occupation traits."""
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

        bible_text = "Simon Peter was a fisherman by trade, casting his nets into the sea."

        result = trait_extraction.extract_character_traits(
            "peter",
            "mark",
            "Mark 1:16",
            bible_text
        )

        traits = result["suggested_traits"]
        occupation_traits = [t for t in traits if t["trait_key"] == "occupation"]
        assert len(occupation_traits) > 0

    def test_extraction_with_action_patterns(self):
        """Should extract action-based traits."""
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

        bible_text = "Nicodemus came to Jesus at night. He asked many questions and sought understanding."

        result = trait_extraction.extract_character_traits(
            "nicodemus",
            "john",
            "John 3:1-2",
            bible_text
        )

        traits = result["suggested_traits"]
        trait_keys = [t["trait_key"] for t in traits]

        # Should find secretive seeking and/or inquisitive nature
        assert any(key in ["secretive_seeking", "inquisitive_nature"] for key in trait_keys)

    def test_extraction_with_dialogue(self):
        """Should extract dialogue content."""
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

        bible_text = '''Nicodemus said to him, "How can a man be born when he is old? Can he enter a second time into his mother's womb and be born?"'''

        result = trait_extraction.extract_character_traits(
            "nicodemus",
            "john",
            "John 3:4",
            bible_text
        )

        traits = result["suggested_traits"]
        dialogue_traits = [t for t in traits if t["trait_key"] == "dialogue_content"]
        assert len(dialogue_traits) > 0

    def test_extraction_with_emotions(self):
        """Should extract emotional states."""
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

        bible_text = "The disciples were afraid and terrified by the storm."

        result = trait_extraction.extract_character_traits(
            "disciples",
            "mark",
            "Mark 4:40",
            bible_text
        )

        traits = result["suggested_traits"]
        emotion_traits = [t for t in traits if t["trait_key"] == "emotional_state"]
        assert len(emotion_traits) > 0

    def test_extraction_with_empty_text(self):
        """Should handle empty text gracefully."""
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

        result = trait_extraction.extract_character_traits(
            "test_char",
            "mark",
            "Mark 1:1",
            ""
        )

        assert result["suggested_traits"] == []

    def test_extraction_with_no_matches(self):
        """Should handle text with no recognizable patterns."""
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

        bible_text = "The sky was blue and the grass was green."

        result = trait_extraction.extract_character_traits(
            "test_char",
            "mark",
            "Mark 1:1",
            bible_text
        )

        # May have no traits or very few
        assert isinstance(result["suggested_traits"], list)


class TestExtractEventDetails:
    """Tests for extract_event_details function."""

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
            trait_extraction.extract_event_details(
                "crucifixion",
                "mark",
                "Mark 15:1-47",
                "Some text"
            )

    def test_basic_event_extraction(self):
        """Should extract basic event details."""
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

        bible_text = "Jesus went to Jerusalem at Passover. Peter and John were with him."

        result = trait_extraction.extract_event_details(
            "jerusalem_visit",
            "john",
            "John 2:13",
            bible_text
        )

        assert result["event_id"] == "jerusalem_visit"
        assert result["source"] == "john"
        assert result["reference"] == "John 2:13"
        assert result["needs_review"] is True

    def test_extraction_finds_participants(self):
        """Should extract participant names."""
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

        bible_text = "Jesus spoke with Nicodemus and Peter about the kingdom."

        result = trait_extraction.extract_event_details(
            "discussion",
            "john",
            "John 3:1",
            bible_text
        )

        participants = result["suggested_participants"]
        assert "jesus" in participants
        assert "nicodemus" in participants or "peter" in participants

    def test_extraction_finds_location(self):
        """Should extract location markers."""
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

        bible_text = "This happened in Jerusalem at the temple during Passover."

        result = trait_extraction.extract_event_details(
            "event",
            "john",
            "John 2:13",
            bible_text
        )

        location = result["suggested_location"]
        assert location is not None
        assert "Jerusalem" in location or "temple" in location

    def test_extraction_finds_time_markers(self):
        """Should extract temporal markers."""
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

        bible_text = "He came at night during Passover on the sabbath."

        result = trait_extraction.extract_event_details(
            "event",
            "john",
            "John 3:1",
            bible_text
        )

        time_markers = result["time_markers"]
        assert len(time_markers) > 0
        # Should find at least one time reference
        assert any("night" in marker.lower() or "passover" in marker.lower() or "sabbath" in marker.lower()
                   for marker in time_markers)

    def test_extraction_generates_summary(self):
        """Should generate a summary."""
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

        bible_text = "Jesus taught in the temple. He spoke about the kingdom of God. Many people listened to his words."

        result = trait_extraction.extract_event_details(
            "teaching",
            "mark",
            "Mark 1:1",
            bible_text
        )

        summary = result["suggested_summary"]
        assert summary is not None
        assert len(summary) > 0
        assert len(summary) <= 250  # Should be reasonably short


class TestExtractParticipants:
    """Tests for _extract_participants helper function."""

    def test_finds_common_character_names(self):
        """Should find common NT character names."""
        text = "Jesus spoke to Peter, John, and Mary Magdalene."
        participants = trait_extraction._extract_participants(text)

        assert "jesus" in participants
        assert "peter" in participants
        assert "john" in participants
        assert "mary" in participants

    def test_deduplicates_names(self):
        """Should deduplicate repeated names."""
        text = "Jesus and Peter walked. Then Jesus spoke to Peter again."
        participants = trait_extraction._extract_participants(text)

        # Each name should appear only once
        assert participants.count("jesus") == 1
        assert participants.count("peter") == 1

    def test_handles_empty_text(self):
        """Should handle empty text."""
        participants = trait_extraction._extract_participants("")
        assert participants == []

    def test_case_insensitive_matching(self):
        """Should match names case-insensitively."""
        text = "JESUS spoke to peter and JoHn."
        participants = trait_extraction._extract_participants(text)

        assert "jesus" in participants
        assert "peter" in participants
        assert "john" in participants


class TestExtractLocation:
    """Tests for _extract_location helper function."""

    def test_finds_city_names(self):
        """Should find city location markers."""
        text = "The event occurred in Jerusalem during the feast."
        location = trait_extraction._extract_location(text)

        assert location is not None
        assert "Jerusalem" in location

    def test_finds_temple_references(self):
        """Should find temple/synagogue references."""
        text = "They met at the temple early in the morning."
        location = trait_extraction._extract_location(text)

        assert location is not None
        assert "temple" in location.lower()

    def test_returns_none_when_no_location(self):
        """Should return None when no location found."""
        text = "This is a text with no location markers at all."
        location = trait_extraction._extract_location(text)

        assert location is None


class TestExtractTimeMarkers:
    """Tests for _extract_time_markers helper function."""

    def test_finds_time_of_day(self):
        """Should find time of day markers."""
        text = "He came at night and left in the morning."
        markers = trait_extraction._extract_time_markers(text)

        assert len(markers) >= 1
        assert any("night" in m.lower() for m in markers)

    def test_finds_feast_references(self):
        """Should find feast/holiday references."""
        text = "This happened during Passover and again at Pentecost."
        markers = trait_extraction._extract_time_markers(text)

        assert len(markers) >= 1
        assert any("Passover" in m or "Pentecost" in m for m in markers)

    def test_finds_day_references(self):
        """Should find day count references."""
        text = "On the third day after these events, they returned."
        markers = trait_extraction._extract_time_markers(text)

        assert len(markers) >= 1
        assert any("third day" in m.lower() for m in markers)

    def test_handles_text_with_no_markers(self):
        """Should return empty list when no time markers."""
        text = "This text has no temporal references."
        markers = trait_extraction._extract_time_markers(text)

        assert markers == []


class TestGenerateSummary:
    """Tests for _generate_summary helper function."""

    def test_generates_summary_from_sentences(self):
        """Should generate summary from first few sentences."""
        text = "First sentence here. Second sentence here. Third sentence here. Fourth sentence."
        summary = trait_extraction._generate_summary(text)

        assert "First sentence" in summary
        assert len(summary) <= 250

    def test_respects_max_length(self):
        """Should respect max_length parameter."""
        long_text = "This is a very long sentence. " * 50
        summary = trait_extraction._generate_summary(long_text, max_length=100)

        assert len(summary) <= 110  # Some margin for ellipsis

    def test_handles_short_text(self):
        """Should handle text shorter than max_length."""
        text = "Short text."
        summary = trait_extraction._generate_summary(text)

        assert "Short text" in summary

    def test_handles_empty_text(self):
        """Should handle empty text."""
        summary = trait_extraction._generate_summary("")
        assert summary == ""

    def test_handles_text_with_no_sentences(self):
        """Should handle text with no sentence boundaries."""
        text = "no punctuation here at all"
        summary = trait_extraction._generate_summary(text, max_length=50)

        # Should truncate at max_length
        assert len(summary) <= 50


class TestExtractContext:
    """Tests for _extract_context helper function."""

    def test_extracts_context_around_match(self):
        """Should extract context around a match position."""
        text = "The quick brown fox jumps over the lazy dog in the forest."
        start = text.find("jumps")
        end = start + len("jumps")

        context = trait_extraction._extract_context(text, start, end, window=10)

        assert "fox jumps over" in context

    def test_handles_match_at_beginning(self):
        """Should handle match at text beginning."""
        text = "Beginning of text with more words following."
        start = 0
        end = 9  # "Beginning"

        context = trait_extraction._extract_context(text, start, end, window=20)

        assert "Beginning" in context

    def test_handles_match_at_end(self):
        """Should handle match at text end."""
        text = "This is some text ending here."
        start = text.find("ending")
        end = len(text) - 1

        context = trait_extraction._extract_context(text, start, end, window=20)

        assert "ending" in context

    def test_adds_ellipsis_when_truncated(self):
        """Should add ellipsis when context is truncated."""
        text = "A" * 200  # Long text
        start = 100
        end = 105

        context = trait_extraction._extract_context(text, start, end, window=20)

        # Should have ellipsis on at least one side
        assert "..." in context


class TestCalculateTraitConfidence:
    """Tests for _calculate_trait_confidence helper function."""

    def test_base_confidence(self):
        """Should return base confidence for minimal trait."""
        trait = {
            "trait_key": "other",
            "trait_value": "some value",
            "evidence": "short"
        }
        full_text = "unrelated text"

        confidence = trait_extraction._calculate_trait_confidence(trait, full_text)

        assert 0.0 <= confidence <= 1.0
        assert confidence >= 0.5  # Base confidence

    def test_increases_for_explicit_match(self):
        """Should increase confidence if trait value is in text."""
        trait = {
            "trait_key": "social_status",
            "trait_value": "Pharisee",
            "evidence": "Text mentions Pharisee"
        }
        full_text = "He was a Pharisee and member of the council."

        confidence = trait_extraction._calculate_trait_confidence(trait, full_text)

        assert confidence > 0.5

    def test_increases_for_substantial_evidence(self):
        """Should increase confidence for substantial evidence."""
        trait = {
            "trait_key": "other",
            "trait_value": "value",
            "evidence": "This is a very long evidence string with substantial content that provides good context"
        }
        full_text = "some text"

        confidence = trait_extraction._calculate_trait_confidence(trait, full_text)

        assert confidence > 0.5

    def test_increases_for_high_confidence_keys(self):
        """Should increase confidence for specific trait keys."""
        for key in ["social_status", "occupation", "role"]:
            trait = {
                "trait_key": key,
                "trait_value": "value",
                "evidence": "evidence"
            }
            full_text = "text"

            confidence = trait_extraction._calculate_trait_confidence(trait, full_text)

            assert confidence > 0.5

    def test_caps_at_max_confidence(self):
        """Should cap confidence at 0.95."""
        trait = {
            "trait_key": "social_status",
            "trait_value": "Pharisee",
            "evidence": "Very long evidence " * 20
        }
        full_text = "He was a Pharisee with clear social status markers"

        confidence = trait_extraction._calculate_trait_confidence(trait, full_text)

        assert confidence <= 0.95


class TestDeduplicateTraits:
    """Tests for _deduplicate_traits helper function."""

    def test_handles_empty_list(self):
        """Should handle empty trait list."""
        result = trait_extraction._deduplicate_traits([])
        assert result == []

    def test_handles_single_trait(self):
        """Should handle single trait."""
        traits = [{"trait_key": "role", "trait_value": "teacher", "evidence": "text"}]
        result = trait_extraction._deduplicate_traits(traits)
        assert result == traits

    def test_removes_exact_duplicates(self):
        """Should remove exact duplicate traits."""
        traits = [
            {"trait_key": "role", "trait_value": "teacher", "evidence": "text1"},
            {"trait_key": "role", "trait_value": "teacher", "evidence": "text2"},
            {"trait_key": "role", "trait_value": "Teacher", "evidence": "text3"},  # Case variation
        ]

        result = trait_extraction._deduplicate_traits(traits)

        # Should keep only one "teacher" role (case-insensitive)
        role_traits = [t for t in result if t["trait_key"] == "role"]
        assert len(role_traits) == 1

    def test_keeps_different_values_for_same_key(self):
        """Should keep different values for same trait key."""
        traits = [
            {"trait_key": "role", "trait_value": "teacher", "evidence": "text1"},
            {"trait_key": "role", "trait_value": "rabbi", "evidence": "text2"},
            {"trait_key": "role", "trait_value": "prophet", "evidence": "text3"},
        ]

        result = trait_extraction._deduplicate_traits(traits)

        # Should keep all three different role values
        assert len(result) == 3

    def test_keeps_traits_with_different_keys(self):
        """Should keep traits with different keys."""
        traits = [
            {"trait_key": "role", "trait_value": "teacher", "evidence": "text1"},
            {"trait_key": "social_status", "trait_value": "Pharisee", "evidence": "text2"},
            {"trait_key": "occupation", "trait_value": "fisherman", "evidence": "text3"},
        ]

        result = trait_extraction._deduplicate_traits(traits)

        assert len(result) == 3


class TestExtractTraitsFromText:
    """Tests for _extract_traits_from_text helper function."""

    def test_finds_multiple_trait_types(self):
        """Should find multiple types of traits in complex text."""
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

        text = '''
        Nicodemus, a Pharisee and ruler of the Jews, came to Jesus at night.
        He asked, "How can these things be?" Jesus replied with compassion,
        "You are a teacher of Israel and do not understand these things?"
        '''

        traits = trait_extraction._extract_traits_from_text("nicodemus", text)

        # Should find multiple trait types
        trait_keys = [t["trait_key"] for t in traits]
        assert len(set(trait_keys)) > 1  # Multiple different trait types

    def test_each_trait_has_required_fields(self):
        """Should ensure each trait has required fields."""
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

        text = "He was a Pharisee who came at night."
        traits = trait_extraction._extract_traits_from_text("test", text)

        for trait in traits:
            assert "trait_key" in trait
            assert "trait_value" in trait
            assert "evidence" in trait

    def test_handles_unicode_quotes_in_dialogue(self):
        """Should handle different quote styles."""
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

        # Test with curly quotes
        text = '"This is spoken text with curly quotes"'
        traits = trait_extraction._extract_traits_from_text("test", text)

        dialogue_traits = [t for t in traits if t["trait_key"] == "dialogue_content"]
        assert len(dialogue_traits) > 0
