from __future__ import annotations

from typing import Dict

from bce.models import Character, SourceProfile
from bce.services import get_source_profile, get_trait_value, has_trait, list_character_sources


class TestGetSourceProfileAndListSources:
    def test_get_source_profile_returns_matching_profile(self) -> None:
        profiles = [
            SourceProfile(source_id="mark"),
            SourceProfile(source_id="matthew"),
        ]
        char = Character(id="test", canonical_name="Test", source_profiles=profiles)

        result = get_source_profile(char, "matthew")

        assert result is profiles[1]

    def test_get_source_profile_returns_none_when_missing(self) -> None:
        char = Character(id="test", canonical_name="Test", source_profiles=[])

        result = get_source_profile(char, "mark")

        assert result is None

    def test_list_character_sources_deduplicates_and_preserves_order(self) -> None:
        profiles = [
            SourceProfile(source_id="mark"),
            SourceProfile(source_id="matthew"),
            SourceProfile(source_id="mark"),
        ]
        char = Character(id="test", canonical_name="Test", source_profiles=profiles)

        sources = list_character_sources(char)

        assert sources == ["mark", "matthew"]


class TestHasTrait:
    def test_has_trait_across_all_sources(self) -> None:
        profiles = [
            SourceProfile(source_id="mark", traits={"role": "teacher"}),
            SourceProfile(source_id="john", traits={"title": "Logos"}),
        ]
        char = Character(id="jesus", canonical_name="Jesus", source_profiles=profiles)

        assert has_trait(char, "role") is True
        assert has_trait(char, "title") is True
        assert has_trait(char, "missing") is False

    def test_has_trait_with_specific_source(self) -> None:
        # When a specific source is provided, has_trait checks only that source profile.
        mark_profile = SourceProfile(source_id="mark", traits={"role": "teacher"})
        char = Character(
            id="jesus",
            canonical_name="Jesus",
            source_profiles=[mark_profile],
            tags=["messiah"],
        )

        assert has_trait(char, "role", source="mark") is True
        # Different trait name should be False even if a matching tag exists.
        assert has_trait(char, "messiah", source="mark") is False


class TestGetTraitValue:
    def test_get_trait_value_from_existing_profile(self) -> None:
        traits: Dict[str, str] = {"title": "teacher"}
        profiles = [SourceProfile(source_id="mark", traits=traits)]
        char = Character(id="jesus", canonical_name="Jesus", source_profiles=profiles)

        value = get_trait_value(char, "title", "mark", default="unknown")

        assert value == "teacher"

    def test_get_trait_value_returns_default_when_profile_missing(self) -> None:
        char = Character(id="jesus", canonical_name="Jesus", source_profiles=[])

        value = get_trait_value(char, "title", "mark", default="unknown")

        assert value == "unknown"

    def test_get_trait_value_returns_default_when_trait_missing(self) -> None:
        profiles = [SourceProfile(source_id="mark", traits={})]
        char = Character(id="jesus", canonical_name="Jesus", source_profiles=profiles)

        value = get_trait_value(char, "title", "mark", default="unknown")

        assert value == "unknown"
