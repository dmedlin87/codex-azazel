from __future__ import annotations

from typing import Dict

import pytest

from bce import queries
import bce.contradictions as contradictions


def test_list_ids_nonempty() -> None:
    """Basic smoke test that core IDs are present."""
    character_ids = queries.list_character_ids()
    event_ids = queries.list_event_ids()

    assert "jesus" in character_ids
    assert "crucifixion" in event_ids


def test_jesus_has_multiple_sources() -> None:
    """Jesus should have multiple source profiles represented."""
    jesus = queries.get_character("jesus")
    source_ids = {sp.source_id for sp in jesus.source_profiles}

    expected_sources = {"mark", "matthew", "paul_undisputed"}
    assert len(source_ids.intersection(expected_sources)) >= 2


def test_events_for_jesus_nonempty() -> None:
    """Events for Jesus should include the crucifixion event."""
    events = queries.list_events_for_character("jesus")
    assert any(e.id == "crucifixion" for e in events)


def test_compare_character_sources_shape() -> None:
    """compare_character_sources should return a nested mapping."""
    cmp = contradictions.compare_character_sources("jesus")
    assert isinstance(cmp, dict)
    if cmp:
        # Pick an arbitrary trait and check its structure
        trait, per_source = next(iter(cmp.items()))
        assert isinstance(per_source, dict)
        for src, value in per_source.items():
            assert isinstance(src, str)
            assert isinstance(value, str)


def test_find_trait_conflicts_subset() -> None:
    """Trait conflicts should be a subset of all compared traits."""
    cmp = contradictions.compare_character_sources("jesus")
    conf = contradictions.find_trait_conflicts("jesus")

    assert isinstance(conf, dict)
    assert set(conf.keys()).issubset(set(cmp.keys()))


def test_crucifixion_conflicts_shape() -> None:
    """find_events_with_conflicting_accounts returns a nested mapping."""
    conf = contradictions.find_events_with_conflicting_accounts("crucifixion")

    assert isinstance(conf, dict)
    if conf:
        field_name, per_source = next(iter(conf.items()))
        assert isinstance(field_name, str)
        assert isinstance(per_source, Dict)
        for src, value in per_source.items():
            assert isinstance(src, str)
            assert isinstance(value, str)
