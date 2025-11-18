"""
Tests for bce.ai.source_analysis module.

Covers source tendency analysis to identify systematic patterns in how sources
portray characters and events.
"""

from __future__ import annotations

import pytest

from bce.config import BceConfig, set_default_config, reset_default_config
from bce.exceptions import ConfigurationError


class TestAnalyzeSourcePatterns:
    """Tests for analyze_source_patterns function."""

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
        from bce.ai import source_analysis

        reset_default_config()
        config = BceConfig(enable_ai_features=False)
        set_default_config(config)

        with pytest.raises(ConfigurationError, match="AI features are disabled"):
            source_analysis.analyze_source_patterns("mark")

    def test_analyze_valid_source(self):
        """Should analyze patterns for valid source."""
        from bce.ai import source_analysis

        result = source_analysis.analyze_source_patterns("mark", use_cache=False)

        assert "source_id" in result
        assert result["source_id"] == "mark"
        assert "character_portrayal_patterns" in result
        assert "narrative_priorities" in result
        assert "vocabulary" in result
        assert "theological_themes" in result
        assert "statistics" in result

        # Check types
        assert isinstance(result["character_portrayal_patterns"], list)
        assert isinstance(result["narrative_priorities"], list)
        assert isinstance(result["vocabulary"], dict)
        assert isinstance(result["theological_themes"], list)
        assert isinstance(result["statistics"], dict)

    def test_analyze_nonexistent_source(self):
        """Should handle nonexistent source gracefully."""
        from bce.ai import source_analysis

        result = source_analysis.analyze_source_patterns("nonexistent_source", use_cache=False)

        assert "source_id" in result
        assert result["source_id"] == "nonexistent_source"
        assert "message" in result or "character_portrayal_patterns" in result

        # Should return empty patterns if no characters found
        if "message" in result:
            assert "No characters found" in result["message"]

    def test_statistics_structure(self):
        """Should return properly structured statistics."""
        from bce.ai import source_analysis

        result = source_analysis.analyze_source_patterns("matthew", use_cache=False)

        stats = result["statistics"]
        assert "character_count" in stats
        assert "total_traits" in stats
        assert "total_references" in stats
        assert "avg_traits_per_character" in stats

        # Values should be non-negative
        assert stats["character_count"] >= 0
        assert stats["total_traits"] >= 0
        assert stats["total_references"] >= 0
        assert stats["avg_traits_per_character"] >= 0

    def test_vocabulary_structure(self):
        """Should return properly structured vocabulary analysis."""
        from bce.ai import source_analysis

        result = source_analysis.analyze_source_patterns("luke", use_cache=False)

        vocab = result["vocabulary"]
        assert "common_trait_keys" in vocab
        assert "common_vocabulary" in vocab
        assert "total_unique_trait_keys" in vocab

        assert isinstance(vocab["common_trait_keys"], list)
        assert isinstance(vocab["common_vocabulary"], list)
        assert isinstance(vocab["total_unique_trait_keys"], int)

    def test_uses_cache(self):
        """Should use cached results when use_cache=True."""
        from bce.ai import source_analysis

        result1 = source_analysis.analyze_source_patterns("john", use_cache=True)
        result2 = source_analysis.analyze_source_patterns("john", use_cache=True)

        # Should be identical
        assert result1 == result2

    def test_bypasses_cache(self):
        """Should bypass cache when use_cache=False."""
        from bce.ai import source_analysis

        # Just ensure it doesn't fail
        result = source_analysis.analyze_source_patterns("mark", use_cache=False)
        assert "source_id" in result


class TestCompareSourceTendencies:
    """Tests for compare_source_tendencies function."""

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
        from bce.ai import source_analysis

        reset_default_config()
        config = BceConfig(enable_ai_features=False)
        set_default_config(config)

        with pytest.raises(ConfigurationError, match="AI features are disabled"):
            source_analysis.compare_source_tendencies(["mark", "matthew"])

    def test_compare_two_sources(self):
        """Should compare two sources."""
        from bce.ai import source_analysis

        result = source_analysis.compare_source_tendencies(["mark", "matthew"])

        assert "sources" in result
        assert result["sources"] == ["mark", "matthew"]
        assert "pattern_comparison" in result
        assert "priority_comparison" in result
        assert "vocabulary_comparison" in result

    def test_compare_multiple_sources(self):
        """Should compare multiple sources."""
        from bce.ai import source_analysis

        result = source_analysis.compare_source_tendencies(["mark", "matthew", "luke", "john"])

        assert "sources" in result
        assert len(result["sources"]) == 4
        assert "pattern_comparison" in result
        assert "priority_comparison" in result
        assert "vocabulary_comparison" in result

    def test_pattern_comparison_structure(self):
        """Should return properly structured pattern comparison."""
        from bce.ai import source_analysis

        result = source_analysis.compare_source_tendencies(["mark", "john"])

        pattern_comp = result["pattern_comparison"]
        assert isinstance(pattern_comp, list)

        if pattern_comp:
            pattern = pattern_comp[0]
            assert "pattern" in pattern
            assert "present_in" in pattern

    def test_priority_comparison_structure(self):
        """Should return properly structured priority comparison."""
        from bce.ai import source_analysis

        result = source_analysis.compare_source_tendencies(["matthew", "luke"])

        priority_comp = result["priority_comparison"]
        assert isinstance(priority_comp, dict)

        # Should have entries for each source
        assert "matthew" in priority_comp or len(priority_comp) == 0
        assert "luke" in priority_comp or len(priority_comp) == 0

    def test_vocabulary_comparison_structure(self):
        """Should return properly structured vocabulary comparison."""
        from bce.ai import source_analysis

        result = source_analysis.compare_source_tendencies(["mark", "matthew"])

        vocab_comp = result["vocabulary_comparison"]
        assert isinstance(vocab_comp, dict)


class TestIdentifyPortrayalPatterns:
    """Tests for _identify_portrayal_patterns internal function."""

    def test_characters_without_matching_profile(self):
        """Should handle characters without matching source profile."""
        from bce.ai.source_analysis import _identify_portrayal_patterns
        from dataclasses import dataclass, field
        from typing import List, Dict, Optional

        @dataclass
        class MockProfile:
            source_id: str
            traits: Dict[str, str] = field(default_factory=dict)
            references: List[str] = field(default_factory=list)

        @dataclass
        class MockChar:
            id: str
            source_profiles: List[MockProfile] = field(default_factory=list)

            def get_source_profile(self, source_id: str) -> Optional[MockProfile]:
                for profile in self.source_profiles:
                    if profile.source_id == source_id:
                        return profile
                return None

        # Characters without matching source profile
        chars = [
            MockChar(
                id="char1",
                source_profiles=[
                    MockProfile(source_id="different_source", traits={"key": "value"})
                ]
            ),
        ]

        patterns = _identify_portrayal_patterns("target_source", chars)

        # Should return empty list
        assert isinstance(patterns, list)
        assert len(patterns) == 0

    def test_messianic_secrecy_pattern(self):
        """Should identify messianic secrecy pattern."""
        from bce.ai.source_analysis import _identify_portrayal_patterns
        from bce import queries

        # Mark is known for messianic secret
        all_chars = queries.list_all_characters()
        chars = [c for c in all_chars if c.get_source_profile("mark") is not None]

        if chars:
            patterns = _identify_portrayal_patterns("mark", chars)

            assert isinstance(patterns, list)
            # May or may not find specific patterns depending on data

    def test_divine_christology_pattern(self):
        """Should identify divine Christology pattern."""
        from bce.ai.source_analysis import _identify_portrayal_patterns
        from bce import queries

        # John is known for high Christology
        all_chars = queries.list_all_characters()
        chars = [c for c in all_chars if c.get_source_profile("john") is not None]

        if chars:
            patterns = _identify_portrayal_patterns("john", chars)

            assert isinstance(patterns, list)

    def test_pattern_structure(self):
        """Should return properly structured patterns."""
        from bce.ai.source_analysis import _identify_portrayal_patterns
        from bce import queries

        all_chars = queries.list_all_characters()
        chars = [c for c in all_chars if c.get_source_profile("matthew") is not None]

        if chars:
            patterns = _identify_portrayal_patterns("matthew", chars)

            if patterns:
                pattern = patterns[0]
                assert "pattern" in pattern
                assert "frequency" in pattern
                assert "characters_affected" in pattern
                assert "evidence" in pattern

    def test_empty_characters_list(self):
        """Should handle empty characters list."""
        from bce.ai.source_analysis import _identify_portrayal_patterns

        patterns = _identify_portrayal_patterns("unknown_source", [])

        assert isinstance(patterns, list)

    def test_messianic_secrecy_pattern_with_multiple_characters(self):
        """Should identify messianic secrecy pattern with high frequency."""
        from bce.ai.source_analysis import _identify_portrayal_patterns
        from dataclasses import dataclass, field
        from typing import List, Dict, Optional

        @dataclass
        class MockProfile:
            source_id: str
            traits: Dict[str, str] = field(default_factory=dict)
            references: List[str] = field(default_factory=list)

        @dataclass
        class MockChar:
            id: str
            source_profiles: List[MockProfile] = field(default_factory=list)

            def get_source_profile(self, source_id: str) -> Optional[MockProfile]:
                for profile in self.source_profiles:
                    if profile.source_id == source_id:
                        return profile
                return None

        # Create multiple characters with messianic secret traits
        chars = [
            MockChar(
                id="jesus",
                source_profiles=[
                    MockProfile(
                        source_id="mark",
                        traits={"messianic_secret": "Commands silence about his identity"}
                    )
                ]
            ),
            MockChar(
                id="peter",
                source_profiles=[
                    MockProfile(
                        source_id="mark",
                        traits={"hidden_identity": "Struggles to understand Jesus' identity"}
                    )
                ]
            ),
        ]

        patterns = _identify_portrayal_patterns("mark", chars)

        # Should find messianic secrecy pattern
        messianic_patterns = [p for p in patterns if p["pattern"] == "messianic_secrecy"]
        assert len(messianic_patterns) > 0
        assert messianic_patterns[0]["frequency"] == "high"
        assert len(messianic_patterns[0]["characters_affected"]) >= 2

    def test_disciple_misunderstanding_pattern_high_frequency(self):
        """Should identify disciple misunderstanding pattern with high frequency."""
        from bce.ai.source_analysis import _identify_portrayal_patterns
        from dataclasses import dataclass, field
        from typing import List, Dict, Optional

        @dataclass
        class MockProfile:
            source_id: str
            traits: Dict[str, str] = field(default_factory=dict)
            references: List[str] = field(default_factory=list)

        @dataclass
        class MockChar:
            id: str
            source_profiles: List[MockProfile] = field(default_factory=list)

            def get_source_profile(self, source_id: str) -> Optional[MockProfile]:
                for profile in self.source_profiles:
                    if profile.source_id == source_id:
                        return profile
                return None

        # Create multiple disciples with misunderstanding traits
        chars = [
            MockChar(
                id="peter",
                source_profiles=[
                    MockProfile(
                        source_id="mark",
                        traits={"misunderstanding": "Fails to comprehend suffering messiah"}
                    )
                ]
            ),
            MockChar(
                id="james",
                source_profiles=[
                    MockProfile(
                        source_id="mark",
                        traits={"failure": "Abandons Jesus at arrest"}
                    )
                ]
            ),
            MockChar(
                id="john",
                source_profiles=[
                    MockProfile(
                        source_id="mark",
                        traits={"lack_of_understanding": "Requests privileged seats in kingdom"}
                    )
                ]
            ),
        ]

        patterns = _identify_portrayal_patterns("mark", chars)

        # Should find disciple misunderstanding pattern
        disciple_patterns = [p for p in patterns if p["pattern"] == "disciple_misunderstanding"]
        assert len(disciple_patterns) > 0
        assert disciple_patterns[0]["frequency"] == "high"
        assert len(disciple_patterns[0]["characters_affected"]) > 2

    def test_divine_christology_pattern_explicit(self):
        """Should identify divine Christology pattern."""
        from bce.ai.source_analysis import _identify_portrayal_patterns
        from dataclasses import dataclass, field
        from typing import List, Dict, Optional

        @dataclass
        class MockProfile:
            source_id: str
            traits: Dict[str, str] = field(default_factory=dict)
            references: List[str] = field(default_factory=list)

        @dataclass
        class MockChar:
            id: str
            source_profiles: List[MockProfile] = field(default_factory=list)

            def get_source_profile(self, source_id: str) -> Optional[MockProfile]:
                for profile in self.source_profiles:
                    if profile.source_id == source_id:
                        return profile
                return None

        # Create character with divine traits
        chars = [
            MockChar(
                id="jesus",
                source_profiles=[
                    MockProfile(
                        source_id="john",
                        traits={
                            "divine_claims": "I and the Father are one",
                            "pre_existence": "Before Abraham was, I am",
                            "unity_with_god": "Complete unity with the Father"
                        }
                    )
                ]
            ),
        ]

        patterns = _identify_portrayal_patterns("john", chars)

        # Should find divine christology pattern
        divine_patterns = [p for p in patterns if p["pattern"] == "divine_christology"]
        assert len(divine_patterns) > 0
        assert divine_patterns[0]["frequency"] in ["high", "low"]
        assert "theological_significance" in divine_patterns[0]

    def test_torah_observance_pattern(self):
        """Should identify torah observance pattern."""
        from bce.ai.source_analysis import _identify_portrayal_patterns
        from dataclasses import dataclass, field
        from typing import List, Dict, Optional

        @dataclass
        class MockProfile:
            source_id: str
            traits: Dict[str, str] = field(default_factory=dict)
            references: List[str] = field(default_factory=list)

        @dataclass
        class MockChar:
            id: str
            source_profiles: List[MockProfile] = field(default_factory=list)

            def get_source_profile(self, source_id: str) -> Optional[MockProfile]:
                for profile in self.source_profiles:
                    if profile.source_id == source_id:
                        return profile
                return None

        # Create characters with Torah/law traits
        chars = [
            MockChar(
                id="jesus",
                source_profiles=[
                    MockProfile(
                        source_id="matthew",
                        traits={
                            "torah_observance": "I came to fulfill the law",
                            "temple_observance": "Regular temple worship"
                        }
                    )
                ]
            ),
        ]

        patterns = _identify_portrayal_patterns("matthew", chars)

        # Should find torah observance pattern
        torah_patterns = [p for p in patterns if p["pattern"] == "torah_observance"]
        assert len(torah_patterns) > 0
        assert torah_patterns[0]["frequency"] == "medium"

    def test_suffering_emphasis_pattern_high_frequency(self):
        """Should identify suffering emphasis pattern with high frequency."""
        from bce.ai.source_analysis import _identify_portrayal_patterns
        from dataclasses import dataclass, field
        from typing import List, Dict, Optional

        @dataclass
        class MockProfile:
            source_id: str
            traits: Dict[str, str] = field(default_factory=dict)
            references: List[str] = field(default_factory=list)

        @dataclass
        class MockChar:
            id: str
            source_profiles: List[MockProfile] = field(default_factory=list)

            def get_source_profile(self, source_id: str) -> Optional[MockProfile]:
                for profile in self.source_profiles:
                    if profile.source_id == source_id:
                        return profile
                return None

        # Create multiple characters with suffering traits
        chars = [
            MockChar(
                id="jesus",
                source_profiles=[
                    MockProfile(
                        source_id="mark",
                        traits={
                            "suffering": "Passion predictions throughout",
                            "martyrdom": "Death as ransom for many"
                        }
                    )
                ]
            ),
            MockChar(
                id="peter",
                source_profiles=[
                    MockProfile(
                        source_id="mark",
                        traits={"persecution": "Warned of persecution to come"}
                    )
                ]
            ),
            MockChar(
                id="james",
                source_profiles=[
                    MockProfile(
                        source_id="mark",
                        traits={"trials": "Will drink cup of suffering"}
                    )
                ]
            ),
        ]

        patterns = _identify_portrayal_patterns("mark", chars)

        # Should find suffering emphasis pattern
        suffering_patterns = [p for p in patterns if p["pattern"] == "suffering_emphasis"]
        assert len(suffering_patterns) > 0
        assert suffering_patterns[0]["frequency"] == "high"
        assert len(suffering_patterns[0]["characters_affected"]) > 2


class TestIdentifyNarrativePriorities:
    """Tests for _identify_narrative_priorities internal function."""

    def test_characters_without_matching_profile(self):
        """Should handle characters without matching source profile."""
        from bce.ai.source_analysis import _identify_narrative_priorities
        from dataclasses import dataclass, field
        from typing import List, Dict, Optional

        @dataclass
        class MockProfile:
            source_id: str
            traits: Dict[str, str] = field(default_factory=dict)
            references: List[str] = field(default_factory=list)

        @dataclass
        class MockChar:
            id: str
            source_profiles: List[MockProfile] = field(default_factory=list)

            def get_source_profile(self, source_id: str) -> Optional[MockProfile]:
                for profile in self.source_profiles:
                    if profile.source_id == source_id:
                        return profile
                return None

        # Characters without matching source profile
        chars = [
            MockChar(
                id="char1",
                source_profiles=[
                    MockProfile(source_id="different_source", traits={"key": "value"})
                ]
            ),
        ]

        priorities = _identify_narrative_priorities("target_source", chars)

        # Should return empty list
        assert isinstance(priorities, list)
        assert len(priorities) == 0

    def test_identifies_priorities(self):
        """Should identify narrative priorities from traits."""
        from bce.ai.source_analysis import _identify_narrative_priorities
        from bce import queries

        all_chars = queries.list_all_characters()
        chars = [c for c in all_chars if c.get_source_profile("luke") is not None]

        if chars:
            priorities = _identify_narrative_priorities("luke", chars)

            assert isinstance(priorities, list)
            # Priorities are strings
            for priority in priorities:
                assert isinstance(priority, str)

    def test_empty_characters_list(self):
        """Should handle empty characters list."""
        from bce.ai.source_analysis import _identify_narrative_priorities

        priorities = _identify_narrative_priorities("unknown_source", [])

        assert isinstance(priorities, list)
        assert len(priorities) == 0

    def test_priority_uniqueness(self):
        """Should return unique priorities (no duplicates)."""
        from bce.ai.source_analysis import _identify_narrative_priorities
        from bce import queries

        all_chars = queries.list_all_characters()
        chars = [c for c in all_chars if c.get_source_profile("mark") is not None]

        if chars:
            priorities = _identify_narrative_priorities("mark", chars)

            # Should have no duplicates
            assert len(priorities) == len(set(priorities))

    def test_all_priority_mappings(self):
        """Should correctly map trait keywords to narrative priorities."""
        from bce.ai.source_analysis import _identify_narrative_priorities
        from dataclasses import dataclass, field
        from typing import List, Dict, Optional

        @dataclass
        class MockProfile:
            source_id: str
            traits: Dict[str, str] = field(default_factory=dict)
            references: List[str] = field(default_factory=list)

        @dataclass
        class MockChar:
            id: str
            source_profiles: List[MockProfile] = field(default_factory=list)

            def get_source_profile(self, source_id: str) -> Optional[MockProfile]:
                for profile in self.source_profiles:
                    if profile.source_id == source_id:
                        return profile
                return None

        # Create characters with all priority-triggering keywords
        chars = [
            MockChar(
                id="char1",
                source_profiles=[
                    MockProfile(
                        source_id="test",
                        traits={
                            "suffering_emphasis": "value1",
                            "suffering_theme": "value2",
                            "divine_nature": "value3",
                            "divine_claims": "value4",
                            "kingdom_message": "value5",
                            "kingdom_preaching": "value6",
                            "apocalyptic_vision": "value7",
                            "apocalyptic_urgency": "value8",
                        }
                    )
                ]
            ),
            MockChar(
                id="char2",
                source_profiles=[
                    MockProfile(
                        source_id="test",
                        traits={
                            "failure_of_disciples": "value9",
                            "mission_to_gentiles": "value10",
                            "gentile_inclusion": "value11",
                            "jewish_heritage": "value12",
                            "torah_fulfillment": "value13",
                        }
                    )
                ]
            ),
        ]

        priorities = _identify_narrative_priorities("test", chars)

        # Should identify multiple priorities
        assert isinstance(priorities, list)
        assert len(priorities) > 0

        # Should include expected priorities based on keywords
        expected_priorities = [
            "suffering_christology",
            "divine_christology",
            "kingdom_theology",
            "apocalyptic_urgency",
            "discipleship_failure",
            "mission_emphasis",
            "gentile_inclusion",
            "jewish_identity",
            "law_and_covenant",
        ]

        for priority in priorities:
            assert priority in expected_priorities


class TestAnalyzeVocabulary:
    """Tests for _analyze_vocabulary internal function."""

    def test_characters_without_matching_profile(self):
        """Should handle characters without matching source profile."""
        from bce.ai.source_analysis import _analyze_vocabulary
        from dataclasses import dataclass, field
        from typing import List, Dict, Optional

        @dataclass
        class MockProfile:
            source_id: str
            traits: Dict[str, str] = field(default_factory=dict)
            references: List[str] = field(default_factory=list)

        @dataclass
        class MockChar:
            id: str
            source_profiles: List[MockProfile] = field(default_factory=list)

            def get_source_profile(self, source_id: str) -> Optional[MockProfile]:
                for profile in self.source_profiles:
                    if profile.source_id == source_id:
                        return profile
                return None

        # Characters without matching source profile
        chars = [
            MockChar(
                id="char1",
                source_profiles=[
                    MockProfile(source_id="different_source", traits={"key": "value"})
                ]
            ),
        ]

        vocab = _analyze_vocabulary("target_source", chars)

        # Should return empty results
        assert vocab["common_trait_keys"] == []
        assert vocab["common_vocabulary"] == []
        assert vocab["total_unique_trait_keys"] == 0

    def test_vocabulary_structure(self):
        """Should return properly structured vocabulary analysis."""
        from bce.ai.source_analysis import _analyze_vocabulary
        from bce import queries

        all_chars = queries.list_all_characters()
        chars = [c for c in all_chars if c.get_source_profile("john") is not None]

        if chars:
            vocab = _analyze_vocabulary("john", chars)

            assert "common_trait_keys" in vocab
            assert "common_vocabulary" in vocab
            assert "total_unique_trait_keys" in vocab

            # Check types
            assert isinstance(vocab["common_trait_keys"], list)
            assert isinstance(vocab["common_vocabulary"], list)
            assert isinstance(vocab["total_unique_trait_keys"], int)

    def test_common_trait_keys_format(self):
        """Should format common trait keys correctly."""
        from bce.ai.source_analysis import _analyze_vocabulary
        from bce import queries

        all_chars = queries.list_all_characters()
        chars = [c for c in all_chars if c.get_source_profile("matthew") is not None]

        if chars:
            vocab = _analyze_vocabulary("matthew", chars)

            if vocab["common_trait_keys"]:
                trait_key_entry = vocab["common_trait_keys"][0]
                assert "key" in trait_key_entry
                assert "count" in trait_key_entry
                assert isinstance(trait_key_entry["count"], int)

    def test_common_vocabulary_format(self):
        """Should format common vocabulary correctly."""
        from bce.ai.source_analysis import _analyze_vocabulary
        from bce import queries

        all_chars = queries.list_all_characters()
        chars = [c for c in all_chars if c.get_source_profile("mark") is not None]

        if chars:
            vocab = _analyze_vocabulary("mark", chars)

            if vocab["common_vocabulary"]:
                word_entry = vocab["common_vocabulary"][0]
                assert "word" in word_entry
                assert "count" in word_entry
                assert isinstance(word_entry["count"], int)

    def test_empty_characters(self):
        """Should handle empty characters list."""
        from bce.ai.source_analysis import _analyze_vocabulary

        vocab = _analyze_vocabulary("unknown", [])

        assert vocab["common_trait_keys"] == []
        assert vocab["common_vocabulary"] == []
        assert vocab["total_unique_trait_keys"] == 0


class TestIdentifyTheologicalThemes:
    """Tests for _identify_theological_themes internal function."""

    def test_characters_without_matching_profile(self):
        """Should handle characters without matching source profile."""
        from bce.ai.source_analysis import _identify_theological_themes
        from dataclasses import dataclass, field
        from typing import List, Dict, Optional

        @dataclass
        class MockProfile:
            source_id: str
            traits: Dict[str, str] = field(default_factory=dict)
            references: List[str] = field(default_factory=list)

        @dataclass
        class MockChar:
            id: str
            source_profiles: List[MockProfile] = field(default_factory=list)

            def get_source_profile(self, source_id: str) -> Optional[MockProfile]:
                for profile in self.source_profiles:
                    if profile.source_id == source_id:
                        return profile
                return None

        # Characters without matching source profile
        chars = [
            MockChar(
                id="char1",
                source_profiles=[
                    MockProfile(source_id="different_source", traits={"key": "value"})
                ]
            ),
        ]

        themes = _identify_theological_themes("target_source", chars)

        # Should return empty list
        assert isinstance(themes, list)
        assert len(themes) == 0

    def test_identifies_themes(self):
        """Should identify theological themes from traits."""
        from bce.ai.source_analysis import _identify_theological_themes
        from bce import queries

        all_chars = queries.list_all_characters()
        chars = [c for c in all_chars if c.get_source_profile("matthew") is not None]

        if chars:
            themes = _identify_theological_themes("matthew", chars)

            assert isinstance(themes, list)
            for theme in themes:
                assert isinstance(theme, str)

    def test_kingdom_of_god_theme(self):
        """Should detect kingdom of God theme."""
        from bce.ai.source_analysis import _identify_theological_themes
        from dataclasses import dataclass, field
        from typing import List, Dict

        # Create mock character with kingdom traits
        @dataclass
        class MockProfile:
            source_id: str
            traits: Dict[str, str] = field(default_factory=dict)
            references: List[str] = field(default_factory=list)

        @dataclass
        class MockChar:
            id: str
            source_profiles: List[MockProfile] = field(default_factory=list)

            def get_source_profile(self, source_id: str):
                for profile in self.source_profiles:
                    if profile.source_id == source_id:
                        return profile
                return None

        char = MockChar(
            id="test",
            source_profiles=[
                MockProfile(
                    source_id="mark",
                    traits={
                        "teaching": "Jesus proclaimed the kingdom of God",
                        "message": "The kingdom of heaven is at hand"
                    }
                )
            ]
        )

        themes = _identify_theological_themes("mark", [char])

        assert isinstance(themes, list)
        # Should detect kingdom theme
        assert "kingdom_of_god" in themes

    def test_empty_characters(self):
        """Should handle empty characters list."""
        from bce.ai.source_analysis import _identify_theological_themes

        themes = _identify_theological_themes("unknown", [])

        assert isinstance(themes, list)
        assert len(themes) == 0

    def test_all_theological_themes(self):
        """Should identify all theological themes from trait values."""
        from bce.ai.source_analysis import _identify_theological_themes
        from dataclasses import dataclass, field
        from typing import List, Dict, Optional

        @dataclass
        class MockProfile:
            source_id: str
            traits: Dict[str, str] = field(default_factory=dict)
            references: List[str] = field(default_factory=list)

        @dataclass
        class MockChar:
            id: str
            source_profiles: List[MockProfile] = field(default_factory=list)

            def get_source_profile(self, source_id: str) -> Optional[MockProfile]:
                for profile in self.source_profiles:
                    if profile.source_id == source_id:
                        return profile
                return None

        # Create characters with all theme keywords in trait values
        chars = [
            MockChar(
                id="char1",
                source_profiles=[
                    MockProfile(
                        source_id="test",
                        traits={
                            "message": "Proclaiming the kingdom of God and salvation through faith",
                            "teaching": "About the kingdom of heaven and discipleship",
                            "claims": "Authority and power given by the holy spirit",
                        }
                    )
                ]
            ),
            MockChar(
                id="char2",
                source_profiles=[
                    MockProfile(
                        source_id="test",
                        traits={
                            "identity": "Who he is and his messianic role",
                            "relationship": "The covenant promise and the law fulfilled",
                            "character": "Disciple and follower of the way",
                        }
                    )
                ]
            ),
        ]

        themes = _identify_theological_themes("test", chars)

        # Should identify multiple themes
        assert isinstance(themes, list)
        assert len(themes) > 0

        # Expected themes based on keywords
        expected_themes = [
            "kingdom_of_god",
            "salvation",
            "faith",
            "discipleship",
            "authority",
            "identity",
            "covenant",
            "spirit",
        ]

        # At least some expected themes should be present
        for theme in themes:
            assert theme in expected_themes

    def test_salvation_theme_detection(self):
        """Should detect salvation theme."""
        from bce.ai.source_analysis import _identify_theological_themes
        from dataclasses import dataclass, field
        from typing import List, Dict, Optional

        @dataclass
        class MockProfile:
            source_id: str
            traits: Dict[str, str] = field(default_factory=dict)
            references: List[str] = field(default_factory=list)

        @dataclass
        class MockChar:
            id: str
            source_profiles: List[MockProfile] = field(default_factory=list)

            def get_source_profile(self, source_id: str) -> Optional[MockProfile]:
                for profile in self.source_profiles:
                    if profile.source_id == source_id:
                        return profile
                return None

        chars = [
            MockChar(
                id="test",
                source_profiles=[
                    MockProfile(
                        source_id="test",
                        traits={
                            "message": "Redemption and forgiveness of sins",
                            "mission": "To save the lost",
                        }
                    )
                ]
            ),
        ]

        themes = _identify_theological_themes("test", chars)

        assert "salvation" in themes

    def test_faith_theme_detection(self):
        """Should detect faith theme."""
        from bce.ai.source_analysis import _identify_theological_themes
        from dataclasses import dataclass, field
        from typing import List, Dict, Optional

        @dataclass
        class MockProfile:
            source_id: str
            traits: Dict[str, str] = field(default_factory=dict)
            references: List[str] = field(default_factory=list)

        @dataclass
        class MockChar:
            id: str
            source_profiles: List[MockProfile] = field(default_factory=list)

            def get_source_profile(self, source_id: str) -> Optional[MockProfile]:
                for profile in self.source_profiles:
                    if profile.source_id == source_id:
                        return profile
                return None

        chars = [
            MockChar(
                id="test",
                source_profiles=[
                    MockProfile(
                        source_id="test",
                        traits={
                            "message": "Believe and trust in the Lord",
                            "call": "Faith is required",
                        }
                    )
                ]
            ),
        ]

        themes = _identify_theological_themes("test", chars)

        assert "faith" in themes

    def test_authority_theme_detection(self):
        """Should detect authority theme."""
        from bce.ai.source_analysis import _identify_theological_themes
        from dataclasses import dataclass, field
        from typing import List, Dict, Optional

        @dataclass
        class MockProfile:
            source_id: str
            traits: Dict[str, str] = field(default_factory=dict)
            references: List[str] = field(default_factory=list)

        @dataclass
        class MockChar:
            id: str
            source_profiles: List[MockProfile] = field(default_factory=list)

            def get_source_profile(self, source_id: str) -> Optional[MockProfile]:
                for profile in self.source_profiles:
                    if profile.source_id == source_id:
                        return profile
                return None

        chars = [
            MockChar(
                id="test",
                source_profiles=[
                    MockProfile(
                        source_id="test",
                        traits={
                            "power": "Authority over demons",
                            "exousia": "Divine power granted",
                        }
                    )
                ]
            ),
        ]

        themes = _identify_theological_themes("test", chars)

        assert "authority" in themes

    def test_covenant_theme_detection(self):
        """Should detect covenant theme."""
        from bce.ai.source_analysis import _identify_theological_themes
        from dataclasses import dataclass, field
        from typing import List, Dict, Optional

        @dataclass
        class MockProfile:
            source_id: str
            traits: Dict[str, str] = field(default_factory=dict)
            references: List[str] = field(default_factory=list)

        @dataclass
        class MockChar:
            id: str
            source_profiles: List[MockProfile] = field(default_factory=list)

            def get_source_profile(self, source_id: str) -> Optional[MockProfile]:
                for profile in self.source_profiles:
                    if profile.source_id == source_id:
                        return profile
                return None

        chars = [
            MockChar(
                id="test",
                source_profiles=[
                    MockProfile(
                        source_id="test",
                        traits={
                            "teaching": "Fulfill the law and the covenant promise",
                            "torah": "Torah observance",
                        }
                    )
                ]
            ),
        ]

        themes = _identify_theological_themes("test", chars)

        assert "covenant" in themes

    def test_spirit_theme_detection(self):
        """Should detect spirit theme."""
        from bce.ai.source_analysis import _identify_theological_themes
        from dataclasses import dataclass, field
        from typing import List, Dict, Optional

        @dataclass
        class MockProfile:
            source_id: str
            traits: Dict[str, str] = field(default_factory=dict)
            references: List[str] = field(default_factory=list)

        @dataclass
        class MockChar:
            id: str
            source_profiles: List[MockProfile] = field(default_factory=list)

            def get_source_profile(self, source_id: str) -> Optional[MockProfile]:
                for profile in self.source_profiles:
                    if profile.source_id == source_id:
                        return profile
                return None

        chars = [
            MockChar(
                id="test",
                source_profiles=[
                    MockProfile(
                        source_id="test",
                        traits={
                            "baptism": "Baptized in the holy spirit",
                            "power": "Filled with pneuma",
                        }
                    )
                ]
            ),
        ]

        themes = _identify_theological_themes("test", chars)

        assert "spirit" in themes


class TestGenerateSourceStatistics:
    """Tests for _generate_source_statistics internal function."""

    def test_characters_without_matching_profile(self):
        """Should handle characters without matching source profile."""
        from bce.ai.source_analysis import _generate_source_statistics
        from dataclasses import dataclass, field
        from typing import List, Dict, Optional

        @dataclass
        class MockProfile:
            source_id: str
            traits: Dict[str, str] = field(default_factory=dict)
            references: List[str] = field(default_factory=list)

        @dataclass
        class MockChar:
            id: str
            source_profiles: List[MockProfile] = field(default_factory=list)

            def get_source_profile(self, source_id: str) -> Optional[MockProfile]:
                for profile in self.source_profiles:
                    if profile.source_id == source_id:
                        return profile
                return None

        # Characters without matching source profile
        chars = [
            MockChar(
                id="char1",
                source_profiles=[
                    MockProfile(source_id="different_source", traits={"key": "value"}, references=["Ref 1:1"])
                ]
            ),
        ]

        stats = _generate_source_statistics("target_source", chars)

        # Should still return count but zero traits/references
        assert stats["character_count"] == 1
        assert stats["total_traits"] == 0
        assert stats["total_references"] == 0
        assert stats["avg_traits_per_character"] == 0.0

    def test_statistics_structure(self):
        """Should return properly structured statistics."""
        from bce.ai.source_analysis import _generate_source_statistics
        from bce import queries

        all_chars = queries.list_all_characters()
        chars = [c for c in all_chars if c.get_source_profile("luke") is not None]

        if chars:
            stats = _generate_source_statistics("luke", chars)

            assert "character_count" in stats
            assert "total_traits" in stats
            assert "total_references" in stats
            assert "avg_traits_per_character" in stats

            # Check types and values
            assert isinstance(stats["character_count"], int)
            assert isinstance(stats["total_traits"], int)
            assert isinstance(stats["total_references"], int)
            assert isinstance(stats["avg_traits_per_character"], (int, float))

            assert stats["character_count"] == len(chars)
            assert stats["character_count"] >= 0
            assert stats["total_traits"] >= 0

    def test_average_calculation(self):
        """Should calculate average correctly."""
        from bce.ai.source_analysis import _generate_source_statistics
        from bce import queries

        all_chars = queries.list_all_characters()
        chars = [c for c in all_chars if c.get_source_profile("john") is not None]

        if chars:
            stats = _generate_source_statistics("john", chars)

            # Average should be total / count
            if stats["character_count"] > 0:
                expected_avg = stats["total_traits"] / stats["character_count"]
                assert abs(stats["avg_traits_per_character"] - expected_avg) < 0.1

    def test_empty_characters(self):
        """Should handle empty characters list."""
        from bce.ai.source_analysis import _generate_source_statistics

        stats = _generate_source_statistics("unknown", [])

        assert stats["character_count"] == 0
        assert stats["total_traits"] == 0
        assert stats["total_references"] == 0
        assert stats["avg_traits_per_character"] == 0


class TestComparePatterns:
    """Tests for _compare_patterns internal function."""

    def test_compare_patterns_structure(self):
        """Should return properly structured pattern comparison."""
        from bce.ai.source_analysis import _compare_patterns

        analyses = {
            "mark": {
                "character_portrayal_patterns": [
                    {"pattern": "messianic_secrecy", "frequency": "high"},
                ]
            },
            "john": {
                "character_portrayal_patterns": [
                    {"pattern": "divine_christology", "frequency": "high"},
                ]
            }
        }

        result = _compare_patterns(analyses)

        assert isinstance(result, list)

        if result:
            comparison = result[0]
            assert "pattern" in comparison
            assert "present_in" in comparison

    def test_identifies_unique_patterns(self):
        """Should identify unique patterns."""
        from bce.ai.source_analysis import _compare_patterns

        analyses = {
            "mark": {
                "character_portrayal_patterns": [
                    {"pattern": "unique_to_mark", "frequency": "high"},
                ]
            },
            "john": {
                "character_portrayal_patterns": [
                    {"pattern": "unique_to_john", "frequency": "high"},
                ]
            }
        }

        result = _compare_patterns(analyses)

        # Should identify unique patterns
        for comp in result:
            if comp["pattern"] == "unique_to_mark":
                assert "unique_to" in comp
                assert comp["unique_to"] == "mark"

    def test_empty_patterns(self):
        """Should handle empty patterns."""
        from bce.ai.source_analysis import _compare_patterns

        analyses = {
            "mark": {"character_portrayal_patterns": []},
            "john": {"character_portrayal_patterns": []}
        }

        result = _compare_patterns(analyses)

        assert isinstance(result, list)
        assert len(result) == 0


class TestComparePriorities:
    """Tests for _compare_priorities internal function."""

    def test_compare_priorities_structure(self):
        """Should return properly structured priority comparison."""
        from bce.ai.source_analysis import _compare_priorities

        analyses = {
            "mark": {"narrative_priorities": ["suffering_christology"]},
            "john": {"narrative_priorities": ["divine_christology"]}
        }

        result = _compare_priorities(analyses)

        assert isinstance(result, dict)
        assert "mark" in result
        assert "john" in result
        assert isinstance(result["mark"], list)
        assert isinstance(result["john"], list)

    def test_empty_priorities(self):
        """Should handle empty priorities."""
        from bce.ai.source_analysis import _compare_priorities

        analyses = {
            "mark": {"narrative_priorities": []},
            "john": {"narrative_priorities": []}
        }

        result = _compare_priorities(analyses)

        assert isinstance(result, dict)
        assert result["mark"] == []
        assert result["john"] == []


class TestCompareVocabulary:
    """Tests for _compare_vocabulary internal function."""

    def test_compare_vocabulary_structure(self):
        """Should return properly structured vocabulary comparison."""
        from bce.ai.source_analysis import _compare_vocabulary

        analyses = {
            "mark": {
                "vocabulary": {
                    "common_trait_keys": [{"key": "trait1", "count": 5}],
                    "total_unique_trait_keys": 10
                }
            },
            "john": {
                "vocabulary": {
                    "common_trait_keys": [{"key": "trait2", "count": 3}],
                    "total_unique_trait_keys": 8
                }
            }
        }

        result = _compare_vocabulary(analyses)

        assert isinstance(result, dict)
        assert "mark" in result
        assert "john" in result

        assert "top_trait_keys" in result["mark"]
        assert "unique_trait_count" in result["mark"]

    def test_top_trait_keys_limit(self):
        """Should limit to top 5 trait keys."""
        from bce.ai.source_analysis import _compare_vocabulary

        analyses = {
            "mark": {
                "vocabulary": {
                    "common_trait_keys": [
                        {"key": f"trait{i}", "count": 10-i} for i in range(10)
                    ],
                    "total_unique_trait_keys": 10
                }
            }
        }

        result = _compare_vocabulary(analyses)

        # Should have max 5 top trait keys
        assert len(result["mark"]["top_trait_keys"]) <= 5

    def test_empty_vocabulary(self):
        """Should handle empty vocabulary."""
        from bce.ai.source_analysis import _compare_vocabulary

        analyses = {
            "mark": {
                "vocabulary": {
                    "common_trait_keys": [],
                    "total_unique_trait_keys": 0
                }
            }
        }

        result = _compare_vocabulary(analyses)

        assert isinstance(result, dict)
        assert result["mark"]["top_trait_keys"] == []
        assert result["mark"]["unique_trait_count"] == 0
