from __future__ import annotations

from bce import queries
from bce.models import SourceProfile


class TestCharacterHelperMethods:
    """Tests for helper methods added to Character and SourceProfile."""

    def test_get_source_profile_on_real_data(self) -> None:
        jesus = queries.get_character("jesus")
        profile = jesus.get_source_profile("mark")
        assert profile is not None
        assert profile.source_id == "mark"

    def test_list_sources_matches_profiles(self) -> None:
        jesus = queries.get_character("jesus")
        from_profiles = {p.source_id for p in jesus.source_profiles}
        from_helper = set(jesus.list_sources())
        assert from_helper == from_profiles

    def test_has_trait_with_and_without_source(self) -> None:
        jesus = queries.get_character("jesus")

        # Traits that are expected to exist in the sample data
        assert jesus.has_trait("resurrection")
        assert jesus.has_trait("resurrection", source="mark")

        # Non-existent traits should return False
        assert not jesus.has_trait("__does_not_exist__")
        assert not jesus.has_trait("__does_not_exist__", source="mark")


class TestSourceProfileHelperMethods:
    def test_source_profile_trait_helpers(self) -> None:
        profile = SourceProfile(source_id="test", traits={"role": "apostle"})

        assert profile.has_trait("role")
        assert not profile.has_trait("other")
        assert profile.get_trait("role") == "apostle"
        assert profile.get_trait("other") is None
        assert profile.get_trait("other", default="x") == "x"
