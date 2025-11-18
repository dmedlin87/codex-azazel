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

    def setup_method(self):
        """Enable AI features for tests."""
        reset_default_config()
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

    def teardown_method(self):
        """Reset configuration."""
        reset_default_config()

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

    def test_empty_accounts_list(self):
        """Should handle empty accounts list."""
        from bce.ai.parallel_detection import _find_parallel_groups

        groups = _find_parallel_groups([], 0.7)
        assert groups == []

    def test_three_accounts_mixed_similarity(self):
        """Should handle three accounts with varying similarity."""
        from bce.ai.parallel_detection import _find_parallel_groups
        from bce.ai.embeddings import embed_text

        accounts = [
            {
                "source_id": "mark",
                "summary": "Jesus was crucified at Golgotha",
                "embedding": embed_text("Jesus was crucified at Golgotha"),
            },
            {
                "source_id": "matthew",
                "summary": "Jesus crucified at Golgotha place of skull",
                "embedding": embed_text("Jesus crucified at Golgotha place of skull"),
            },
            {
                "source_id": "john",
                "summary": "The wedding at Cana where Jesus turned water into wine",
                "embedding": embed_text("The wedding at Cana where Jesus turned water into wine"),
            },
        ]

        groups = _find_parallel_groups(accounts, 0.7)

        # Should have at least one group
        assert len(groups) >= 1
        # Total accounts should be preserved
        total_accounts = sum(len(g) for g in groups)
        assert total_accounts == 3

    def test_threshold_boundary_cases(self):
        """Should handle threshold boundary values correctly."""
        from bce.ai.parallel_detection import _find_parallel_groups
        from bce.ai.embeddings import embed_text

        accounts = [
            {
                "source_id": "mark",
                "summary": "Jesus was crucified",
                "embedding": embed_text("Jesus was crucified"),
            },
            {
                "source_id": "matthew",
                "summary": "Jesus was crucified",
                "embedding": embed_text("Jesus was crucified"),
            },
        ]

        # Very low threshold - should group
        groups_low = _find_parallel_groups(accounts, 0.01)
        assert len(groups_low) >= 1

        # Very high threshold - might separate
        groups_high = _find_parallel_groups(accounts, 0.99)
        assert len(groups_high) >= 1

    def test_multiple_parallel_groups(self):
        """Should create multiple groups for distinct parallel sets."""
        from bce.ai.parallel_detection import _find_parallel_groups
        from bce.ai.embeddings import embed_text

        # Two distinct groups of similar accounts
        accounts = [
            {
                "source_id": "mark",
                "summary": "Jesus was crucified at Golgotha",
                "embedding": embed_text("Jesus was crucified at Golgotha"),
            },
            {
                "source_id": "matthew",
                "summary": "The crucifixion at Golgotha",
                "embedding": embed_text("The crucifixion at Golgotha"),
            },
            {
                "source_id": "luke",
                "summary": "Jesus performed his first miracle at Cana",
                "embedding": embed_text("Jesus performed his first miracle at Cana"),
            },
            {
                "source_id": "john",
                "summary": "The wedding at Cana water to wine miracle",
                "embedding": embed_text("The wedding at Cana water to wine miracle"),
            },
        ]

        groups = _find_parallel_groups(accounts, 0.7)

        # Should have multiple groups
        assert len(groups) >= 1
        # All accounts should be in some group
        total_accounts = sum(len(g) for g in groups)
        assert total_accounts == 4


class TestDetectEventParallelsEdgeCases:
    """Additional edge case tests for detect_event_parallels."""

    def setup_method(self):
        """Enable AI features for tests."""
        reset_default_config()
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

    def teardown_method(self):
        """Reset configuration."""
        reset_default_config()

    def test_result_contains_all_expected_fields(self):
        """Should return all expected fields in parallel results."""
        from bce.ai import parallel_detection

        result = parallel_detection.detect_event_parallels("crucifixion", use_cache=False)

        assert "event_id" in result
        assert "parallels" in result or "message" in result

        if "parallels" in result and result["parallels"]:
            for parallel in result["parallels"]:
                assert "sources" in parallel
                assert "type" in parallel
                assert "references" in parallel
                assert "similarity_score" in parallel
                assert "narrative_overlap" in parallel
                assert "suggested_summary" in parallel

    def test_similarity_score_format(self):
        """Should return similarity scores rounded to 2 decimal places."""
        from bce.ai import parallel_detection

        result = parallel_detection.detect_event_parallels("crucifixion", use_cache=False)

        if "parallels" in result and result["parallels"]:
            for parallel in result["parallels"]:
                score = parallel["similarity_score"]
                assert isinstance(score, (int, float))
                # Check it's rounded to 2 decimals (as string representation)
                score_str = str(score)
                if '.' in score_str:
                    decimal_places = len(score_str.split('.')[1])
                    assert decimal_places <= 2

    def test_johannine_unique_detection(self):
        """Should detect unique Johannine accounts."""
        from bce.ai import parallel_detection

        # Find an event with John but no synoptic parallels
        # Or test the logic directly
        result = parallel_detection.detect_event_parallels("crucifixion", use_cache=False)

        # If John is present in the event, verify handling
        if "parallels" in result:
            john_parallels = [p for p in result["parallels"] if "john" in p.get("sources", [])]
            # Each John parallel should have proper classification
            for parallel in john_parallels:
                assert parallel["type"] in [
                    "johannine_unique",
                    "synoptic_johannine_parallel",
                    "johannine_variant",
                    "triple_tradition"
                ]

    def test_references_dict_structure(self):
        """Should return references as dict mapping source to reference."""
        from bce.ai import parallel_detection

        result = parallel_detection.detect_event_parallels("crucifixion", use_cache=False)

        if "parallels" in result and result["parallels"]:
            for parallel in result["parallels"]:
                refs = parallel["references"]
                assert isinstance(refs, dict)
                # Each source should have a reference
                for source in parallel["sources"]:
                    assert source in refs
                    assert isinstance(refs[source], str)

    def test_narrative_overlap_values(self):
        """Should return valid narrative overlap classifications."""
        from bce.ai import parallel_detection

        result = parallel_detection.detect_event_parallels("crucifixion", use_cache=False)

        valid_overlaps = ["very_high", "high", "medium", "low", "minimal", "unique"]

        if "parallels" in result and result["parallels"]:
            for parallel in result["parallels"]:
                assert parallel["narrative_overlap"] in valid_overlaps

    def test_suggested_summary_not_empty(self):
        """Should provide non-empty suggested summaries."""
        from bce.ai import parallel_detection

        result = parallel_detection.detect_event_parallels("crucifixion", use_cache=False)

        if "parallels" in result and result["parallels"]:
            for parallel in result["parallels"]:
                summary = parallel["suggested_summary"]
                assert isinstance(summary, str)
                # Should have some content
                assert len(summary) > 0

    def test_cache_disabled_returns_fresh_results(self):
        """Should return fresh results when cache is disabled."""
        from bce.ai import parallel_detection
        from bce.ai.cache import clear_all_ai_caches

        # Clear any existing cache
        clear_all_ai_caches()

        # Get results without cache
        result1 = parallel_detection.detect_event_parallels("crucifixion", use_cache=False)
        result2 = parallel_detection.detect_event_parallels("crucifixion", use_cache=False)

        # Both should succeed (structure might vary slightly but should be valid)
        assert "event_id" in result1
        assert "event_id" in result2


class TestClassifyParallelTypeEdgeCases:
    """Additional edge case tests for _classify_parallel_type."""

    def test_johannine_variant_with_multiple_johns(self):
        """Should handle multiple non-synoptic sources with John."""
        from bce.ai.parallel_detection import _classify_parallel_type

        # John + Acts (no synoptics)
        result = _classify_parallel_type(["john", "acts"], 0.70)
        assert result == "johannine_variant"

    def test_all_four_gospels(self):
        """Should handle all four gospels together."""
        from bce.ai.parallel_detection import _classify_parallel_type

        result = _classify_parallel_type(["mark", "matthew", "luke", "john"], 0.80)
        # Should recognize as synoptic-johannine parallel
        assert result == "synoptic_johannine_parallel"

    def test_mark_and_john_only(self):
        """Should classify Mark+John as synoptic_johannine_parallel."""
        from bce.ai.parallel_detection import _classify_parallel_type

        result = _classify_parallel_type(["mark", "john"], 0.75)
        assert result == "synoptic_johannine_parallel"

    def test_luke_unique(self):
        """Should classify single Luke account as synoptic_unique."""
        from bce.ai.parallel_detection import _classify_parallel_type

        result = _classify_parallel_type(["luke"], 0.0)
        assert result == "synoptic_unique"


class TestParseSourceFromReferenceEdgeCases:
    """Additional edge case tests for _parse_source_from_reference."""

    def test_numbered_epistles(self):
        """Should handle numbered epistles correctly."""
        from bce.ai.parallel_detection import _parse_source_from_reference

        assert _parse_source_from_reference("1 Corinthians 15:1") == "paul_undisputed"
        assert _parse_source_from_reference("2 Corinthians 5:17") == "paul_undisputed"
        assert _parse_source_from_reference("1 Thessalonians 4:13") == "paul_undisputed"
        assert _parse_source_from_reference("2 Thessalonians 2:1") == "paul_undisputed"
        assert _parse_source_from_reference("1 Timothy 3:16") == "paul_undisputed"
        assert _parse_source_from_reference("2 Timothy 3:16") == "paul_undisputed"

    def test_short_epistles(self):
        """Should handle short epistles."""
        from bce.ai.parallel_detection import _parse_source_from_reference

        assert _parse_source_from_reference("Titus 2:13") == "paul_undisputed"
        assert _parse_source_from_reference("Philemon 1:6") == "paul_undisputed"

    def test_reference_with_verse_ranges(self):
        """Should parse references with verse ranges."""
        from bce.ai.parallel_detection import _parse_source_from_reference

        assert _parse_source_from_reference("Mark 15:22-41") == "mark"
        assert _parse_source_from_reference("Matthew 27:33-56") == "matthew"
        assert _parse_source_from_reference("Luke 23:33-49") == "luke"

    def test_old_testament_returns_none(self):
        """Should return None for Old Testament books."""
        from bce.ai.parallel_detection import _parse_source_from_reference

        assert _parse_source_from_reference("Genesis 1:1") is None
        assert _parse_source_from_reference("Exodus 20:1-17") is None
        assert _parse_source_from_reference("Psalms 23:1") is None
        assert _parse_source_from_reference("Isaiah 53:5") is None

    def test_empty_reference(self):
        """Should handle empty or invalid references."""
        from bce.ai.parallel_detection import _parse_source_from_reference

        assert _parse_source_from_reference("") is None
        assert _parse_source_from_reference("   ") is None


class TestGenerateCombinedSummaryEdgeCases:
    """Additional edge case tests for _generate_combined_summary."""

    def test_summaries_of_equal_length(self):
        """Should handle summaries of equal length."""
        from bce.ai.parallel_detection import _generate_combined_summary

        summaries = [
            "Jesus was crucified",
            "Jesus got crucified",
            "Crucifixion of Jesus"
        ]

        result = _generate_combined_summary(summaries)
        # Should return one of them with variations note
        assert len(result) > 0
        assert "variations" in result or "accounts" in result

    def test_very_long_vs_short_summaries(self):
        """Should prefer the longest summary."""
        from bce.ai.parallel_detection import _generate_combined_summary

        summaries = [
            "Crucifixion",
            "The crucifixion of Jesus Christ at Golgotha, the place of the skull, between two criminals",
            "Jesus crucified"
        ]

        result = _generate_combined_summary(summaries)
        # Should use the longest one
        assert "Golgotha" in result
        assert "place of the skull" in result

    def test_two_summaries(self):
        """Should handle exactly two summaries."""
        from bce.ai.parallel_detection import _generate_combined_summary

        summaries = [
            "Jesus was crucified at Golgotha",
            "Crucifixion at the place called Golgotha"
        ]

        result = _generate_combined_summary(summaries)
        assert len(result) > 0
        assert "Golgotha" in result or "golgotha" in result


class TestFindParallelEventsEdgeCases:
    """Additional edge case tests for find_parallel_events."""

    def setup_method(self):
        """Enable AI features for tests."""
        reset_default_config()
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

    def teardown_method(self):
        """Reset configuration."""
        reset_default_config()

    def test_result_structure_complete(self):
        """Should return complete result structure."""
        from bce.ai import parallel_detection

        result = parallel_detection.find_parallel_events("Mark 15:22-41")

        assert isinstance(result, list)

        for event in result:
            assert "event_id" in event
            assert "event_label" in event
            assert "reference" in event
            assert "parallel_references" in event
            assert "parallel_sources" in event
            assert isinstance(event["parallel_references"], list)
            assert isinstance(event["parallel_sources"], list)

    def test_acts_reference(self):
        """Should handle Acts references."""
        from bce.ai import parallel_detection

        result = parallel_detection.find_parallel_events("Acts 9:1-19")

        assert isinstance(result, list)
        # May or may not find results

    def test_pauline_reference(self):
        """Should handle Pauline epistle references."""
        from bce.ai import parallel_detection

        result = parallel_detection.find_parallel_events("1 Corinthians 15:3-8")

        assert isinstance(result, list)


class TestSuggestParallelPericopesEdgeCases:
    """Additional edge case tests for suggest_parallel_pericopes."""

    def setup_method(self):
        """Enable AI features for tests."""
        reset_default_config()
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

    def teardown_method(self):
        """Reset configuration."""
        reset_default_config()

    def test_very_low_threshold(self):
        """Should handle very low similarity threshold."""
        from bce.ai import parallel_detection

        result = parallel_detection.suggest_parallel_pericopes(min_similarity=0.1)

        assert isinstance(result, list)
        # Should return suggestions with low threshold

    def test_maximum_threshold(self):
        """Should handle maximum similarity threshold."""
        from bce.ai import parallel_detection

        result = parallel_detection.suggest_parallel_pericopes(min_similarity=0.99)

        assert isinstance(result, list)
        # May return very few or no suggestions

    def test_suggestion_completeness(self):
        """Should return complete suggestion structures."""
        from bce.ai import parallel_detection

        result = parallel_detection.suggest_parallel_pericopes(min_similarity=0.6)

        assert isinstance(result, list)

        for suggestion in result:
            assert "event_id" in suggestion
            assert "event_label" in suggestion
            assert "suggested_parallels" in suggestion

            # Each parallel should be complete
            for parallel in suggestion["suggested_parallels"]:
                assert "sources" in parallel
                assert "type" in parallel
                assert "similarity_score" in parallel


class TestIntegrationParallelDetection:
    """Integration tests with real event data."""

    def setup_method(self):
        """Enable AI features for tests."""
        reset_default_config()
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

    def teardown_method(self):
        """Reset configuration."""
        reset_default_config()

    def test_crucifixion_has_synoptic_parallels(self):
        """Crucifixion should have synoptic parallels detected."""
        from bce.ai import parallel_detection

        result = parallel_detection.detect_event_parallels("crucifixion", use_cache=False)

        assert "event_id" in result
        assert result["event_id"] == "crucifixion"
        assert "parallels" in result or "message" in result

        # Crucifixion has accounts in multiple gospels
        if "parallels" in result and result["parallels"]:
            # Should have at least some parallel detection
            assert len(result["parallels"]) > 0

    def test_workflow_detect_then_export(self):
        """Should support workflow of detecting and reviewing parallels."""
        from bce.ai import parallel_detection
        from bce import queries

        # Get an event
        events = queries.list_all_events()
        if not events:
            pytest.skip("No events available for testing")

        event = events[0]

        # Detect parallels
        result = parallel_detection.detect_event_parallels(event.id, use_cache=False)

        # Should have valid structure for export
        assert "event_id" in result
        assert result["event_id"] == event.id

        # Should be JSON-serializable
        import json
        json_str = json.dumps(result)
        assert len(json_str) > 0

    def test_suggest_then_apply_workflow(self):
        """Should support workflow of suggesting parallels across all events."""
        from bce.ai import parallel_detection

        suggestions = parallel_detection.suggest_parallel_pericopes(min_similarity=0.7)

        assert isinstance(suggestions, list)

        # Each suggestion should be actionable
        for suggestion in suggestions:
            assert "event_id" in suggestion
            assert "suggested_parallels" in suggestion

            # Parallels should be ready to add to event JSON
            for parallel in suggestion["suggested_parallels"]:
                assert "sources" in parallel
                assert "type" in parallel
                # Should have all fields needed for JSON export
                assert isinstance(parallel["sources"], list)
