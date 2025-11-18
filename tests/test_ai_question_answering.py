"""
Comprehensive tests for bce/ai/question_answering.py.

Tests question answering functionality including:
- Question classification
- Multiple answer modes (character comparison, source analysis, traits, etc.)
- Evidence gathering and synthesis
- Confidence calculation
- Caching behavior
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from bce.config import BceConfig, set_default_config, reset_default_config
from bce.exceptions import ConfigurationError
from bce.models import Character, SourceProfile, Event, EventAccount


class TestQuestionAnsweringConfiguration:
    """Tests for configuration and error handling."""

    def setup_method(self):
        """Setup for each test."""
        reset_default_config()

    def teardown_method(self):
        """Cleanup after each test."""
        reset_default_config()

    def test_ask_raises_when_ai_disabled(self):
        """ask() should raise ConfigurationError when AI is disabled."""
        from bce.ai import question_answering

        config = BceConfig(enable_ai_features=False)
        set_default_config(config)

        with pytest.raises(ConfigurationError, match="AI features are disabled"):
            question_answering.ask("test question")

    def test_ask_respects_use_cache_parameter(self):
        """ask() should respect use_cache parameter."""
        from bce.ai import question_answering

        with tempfile.TemporaryDirectory() as tmpdir:
            config = BceConfig(
                enable_ai_features=True,
                ai_cache_dir=Path(tmpdir)
            )
            set_default_config(config)

            # Mock the internal implementation
            with patch("bce.ai.question_answering._ask_impl") as mock_impl:
                mock_impl.return_value = {
                    "answer": "test",
                    "confidence": 0.8,
                    "evidence": [],
                    "comparison": {}
                }

                # Test with cache disabled
                question_answering.ask("test", use_cache=False)
                assert mock_impl.called


class TestQuestionClassification:
    """Tests for _classify_question function."""

    def setup_method(self):
        """Setup for each test."""
        reset_default_config()

    def test_classify_character_comparison(self):
        """Should classify character comparison questions."""
        from bce.ai.question_answering import _classify_question

        questions = [
            "Which gospel portrays Jesus as most divine?",
            "Which source shows the most authoritative Paul?",
            "Which gospel has the least messianic claims?",
        ]

        for q in questions:
            result = _classify_question(q)
            assert result == "character_comparison", f"Failed for: {q}"

    def test_classify_source_analysis(self):
        """Should classify source analysis questions."""
        from bce.ai.question_answering import _classify_question

        questions = [
            "How does the Gospel of Mark portray Jesus?",
            "How does Paul depict resurrection?",
            "How does Acts present Peter?",
        ]

        for q in questions:
            result = _classify_question(q)
            assert result == "source_analysis", f"Failed for: {q}"

    def test_classify_trait_query(self):
        """Should classify trait queries."""
        from bce.ai.question_answering import _classify_question

        questions = [
            "Who has the trait of doubt?",
            "Which character has the trait of leadership?",
        ]

        for q in questions:
            result = _classify_question(q)
            assert result == "trait_query", f"Failed for: {q}"

    def test_classify_relationship_query(self):
        """Should classify relationship queries."""
        from bce.ai.question_answering import _classify_question

        questions = [
            "What is the relationship between Peter and Paul?",
            "Who is related to Jesus?",
            "How is Mary connected to the disciples?",
        ]

        for q in questions:
            result = _classify_question(q)
            assert result == "relationship_query", f"Failed for: {q}"

    def test_classify_event_query(self):
        """Should classify event queries."""
        from bce.ai.question_answering import _classify_question

        questions = [
            "What events happened at the crucifixion?",
            "When did the resurrection occur?",
            "Where did Paul's conversion happen?",
        ]

        for q in questions:
            result = _classify_question(q)
            assert result == "event_query", f"Failed for: {q}"

    def test_classify_general(self):
        """Should classify general questions as 'general'."""
        from bce.ai.question_answering import _classify_question

        questions = [
            "Tell me about Paul",
            "What is in the dataset?",
            "Random question with no keywords",
        ]

        for q in questions:
            result = _classify_question(q)
            assert result == "general", f"Failed for: {q}"


class TestAnswerCharacterComparison:
    """Tests for _answer_character_comparison function."""

    def setup_method(self):
        """Setup for each test."""
        reset_default_config()

    def test_answer_character_comparison_with_results(self):
        """Should answer character comparison with semantic search results."""
        from bce.ai.question_answering import _answer_character_comparison

        # Mock semantic search results
        mock_results = [
            {"type": "character", "id": "jesus", "match_in": "traits.john.divinity"},
            {"type": "character", "id": "paul", "match_in": "traits.acts.authority"},
        ]

        # Mock character data
        jesus = Character(
            id="jesus",
            canonical_name="Jesus",
            aliases=[],
            roles=["teacher"],
            source_profiles=[
                SourceProfile(
                    source_id="john",
                    traits={"divinity": "High divine claims"},
                    references=["John 1:1"]
                )
            ],
            relationships=[],
            tags=[]
        )

        paul = Character(
            id="paul",
            canonical_name="Paul",
            aliases=[],
            roles=["apostle"],
            source_profiles=[
                SourceProfile(
                    source_id="acts",
                    traits={"authority": "Apostolic authority"},
                    references=["Acts 9:1"]
                )
            ],
            relationships=[],
            tags=[]
        )

        with patch("bce.ai.semantic_search.query") as mock_search, \
             patch("bce.ai.question_answering.queries.get_character") as mock_get:
            mock_search.return_value = mock_results
            mock_get.side_effect = lambda char_id: jesus if char_id == "jesus" else paul

            result = _answer_character_comparison("Which gospel portrays Jesus as divine?")

            assert "answer" in result
            assert "confidence" in result
            assert "evidence" in result
            assert "comparison" in result
            assert len(result["evidence"]) > 0
            assert result["confidence"] > 0

    def test_answer_character_comparison_no_results(self):
        """Should handle no search results gracefully."""
        from bce.ai.question_answering import _answer_character_comparison

        with patch("bce.ai.semantic_search.query") as mock_search:
            mock_search.return_value = []

            result = _answer_character_comparison("Which gospel portrays nobody?")

            assert result["answer"]
            assert result["confidence"] == 0.0
            assert result["evidence"] == []
            assert result["comparison"] == {}


class TestAnswerSourceAnalysis:
    """Tests for _answer_source_analysis function."""

    def setup_method(self):
        """Setup for each test."""
        reset_default_config()

    def test_answer_source_analysis_mark(self):
        """Should extract and analyze Mark source."""
        from bce.ai.question_answering import _answer_source_analysis

        # Mock character data
        char = Character(
            id="jesus",
            canonical_name="Jesus",
            aliases=[],
            roles=["teacher"],
            source_profiles=[
                SourceProfile(
                    source_id="mark",
                    traits={"portrayal": "Suffering servant"},
                    references=["Mark 1:1"]
                )
            ],
            relationships=[],
            tags=[]
        )

        with patch("bce.ai.question_answering.queries.list_all_characters") as mock_list:
            mock_list.return_value = [char]

            result = _answer_source_analysis("How does the Gospel of Mark portray Jesus?")

            assert "answer" in result
            assert "mark" in result["answer"].lower()
            assert result["confidence"] > 0
            assert len(result["evidence"]) > 0

    def test_answer_source_analysis_no_source_match(self):
        """Should fall back to general answer if no source match."""
        from bce.ai.question_answering import _answer_source_analysis

        with patch("bce.ai.question_answering._answer_general") as mock_general:
            mock_general.return_value = {
                "answer": "general answer",
                "confidence": 0.5,
                "evidence": [],
                "comparison": {}
            }

            result = _answer_source_analysis("How does XYZ portray something?")

            assert mock_general.called

    def test_answer_source_analysis_empty_evidence(self):
        """Should handle empty evidence gracefully."""
        from bce.ai.question_answering import _answer_source_analysis

        with patch("bce.ai.question_answering.queries.list_all_characters") as mock_list:
            mock_list.return_value = []

            result = _answer_source_analysis("How does Mark portray nobody?")

            assert result["confidence"] == 0.3
            assert result["evidence"] == []


class TestAnswerTraitQuery:
    """Tests for _answer_trait_query function."""

    def setup_method(self):
        """Setup for each test."""
        reset_default_config()

    def test_answer_trait_query_with_matches(self):
        """Should extract traits from semantic search results."""
        from bce.ai.question_answering import _answer_trait_query

        mock_results = [
            {
                "type": "character",
                "id": "thomas",
                "match_in": "traits.john.doubt"
            }
        ]

        char = Character(
            id="thomas",
            canonical_name="Thomas",
            aliases=[],
            roles=["disciple"],
            source_profiles=[
                SourceProfile(
                    source_id="john",
                    traits={"doubt": "Doubting disciple"},
                    references=["John 20:24"]
                )
            ],
            relationships=[],
            tags=[]
        )

        with patch("bce.ai.semantic_search.query") as mock_search, \
             patch("bce.ai.question_answering.queries.get_character") as mock_get:
            mock_search.return_value = mock_results
            mock_get.return_value = char

            result = _answer_trait_query("Who has the trait of doubt?")

            assert "thomas" in result["answer"].lower()
            assert len(result["evidence"]) > 0

    def test_answer_trait_query_no_matches(self):
        """Should handle no matches gracefully."""
        from bce.ai.question_answering import _answer_trait_query

        with patch("bce.ai.semantic_search.query") as mock_search:
            mock_search.return_value = []

            result = _answer_trait_query("Who has impossible trait?")

            assert "no characters found" in result["answer"].lower()
            assert result["evidence"] == []


class TestAnswerRelationshipQuery:
    """Tests for _answer_relationship_query function."""

    def setup_method(self):
        """Setup for each test."""
        reset_default_config()

    def test_answer_relationship_query_with_matches(self):
        """Should extract relationships from search results."""
        from bce.ai.question_answering import _answer_relationship_query

        mock_results = [
            {"type": "character", "id": "peter"}
        ]

        char = Character(
            id="peter",
            canonical_name="Peter",
            aliases=[],
            roles=["apostle"],
            source_profiles=[],
            relationships=[
                {"type": "brother", "to": "andrew", "description": "Brothers"}
            ],
            tags=[]
        )

        with patch("bce.ai.semantic_search.query") as mock_search, \
             patch("bce.ai.question_answering.queries.get_character") as mock_get:
            mock_search.return_value = mock_results
            mock_get.return_value = char

            result = _answer_relationship_query("What is Peter's relationship to Andrew?")

            assert len(result["evidence"]) > 0
            assert result["evidence"][0]["relationship_type"] == "brother"

    def test_answer_relationship_query_no_matches(self):
        """Should handle no matches gracefully."""
        from bce.ai.question_answering import _answer_relationship_query

        with patch("bce.ai.semantic_search.query") as mock_search:
            mock_search.return_value = []

            result = _answer_relationship_query("Who is related to nobody?")

            assert "no relationships found" in result["answer"].lower()


class TestAnswerEventQuery:
    """Tests for _answer_event_query function."""

    def setup_method(self):
        """Setup for each test."""
        reset_default_config()

    def test_answer_event_query_with_matches(self):
        """Should extract event accounts from search results."""
        from bce.ai.question_answering import _answer_event_query

        mock_results = [
            {"type": "event", "id": "crucifixion"}
        ]

        event = Event(
            id="crucifixion",
            label="Crucifixion",
            participants=["jesus"],
            accounts=[
                EventAccount(
                    source_id="mark",
                    reference="Mark 15:1-47",
                    summary="Jesus crucified",
                    notes=None
                )
            ],
            parallels=[],
            tags=[]
        )

        with patch("bce.ai.semantic_search.query") as mock_search, \
             patch("bce.ai.question_answering.queries.get_event") as mock_get:
            mock_search.return_value = mock_results
            mock_get.return_value = event

            result = _answer_event_query("When did the crucifixion happen?")

            assert len(result["evidence"]) > 0
            assert result["evidence"][0]["event"] == "crucifixion"

    def test_answer_event_query_no_matches(self):
        """Should handle no matches gracefully."""
        from bce.ai.question_answering import _answer_event_query

        with patch("bce.ai.semantic_search.query") as mock_search:
            mock_search.return_value = []

            result = _answer_event_query("What events never happened?")

            assert "no events found" in result["answer"].lower()


class TestAnswerGeneral:
    """Tests for _answer_general function."""

    def setup_method(self):
        """Setup for each test."""
        reset_default_config()

    def test_answer_general_with_results(self):
        """Should return general results from semantic search."""
        from bce.ai.question_answering import _answer_general

        mock_results = [
            {
                "type": "character",
                "id": "paul",
                "match_in": "traits.acts.conversion",
                "matching_context": "Paul's conversion on Damascus road",
                "relevance_score": 0.85
            }
        ]

        with patch("bce.ai.semantic_search.query") as mock_search:
            mock_search.return_value = mock_results

            result = _answer_general("Tell me about Paul")

            assert "10 relevant items" in result["answer"] or "1 relevant" in result["answer"]
            assert len(result["evidence"]) > 0

    def test_answer_general_no_results(self):
        """Should handle no results gracefully."""
        from bce.ai.question_answering import _answer_general

        with patch("bce.ai.semantic_search.query") as mock_search:
            mock_search.return_value = []

            result = _answer_general("Gibberish query xyz123")

            assert "no relevant data" in result["answer"].lower()


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_synthesize_answer_no_evidence(self):
        """Should return insufficient data message for empty evidence."""
        from bce.ai.question_answering import _synthesize_answer

        result = _synthesize_answer("test question", [], {})
        assert "insufficient data" in result.lower()

    def test_synthesize_answer_single_character(self):
        """Should synthesize answer for single character."""
        from bce.ai.question_answering import _synthesize_answer

        evidence = [
            {"character": "paul", "source": "acts", "trait": "conversion"}
        ]

        result = _synthesize_answer("test", evidence, {})
        assert "paul" in result.lower()
        assert "acts" in result.lower()

    def test_synthesize_answer_multiple_characters(self):
        """Should synthesize answer for multiple characters."""
        from bce.ai.question_answering import _synthesize_answer

        evidence = [
            {"character": "paul", "source": "acts"},
            {"character": "peter", "source": "mark"},
            {"character": "john", "source": "john"},
            {"character": "james", "source": "acts"},
        ]

        result = _synthesize_answer("test", evidence, {})
        assert "4 characters" in result or "paul" in result.lower()

    def test_calculate_confidence_empty(self):
        """Should return 0.0 for empty evidence."""
        from bce.ai.question_answering import _calculate_confidence

        result = _calculate_confidence([])
        assert result == 0.0

    def test_calculate_confidence_with_evidence(self):
        """Should calculate confidence based on evidence amount."""
        from bce.ai.question_answering import _calculate_confidence

        evidence = [{"data": i} for i in range(5)]
        result = _calculate_confidence(evidence)
        assert 0.0 < result <= 1.0

    def test_calculate_confidence_with_references(self):
        """Should boost confidence for evidence with references."""
        from bce.ai.question_answering import _calculate_confidence

        evidence = [
            {"reference": "John 1:1"},
            {"reference": "Mark 1:1"},
        ]

        result = _calculate_confidence(evidence)
        assert result > 0.5


class TestIntegration:
    """Integration tests for full ask() function."""

    def setup_method(self):
        """Setup for each test."""
        reset_default_config()

    def test_ask_full_pipeline(self):
        """Test full ask pipeline with mocked dependencies."""
        from bce.ai import question_answering

        with tempfile.TemporaryDirectory() as tmpdir:
            config = BceConfig(
                enable_ai_features=True,
                ai_cache_dir=Path(tmpdir)
            )
            set_default_config(config)

            # Mock semantic search
            with patch("bce.ai.semantic_search.query") as mock_search:
                mock_search.return_value = []

                result = question_answering.ask(
                    "What is Paul's role?",
                    use_cache=False
                )

                assert "answer" in result
                assert "confidence" in result
                assert "evidence" in result
                assert "comparison" in result
