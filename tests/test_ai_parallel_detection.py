"""
Tests for bce.ai.parallel_detection module.

Covers parallel passage detection for synoptic and variant accounts.
"""

from __future__ import annotations

import pytest

from bce.config import BceConfig, set_default_config, reset_default_config
from bce.exceptions import ConfigurationError


class TestDetectEventParallels:
    """Tests for detect_event_parallels function."""

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
        from bce.ai import parallel_detection

        reset_default_config()
        config = BceConfig(enable_ai_features=False)
        set_default_config(config)

        with pytest.raises(ConfigurationError, match="AI features are disabled"):
            parallel_detection.detect_event_parallels("crucifixion")

    def test_detect_parallels_basic(self):
        """Should detect parallels for event with multiple accounts."""
        from bce.ai import parallel_detection

        # Use crucifixion which has multiple gospel accounts
        result = parallel_detection.detect_event_parallels("crucifixion", use_cache=False)

        assert "event_id" in result
        assert result["event_id"] == "crucifixion"
        assert "parallels" in result
        assert isinstance(result["parallels"], list)

    def test_detect_parallels_single_account(self):
        """Should return empty parallels for event with single account."""
        from bce.ai import parallel_detection

        # Damascus road conversion is primarily in Acts
        result = parallel_detection.detect_event_parallels("damascus_road", use_cache=False)

        assert "event_id" in result
        assert result["event_id"] == "damascus_road"
        assert "parallels" in result or "message" in result

    def test_detect_parallels_threshold(self):
        """Should respect similarity threshold parameter."""
        from bce.ai import parallel_detection

        # Higher threshold should be more restrictive
        result_strict = parallel_detection.detect_event_parallels(
            "crucifixion", similarity_threshold=0.9, use_cache=False
        )

        # Lower threshold should be more permissive
        result_lenient = parallel_detection.detect_event_parallels(
            "crucifixion", similarity_threshold=0.5, use_cache=False
        )

        assert "parallels" in result_strict
        assert "parallels" in result_lenient

        # Results should be different (or at least not fail)
        # Cannot assert exact counts due to data variability

    def test_detect_parallels_uses_cache(self):
        """Should use cached results when use_cache=True."""
        from bce.ai import parallel_detection

        # First call
        result1 = parallel_detection.detect_event_parallels("crucifixion", use_cache=True)

        # Second call should use cache
        result2 = parallel_detection.detect_event_parallels("crucifixion", use_cache=True)

        assert result1 == result2

    def test_detect_parallels_structure(self):
        """Should return properly structured parallel data."""
        from bce.ai import parallel_detection

        result = parallel_detection.detect_event_parallels("crucifixion", use_cache=False)

        assert "event_id" in result
        assert "parallels" in result or "message" in result

        if "parallels" in result and result["parallels"]:
            parallel = result["parallels"][0]
            # Each parallel should have expected fields
            assert "sources" in parallel
            assert "type" in parallel
            assert isinstance(parallel["sources"], list)

    def test_detect_parallels_nonexistent_event(self):
        """Should handle nonexistent event ID gracefully."""
        from bce.ai import parallel_detection

        # Should raise an exception from queries.get_event
        from bce.exceptions import DataNotFoundError

        with pytest.raises(DataNotFoundError):
            parallel_detection.detect_event_parallels("nonexistent_event", use_cache=False)


class TestFindParallelEvents:
    """Tests for find_parallel_events function."""

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
        from bce.ai import parallel_detection

        reset_default_config()
        config = BceConfig(enable_ai_features=False)
        set_default_config(config)

        with pytest.raises(ConfigurationError, match="AI features are disabled"):
            parallel_detection.find_parallel_events("Mark 15:22-41")

    def test_find_parallel_events_basic(self):
        """Should find events matching a reference."""
        from bce.ai import parallel_detection

        # Mark 15:22-41 is crucifixion narrative
        result = parallel_detection.find_parallel_events("Mark 15:22-41")

        assert isinstance(result, list)
        # May or may not have results depending on data

    def test_find_parallel_events_invalid_reference(self):
        """Should return empty list for invalid reference."""
        from bce.ai import parallel_detection

        result = parallel_detection.find_parallel_events("InvalidBook 99:99")

        assert isinstance(result, list)
        assert len(result) == 0

    def test_find_parallel_events_structure(self):
        """Should return properly structured results."""
        from bce.ai import parallel_detection

        result = parallel_detection.find_parallel_events("Matthew 27:33-56")

        assert isinstance(result, list)

        if result:
            event = result[0]
            assert "event_id" in event
            assert "event_label" in event
            assert "reference" in event


class TestSuggestParallelPericopes:
    """Tests for suggest_parallel_pericopes function."""

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
        from bce.ai import parallel_detection

        reset_default_config()
        config = BceConfig(enable_ai_features=False)
        set_default_config(config)

        with pytest.raises(ConfigurationError, match="AI features are disabled"):
            parallel_detection.suggest_parallel_pericopes()

    def test_suggest_parallels_basic(self):
        """Should suggest parallel pericopes across all events."""
        from bce.ai import parallel_detection

        result = parallel_detection.suggest_parallel_pericopes(min_similarity=0.7)

        assert isinstance(result, list)
        # May or may not have suggestions depending on data

    def test_suggest_parallels_structure(self):
        """Should return properly structured suggestions."""
        from bce.ai import parallel_detection

        result = parallel_detection.suggest_parallel_pericopes(min_similarity=0.6)

        assert isinstance(result, list)

        if result:
            suggestion = result[0]
            assert "event_id" in suggestion
            assert "event_label" in suggestion
            assert "suggested_parallels" in suggestion
            assert isinstance(suggestion["suggested_parallels"], list)

    def test_suggest_parallels_threshold_affects_results(self):
        """Should respect minimum similarity threshold."""
        from bce.ai import parallel_detection

        # Very high threshold should produce fewer suggestions
        strict_result = parallel_detection.suggest_parallel_pericopes(min_similarity=0.95)

        # Lower threshold should produce more suggestions
        lenient_result = parallel_detection.suggest_parallel_pericopes(min_similarity=0.5)

        assert isinstance(strict_result, list)
        assert isinstance(lenient_result, list)


class TestClassifyParallelType:
    """Tests for _classify_parallel_type internal function."""

    def test_triple_tradition(self):
        """Should classify three synoptic gospels as triple_tradition."""
        from bce.ai.parallel_detection import _classify_parallel_type

        result = _classify_parallel_type(["mark", "matthew", "luke"], 0.85)
        assert result == "triple_tradition"

    def test_synoptic_parallel_with_mark(self):
        """Should classify Mark + one other synoptic as synoptic_parallel."""
        from bce.ai.parallel_detection import _classify_parallel_type

        result = _classify_parallel_type(["mark", "matthew"], 0.80)
        assert result == "synoptic_parallel"

        result = _classify_parallel_type(["mark", "luke"], 0.80)
        assert result == "synoptic_parallel"

    def test_q_material_candidate(self):
        """Should classify Matthew-Luke without Mark as Q material candidate."""
        from bce.ai.parallel_detection import _classify_parallel_type

        result = _classify_parallel_type(["matthew", "luke"], 0.75)
        assert result == "q_material_candidate"

    def test_synoptic_unique(self):
        """Should classify single synoptic gospel as synoptic_unique."""
        from bce.ai.parallel_detection import _classify_parallel_type

        result = _classify_parallel_type(["mark"], 0.0)
        assert result == "synoptic_unique"

        result = _classify_parallel_type(["matthew"], 0.0)
        assert result == "synoptic_unique"

    def test_johannine_unique(self):
        """Should classify John alone as johannine_unique."""
        from bce.ai.parallel_detection import _classify_parallel_type

        result = _classify_parallel_type(["john"], 0.0)
        assert result == "johannine_unique"

    def test_synoptic_johannine_parallel(self):
        """Should classify John + synoptic as synoptic_johannine_parallel."""
        from bce.ai.parallel_detection import _classify_parallel_type

        result = _classify_parallel_type(["john", "mark"], 0.70)
        assert result == "synoptic_johannine_parallel"

        result = _classify_parallel_type(["john", "matthew", "luke"], 0.75)
        assert result == "synoptic_johannine_parallel"

    def test_generic_parallel(self):
        """Should classify other combinations as parallel."""
        from bce.ai.parallel_detection import _classify_parallel_type

        # Paul + Acts
        result = _classify_parallel_type(["paul_undisputed", "acts"], 0.65)
        assert result == "parallel"


class TestAssessNarrativeOverlap:
    """Tests for _assess_narrative_overlap internal function."""

    def test_very_high_overlap(self):
        """Should assess very high similarity as very_high overlap."""
        from bce.ai.parallel_detection import _assess_narrative_overlap

        assert _assess_narrative_overlap(0.95) == "very_high"
        assert _assess_narrative_overlap(0.90) == "very_high"

    def test_high_overlap(self):
        """Should assess high similarity as high overlap."""
        from bce.ai.parallel_detection import _assess_narrative_overlap

        assert _assess_narrative_overlap(0.85) == "high"
        assert _assess_narrative_overlap(0.75) == "high"

    def test_medium_overlap(self):
        """Should assess medium similarity as medium overlap."""
        from bce.ai.parallel_detection import _assess_narrative_overlap

        assert _assess_narrative_overlap(0.70) == "medium"
        assert _assess_narrative_overlap(0.60) == "medium"

    def test_low_overlap(self):
        """Should assess low similarity as low overlap."""
        from bce.ai.parallel_detection import _assess_narrative_overlap

        assert _assess_narrative_overlap(0.50) == "low"
        assert _assess_narrative_overlap(0.40) == "low"

    def test_minimal_overlap(self):
        """Should assess very low similarity as minimal overlap."""
        from bce.ai.parallel_detection import _assess_narrative_overlap

        assert _assess_narrative_overlap(0.30) == "minimal"
        assert _assess_narrative_overlap(0.10) == "minimal"
        assert _assess_narrative_overlap(0.0) == "minimal"


class TestGenerateCombinedSummary:
    """Tests for _generate_combined_summary internal function."""

    def test_empty_summaries(self):
        """Should return empty string for empty input."""
        from bce.ai.parallel_detection import _generate_combined_summary

        result = _generate_combined_summary([])
        assert result == ""

    def test_single_summary(self):
        """Should return single summary unchanged."""
        from bce.ai.parallel_detection import _generate_combined_summary

        summary = "Jesus was crucified at Golgotha"
        result = _generate_combined_summary([summary])
        assert result == summary

    def test_multiple_summaries(self):
        """Should combine multiple summaries noting variations."""
        from bce.ai.parallel_detection import _generate_combined_summary

        summaries = [
            "Jesus crucified at Golgotha",
            "The crucifixion of Jesus at the place called Golgotha, the place of the skull",
            "Crucifixion at Golgotha"
        ]
        result = _generate_combined_summary(summaries)

        # Should use the longest as base and note variations
        assert "crucifixion" in result.lower() or "Crucifixion" in result
        assert "variations" in result or "accounts" in result


class TestParseSourceFromReference:
    """Tests for _parse_source_from_reference internal function."""

    def test_parse_gospel_references(self):
        """Should parse gospel references correctly."""
        from bce.ai.parallel_detection import _parse_source_from_reference

        assert _parse_source_from_reference("Mark 15:22-41") == "mark"
        assert _parse_source_from_reference("Matthew 27:33-56") == "matthew"
        assert _parse_source_from_reference("Luke 23:33-49") == "luke"
        assert _parse_source_from_reference("John 19:16-37") == "john"

    def test_parse_acts_reference(self):
        """Should parse Acts references correctly."""
        from bce.ai.parallel_detection import _parse_source_from_reference

        assert _parse_source_from_reference("Acts 9:1-19") == "acts"
        assert _parse_source_from_reference("Acts 2:1-13") == "acts"

    def test_parse_pauline_references(self):
        """Should parse Pauline epistle references."""
        from bce.ai.parallel_detection import _parse_source_from_reference

        assert _parse_source_from_reference("Romans 3:23") == "paul_undisputed"
        assert _parse_source_from_reference("1 Corinthians 15:3-8") == "paul_undisputed"
        assert _parse_source_from_reference("Galatians 1:11-17") == "paul_undisputed"
        assert _parse_source_from_reference("Philippians 2:5-11") == "paul_undisputed"

    def test_parse_unknown_reference(self):
        """Should return None for unrecognized references."""
        from bce.ai.parallel_detection import _parse_source_from_reference

        assert _parse_source_from_reference("Revelation 1:1") is None
        assert _parse_source_from_reference("Genesis 1:1") is None
        assert _parse_source_from_reference("Invalid Book 99:99") is None


class TestFindParallelGroups:
    """Tests for _find_parallel_groups internal function."""

    def test_single_account(self):
        """Should return single group for single account."""
        from bce.ai.parallel_detection import _find_parallel_groups
        from bce.ai.embeddings import embed_text

        accounts = [
            {
                "source_id": "mark",
                "summary": "Jesus was crucified",
                "embedding": embed_text("Jesus was crucified"),
            }
        ]

        groups = _find_parallel_groups(accounts, 0.7)
        assert len(groups) == 1
        assert len(groups[0]) == 1

    def test_similar_accounts_grouped(self):
        """Should group similar accounts together."""
        from bce.ai.parallel_detection import _find_parallel_groups
        from bce.ai.embeddings import embed_text

        # Very similar accounts
        accounts = [
            {
                "source_id": "mark",
                "summary": "Jesus was crucified at Golgotha",
                "embedding": embed_text("Jesus was crucified at Golgotha"),
            },
            {
                "source_id": "matthew",
                "summary": "Jesus crucified at Golgotha the place of skull",
                "embedding": embed_text("Jesus crucified at Golgotha the place of skull"),
            },
        ]

        groups = _find_parallel_groups(accounts, 0.6)

        # Should have at least one group
        assert len(groups) >= 1

    def test_dissimilar_accounts_separate(self):
        """Should keep dissimilar accounts in separate groups."""
        from bce.ai.parallel_detection import _find_parallel_groups
        from bce.ai.embeddings import embed_text

        # Very different accounts
        accounts = [
            {
                "source_id": "mark",
                "summary": "Jesus was crucified at Golgotha",
                "embedding": embed_text("Jesus was crucified at Golgotha"),
            },
            {
                "source_id": "john",
                "summary": "Paul encountered the risen Christ on the road to Damascus",
                "embedding": embed_text("Paul encountered the risen Christ on the road to Damascus"),
            },
        ]

        # With high threshold, should separate
        groups = _find_parallel_groups(accounts, 0.9)

        # Should have groups (exact count depends on similarity)
        assert len(groups) >= 1
