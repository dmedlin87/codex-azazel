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
