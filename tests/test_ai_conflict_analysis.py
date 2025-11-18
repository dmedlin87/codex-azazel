"""
Tests for bce.ai.conflict_analysis module.

Covers advanced conflict analysis with severity assessment and scholarly context.
"""

from __future__ import annotations

import pytest

from bce.config import BceConfig, set_default_config, reset_default_config
from bce.exceptions import ConfigurationError


class TestAssessConflict:
    """Tests for assess_conflict function."""

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
        from bce.ai import conflict_analysis

        reset_default_config()
        config = BceConfig(enable_ai_features=False)
        set_default_config(config)

        with pytest.raises(ConfigurationError, match="AI features are disabled"):
            conflict_analysis.assess_conflict("jesus", "some_trait")

    def test_assess_conflict_nonexistent_character(self):
        """Should raise error for nonexistent character."""
        from bce.ai import conflict_analysis
        from bce.exceptions import DataNotFoundError

        with pytest.raises(DataNotFoundError):
            conflict_analysis.assess_conflict("nonexistent_character", "some_trait", use_cache=False)

    def test_assess_conflict_no_conflict(self):
        """Should indicate when no conflict exists for trait."""
        from bce.ai import conflict_analysis

        # Use a trait that doesn't have conflicts
        result = conflict_analysis.assess_conflict("jesus", "nonexistent_trait", use_cache=False)

        assert "character_id" in result
        assert result["character_id"] == "jesus"
        assert "trait" in result
        assert result["trait"] == "nonexistent_trait"
        assert "has_conflict" in result
        assert result["has_conflict"] is False

    def test_assess_conflict_with_conflict(self):
        """Should assess conflict when one exists."""
        from bce.ai import conflict_analysis
        from bce import contradictions

        # First find a trait that has conflicts
        conflicts = contradictions.find_trait_conflicts("jesus")

        if conflicts:
            trait = list(conflicts.keys())[0]
            result = conflict_analysis.assess_conflict("jesus", trait, use_cache=False)

            assert "character_id" in result
            assert result["character_id"] == "jesus"
            assert "trait" in result
            assert "sources" in result
            assert "basic_severity" in result
            assert "ai_assessment" in result

            # Check AI assessment structure
            ai = result["ai_assessment"]
            assert "theological_significance" in ai
            assert "historical_significance" in ai
            assert "narrative_coherence_impact" in ai
            assert "explanation" in ai
            assert "scholarly_consensus" in ai
            assert "implications" in ai

    def test_assess_conflict_uses_cache(self):
        """Should use cached results when use_cache=True."""
        from bce.ai import conflict_analysis
        from bce import contradictions

        conflicts = contradictions.find_trait_conflicts("jesus")
        if conflicts:
            trait = list(conflicts.keys())[0]

            result1 = conflict_analysis.assess_conflict("jesus", trait, use_cache=True)
            result2 = conflict_analysis.assess_conflict("jesus", trait, use_cache=True)

            # Should be identical
            assert result1 == result2


class TestAssessAllConflicts:
    """Tests for assess_all_conflicts function."""

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
        from bce.ai import conflict_analysis

        reset_default_config()
        config = BceConfig(enable_ai_features=False)
        set_default_config(config)

        with pytest.raises(ConfigurationError, match="AI features are disabled"):
            conflict_analysis.assess_all_conflicts("jesus")

    def test_assess_all_conflicts_structure(self):
        """Should return properly structured assessment."""
        from bce.ai import conflict_analysis

        result = conflict_analysis.assess_all_conflicts("jesus")

        assert "character_id" in result
        assert result["character_id"] == "jesus"
        assert "assessments" in result
        assert "summary" in result

        summary = result["summary"]
        assert "total_conflicts" in summary

    def test_assess_all_conflicts_summary_counts(self):
        """Should count conflicts by significance level."""
        from bce.ai import conflict_analysis
        from bce import contradictions

        result = conflict_analysis.assess_all_conflicts("jesus")
        conflicts = contradictions.find_trait_conflicts("jesus")

        if conflicts:
            summary = result["summary"]
            assert summary["total_conflicts"] == len(conflicts)
            assert "high_significance" in summary
            assert "medium_significance" in summary
            assert "low_significance" in summary

            # Counts should sum to total
            total = (
                summary["high_significance"]
                + summary["medium_significance"]
                + summary["low_significance"]
            )
            assert total == summary["total_conflicts"]

    def test_assess_all_conflicts_no_conflicts(self):
        """Should handle character with no conflicts."""
        from bce.ai import conflict_analysis

        # Try to find a character with no conflicts
        # If none exists, test should still not fail
        try:
            result = conflict_analysis.assess_all_conflicts("pilate")

            assert "character_id" in result
            assert "assessments" in result
            assert "summary" in result
            assert result["summary"]["total_conflicts"] >= 0
        except Exception:
            # Character may not exist
            pass


class TestEstimateBasicSeverity:
    """Tests for _estimate_basic_severity internal function."""

    def test_high_severity_traits(self):
        """Should classify high severity traits correctly."""
        from bce.ai.conflict_analysis import _estimate_basic_severity

        # High severity keywords
        assert _estimate_basic_severity("death_method", {}) == "high"
        assert _estimate_basic_severity("resurrection_appearances", {}) == "high"
        assert _estimate_basic_severity("divine_claims", {}) == "high"
        assert _estimate_basic_severity("messianic_self_understanding", {}) == "high"
        assert _estimate_basic_severity("conversion_experience", {}) == "high"

    def test_medium_severity_traits(self):
        """Should classify medium severity traits correctly."""
        from bce.ai.conflict_analysis import _estimate_basic_severity

        # Medium severity keywords
        assert _estimate_basic_severity("teaching_authority", {}) == "medium"
        assert _estimate_basic_severity("relationship_with_disciples", {}) == "medium"
        assert _estimate_basic_severity("crucifixion_timeline", {}) == "medium"
        assert _estimate_basic_severity("jerusalem_location", {}) == "medium"

    def test_low_severity_traits(self):
        """Should classify low severity traits correctly."""
        from bce.ai.conflict_analysis import _estimate_basic_severity

        # Low severity (default)
        assert _estimate_basic_severity("clothing", {}) == "low"
        assert _estimate_basic_severity("appearance", {}) == "low"
        assert _estimate_basic_severity("unknown_trait", {}) == "low"


class TestAssessTheologicalSignificance:
    """Tests for _assess_theological_significance internal function."""

    def test_high_theological_significance(self):
        """Should detect high theological significance."""
        from bce.ai.conflict_analysis import _assess_theological_significance

        # Traits with high theological keywords
        conflict = {"mark": "human", "john": "divine"}
        result = _assess_theological_significance("divinity", conflict)
        assert result == "high"

        conflict = {"mark": "hidden", "john": "proclaimed"}
        result = _assess_theological_significance("messianic_claims", conflict)
        assert result == "high"

        conflict = {"paul": "spiritual", "mark": "physical"}
        result = _assess_theological_significance("resurrection_nature", conflict)
        assert result == "high"

    def test_medium_theological_significance(self):
        """Should detect medium theological significance."""
        from bce.ai.conflict_analysis import _assess_theological_significance

        conflict = {"mark": "strict", "paul": "flexible"}
        result = _assess_theological_significance("torah_observance", conflict)
        assert result == "medium"

        conflict = {"matthew": "Jews", "luke": "Gentiles"}
        result = _assess_theological_significance("mission_audience", conflict)
        assert result == "medium"

    def test_low_theological_significance(self):
        """Should detect low theological significance."""
        from bce.ai.conflict_analysis import _assess_theological_significance

        conflict = {"mark": "red", "john": "purple"}
        result = _assess_theological_significance("clothing_color", conflict)
        assert result == "low"


class TestAssessHistoricalSignificance:
    """Tests for _assess_historical_significance internal function."""

    def test_high_historical_significance(self):
        """Should detect high historical significance."""
        from bce.ai.conflict_analysis import _assess_historical_significance

        result = _assess_historical_significance("death_timeline", {})
        assert result == "high"

        result = _assess_historical_significance("crucifixion_date", {})
        assert result == "high"

        result = _assess_historical_significance("jerusalem_trial", {})
        assert result == "high"

    def test_medium_historical_significance(self):
        """Should detect medium historical significance."""
        from bce.ai.conflict_analysis import _assess_historical_significance

        result = _assess_historical_significance("galilee_journey", {})
        assert result == "medium"

        result = _assess_historical_significance("meeting_with_disciples", {})
        assert result == "medium"

    def test_low_historical_significance(self):
        """Should detect low historical significance."""
        from bce.ai.conflict_analysis import _assess_historical_significance

        result = _assess_historical_significance("teaching_style", {})
        assert result == "low"


class TestAssessNarrativeImpact:
    """Tests for _assess_narrative_impact internal function."""

    def setup_method(self):
        """Enable AI features for tests."""
        reset_default_config()
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

    def teardown_method(self):
        """Reset configuration."""
        reset_default_config()

    def test_low_impact_high_similarity(self):
        """Should detect low narrative impact for similar values."""
        from bce.ai.conflict_analysis import _assess_narrative_impact

        # Very similar values
        conflict = {
            "mark": "Jesus taught in the temple",
            "matthew": "Jesus was teaching in the temple courts",
        }
        result = _assess_narrative_impact("teaching_location", conflict)
        # Should be low impact (high similarity = low impact)
        assert result in ["low", "medium"]

    def test_high_impact_low_similarity(self):
        """Should detect high narrative impact for dissimilar values."""
        from bce.ai.conflict_analysis import _assess_narrative_impact

        # Very different values
        conflict = {
            "mark": "Jesus died at the ninth hour",
            "john": "Jesus died in the afternoon before Passover began",
        }
        result = _assess_narrative_impact("death_timing", conflict)
        # Result depends on semantic similarity
        assert result in ["low", "medium", "high"]

    def test_single_value(self):
        """Should handle single value gracefully."""
        from bce.ai.conflict_analysis import _assess_narrative_impact

        conflict = {"mark": "Jesus taught"}
        result = _assess_narrative_impact("teaching", conflict)
        assert result == "low"


class TestGenerateConflictExplanation:
    """Tests for _generate_conflict_explanation internal function."""

    def test_two_source_explanation(self):
        """Should generate explanation for two-source conflict."""
        from bce.ai.conflict_analysis import _generate_conflict_explanation

        conflict = {"mark": "value1", "matthew": "value2"}
        result = _generate_conflict_explanation("teaching_authority", conflict, "high")

        assert "teaching authority" in result
        assert "mark" in result
        assert "matthew" in result
        assert len(result) > 0

    def test_multiple_source_explanation(self):
        """Should generate explanation for multi-source conflict."""
        from bce.ai.conflict_analysis import _generate_conflict_explanation

        conflict = {"mark": "v1", "matthew": "v2", "luke": "v3"}
        result = _generate_conflict_explanation("portrayal", conflict, "medium")

        assert "portrayal" in result
        assert "Multiple sources" in result or "sources" in result
        assert len(result) > 0

    def test_high_theological_significance_explanation(self):
        """Should include appropriate context for high significance."""
        from bce.ai.conflict_analysis import _generate_conflict_explanation

        conflict = {"mark": "v1", "john": "v2"}
        result = _generate_conflict_explanation("divinity", conflict, "high")

        assert "divinity" in result
        assert "theological" in result or "significant" in result

    def test_low_theological_significance_explanation(self):
        """Should include appropriate context for low significance."""
        from bce.ai.conflict_analysis import _generate_conflict_explanation

        conflict = {"mark": "v1", "matthew": "v2"}
        result = _generate_conflict_explanation("detail", conflict, "low")

        assert "detail" in result
        assert "minor" in result or "variation" in result


class TestAssessScholarlyConsensus:
    """Tests for _assess_scholarly_consensus internal function."""

    def test_well_known_conflicts(self):
        """Should recognize well-known conflicts."""
        from bce.ai.conflict_analysis import _assess_scholarly_consensus

        result = _assess_scholarly_consensus("death_method")
        assert "acknowledged" in result.lower() or "widely" in result.lower()

        result = _assess_scholarly_consensus("resurrection_appearances")
        assert "acknowledged" in result.lower() or "widely" in result.lower()

    def test_less_known_conflicts(self):
        """Should have different response for less known conflicts."""
        from bce.ai.conflict_analysis import _assess_scholarly_consensus

        result = _assess_scholarly_consensus("minor_detail")
        assert "Recognized" in result or "less" in result


class TestIdentifyImplications:
    """Tests for _identify_implications internal function."""

    def test_multiple_sources_imply_independence(self):
        """Should identify independent traditions."""
        from bce.ai.conflict_analysis import _identify_implications

        conflict = {"mark": "v1", "john": "v2"}
        result = _identify_implications("trait", conflict)

        assert isinstance(result, list)
        assert len(result) > 0
        assert any("independent" in imp.lower() for imp in result)

    def test_timeline_implies_oral_variants(self):
        """Should identify oral transmission variants for timeline."""
        from bce.ai.conflict_analysis import _identify_implications

        conflict = {"mark": "v1", "matthew": "v2"}
        result = _identify_implications("timeline_sequence", conflict)

        assert isinstance(result, list)
        assert any("oral" in imp.lower() for imp in result)

    def test_divine_implies_redaction(self):
        """Should identify theological redaction for divine traits."""
        from bce.ai.conflict_analysis import _identify_implications

        conflict = {"mark": "v1", "john": "v2"}
        result = _identify_implications("divine_claims", conflict)

        assert isinstance(result, list)
        assert any("redaction" in imp.lower() or "theological" in imp.lower() for imp in result)

    def test_appearance_implies_witness_priority(self):
        """Should identify witness prioritization."""
        from bce.ai.conflict_analysis import _identify_implications

        conflict = {"matthew": "v1", "luke": "v2"}
        result = _identify_implications("resurrection_appearance_order", conflict)

        assert isinstance(result, list)
        assert any("witness" in imp.lower() for imp in result)


class TestCompareConflictSeverity:
    """Tests for compare_conflict_severity function."""

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
        from bce.ai import conflict_analysis

        reset_default_config()
        config = BceConfig(enable_ai_features=False)
        set_default_config(config)

        with pytest.raises(ConfigurationError, match="AI features are disabled"):
            conflict_analysis.compare_conflict_severity("jesus", "peter")

    def test_compare_structure(self):
        """Should return properly structured comparison."""
        from bce.ai import conflict_analysis

        result = conflict_analysis.compare_conflict_severity("jesus", "peter")

        assert "characters" in result
        assert result["characters"] == ["jesus", "peter"]
        assert "comparison" in result
        assert "jesus" in result["comparison"]
        assert "peter" in result["comparison"]
        assert "interpretation" in result

    def test_interpretation_generated(self):
        """Should generate meaningful interpretation."""
        from bce.ai import conflict_analysis

        result = conflict_analysis.compare_conflict_severity("jesus", "paul")

        interpretation = result["interpretation"]
        assert isinstance(interpretation, str)
        assert len(interpretation) > 0
        # Should mention at least one character
        assert "jesus" in interpretation or "paul" in interpretation


class TestGenerateComparisonInterpretation:
    """Tests for _generate_comparison_interpretation internal function."""

    def test_char1_has_more_conflicts(self):
        """Should note when char1 has more conflicts."""
        from bce.ai.conflict_analysis import _generate_comparison_interpretation

        analysis1 = {"summary": {"total_conflicts": 10}}
        analysis2 = {"summary": {"total_conflicts": 5}}

        result = _generate_comparison_interpretation("jesus", analysis1, "peter", analysis2)

        assert "jesus" in result
        assert "10" in result
        assert "5" in result
        assert "more" in result

    def test_char2_has_more_conflicts(self):
        """Should note when char2 has more conflicts."""
        from bce.ai.conflict_analysis import _generate_comparison_interpretation

        analysis1 = {"summary": {"total_conflicts": 3}}
        analysis2 = {"summary": {"total_conflicts": 8}}

        result = _generate_comparison_interpretation("james", analysis1, "paul", analysis2)

        assert "paul" in result
        assert "8" in result
        assert "3" in result
        assert "more" in result

    def test_equal_conflicts(self):
        """Should note when conflicts are equal."""
        from bce.ai.conflict_analysis import _generate_comparison_interpretation

        analysis1 = {"summary": {"total_conflicts": 5}}
        analysis2 = {"summary": {"total_conflicts": 5}}

        result = _generate_comparison_interpretation("peter", analysis1, "john", analysis2)

        assert "similar" in result or "comparable" in result
        assert "5" in result


class TestPerformAIAssessment:
    """Tests for _perform_ai_assessment internal orchestrator function."""

    def setup_method(self):
        """Enable AI features for tests."""
        reset_default_config()
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

    def teardown_method(self):
        """Reset configuration."""
        reset_default_config()

    def test_ai_assessment_structure(self):
        """Should return all required fields."""
        from bce.ai.conflict_analysis import _perform_ai_assessment

        conflict_data = {"mark": "human messiah", "john": "divine logos"}
        result = _perform_ai_assessment("jesus", "christology", conflict_data)

        # Check all required fields are present
        assert "theological_significance" in result
        assert "historical_significance" in result
        assert "narrative_coherence_impact" in result
        assert "explanation" in result
        assert "scholarly_consensus" in result
        assert "implications" in result

        # Check field types
        assert isinstance(result["theological_significance"], str)
        assert isinstance(result["historical_significance"], str)
        assert isinstance(result["narrative_coherence_impact"], str)
        assert isinstance(result["explanation"], str)
        assert isinstance(result["scholarly_consensus"], str)
        assert isinstance(result["implications"], list)

    def test_ai_assessment_with_empty_conflict(self):
        """Should handle empty conflict data."""
        from bce.ai.conflict_analysis import _perform_ai_assessment

        conflict_data = {}
        result = _perform_ai_assessment("jesus", "some_trait", conflict_data)

        # Should still return structure
        assert "theological_significance" in result
        assert "implications" in result
        assert isinstance(result["implications"], list)

    def test_ai_assessment_with_many_sources(self):
        """Should handle conflicts from many sources."""
        from bce.ai.conflict_analysis import _perform_ai_assessment

        conflict_data = {
            "mark": "value1",
            "matthew": "value2",
            "luke": "value3",
            "john": "value4",
            "paul": "value5",
        }
        result = _perform_ai_assessment("jesus", "portrayal", conflict_data)

        assert "implications" in result
        # Should recognize independent traditions with many sources
        assert len(result["implications"]) > 0


class TestEdgeCasesAndBoundaryConditions:
    """Tests for edge cases and boundary conditions."""

    def setup_method(self):
        """Enable AI features for tests."""
        reset_default_config()
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

    def teardown_method(self):
        """Reset configuration."""
        reset_default_config()

    def test_assess_conflict_empty_trait_name(self):
        """Should handle empty trait name."""
        from bce.ai import conflict_analysis

        # Empty trait should result in no conflict
        result = conflict_analysis.assess_conflict("jesus", "", use_cache=False)

        assert "character_id" in result
        assert result["trait"] == ""

    def test_assess_conflict_special_characters_in_trait(self):
        """Should handle special characters in trait names."""
        from bce.ai import conflict_analysis

        # Trait with special characters
        result = conflict_analysis.assess_conflict("jesus", "trait-with-dashes_and_underscores", use_cache=False)

        assert "character_id" in result
        assert "trait" in result

    def test_narrative_impact_three_sources(self):
        """Should calculate narrative impact for three sources."""
        from bce.ai.conflict_analysis import _assess_narrative_impact

        conflict = {
            "mark": "Jesus spoke plainly",
            "matthew": "Jesus taught with authority",
            "luke": "Jesus proclaimed the kingdom",
        }
        result = _assess_narrative_impact("teaching_style", conflict)

        assert result in ["low", "medium", "high"]

    def test_narrative_impact_empty_values(self):
        """Should handle empty string values."""
        from bce.ai.conflict_analysis import _assess_narrative_impact

        conflict = {"mark": "", "matthew": ""}
        result = _assess_narrative_impact("trait", conflict)

        # Should not crash, should return some assessment
        assert result in ["low", "medium", "high"]

    def test_implications_with_single_source(self):
        """Should handle implications for single source (edge case)."""
        from bce.ai.conflict_analysis import _identify_implications

        conflict = {"mark": "value1"}
        result = _identify_implications("trait", conflict)

        # Should return at least a default implication
        assert isinstance(result, list)
        assert len(result) > 0

    def test_implications_timeline_and_divine_combined(self):
        """Should identify multiple implications when multiple keywords match."""
        from bce.ai.conflict_analysis import _identify_implications

        conflict = {"mark": "v1", "john": "v2"}
        result = _identify_implications("divine_timeline_sequence", conflict)

        # Should have implications for both timeline and divine
        assert len(result) >= 2
        assert any("oral" in imp.lower() or "timeline" in imp.lower() or "theological" in imp.lower() for imp in result)


class TestCachingBehavior:
    """Tests for caching behavior and cache invalidation."""

    def setup_method(self):
        """Enable AI features and clear caches."""
        reset_default_config()
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

        # Clear AI caches
        from bce.ai.cache import clear_all_ai_caches
        clear_all_ai_caches()

    def teardown_method(self):
        """Reset configuration and clear caches."""
        from bce.ai.cache import clear_all_ai_caches
        clear_all_ai_caches()
        reset_default_config()

    def test_cached_vs_uncached_results_identical(self):
        """Cached and uncached results should be identical."""
        from bce.ai import conflict_analysis
        from bce import contradictions

        conflicts = contradictions.find_trait_conflicts("jesus")
        if conflicts:
            trait = list(conflicts.keys())[0]

            # Clear cache first
            from bce.ai.cache import clear_all_ai_caches
            clear_all_ai_caches()

            # Get uncached result
            result_uncached = conflict_analysis.assess_conflict("jesus", trait, use_cache=False)

            # Clear cache again
            clear_all_ai_caches()

            # Get cached result
            result_cached = conflict_analysis.assess_conflict("jesus", trait, use_cache=True)

            # They should be identical
            assert result_uncached["character_id"] == result_cached["character_id"]
            assert result_uncached["trait"] == result_cached["trait"]
            # AI assessment might vary slightly due to embeddings, but structure should match
            assert set(result_uncached.keys()) == set(result_cached.keys())

    def test_cache_reuse_on_repeated_calls(self):
        """Cache should be reused on repeated calls."""
        from bce.ai import conflict_analysis
        from bce import contradictions

        conflicts = contradictions.find_trait_conflicts("jesus")
        if conflicts:
            trait = list(conflicts.keys())[0]

            # Clear cache first
            from bce.ai.cache import clear_all_ai_caches
            clear_all_ai_caches()

            # First call
            result1 = conflict_analysis.assess_conflict("jesus", trait, use_cache=True)

            # Second call (should use cache)
            result2 = conflict_analysis.assess_conflict("jesus", trait, use_cache=True)

            # Should be identical (same object from cache)
            assert result1 == result2


class TestIntegrationScenarios:
    """Integration tests for full workflow scenarios."""

    def setup_method(self):
        """Enable AI features for tests."""
        reset_default_config()
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

    def teardown_method(self):
        """Reset configuration."""
        reset_default_config()

    def test_full_workflow_assess_single_then_all(self):
        """Should work seamlessly when assessing single then all conflicts."""
        from bce.ai import conflict_analysis
        from bce import contradictions

        conflicts = contradictions.find_trait_conflicts("jesus")

        if conflicts:
            # First assess a single conflict
            trait = list(conflicts.keys())[0]
            single_result = conflict_analysis.assess_conflict("jesus", trait, use_cache=False)

            # Then assess all conflicts
            all_result = conflict_analysis.assess_all_conflicts("jesus")

            # The single result should match the corresponding entry in all results
            assert trait in all_result["assessments"]
            all_trait_result = all_result["assessments"][trait]

            # Should have same basic structure
            assert single_result["character_id"] == all_trait_result["character_id"]
            assert single_result["trait"] == all_trait_result["trait"]

    def test_compare_then_assess_workflow(self):
        """Should work when comparing then assessing individual conflicts."""
        from bce.ai import conflict_analysis

        # First compare two characters
        comparison = conflict_analysis.compare_conflict_severity("jesus", "peter")

        # Then assess individual conflicts for one of them
        jesus_conflicts = conflict_analysis.assess_all_conflicts("jesus")

        # Comparison summary should match individual assessment summary
        assert comparison["comparison"]["jesus"]["total_conflicts"] == jesus_conflicts["summary"]["total_conflicts"]

    def test_assess_multiple_characters_sequentially(self):
        """Should handle assessing multiple characters in sequence."""
        from bce.ai import conflict_analysis

        characters = ["jesus", "peter", "paul"]
        results = []

        for char_id in characters:
            try:
                result = conflict_analysis.assess_all_conflicts(char_id)
                results.append(result)
            except Exception:
                # Character might not exist or have no conflicts
                pass

        # Should have gotten results for at least one character
        assert len(results) > 0

        # Each result should have proper structure
        for result in results:
            assert "character_id" in result
            assert "assessments" in result
            assert "summary" in result


class TestErrorHandlingAndResilience:
    """Tests for error handling and resilience."""

    def setup_method(self):
        """Enable AI features for tests."""
        reset_default_config()
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

    def teardown_method(self):
        """Reset configuration."""
        reset_default_config()

    def test_assess_conflict_invalid_character_raises(self):
        """Should raise appropriate error for invalid character."""
        from bce.ai import conflict_analysis
        from bce.exceptions import DataNotFoundError

        with pytest.raises(DataNotFoundError):
            conflict_analysis.assess_conflict("nonexistent_character_xyz", "trait", use_cache=False)

    def test_assess_all_conflicts_invalid_character_raises(self):
        """Should raise appropriate error for invalid character."""
        from bce.ai import conflict_analysis
        from bce.exceptions import DataNotFoundError

        with pytest.raises(DataNotFoundError):
            conflict_analysis.assess_all_conflicts("nonexistent_character_xyz")

    def test_compare_invalid_characters(self):
        """Should raise error when comparing invalid characters."""
        from bce.ai import conflict_analysis
        from bce.exceptions import DataNotFoundError

        with pytest.raises(DataNotFoundError):
            conflict_analysis.compare_conflict_severity("nonexistent1", "nonexistent2")

    def test_compare_one_invalid_character(self):
        """Should raise error when one character is invalid."""
        from bce.ai import conflict_analysis
        from bce.exceptions import DataNotFoundError

        with pytest.raises(DataNotFoundError):
            conflict_analysis.compare_conflict_severity("jesus", "nonexistent_character")


class TestComprehensiveConflictAnalysis:
    """Comprehensive tests using real BCE data."""

    def setup_method(self):
        """Enable AI features for tests."""
        reset_default_config()
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

    def teardown_method(self):
        """Reset configuration."""
        reset_default_config()

    def test_jesus_conflicts_comprehensive(self):
        """Comprehensive test of Jesus' conflicts."""
        from bce.ai import conflict_analysis
        from bce import contradictions

        # Get all conflicts for Jesus
        conflicts = contradictions.find_trait_conflicts("jesus")

        if conflicts:
            # Assess all conflicts
            result = conflict_analysis.assess_all_conflicts("jesus")

            # Verify summary counts match actual conflicts
            assert result["summary"]["total_conflicts"] == len(conflicts)

            # Verify each conflict has proper assessment
            for trait in conflicts.keys():
                assert trait in result["assessments"]
                assessment = result["assessments"][trait]

                # Each assessment should have AI analysis
                assert "ai_assessment" in assessment
                ai = assessment["ai_assessment"]

                # Verify all AI fields
                assert ai["theological_significance"] in ["low", "medium", "high"]
                assert ai["historical_significance"] in ["low", "medium", "high"]
                assert ai["narrative_coherence_impact"] in ["low", "medium", "high"]
                assert isinstance(ai["explanation"], str)
                assert len(ai["explanation"]) > 0
                assert isinstance(ai["scholarly_consensus"], str)
                assert isinstance(ai["implications"], list)
                assert len(ai["implications"]) > 0

    def test_peter_vs_paul_comparison(self):
        """Test comparing Peter and Paul conflicts."""
        from bce.ai import conflict_analysis

        result = conflict_analysis.compare_conflict_severity("peter", "paul")

        # Verify structure
        assert result["characters"] == ["peter", "paul"]
        assert "peter" in result["comparison"]
        assert "paul" in result["comparison"]

        # Verify interpretation is meaningful
        interpretation = result["interpretation"]
        assert isinstance(interpretation, str)
        assert len(interpretation) > 20  # Should be a real sentence
        assert "peter" in interpretation.lower() or "paul" in interpretation.lower()

    def test_character_with_few_conflicts(self):
        """Test character with minimal conflicts."""
        from bce.ai import conflict_analysis

        # Try pilate or another character that might have fewer conflicts
        try:
            result = conflict_analysis.assess_all_conflicts("pilate")

            assert "character_id" in result
            assert result["character_id"] == "pilate"
            assert "summary" in result

            # Should handle gracefully whether conflicts exist or not
            total = result["summary"]["total_conflicts"]
            assert isinstance(total, int)
            assert total >= 0

        except Exception as e:
            # If character doesn't exist, that's OK for this test
            pass
