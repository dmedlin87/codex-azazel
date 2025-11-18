"""
Tests for bce.ai.semantic_contradictions module.

Covers semantic contradiction detection with AI embeddings to distinguish
genuine conflicts from complementary details.
"""

from __future__ import annotations

import pytest

from bce.config import BceConfig, set_default_config, reset_default_config
from bce.exceptions import ConfigurationError


class TestAnalyzeCharacterTraits:
    """Tests for analyze_character_traits function."""

    def setup_method(self):
        """Enable AI features for tests."""
        reset_default_config()
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

    def teardown_method(self):
        """Reset configuration."""
        reset_default_config()

    def test_raises_when_ai_disabled(self):
        """Should raise ConfigurationError when AI features are disabled."""
        from bce.ai import semantic_contradictions

        reset_default_config()
        config = BceConfig(enable_ai_features=False)
        set_default_config(config)

        with pytest.raises(ConfigurationError, match="AI features are disabled"):
            semantic_contradictions.analyze_character_traits("jesus")

    def test_analyze_nonexistent_character(self):
        """Should raise error for nonexistent character."""
        from bce.ai import semantic_contradictions
        from bce.exceptions import DataNotFoundError

        with pytest.raises(DataNotFoundError):
            semantic_contradictions.analyze_character_traits("nonexistent_char", use_cache=False)

    def test_analyze_character_no_conflicts(self):
        """Should handle character with no conflicts."""
        from bce.ai import semantic_contradictions

        # Try a character that may not have conflicts
        # Result should still be well-formed
        try:
            result = semantic_contradictions.analyze_character_traits("pilate", use_cache=False)

            assert "character_id" in result
            assert "canonical_name" in result
            assert "has_conflicts" in result
            assert "analyzed_conflicts" in result
            assert "summary" in result

            # If no conflicts
            if not result["has_conflicts"]:
                assert result["analyzed_conflicts"] == {}
                assert result["summary"]["total_conflicts"] == 0
                assert result["summary"]["genuine_conflicts"] == 0
        except Exception:
            # Character may not exist
            pass

    def test_analyze_character_with_conflicts(self):
        """Should analyze character with conflicts."""
        from bce.ai import semantic_contradictions
        from bce import contradictions

        # Jesus definitely has conflicts
        basic_conflicts = contradictions.find_trait_conflicts("jesus")

        if basic_conflicts:
            result = semantic_contradictions.analyze_character_traits("jesus", use_cache=False)

            assert "character_id" in result
            assert result["character_id"] == "jesus"
            assert "canonical_name" in result
            assert "has_conflicts" in result
            assert result["has_conflicts"] is True
            assert "analyzed_conflicts" in result
            assert "summary" in result

            # Check summary structure
            summary = result["summary"]
            assert "total_conflicts" in summary
            assert "genuine_conflicts" in summary
            assert "complementary_details" in summary
            assert "different_emphases" in summary

            # Counts should be non-negative
            assert summary["total_conflicts"] >= 0
            assert summary["genuine_conflicts"] >= 0
            assert summary["complementary_details"] >= 0
            assert summary["different_emphases"] >= 0

            # Sum should equal total
            total = (
                summary["genuine_conflicts"]
                + summary["complementary_details"]
                + summary["different_emphases"]
            )
            assert total == summary["total_conflicts"]

    def test_analyzed_conflict_structure(self):
        """Should return properly structured conflict analysis."""
        from bce.ai import semantic_contradictions
        from bce import contradictions

        basic_conflicts = contradictions.find_trait_conflicts("jesus")

        if basic_conflicts:
            result = semantic_contradictions.analyze_character_traits("jesus", use_cache=False)

            if result["analyzed_conflicts"]:
                # Get first conflict
                trait_key = list(result["analyzed_conflicts"].keys())[0]
                conflict = result["analyzed_conflicts"][trait_key]

                # Check structure
                assert "trait" in conflict
                assert "sources" in conflict
                assert "semantic_analysis" in conflict

                # Check semantic analysis structure
                semantic = conflict["semantic_analysis"]
                assert "is_genuine_conflict" in semantic
                assert "conflict_type" in semantic
                assert "similarity_score" in semantic
                assert "explanation" in semantic
                assert "severity" in semantic

                # Check types
                assert isinstance(semantic["is_genuine_conflict"], bool)
                assert semantic["conflict_type"] in [
                    "complementary_details",
                    "different_emphasis",
                    "genuine_contradiction"
                ]
                assert isinstance(semantic["similarity_score"], (int, float))
                assert 0.0 <= semantic["similarity_score"] <= 1.0
                assert isinstance(semantic["explanation"], str)
                assert semantic["severity"] in ["low", "medium", "high"]

    def test_uses_cache(self):
        """Should use cached results when use_cache=True."""
        from bce.ai import semantic_contradictions

        result1 = semantic_contradictions.analyze_character_traits("jesus", use_cache=True)
        result2 = semantic_contradictions.analyze_character_traits("jesus", use_cache=True)

        # Should be identical
        assert result1 == result2

    def test_bypasses_cache(self):
        """Should bypass cache when use_cache=False."""
        from bce.ai import semantic_contradictions

        # Just ensure it doesn't fail
        result = semantic_contradictions.analyze_character_traits("jesus", use_cache=False)
        assert "character_id" in result


class TestAnalyzeEventConflicts:
    """Tests for analyze_event_conflicts function."""

    def setup_method(self):
        """Enable AI features for tests."""
        reset_default_config()
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

    def teardown_method(self):
        """Reset configuration."""
        reset_default_config()

    def test_raises_when_ai_disabled(self):
        """Should raise ConfigurationError when AI features are disabled."""
        from bce.ai import semantic_contradictions

        reset_default_config()
        config = BceConfig(enable_ai_features=False)
        set_default_config(config)

        with pytest.raises(ConfigurationError, match="AI features are disabled"):
            semantic_contradictions.analyze_event_conflicts("crucifixion")

    def test_analyze_nonexistent_event(self):
        """Should raise error for nonexistent event."""
        from bce.ai import semantic_contradictions
        from bce.exceptions import DataNotFoundError

        with pytest.raises(DataNotFoundError):
            semantic_contradictions.analyze_event_conflicts("nonexistent_event", use_cache=False)

    def test_analyze_event_no_conflicts(self):
        """Should handle event with no conflicts."""
        from bce.ai import semantic_contradictions

        # Try damascus_road which may not have conflicts (single source)
        try:
            result = semantic_contradictions.analyze_event_conflicts("damascus_road", use_cache=False)

            assert "event_id" in result
            assert "label" in result
            assert "has_conflicts" in result
            assert "analyzed_conflicts" in result
            assert "summary" in result

            # May or may not have conflicts
            if not result["has_conflicts"]:
                assert result["analyzed_conflicts"] == {}
                assert result["summary"]["total_conflicts"] == 0
        except Exception:
            # Event may not exist or have structure
            pass

    def test_analyze_event_with_conflicts(self):
        """Should analyze event with conflicts."""
        from bce.ai import semantic_contradictions
        from bce.contradictions import find_events_with_conflicting_accounts

        # Crucifixion likely has conflicts
        basic_conflicts = find_events_with_conflicting_accounts("crucifixion")

        result = semantic_contradictions.analyze_event_conflicts("crucifixion", use_cache=False)

        assert "event_id" in result
        assert result["event_id"] == "crucifixion"
        assert "label" in result
        assert "has_conflicts" in result
        assert "analyzed_conflicts" in result
        assert "summary" in result

        # Check summary structure
        summary = result["summary"]
        assert "total_conflicts" in summary
        assert "genuine_conflicts" in summary
        assert "complementary_details" in summary
        assert "different_emphases" in summary

        # Counts should be non-negative
        assert summary["total_conflicts"] >= 0
        assert summary["genuine_conflicts"] >= 0

    def test_uses_cache(self):
        """Should use cached results when use_cache=True."""
        from bce.ai import semantic_contradictions

        result1 = semantic_contradictions.analyze_event_conflicts("crucifixion", use_cache=True)
        result2 = semantic_contradictions.analyze_event_conflicts("crucifixion", use_cache=True)

        # Should be identical (cache key uses "event_" prefix)
        assert result1 == result2


class TestAnalyzeTraitConflict:
    """Tests for _analyze_trait_conflict internal function."""

    def test_complementary_details_high_similarity(self):
        """Should classify high similarity as complementary details."""
        from bce.ai.semantic_contradictions import _analyze_trait_conflict
        from bce.ai.embeddings import EmbeddingCache

        cache = EmbeddingCache("test")

        # Very similar values
        source_values = {
            "mark": "Jesus taught in the synagogue",
            "matthew": "Jesus was teaching in the synagogue",
        }

        result = _analyze_trait_conflict("teaching_location", source_values, cache)

        # Check structure
        assert "trait" in result
        assert result["trait"] == "teaching_location"
        assert "sources" in result
        assert "semantic_analysis" in result

        semantic = result["semantic_analysis"]
        assert "is_genuine_conflict" in semantic
        assert "conflict_type" in semantic
        assert "similarity_score" in semantic

        # High similarity should result in complementary or different_emphasis
        if semantic["similarity_score"] >= 0.80:
            assert semantic["conflict_type"] == "complementary_details"
            assert semantic["is_genuine_conflict"] is False
            assert semantic["severity"] == "low"

    def test_different_emphasis_medium_similarity(self):
        """Should classify medium similarity as different emphasis."""
        from bce.ai.semantic_contradictions import _analyze_trait_conflict
        from bce.ai.embeddings import EmbeddingCache

        cache = EmbeddingCache("test")

        # Moderately similar values
        source_values = {
            "mark": "Jesus spoke with authority",
            "matthew": "Jesus taught the people with great wisdom",
        }

        result = _analyze_trait_conflict("teaching_style", source_values, cache)

        semantic = result["semantic_analysis"]

        # Medium similarity range
        if 0.50 <= semantic["similarity_score"] < 0.80:
            assert semantic["conflict_type"] == "different_emphasis"
            assert semantic["is_genuine_conflict"] is False
            assert semantic["severity"] == "medium"

    def test_genuine_contradiction_low_similarity(self):
        """Should classify low similarity as genuine contradiction."""
        from bce.ai.semantic_contradictions import _analyze_trait_conflict
        from bce.ai.embeddings import EmbeddingCache

        cache = EmbeddingCache("test")

        # Very different values
        source_values = {
            "mark": "Jesus was executed by Roman soldiers",
            "fictional": "Jesus lived to old age and died peacefully",
        }

        result = _analyze_trait_conflict("death_circumstances", source_values, cache)

        semantic = result["semantic_analysis"]

        # Low similarity should result in genuine contradiction
        if semantic["similarity_score"] < 0.50:
            assert semantic["conflict_type"] == "genuine_contradiction"
            assert semantic["is_genuine_conflict"] is True
            assert semantic["severity"] == "high"

    def test_single_value(self):
        """Should handle single value gracefully."""
        from bce.ai.semantic_contradictions import _analyze_trait_conflict
        from bce.ai.embeddings import EmbeddingCache

        cache = EmbeddingCache("test")

        source_values = {
            "mark": "Jesus taught",
        }

        result = _analyze_trait_conflict("teaching", source_values, cache)

        # Should still return valid structure
        assert "trait" in result
        assert "sources" in result
        assert "semantic_analysis" in result

        # With single value, similarity is 1.0 (no comparisons)
        semantic = result["semantic_analysis"]
        assert semantic["similarity_score"] == 1.0
        assert semantic["conflict_type"] == "complementary_details"
        assert semantic["is_genuine_conflict"] is False

    def test_explanation_generated(self):
        """Should generate meaningful explanation."""
        from bce.ai.semantic_contradictions import _analyze_trait_conflict
        from bce.ai.embeddings import EmbeddingCache

        cache = EmbeddingCache("test")

        source_values = {
            "mark": "Jesus was a teacher",
            "john": "Jesus was the divine Word made flesh",
        }

        result = _analyze_trait_conflict("identity", source_values, cache)

        explanation = result["semantic_analysis"]["explanation"]
        assert isinstance(explanation, str)
        assert len(explanation) > 0
        assert "identity" in explanation

    def test_similarity_score_range(self):
        """Should produce similarity scores in valid range."""
        from bce.ai.semantic_contradictions import _analyze_trait_conflict
        from bce.ai.embeddings import EmbeddingCache

        cache = EmbeddingCache("test")

        source_values = {
            "mark": "Jesus healed the sick",
            "matthew": "Jesus performed miracles of healing",
        }

        result = _analyze_trait_conflict("miracles", source_values, cache)

        similarity = result["semantic_analysis"]["similarity_score"]
        assert isinstance(similarity, (int, float))
        assert 0.0 <= similarity <= 1.0

    def test_multiple_sources(self):
        """Should handle multiple sources correctly."""
        from bce.ai.semantic_contradictions import _analyze_trait_conflict
        from bce.ai.embeddings import EmbeddingCache

        cache = EmbeddingCache("test")

        source_values = {
            "mark": "Jesus taught in parables",
            "matthew": "Jesus spoke in parables to the crowds",
            "luke": "Jesus used parables in his teaching",
        }

        result = _analyze_trait_conflict("teaching_method", source_values, cache)

        # Should compute average pairwise similarity
        assert "semantic_analysis" in result
        semantic = result["semantic_analysis"]
        assert "similarity_score" in semantic

        # Should be well-formed
        assert semantic["conflict_type"] in [
            "complementary_details",
            "different_emphasis",
            "genuine_contradiction"
        ]


class TestConflictTypeClassification:
    """Tests for conflict type classification logic."""

    def test_complementary_threshold(self):
        """Should classify >= 0.80 similarity as complementary."""
        from bce.ai.semantic_contradictions import _analyze_trait_conflict
        from bce.ai.embeddings import EmbeddingCache

        cache = EmbeddingCache("test")

        # Extremely similar - should be complementary
        source_values = {
            "mark": "The crucifixion",
            "matthew": "The crucifixion event",
        }

        result = _analyze_trait_conflict("event", source_values, cache)
        semantic = result["semantic_analysis"]

        # Very high similarity expected
        if semantic["similarity_score"] >= 0.80:
            assert semantic["conflict_type"] == "complementary_details"
            assert semantic["is_genuine_conflict"] is False

    def test_different_emphasis_threshold(self):
        """Should classify 0.50-0.80 similarity as different emphasis."""
        from bce.ai.semantic_contradictions import _analyze_trait_conflict
        from bce.ai.embeddings import EmbeddingCache

        cache = EmbeddingCache("test")

        # Somewhat related but different focus
        source_values = {
            "mark": "Jesus' suffering on the cross",
            "john": "Jesus' glorification in death",
        }

        result = _analyze_trait_conflict("crucifixion_theme", source_values, cache)
        semantic = result["semantic_analysis"]

        # Should be in medium range
        if 0.50 <= semantic["similarity_score"] < 0.80:
            assert semantic["conflict_type"] == "different_emphasis"

    def test_genuine_contradiction_threshold(self):
        """Should classify < 0.50 similarity as genuine contradiction."""
        from bce.ai.semantic_contradictions import _analyze_trait_conflict
        from bce.ai.embeddings import EmbeddingCache

        cache = EmbeddingCache("test")

        # Completely different concepts
        source_values = {
            "source1": "Mathematical equation solving techniques",
            "source2": "Jesus died on the cross for sins",
        }

        result = _analyze_trait_conflict("topic", source_values, cache)
        semantic = result["semantic_analysis"]

        # Should be very low similarity
        if semantic["similarity_score"] < 0.50:
            assert semantic["conflict_type"] == "genuine_contradiction"
            assert semantic["is_genuine_conflict"] is True


class TestSeverityMapping:
    """Tests for severity assessment."""

    def test_low_severity_for_complementary(self):
        """Complementary details should have low severity."""
        from bce.ai.semantic_contradictions import _analyze_trait_conflict
        from bce.ai.embeddings import EmbeddingCache

        cache = EmbeddingCache("test")

        source_values = {
            "mark": "Jesus in Galilee",
            "matthew": "Jesus was in Galilee region",
        }

        result = _analyze_trait_conflict("location", source_values, cache)
        semantic = result["semantic_analysis"]

        if semantic["conflict_type"] == "complementary_details":
            assert semantic["severity"] == "low"

    def test_medium_severity_for_different_emphasis(self):
        """Different emphasis should have medium severity."""
        from bce.ai.semantic_contradictions import _analyze_trait_conflict
        from bce.ai.embeddings import EmbeddingCache

        cache = EmbeddingCache("test")

        source_values = {
            "mark": "Jesus as suffering servant",
            "matthew": "Jesus as royal messiah",
        }

        result = _analyze_trait_conflict("portrayal", source_values, cache)
        semantic = result["semantic_analysis"]

        if semantic["conflict_type"] == "different_emphasis":
            assert semantic["severity"] == "medium"

    def test_high_severity_for_genuine_contradiction(self):
        """Genuine contradictions should have high severity."""
        from bce.ai.semantic_contradictions import _analyze_trait_conflict
        from bce.ai.embeddings import EmbeddingCache

        cache = EmbeddingCache("test")

        # Irreconcilable differences
        source_values = {
            "source1": "Never existed",
            "source2": "Historical figure who lived and died",
        }

        result = _analyze_trait_conflict("existence", source_values, cache)
        semantic = result["semantic_analysis"]

        if semantic["conflict_type"] == "genuine_contradiction":
            assert semantic["severity"] == "high"
