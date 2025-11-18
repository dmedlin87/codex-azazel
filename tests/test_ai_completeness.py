"""
Tests for AI completeness auditing module (Phase 6.2).

Comprehensive tests for bce/ai/completeness.py to achieve 75-80% coverage.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from bce.config import BceConfig, set_default_config, reset_default_config
from bce.exceptions import ConfigurationError
from bce.models import Character, Event, SourceProfile, EventAccount
from bce.ai import completeness


class TestCompletenessWithAIDisabled:
    """Tests that verify AI features are properly gated."""

    def setup_method(self):
        """Reset configuration before each test."""
        reset_default_config()
        os.environ.pop("BCE_ENABLE_AI_FEATURES", None)

    def teardown_method(self):
        """Clean up after each test."""
        reset_default_config()

    def test_audit_character_requires_ai_enabled(self):
        """Should raise ConfigurationError when AI is disabled."""
        config = BceConfig(enable_ai_features=False)
        set_default_config(config)

        with pytest.raises(ConfigurationError, match="AI features are disabled"):
            completeness.audit_character("jesus")

    def test_audit_characters_requires_ai_enabled(self):
        """Should raise ConfigurationError when AI is disabled."""
        config = BceConfig(enable_ai_features=False)
        set_default_config(config)

        with pytest.raises(ConfigurationError, match="AI features are disabled"):
            completeness.audit_characters()

    def test_audit_event_requires_ai_enabled(self):
        """Should raise ConfigurationError when AI is disabled."""
        config = BceConfig(enable_ai_features=False)
        set_default_config(config)

        with pytest.raises(ConfigurationError, match="AI features are disabled"):
            completeness.audit_event("crucifixion")

    def test_audit_events_requires_ai_enabled(self):
        """Should raise ConfigurationError when AI is disabled."""
        config = BceConfig(enable_ai_features=False)
        set_default_config(config)

        with pytest.raises(ConfigurationError, match="AI features are disabled"):
            completeness.audit_events()


class TestCharacterAudit:
    """Tests for character completeness auditing."""

    def setup_method(self):
        """Enable AI features for testing."""
        reset_default_config()
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

    def teardown_method(self):
        """Clean up after each test."""
        reset_default_config()

    def test_audit_character_basic_structure(self):
        """Should return audit with required fields."""
        result = completeness.audit_character("jesus", use_cache=False)

        # Check required fields
        assert "character_id" in result
        assert "canonical_name" in result
        assert "completeness_score" in result
        assert "score_components" in result
        assert "gaps" in result
        assert "inconsistencies" in result
        assert "gap_count" in result
        assert "inconsistency_count" in result

        # Check types
        assert isinstance(result["completeness_score"], (int, float))
        assert isinstance(result["score_components"], dict)
        assert isinstance(result["gaps"], list)
        assert isinstance(result["inconsistencies"], list)
        assert isinstance(result["gap_count"], int)
        assert isinstance(result["inconsistency_count"], int)

    def test_audit_character_score_range(self):
        """Completeness score should be between 0.0 and 1.0."""
        result = completeness.audit_character("jesus", use_cache=False)
        score = result["completeness_score"]

        assert 0.0 <= score <= 1.0

    def test_audit_character_with_complete_data(self):
        """Jesus character should have high completeness score."""
        result = completeness.audit_character("jesus", use_cache=False)

        # Jesus is well-documented, should have high score
        assert result["completeness_score"] >= 0.7
        assert result["character_id"] == "jesus"

    def test_audit_character_score_components(self):
        """Should include all expected score components."""
        result = completeness.audit_character("jesus", use_cache=False)
        components = result["score_components"]

        # Check all expected components exist
        expected_components = [
            "has_source_profiles",
            "trait_coverage",
            "has_references",
            "has_tags",
            "has_relationships",
        ]

        for component in expected_components:
            assert component in components
            assert isinstance(components[component], (int, float))
            assert 0.0 <= components[component] <= 1.0

    def test_audit_character_gap_structure(self):
        """Gaps should have proper structure."""
        # Use a less complete character if available, otherwise use any
        result = completeness.audit_character("jesus", use_cache=False)

        for gap in result["gaps"]:
            assert "type" in gap
            assert "priority" in gap
            assert "suggestion" in gap
            # Some gaps may have a "source" field
            if "source" in gap:
                assert isinstance(gap["source"], str)

    def test_audit_character_caching(self):
        """Should use cache when enabled."""
        # First call without cache
        result1 = completeness.audit_character("jesus", use_cache=False)

        # Second call with cache enabled
        result2 = completeness.audit_character("jesus", use_cache=True)

        # Results should be similar (may not be identical due to cache timing)
        assert result1["character_id"] == result2["character_id"]
        assert result1["completeness_score"] == result2["completeness_score"]

    def test_audit_character_no_cache(self):
        """Should skip cache when disabled."""
        result = completeness.audit_character("jesus", use_cache=False)

        # Should successfully return without using cache
        assert result["character_id"] == "jesus"
        assert "completeness_score" in result


class TestCharactersAudit:
    """Tests for auditing all characters."""

    def setup_method(self):
        """Enable AI features for testing."""
        reset_default_config()
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

    def teardown_method(self):
        """Clean up after each test."""
        reset_default_config()

    def test_audit_characters_structure(self):
        """Should return audit with required top-level fields."""
        result = completeness.audit_characters(use_cache=False)

        assert "audit_type" in result
        assert result["audit_type"] == "characters"
        assert "total_characters" in result
        assert "results" in result
        assert "summary" in result

        assert isinstance(result["total_characters"], int)
        assert isinstance(result["results"], dict)
        assert isinstance(result["summary"], dict)

    def test_audit_characters_includes_all_characters(self):
        """Should audit all characters in the dataset."""
        result = completeness.audit_characters(use_cache=False)

        # Should have results for each character
        assert result["total_characters"] > 0
        assert len(result["results"]) == result["total_characters"]

        # Jesus should be included
        assert "jesus" in result["results"]

    def test_audit_characters_summary_structure(self):
        """Summary should have expected fields."""
        result = completeness.audit_characters(use_cache=False)
        summary = result["summary"]

        expected_fields = [
            "total_gaps",
            "total_inconsistencies",
            "average_completeness",
            "characters_needing_attention",
            "attention_count",
        ]

        for field in expected_fields:
            assert field in summary

        assert isinstance(summary["total_gaps"], int)
        assert isinstance(summary["total_inconsistencies"], int)
        assert isinstance(summary["average_completeness"], (int, float))
        assert isinstance(summary["characters_needing_attention"], list)
        assert isinstance(summary["attention_count"], int)

    def test_audit_characters_summary_consistency(self):
        """Summary attention_count should match list length."""
        result = completeness.audit_characters(use_cache=False)
        summary = result["summary"]

        assert summary["attention_count"] == len(summary["characters_needing_attention"])

    def test_audit_characters_average_completeness_range(self):
        """Average completeness should be between 0.0 and 1.0."""
        result = completeness.audit_characters(use_cache=False)
        avg = result["summary"]["average_completeness"]

        assert 0.0 <= avg <= 1.0

    def test_audit_characters_caching(self):
        """Should cache results when enabled."""
        result1 = completeness.audit_characters(use_cache=False)
        result2 = completeness.audit_characters(use_cache=True)

        # Should have same structure
        assert result1["audit_type"] == result2["audit_type"]
        assert result1["total_characters"] == result2["total_characters"]


class TestEventAudit:
    """Tests for event completeness auditing."""

    def setup_method(self):
        """Enable AI features for testing."""
        reset_default_config()
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

    def teardown_method(self):
        """Clean up after each test."""
        reset_default_config()

    def test_audit_event_basic_structure(self):
        """Should return audit with required fields."""
        result = completeness.audit_event("crucifixion", use_cache=False)

        assert "event_id" in result
        assert "label" in result
        assert "completeness_score" in result
        assert "score_components" in result
        assert "gaps" in result
        assert "inconsistencies" in result
        assert "gap_count" in result
        assert "inconsistency_count" in result

    def test_audit_event_score_range(self):
        """Completeness score should be between 0.0 and 1.0."""
        result = completeness.audit_event("crucifixion", use_cache=False)
        score = result["completeness_score"]

        assert 0.0 <= score <= 1.0

    def test_audit_event_score_components(self):
        """Should include all expected score components."""
        result = completeness.audit_event("crucifixion", use_cache=False)
        components = result["score_components"]

        expected_components = [
            "has_accounts",
            "has_participants",
            "has_tags",
            "has_parallels",
            "account_quality",
        ]

        for component in expected_components:
            assert component in components
            assert isinstance(components[component], (int, float))
            assert 0.0 <= components[component] <= 1.0

    def test_audit_event_gap_structure(self):
        """Gaps should have proper structure."""
        result = completeness.audit_event("crucifixion", use_cache=False)

        for gap in result["gaps"]:
            assert "type" in gap
            assert "priority" in gap
            assert "suggestion" in gap

    def test_audit_event_caching(self):
        """Should use cache when enabled."""
        result1 = completeness.audit_event("crucifixion", use_cache=False)
        result2 = completeness.audit_event("crucifixion", use_cache=True)

        assert result1["event_id"] == result2["event_id"]
        assert result1["completeness_score"] == result2["completeness_score"]


class TestEventsAudit:
    """Tests for auditing all events."""

    def setup_method(self):
        """Enable AI features for testing."""
        reset_default_config()
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

    def teardown_method(self):
        """Clean up after each test."""
        reset_default_config()

    def test_audit_events_structure(self):
        """Should return audit with required top-level fields."""
        result = completeness.audit_events(use_cache=False)

        assert "audit_type" in result
        assert result["audit_type"] == "events"
        assert "total_events" in result
        assert "results" in result
        assert "summary" in result

    def test_audit_events_includes_all_events(self):
        """Should audit all events in the dataset."""
        result = completeness.audit_events(use_cache=False)

        assert result["total_events"] > 0
        assert len(result["results"]) == result["total_events"]

    def test_audit_events_summary_structure(self):
        """Summary should have expected fields."""
        result = completeness.audit_events(use_cache=False)
        summary = result["summary"]

        expected_fields = [
            "total_gaps",
            "total_inconsistencies",
            "average_completeness",
            "events_needing_attention",
            "attention_count",
        ]

        for field in expected_fields:
            assert field in summary

    def test_audit_events_summary_consistency(self):
        """Summary attention_count should match list length."""
        result = completeness.audit_events(use_cache=False)
        summary = result["summary"]

        assert summary["attention_count"] == len(summary["events_needing_attention"])


class TestLikelyAppearsInSource:
    """Tests for the _likely_appears_in_source heuristic."""

    def setup_method(self):
        """Create test character."""
        self.test_char_gospel = Character(
            id="test_char",
            canonical_name="Test Character",
            aliases=[],
            roles=[],
            tags=[],
            relationships=[],
            source_profiles=[
                SourceProfile(
                    source_id="mark",
                    traits={"test": "value"},
                    references=["Mark 1:1"]
                ),
            ],
        )

        self.test_char_paul = Character(
            id="test_char_paul",
            canonical_name="Test Paul Character",
            aliases=[],
            roles=[],
            tags=[],
            relationships=[],
            source_profiles=[
                SourceProfile(
                    source_id="paul_undisputed",
                    traits={"test": "value"},
                    references=["Romans 1:1"]
                ),
            ],
        )

        self.test_char_no_profiles = Character(
            id="test_char_empty",
            canonical_name="Empty Character",
            aliases=[],
            roles=[],
            tags=[],
            relationships=[],
            source_profiles=[],
        )

    def test_likely_appears_gospel_to_gospel(self):
        """Character in one gospel likely appears in other gospels."""
        # Has Mark profile, likely appears in other gospels
        assert completeness._likely_appears_in_source(self.test_char_gospel, "matthew")
        assert completeness._likely_appears_in_source(self.test_char_gospel, "luke")
        assert completeness._likely_appears_in_source(self.test_char_gospel, "john")

    def test_likely_appears_pauline_to_pauline(self):
        """Character in one Pauline source likely appears in others."""
        assert completeness._likely_appears_in_source(
            self.test_char_paul, "paul_disputed"
        )

    def test_not_likely_appears_no_profiles(self):
        """Character with no profiles is not flagged as likely."""
        # Conservative heuristic: don't flag if no profiles
        assert not completeness._likely_appears_in_source(
            self.test_char_no_profiles, "mark"
        )
        assert not completeness._likely_appears_in_source(
            self.test_char_no_profiles, "paul_undisputed"
        )

    def test_not_likely_appears_cross_category(self):
        """Gospel character not automatically flagged for Pauline sources."""
        # Conservative: don't assume gospel char appears in Paul
        assert not completeness._likely_appears_in_source(
            self.test_char_gospel, "paul_undisputed"
        )


class TestSummarizeCharacterAudits:
    """Tests for _summarize_character_audits helper."""

    def test_summarize_empty_audits(self):
        """Should handle empty audit dict."""
        summary = completeness._summarize_character_audits({})

        assert summary["total_gaps"] == 0
        assert summary["total_inconsistencies"] == 0
        assert summary["average_completeness"] == 0.0
        assert summary["characters_needing_attention"] == []
        assert summary["attention_count"] == 0

    def test_summarize_single_audit(self):
        """Should correctly summarize single character."""
        audits = {
            "char1": {
                "gap_count": 3,
                "inconsistency_count": 1,
                "completeness_score": 0.85,
            }
        }

        summary = completeness._summarize_character_audits(audits)

        assert summary["total_gaps"] == 3
        assert summary["total_inconsistencies"] == 1
        assert summary["average_completeness"] == 0.85
        assert "char1" not in summary["characters_needing_attention"]  # 0.85 > 0.70

    def test_summarize_multiple_audits(self):
        """Should correctly aggregate multiple characters."""
        audits = {
            "char1": {
                "gap_count": 3,
                "inconsistency_count": 1,
                "completeness_score": 0.85,
            },
            "char2": {
                "gap_count": 5,
                "inconsistency_count": 2,
                "completeness_score": 0.65,  # Below 0.70 threshold
            },
            "char3": {
                "gap_count": 1,
                "inconsistency_count": 0,
                "completeness_score": 0.95,
            },
        }

        summary = completeness._summarize_character_audits(audits)

        assert summary["total_gaps"] == 9  # 3 + 5 + 1
        assert summary["total_inconsistencies"] == 3  # 1 + 2 + 0
        # Average: (0.85 + 0.65 + 0.95) / 3 = 0.82 (rounded)
        assert abs(summary["average_completeness"] - 0.82) < 0.01
        assert "char2" in summary["characters_needing_attention"]
        assert summary["attention_count"] == 1

    def test_summarize_characters_needing_attention_threshold(self):
        """Characters below 0.70 should need attention."""
        audits = {
            "good1": {"gap_count": 0, "inconsistency_count": 0, "completeness_score": 0.90},
            "good2": {"gap_count": 1, "inconsistency_count": 0, "completeness_score": 0.70},  # Exactly 0.70
            "bad1": {"gap_count": 5, "inconsistency_count": 2, "completeness_score": 0.69},
            "bad2": {"gap_count": 8, "inconsistency_count": 3, "completeness_score": 0.50},
        }

        summary = completeness._summarize_character_audits(audits)

        # Only scores < 0.70 need attention
        assert "bad1" in summary["characters_needing_attention"]
        assert "bad2" in summary["characters_needing_attention"]
        assert "good1" not in summary["characters_needing_attention"]
        assert "good2" not in summary["characters_needing_attention"]
        assert summary["attention_count"] == 2


class TestSummarizeEventAudits:
    """Tests for _summarize_event_audits helper."""

    def test_summarize_empty_audits(self):
        """Should handle empty audit dict."""
        summary = completeness._summarize_event_audits({})

        assert summary["total_gaps"] == 0
        assert summary["total_inconsistencies"] == 0
        assert summary["average_completeness"] == 0.0
        assert summary["events_needing_attention"] == []
        assert summary["attention_count"] == 0

    def test_summarize_single_event(self):
        """Should correctly summarize single event."""
        audits = {
            "event1": {
                "gap_count": 2,
                "inconsistency_count": 0,
                "completeness_score": 0.80,
            }
        }

        summary = completeness._summarize_event_audits(audits)

        assert summary["total_gaps"] == 2
        assert summary["total_inconsistencies"] == 0
        assert summary["average_completeness"] == 0.80
        assert summary["attention_count"] == 0

    def test_summarize_multiple_events(self):
        """Should correctly aggregate multiple events."""
        audits = {
            "event1": {
                "gap_count": 2,
                "inconsistency_count": 1,
                "completeness_score": 0.75,
            },
            "event2": {
                "gap_count": 4,
                "inconsistency_count": 0,
                "completeness_score": 0.60,
            },
        }

        summary = completeness._summarize_event_audits(audits)

        assert summary["total_gaps"] == 6
        assert summary["total_inconsistencies"] == 1
        # Average: (0.75 + 0.60) / 2 = 0.68 (rounded)
        assert abs(summary["average_completeness"] - 0.68) < 0.01
        assert "event2" in summary["events_needing_attention"]
        assert summary["attention_count"] == 1


class TestCompletenessDetection:
    """Tests for specific completeness gap detection."""

    def setup_method(self):
        """Enable AI features for testing."""
        reset_default_config()
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

    def teardown_method(self):
        """Clean up after each test."""
        reset_default_config()

    def test_detect_missing_tags(self):
        """Should detect when character has no tags."""
        # Create mock character without tags
        with patch("bce.ai.completeness.get_character") as mock_get:
            mock_get.return_value = Character(
                id="test_char",
                canonical_name="Test",
                aliases=[],
                roles=["role1"],
                tags=[],  # No tags
                relationships=[],
                source_profiles=[
                    SourceProfile(
                        source_id="mark",
                        traits={"trait1": "value1", "trait2": "value2"},
                        references=["Mark 1:1"]
                    )
                ],
            )

            with patch("bce.ai.completeness.list_source_ids", return_value=["mark"]):
                result = completeness.audit_character("test_char", use_cache=False)

                # Should have gap for missing tags
                missing_tags_gaps = [g for g in result["gaps"] if g["type"] == "missing_tags"]
                assert len(missing_tags_gaps) > 0

    def test_detect_missing_relationships(self):
        """Should detect when character has no relationships."""
        with patch("bce.ai.completeness.get_character") as mock_get:
            mock_get.return_value = Character(
                id="test_char",
                canonical_name="Test",
                aliases=[],
                roles=["role1"],
                tags=["tag1"],
                relationships=[],  # No relationships
                source_profiles=[
                    SourceProfile(
                        source_id="mark",
                        traits={"trait1": "value1"},
                        references=["Mark 1:1"]
                    )
                ],
            )

            with patch("bce.ai.completeness.list_source_ids", return_value=["mark"]):
                result = completeness.audit_character("test_char", use_cache=False)

                # Should have gap for missing relationships
                missing_rel_gaps = [g for g in result["gaps"] if g["type"] == "missing_relationships"]
                assert len(missing_rel_gaps) > 0

    def test_detect_sparse_traits(self):
        """Should detect profiles with very few traits."""
        with patch("bce.ai.completeness.get_character") as mock_get:
            mock_get.return_value = Character(
                id="test_char",
                canonical_name="Test",
                aliases=[],
                roles=[],
                tags=["tag1"],
                relationships=[],
                source_profiles=[
                    SourceProfile(
                        source_id="mark",
                        traits={"only_one": "trait"},  # Only 1 trait
                        references=["Mark 1:1"]
                    )
                ],
            )

            with patch("bce.ai.completeness.list_source_ids", return_value=["mark"]):
                result = completeness.audit_character("test_char", use_cache=False)

                # Should have gap for sparse traits
                sparse_gaps = [g for g in result["gaps"] if g["type"] == "sparse_traits"]
                assert len(sparse_gaps) > 0

    def test_detect_missing_references(self):
        """Should detect profiles without scripture references."""
        with patch("bce.ai.completeness.get_character") as mock_get:
            mock_get.return_value = Character(
                id="test_char",
                canonical_name="Test",
                aliases=[],
                roles=[],
                tags=["tag1"],
                relationships=[],
                source_profiles=[
                    SourceProfile(
                        source_id="mark",
                        traits={"trait1": "value1", "trait2": "value2"},
                        references=[]  # No references
                    )
                ],
            )

            with patch("bce.ai.completeness.list_source_ids", return_value=["mark"]):
                result = completeness.audit_character("test_char", use_cache=False)

                # Should have high-priority gap for missing references
                missing_ref_gaps = [g for g in result["gaps"] if g["type"] == "missing_references"]
                assert len(missing_ref_gaps) > 0
                assert missing_ref_gaps[0]["priority"] == "high"

    def test_detect_event_no_accounts(self):
        """Should detect events with no accounts."""
        with patch("bce.ai.completeness.get_event") as mock_get:
            mock_get.return_value = Event(
                id="test_event",
                label="Test Event",
                participants=["char1"],
                tags=["tag1"],
                parallels=[],
                accounts=[]  # No accounts
            )

            result = completeness.audit_event("test_event", use_cache=False)

            # Should have critical gap for no accounts
            no_account_gaps = [g for g in result["gaps"] if g["type"] == "no_accounts"]
            assert len(no_account_gaps) > 0
            assert no_account_gaps[0]["priority"] == "critical"

    def test_detect_event_single_account(self):
        """Should detect events with only one account."""
        with patch("bce.ai.completeness.get_event") as mock_get:
            mock_get.return_value = Event(
                id="test_event",
                label="Test Event",
                participants=["char1"],
                tags=["tag1"],
                parallels=[],
                accounts=[
                    EventAccount(
                        source_id="mark",
                        reference="Mark 1:1",
                        summary="Summary text here",
                        notes=None
                    )
                ]  # Only one account
            )

            result = completeness.audit_event("test_event", use_cache=False)

            # Should have gap for single account
            single_account_gaps = [g for g in result["gaps"] if g["type"] == "single_account"]
            assert len(single_account_gaps) > 0

    def test_detect_event_missing_participants(self):
        """Should detect events with no participants."""
        with patch("bce.ai.completeness.get_event") as mock_get:
            mock_get.return_value = Event(
                id="test_event",
                label="Test Event",
                participants=[],  # No participants
                tags=["tag1"],
                parallels=[],
                accounts=[
                    EventAccount(
                        source_id="mark",
                        reference="Mark 1:1",
                        summary="Summary",
                        notes=None
                    )
                ]
            )

            result = completeness.audit_event("test_event", use_cache=False)

            # Should have high-priority gap for missing participants
            missing_part_gaps = [g for g in result["gaps"] if g["type"] == "missing_participants"]
            assert len(missing_part_gaps) > 0
            assert missing_part_gaps[0]["priority"] == "high"

    def test_detect_sparse_account_summary(self):
        """Should detect accounts with very brief summaries."""
        with patch("bce.ai.completeness.get_event") as mock_get:
            mock_get.return_value = Event(
                id="test_event",
                label="Test Event",
                participants=["char1"],
                tags=["tag1"],
                parallels=[],
                accounts=[
                    EventAccount(
                        source_id="mark",
                        reference="Mark 1:1",
                        summary="Short",  # Very brief summary
                        notes=None
                    )
                ]
            )

            result = completeness.audit_event("test_event", use_cache=False)

            # Should have gap for sparse summary
            sparse_summary_gaps = [g for g in result["gaps"] if g["type"] == "sparse_account_summary"]
            assert len(sparse_summary_gaps) > 0
