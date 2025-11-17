from __future__ import annotations

from typing import Any, Dict, List

from bce import api
from bce.export_graph import GraphSnapshot


def test_get_character_and_event() -> None:
    jesus = api.get_character("jesus")
    crucifixion = api.get_event("crucifixion")

    assert jesus.id == "jesus"
    assert crucifixion.id == "crucifixion"


def test_list_ids_via_api() -> None:
    char_ids = api.list_character_ids()
    event_ids = api.list_event_ids()

    assert "jesus" in char_ids
    assert "crucifixion" in event_ids


def test_build_dossiers_via_api() -> None:
    char_dossier = api.build_character_dossier("jesus")
    event_dossier = api.build_event_dossier("crucifixion")

    assert isinstance(char_dossier, dict)
    assert isinstance(event_dossier, dict)
    assert char_dossier["id"] == "jesus"
    assert event_dossier["id"] == "crucifixion"


def test_conflict_summaries_via_api() -> None:
    char_summary = api.summarize_character_conflicts("jesus")
    event_summary = api.summarize_event_conflicts("crucifixion")

    assert isinstance(char_summary, dict)
    assert isinstance(event_summary, dict)


def test_tag_helpers_via_api() -> None:
    chars = api.list_characters_with_tag("resurrection")
    events = api.list_events_with_tag("resurrection")

    assert "jesus" in chars
    assert "empty_tomb" in events


def test_search_all_via_api() -> None:
    results: List[Dict[str, Any]] = api.search_all("resurrection", scope=["traits"])

    assert any(r["type"] == "character" and r["id"] == "jesus" for r in results)


def test_export_all_characters_and_events_via_api() -> None:
    chars = api.export_all_characters()
    events = api.export_all_events()

    assert isinstance(chars, list)
    assert isinstance(events, list)
    assert any(c["id"] == "jesus" for c in chars)
    assert any(e["id"] == "crucifixion" for e in events)


def test_export_citations_via_api() -> None:
    entries = api.export_citations()

    assert isinstance(entries, list)
    assert entries


def test_build_graph_snapshot_via_api() -> None:
    snapshot = api.build_graph_snapshot()

    assert isinstance(snapshot, GraphSnapshot)
    assert snapshot.nodes
    assert snapshot.edges
