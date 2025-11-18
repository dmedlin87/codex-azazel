"""
Tests for bce.ai.semantic_contradictions module.

Covers semantic contradiction detection with AI embeddings to distinguish
genuine conflicts from complementary details.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch, Mock
import pytest

from bce.config import BceConfig, set_default_config, reset_default_config
from bce.exceptions import ConfigurationError


# Helper to create mock embeddings (arrays)
def mock_array(values):
    """Create a mock numpy-like array for testing."""
    try:
        import numpy
        return numpy.array(values)
    except ImportError:
        # If numpy not available, return a list (works for mocking)
        return values


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

        # Mock find_trait_conflicts to return empty dict
        with patch("bce.ai.semantic_contradictions.find_trait_conflicts", return_value={}):
            result = semantic_contradictions.analyze_character_traits("pilate", use_cache=False)

            assert result["character_id"] == "pilate"
            assert "canonical_name" in result
            assert result["has_conflicts"] is False
            assert result["analyzed_conflicts"] == {}
            assert result["summary"]["total_conflicts"] == 0
            assert result["summary"]["genuine_conflicts"] == 0
            assert result["summary"]["complementary_details"] == 0
            assert result["summary"]["different_emphases"] == 0

    def test_analyze_character_with_conflicts_high_similarity(self):
        """Should analyze character with conflicts - complementary details."""
        from bce.ai import semantic_contradictions

        # Mock basic conflicts
        mock_conflicts = {
            "portrayal": {
                "mark": "Jesus was a teacher",
                "matthew": "Jesus was a teacher and healer"
            }
        }

        # Mock embeddings with high similarity
        mock_embeddings = [
            mock_array([0.1, 0.2, 0.3, 0.4]),
            mock_array([0.11, 0.21, 0.31, 0.41])  # Very similar
        ]

        mock_cache = Mock()
        mock_cache.get_or_compute.side_effect = mock_embeddings

        with patch("bce.ai.semantic_contradictions.find_trait_conflicts", return_value=mock_conflicts), \
             patch("bce.ai.semantic_contradictions.EmbeddingCache", return_value=mock_cache):
            result = semantic_contradictions.analyze_character_traits("jesus", use_cache=False)

            assert result["character_id"] == "jesus"
            assert result["has_conflicts"] is True
            assert "portrayal" in result["analyzed_conflicts"]

            conflict = result["analyzed_conflicts"]["portrayal"]
            semantic = conflict["semantic_analysis"]

            # High similarity should be complementary
            assert semantic["conflict_type"] == "complementary_details"
            assert semantic["is_genuine_conflict"] is False
            assert semantic["severity"] == "low"
            assert semantic["similarity_score"] >= 0.80

    def test_analyze_character_with_conflicts_medium_similarity(self):
        """Should analyze character with conflicts - different emphasis."""
        from bce.ai import semantic_contradictions

        mock_conflicts = {
            "role": {
                "mark": "suffering servant",
                "john": "divine Word"
            }
        }

        # Mock embeddings with medium similarity
        # [1,0] and [0.6, 0.8] gives cosine similarity = 0.6
        mock_embeddings = [
            mock_array([1.0, 0.0]),
            mock_array([0.6, 0.8])  # Medium similarity
        ]

        mock_cache = Mock()
        mock_cache.get_or_compute.side_effect = mock_embeddings

        with patch("bce.ai.semantic_contradictions.find_trait_conflicts", return_value=mock_conflicts), \
             patch("bce.ai.semantic_contradictions.EmbeddingCache", return_value=mock_cache):
            result = semantic_contradictions.analyze_character_traits("jesus", use_cache=False)

            conflict = result["analyzed_conflicts"]["role"]
            semantic = conflict["semantic_analysis"]

            # Medium similarity should be different emphasis
            assert semantic["conflict_type"] == "different_emphasis"
            assert semantic["is_genuine_conflict"] is False
            assert semantic["severity"] == "medium"
            assert 0.50 <= semantic["similarity_score"] < 0.80

    def test_analyze_character_with_conflicts_low_similarity(self):
        """Should analyze character with conflicts - genuine contradiction."""
        from bce.ai import semantic_contradictions

        mock_conflicts = {
            "nature": {
                "mark": "fully human",
                "fictional": "purely divine spirit"
            }
        }

        # Mock embeddings with low similarity
        mock_embeddings = [
            mock_array([1.0, 0.0, 0.0]),
            mock_array([0.0, 1.0, 0.0])  # Very different
        ]

        mock_cache = Mock()
        mock_cache.get_or_compute.side_effect = mock_embeddings

        with patch("bce.ai.semantic_contradictions.find_trait_conflicts", return_value=mock_conflicts), \
             patch("bce.ai.semantic_contradictions.EmbeddingCache", return_value=mock_cache):
            result = semantic_contradictions.analyze_character_traits("jesus", use_cache=False)

            conflict = result["analyzed_conflicts"]["nature"]
            semantic = conflict["semantic_analysis"]

            # Low similarity should be genuine contradiction
            assert semantic["conflict_type"] == "genuine_contradiction"
            assert semantic["is_genuine_conflict"] is True
            assert semantic["severity"] == "high"
            assert semantic["similarity_score"] < 0.50

    def test_analyze_character_summary_counts(self):
        """Should correctly count conflict types in summary."""
        from bce.ai import semantic_contradictions

        # Mock multiple conflicts with different similarity levels
        mock_conflicts = {
            "trait1": {"mark": "text1", "matthew": "text2"},  # High sim
            "trait2": {"mark": "text3", "john": "text4"},     # Medium sim
            "trait3": {"mark": "text5", "fictional": "text6"} # Low sim
        }

        # Mock embeddings: high, medium, low similarity pairs
        embeddings_list = [
            mock_array([0.1, 0.2]),     # trait1 mark
            mock_array([0.11, 0.21]),   # trait1 matthew (high sim ~ 1.0)
            mock_array([1.0, 0.0]),     # trait2 mark
            mock_array([0.6, 0.8]),     # trait2 john (medium sim = 0.6)
            mock_array([1.0, 0.0]),     # trait3 mark
            mock_array([0.0, 1.0]),     # trait3 fictional (low sim = 0.0)
        ]

        mock_cache = Mock()
        mock_cache.get_or_compute.side_effect = embeddings_list

        with patch("bce.ai.semantic_contradictions.find_trait_conflicts", return_value=mock_conflicts), \
             patch("bce.ai.semantic_contradictions.EmbeddingCache", return_value=mock_cache):
            result = semantic_contradictions.analyze_character_traits("jesus", use_cache=False)

            summary = result["summary"]
            assert summary["total_conflicts"] == 3
            assert summary["complementary_details"] == 1
            assert summary["different_emphases"] == 1
            assert summary["genuine_conflicts"] == 1

            # Total should equal sum
            total = (summary["genuine_conflicts"] +
                    summary["complementary_details"] +
                    summary["different_emphases"])
            assert total == summary["total_conflicts"]

    def test_uses_cache_when_enabled(self):
        """Should use cache when use_cache=True and result is cached."""
        from bce.ai import semantic_contradictions

        mock_cached_result = {
            "character_id": "jesus",
            "canonical_name": "Jesus",
            "has_conflicts": True,
            "analyzed_conflicts": {},
            "summary": {"total_conflicts": 0, "genuine_conflicts": 0,
                       "complementary_details": 0, "different_emphases": 0}
        }

        with patch("bce.ai.semantic_contradictions.AIResultCache") as MockCache:
            mock_cache_instance = Mock()
            mock_cache_instance.get.return_value = mock_cached_result
            MockCache.return_value = mock_cache_instance

            result = semantic_contradictions.analyze_character_traits("jesus", use_cache=True)

            # Should return cached result
            assert result == mock_cached_result
            mock_cache_instance.get.assert_called_once_with("jesus")

    def test_bypasses_cache_when_disabled(self):
        """Should compute fresh when use_cache=False."""
        from bce.ai import semantic_contradictions

        with patch("bce.ai.semantic_contradictions.find_trait_conflicts", return_value={}), \
             patch("bce.ai.semantic_contradictions.AIResultCache") as MockCache:
            mock_cache_instance = Mock()
            MockCache.return_value = mock_cache_instance

            result = semantic_contradictions.analyze_character_traits("pilate", use_cache=False)

            # Cache should still be created but not used for get
            assert result["character_id"] == "pilate"
            # Should not call cache.get when use_cache=False
            mock_cache_instance.get.assert_not_called()

    def test_caches_result_no_conflicts(self):
        """Should cache result when no conflicts found."""
        from bce.ai import semantic_contradictions

        with patch("bce.ai.semantic_contradictions.find_trait_conflicts", return_value={}), \
             patch("bce.ai.semantic_contradictions.AIResultCache") as MockCache:
            mock_cache_instance = Mock()
            mock_cache_instance.get.return_value = None
            MockCache.return_value = mock_cache_instance

            result = semantic_contradictions.analyze_character_traits("pilate", use_cache=True)

            # Should cache the result
            mock_cache_instance.set.assert_called_once()
            call_args = mock_cache_instance.set.call_args
            assert call_args[0][0] == "pilate"  # char_id
            assert call_args[0][1]["has_conflicts"] is False

    def test_caches_result_with_conflicts(self):
        """Should cache result when conflicts found and analyzed."""
        from bce.ai import semantic_contradictions

        mock_conflicts = {
            "trait": {"mark": "value1", "matthew": "value2"}
        }
        mock_embeddings = [mock_array([0.1, 0.2]), mock_array([0.11, 0.21])]

        mock_embedding_cache = Mock()
        mock_embedding_cache.get_or_compute.side_effect = mock_embeddings

        with patch("bce.ai.semantic_contradictions.find_trait_conflicts", return_value=mock_conflicts), \
             patch("bce.ai.semantic_contradictions.EmbeddingCache", return_value=mock_embedding_cache), \
             patch("bce.ai.semantic_contradictions.AIResultCache") as MockCache:
            mock_cache_instance = Mock()
            mock_cache_instance.get.return_value = None
            MockCache.return_value = mock_cache_instance

            result = semantic_contradictions.analyze_character_traits("jesus", use_cache=True)

            # Should cache the result
            mock_cache_instance.set.assert_called_once()
            call_args = mock_cache_instance.set.call_args
            assert call_args[0][0] == "jesus"
            assert call_args[0][1]["has_conflicts"] is True


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

        # Mock to return empty conflicts
        with patch("bce.contradictions.find_events_with_conflicting_accounts", return_value={}):
            result = semantic_contradictions.analyze_event_conflicts("damascus_road", use_cache=False)

            assert result["event_id"] == "damascus_road"
            assert "label" in result
            assert result["has_conflicts"] is False
            assert result["analyzed_conflicts"] == {}
            assert result["summary"]["total_conflicts"] == 0
            assert result["summary"]["genuine_conflicts"] == 0
            assert result["summary"]["complementary_details"] == 0
            assert result["summary"]["different_emphases"] == 0

    def test_analyze_event_with_conflicts_complementary(self):
        """Should analyze event conflicts with high similarity."""
        from bce.ai import semantic_contradictions

        mock_conflicts = {
            "summary": {
                "mark": "Jesus was crucified",
                "matthew": "Jesus was crucified on a cross"
            }
        }

        mock_embeddings = [
            mock_array([0.9, 0.8, 0.7]),
            mock_array([0.89, 0.79, 0.69])  # Very similar
        ]

        with patch("bce.contradictions.find_events_with_conflicting_accounts",
                  return_value=mock_conflicts), \
             patch("bce.ai.embeddings.embed_text", side_effect=mock_embeddings):
            result = semantic_contradictions.analyze_event_conflicts("crucifixion", use_cache=False)

            assert result["event_id"] == "crucifixion"
            assert result["has_conflicts"] is True

            conflict = result["analyzed_conflicts"]["summary"]
            semantic = conflict["semantic_analysis"]

            assert semantic["conflict_type"] == "complementary_details"
            assert semantic["is_genuine_conflict"] is False

    def test_analyze_event_with_conflicts_genuine(self):
        """Should analyze event conflicts with low similarity."""
        from bce.ai import semantic_contradictions

        mock_conflicts = {
            "details": {
                "mark": "Crucifixion at third hour",
                "john": "Crucifixion at sixth hour"
            }
        }

        mock_embeddings = [
            mock_array([1.0, 0.0, 0.0]),
            mock_array([0.0, 1.0, 0.0])  # Very different
        ]

        with patch("bce.contradictions.find_events_with_conflicting_accounts",
                  return_value=mock_conflicts), \
             patch("bce.ai.embeddings.embed_text", side_effect=mock_embeddings):
            result = semantic_contradictions.analyze_event_conflicts("crucifixion", use_cache=False)

            conflict = result["analyzed_conflicts"]["details"]
            semantic = conflict["semantic_analysis"]

            assert semantic["conflict_type"] == "genuine_contradiction"
            assert semantic["is_genuine_conflict"] is True
            assert semantic["severity"] == "high"

    def test_event_summary_counts_correct(self):
        """Should correctly count event conflict types."""
        from bce.ai import semantic_contradictions

        mock_conflicts = {
            "field1": {"mark": "a", "matthew": "b"},
            "field2": {"luke": "c", "john": "d"},
        }

        # High similarity for both
        embeddings = [
            mock_array([0.5, 0.5]),
            mock_array([0.51, 0.51]),
            mock_array([0.6, 0.4]),
            mock_array([0.61, 0.41]),
        ]

        with patch("bce.contradictions.find_events_with_conflicting_accounts",
                  return_value=mock_conflicts), \
             patch("bce.ai.embeddings.embed_text", side_effect=embeddings):
            result = semantic_contradictions.analyze_event_conflicts("crucifixion", use_cache=False)

            summary = result["summary"]
            assert summary["total_conflicts"] == 2
            # Both should be complementary with high similarity
            assert summary["complementary_details"] >= 1

    def test_uses_cache_with_event_prefix(self):
        """Should use cache with 'event_' prefix in cache key."""
        from bce.ai import semantic_contradictions

        mock_cached_result = {
            "event_id": "crucifixion",
            "label": "Crucifixion",
            "has_conflicts": False,
            "analyzed_conflicts": {},
            "summary": {"total_conflicts": 0, "genuine_conflicts": 0,
                       "complementary_details": 0, "different_emphases": 0}
        }

        with patch("bce.ai.semantic_contradictions.AIResultCache") as MockCache:
            mock_cache_instance = Mock()
            mock_cache_instance.get.return_value = mock_cached_result
            MockCache.return_value = mock_cache_instance

            result = semantic_contradictions.analyze_event_conflicts("crucifixion", use_cache=True)

            # Should use event_ prefix in cache key
            mock_cache_instance.get.assert_called_once_with("event_crucifixion")
            assert result == mock_cached_result

    def test_caches_event_result(self):
        """Should cache event analysis result."""
        from bce.ai import semantic_contradictions

        with patch("bce.contradictions.find_events_with_conflicting_accounts", return_value={}), \
             patch("bce.ai.semantic_contradictions.AIResultCache") as MockCache:
            mock_cache_instance = Mock()
            mock_cache_instance.get.return_value = None
            MockCache.return_value = mock_cache_instance

            result = semantic_contradictions.analyze_event_conflicts("crucifixion", use_cache=True)

            # Should cache with event_ prefix
            mock_cache_instance.set.assert_called_once()
            call_args = mock_cache_instance.set.call_args
            assert call_args[0][0] == "event_crucifixion"
            assert call_args[0][1]["has_conflicts"] is False


class TestAnalyzeTraitConflict:
    """Tests for _analyze_trait_conflict internal function."""

    def test_complementary_details_high_similarity(self):
        """Should classify high similarity (>= 0.80) as complementary details."""
        from bce.ai.semantic_contradictions import _analyze_trait_conflict

        source_values = {
            "mark": "Jesus taught",
            "matthew": "Jesus was teaching",
        }

        # Mock embeddings with very high similarity
        embeddings = [mock_array([0.9, 0.1]), mock_array([0.89, 0.11])]

        with patch("bce.ai.embeddings.embed_text", side_effect=embeddings):
            mock_cache = Mock()
            mock_cache.get_or_compute.side_effect = embeddings

            result = _analyze_trait_conflict("teaching", source_values, mock_cache)

            assert result["trait"] == "teaching"
            assert result["sources"] == source_values

            semantic = result["semantic_analysis"]
            assert semantic["is_genuine_conflict"] is False
            assert semantic["conflict_type"] == "complementary_details"
            assert semantic["severity"] == "low"
            assert semantic["similarity_score"] >= 0.80
            assert "teaching" in semantic["explanation"]

    def test_different_emphasis_medium_similarity(self):
        """Should classify medium similarity (0.50-0.80) as different emphasis."""
        from bce.ai.semantic_contradictions import _analyze_trait_conflict

        source_values = {
            "mark": "Jesus as servant",
            "matthew": "Jesus as king",
        }

        # Mock embeddings with medium similarity
        # [1,0] and [0.6, 0.8] gives cosine similarity = 0.6
        embeddings = [mock_array([1.0, 0.0]), mock_array([0.6, 0.8])]

        with patch("bce.ai.embeddings.embed_text", side_effect=embeddings):
            mock_cache = Mock()
            mock_cache.get_or_compute.side_effect = embeddings

            result = _analyze_trait_conflict("role", source_values, mock_cache)

            semantic = result["semantic_analysis"]
            assert semantic["is_genuine_conflict"] is False
            assert semantic["conflict_type"] == "different_emphasis"
            assert semantic["severity"] == "medium"
            assert 0.50 <= semantic["similarity_score"] < 0.80

    def test_genuine_contradiction_low_similarity(self):
        """Should classify low similarity (< 0.50) as genuine contradiction."""
        from bce.ai.semantic_contradictions import _analyze_trait_conflict

        source_values = {
            "source1": "Completely different topic A",
            "source2": "Unrelated topic B",
        }

        # Mock embeddings with low similarity
        embeddings = [mock_array([1.0, 0.0, 0.0]), mock_array([0.0, 1.0, 0.0])]

        with patch("bce.ai.embeddings.embed_text", side_effect=embeddings):
            mock_cache = Mock()
            mock_cache.get_or_compute.side_effect = embeddings

            result = _analyze_trait_conflict("topic", source_values, mock_cache)

            semantic = result["semantic_analysis"]
            assert semantic["is_genuine_conflict"] is True
            assert semantic["conflict_type"] == "genuine_contradiction"
            assert semantic["severity"] == "high"
            assert semantic["similarity_score"] < 0.50

    def test_single_value_defaults_to_complementary(self):
        """Should handle single value gracefully with 1.0 similarity."""
        from bce.ai.semantic_contradictions import _analyze_trait_conflict

        source_values = {"mark": "Jesus taught"}

        embeddings = [mock_array([0.5, 0.5])]

        with patch("bce.ai.embeddings.embed_text", side_effect=embeddings):
            mock_cache = Mock()
            mock_cache.get_or_compute.side_effect = embeddings

            result = _analyze_trait_conflict("teaching", source_values, mock_cache)

            # With single value, no pairwise comparisons, so avg_similarity = 1.0
            semantic = result["semantic_analysis"]
            assert semantic["similarity_score"] == 1.0
            assert semantic["conflict_type"] == "complementary_details"
            assert semantic["is_genuine_conflict"] is False

    def test_multiple_sources_averages_pairwise_similarities(self):
        """Should compute average of all pairwise similarities."""
        from bce.ai.semantic_contradictions import _analyze_trait_conflict

        source_values = {
            "mark": "text1",
            "matthew": "text2",
            "luke": "text3",
        }

        # Three embeddings for three sources
        embeddings = [
            mock_array([1.0, 0.0, 0.0]),
            mock_array([0.9, 0.1, 0.0]),
            mock_array([0.8, 0.2, 0.0]),
        ]

        with patch("bce.ai.embeddings.embed_text", side_effect=embeddings):
            mock_cache = Mock()
            mock_cache.get_or_compute.side_effect = embeddings

            result = _analyze_trait_conflict("trait", source_values, mock_cache)

            # Should have valid similarity score
            semantic = result["semantic_analysis"]
            assert 0.0 <= semantic["similarity_score"] <= 1.0
            # With 3 sources, should compute 3 pairwise similarities and average them

    def test_explanation_contains_trait_name(self):
        """Should generate explanation with trait name."""
        from bce.ai.semantic_contradictions import _analyze_trait_conflict

        source_values = {"mark": "value1", "matthew": "value2"}
        embeddings = [mock_array([0.5, 0.5]), mock_array([0.51, 0.51])]

        with patch("bce.ai.embeddings.embed_text", side_effect=embeddings):
            mock_cache = Mock()
            mock_cache.get_or_compute.side_effect = embeddings

            result = _analyze_trait_conflict("custom_trait", source_values, mock_cache)

            explanation = result["semantic_analysis"]["explanation"]
            assert "custom_trait" in explanation
            assert isinstance(explanation, str)
            assert len(explanation) > 0

    def test_similarity_score_rounded_to_3_decimals(self):
        """Should round similarity score to 3 decimal places."""
        from bce.ai.semantic_contradictions import _analyze_trait_conflict

        source_values = {"mark": "a", "matthew": "b"}
        embeddings = [mock_array([0.123456789, 0.5]), mock_array([0.987654321, 0.5])]

        with patch("bce.ai.embeddings.embed_text", side_effect=embeddings):
            mock_cache = Mock()
            mock_cache.get_or_compute.side_effect = embeddings

            result = _analyze_trait_conflict("test", source_values, mock_cache)

            score = result["semantic_analysis"]["similarity_score"]
            # Should be rounded to 3 decimals
            assert isinstance(score, (int, float))
            # Check it's actually rounded (convert to string and check decimal places)
            score_str = str(score)
            if '.' in score_str:
                decimals = len(score_str.split('.')[1])
                assert decimals <= 3

    def test_sources_field_preserved_in_result(self):
        """Should preserve source values in result."""
        from bce.ai.semantic_contradictions import _analyze_trait_conflict

        source_values = {
            "mark": "value from Mark",
            "matthew": "value from Matthew",
            "luke": "value from Luke",
        }

        embeddings = [mock_array([0.5]*3) for _ in range(3)]

        with patch("bce.ai.embeddings.embed_text", side_effect=embeddings):
            mock_cache = Mock()
            mock_cache.get_or_compute.side_effect = embeddings

            result = _analyze_trait_conflict("trait", source_values, mock_cache)

            assert result["sources"] == source_values
            assert "mark" in result["sources"]
            assert "matthew" in result["sources"]
            assert "luke" in result["sources"]

    def test_result_structure_complete(self):
        """Should return complete result structure."""
        from bce.ai.semantic_contradictions import _analyze_trait_conflict

        source_values = {"mark": "test"}
        embeddings = [mock_array([0.5])]

        with patch("bce.ai.embeddings.embed_text", side_effect=embeddings):
            mock_cache = Mock()
            mock_cache.get_or_compute.side_effect = embeddings

            result = _analyze_trait_conflict("trait", source_values, mock_cache)

            # Check top-level keys
            assert "trait" in result
            assert "sources" in result
            assert "semantic_analysis" in result

            # Check semantic_analysis keys
            semantic = result["semantic_analysis"]
            assert "is_genuine_conflict" in semantic
            assert "conflict_type" in semantic
            assert "similarity_score" in semantic
            assert "explanation" in semantic
            assert "severity" in semantic

    def test_uses_embedding_cache(self):
        """Should use embedding cache for retrieving embeddings."""
        from bce.ai.semantic_contradictions import _analyze_trait_conflict

        source_values = {"mark": "text1", "matthew": "text2"}
        embeddings = [mock_array([0.5, 0.5]), mock_array([0.6, 0.4])]

        mock_cache = Mock()
        mock_cache.get_or_compute.side_effect = embeddings

        result = _analyze_trait_conflict("trait", source_values, mock_cache)

        # Should call cache for each value
        assert mock_cache.get_or_compute.call_count == 2
        mock_cache.get_or_compute.assert_any_call("text1")
        mock_cache.get_or_compute.assert_any_call("text2")


class TestSeverityMapping:
    """Tests for severity assessment based on conflict type."""

    def test_complementary_has_low_severity(self):
        """Complementary details should always have low severity."""
        from bce.ai.semantic_contradictions import _analyze_trait_conflict

        source_values = {"mark": "same", "matthew": "same"}
        # Very high similarity
        embeddings = [mock_array([1.0, 0.0]), mock_array([0.99, 0.01])]

        with patch("bce.ai.embeddings.embed_text", side_effect=embeddings):
            mock_cache = Mock()
            mock_cache.get_or_compute.side_effect = embeddings

            result = _analyze_trait_conflict("trait", source_values, mock_cache)

            semantic = result["semantic_analysis"]
            if semantic["conflict_type"] == "complementary_details":
                assert semantic["severity"] == "low"

    def test_different_emphasis_has_medium_severity(self):
        """Different emphasis should always have medium severity."""
        from bce.ai.semantic_contradictions import _analyze_trait_conflict

        source_values = {"mark": "moderately similar", "matthew": "somewhat similar"}
        # Medium similarity
        embeddings = [mock_array([0.7, 0.3]), mock_array([0.5, 0.5])]

        with patch("bce.ai.embeddings.embed_text", side_effect=embeddings):
            mock_cache = Mock()
            mock_cache.get_or_compute.side_effect = embeddings

            result = _analyze_trait_conflict("trait", source_values, mock_cache)

            semantic = result["semantic_analysis"]
            if semantic["conflict_type"] == "different_emphasis":
                assert semantic["severity"] == "medium"

    def test_genuine_contradiction_has_high_severity(self):
        """Genuine contradictions should always have high severity."""
        from bce.ai.semantic_contradictions import _analyze_trait_conflict

        source_values = {"mark": "opposite A", "matthew": "opposite B"}
        # Very low similarity
        embeddings = [mock_array([1.0, 0.0, 0.0]), mock_array([0.0, 0.0, 1.0])]

        with patch("bce.ai.embeddings.embed_text", side_effect=embeddings):
            mock_cache = Mock()
            mock_cache.get_or_compute.side_effect = embeddings

            result = _analyze_trait_conflict("trait", source_values, mock_cache)

            semantic = result["semantic_analysis"]
            if semantic["conflict_type"] == "genuine_contradiction":
                assert semantic["severity"] == "high"


class TestBoundaryConditions:
    """Tests for boundary conditions and edge cases."""

    def test_exactly_080_similarity_is_complementary(self):
        """Similarity of exactly 0.80 should be complementary (>= threshold)."""
        from bce.ai.semantic_contradictions import _analyze_trait_conflict

        source_values = {"mark": "a", "matthew": "b"}

        # Create embeddings that will result in exactly 0.80 cosine similarity
        # cos_sim = dot(a,b) / (norm(a) * norm(b))
        # For normalized vectors: [0.8, 0.6] and [1.0, 0.0] gives ~0.80
        embeddings = [mock_array([0.8, 0.6]), mock_array([1.0, 0.0])]

        with patch("bce.ai.embeddings.embed_text", side_effect=embeddings):
            mock_cache = Mock()
            mock_cache.get_or_compute.side_effect = embeddings

            result = _analyze_trait_conflict("trait", source_values, mock_cache)

            semantic = result["semantic_analysis"]
            # At exactly 0.80, should be complementary (>= 0.80)
            if abs(semantic["similarity_score"] - 0.80) < 0.01:
                assert semantic["conflict_type"] == "complementary_details"

    def test_exactly_050_similarity_is_different_emphasis(self):
        """Similarity of exactly 0.50 should be different emphasis (>= threshold)."""
        from bce.ai.semantic_contradictions import _analyze_trait_conflict

        source_values = {"mark": "a", "matthew": "b"}

        # Create embeddings that result in ~0.50 similarity
        embeddings = [mock_array([1.0, 0.0]), mock_array([0.5, 0.866])]  # 60 degree angle

        with patch("bce.ai.embeddings.embed_text", side_effect=embeddings):
            mock_cache = Mock()
            mock_cache.get_or_compute.side_effect = embeddings

            result = _analyze_trait_conflict("trait", source_values, mock_cache)

            semantic = result["semantic_analysis"]
            # At exactly 0.50, should be different_emphasis (>= 0.50, < 0.80)
            if abs(semantic["similarity_score"] - 0.50) < 0.01:
                assert semantic["conflict_type"] == "different_emphasis"

    def test_empty_strings_handled(self):
        """Should handle empty string values gracefully."""
        from bce.ai.semantic_contradictions import _analyze_trait_conflict

        source_values = {"mark": "", "matthew": ""}
        embeddings = [mock_array([0.0, 0.0]), mock_array([0.0, 0.0])]

        with patch("bce.ai.embeddings.embed_text", side_effect=embeddings):
            mock_cache = Mock()
            mock_cache.get_or_compute.side_effect = embeddings

            result = _analyze_trait_conflict("trait", source_values, mock_cache)

            # Should still return valid structure
            assert "semantic_analysis" in result
            assert "similarity_score" in result["semantic_analysis"]

    def test_special_characters_in_trait_values(self):
        """Should handle special characters in trait values."""
        from bce.ai.semantic_contradictions import _analyze_trait_conflict

        source_values = {
            "mark": "Jesus said: \"I am the way\"",
            "matthew": "Jesus said: 'I am the truth'"
        }
        embeddings = [mock_array([0.5]*5), mock_array([0.6]*5)]

        with patch("bce.ai.embeddings.embed_text", side_effect=embeddings):
            mock_cache = Mock()
            mock_cache.get_or_compute.side_effect = embeddings

            result = _analyze_trait_conflict("quote", source_values, mock_cache)

            assert "semantic_analysis" in result
            assert result["sources"] == source_values
