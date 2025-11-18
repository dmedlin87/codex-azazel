from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Dict, Iterable, List

from bce import search as search_module


def _fake_characters() -> Iterable[Dict[str, Any]]:
    char = SimpleNamespace(
        id="char1",
        source_profiles=[
            SimpleNamespace(
                source_id="source1",
                traits={"role": "Teacher", "title": "Messiah"},
                references=["Ref 1:1", "Other 2:2"],
            )
        ],
        tags=["featured", "Messiah"],
    )
    yield {"type": "character", "id": char.id, "character": char}


def _fake_events() -> Iterable[Dict[str, Any]]:
    event = SimpleNamespace(
        id="event1",
        accounts=[
            SimpleNamespace(
                source_id="source1",
                reference="Ref 1:1",
                summary="Summary mentioning keyword",
                notes="Important note",
            )
        ],
        tags=["featured"],
    )
    yield {"type": "event", "id": event.id, "event": event}


class TestSearchScopes:
    def test_traits_scope_matches_on_key_and_value(self, monkeypatch) -> None:
        monkeypatch.setattr(search_module, "_iter_characters", _fake_characters)
        monkeypatch.setattr(search_module, "_iter_events", _fake_events)

        # Match on trait key
        results_key = search_module.search_all("role", scope=["traits"])
        assert any(r["match_in"] == "traits" and r["field"] == "role" for r in results_key)

        # Match on trait value (case-insensitive)
        results_value = search_module.search_all("messiah", scope=["traits"])
        assert any("Messiah" in r["value"] for r in results_value)

    def test_references_scope_matches_references(self, monkeypatch) -> None:
        monkeypatch.setattr(search_module, "_iter_characters", _fake_characters)
        monkeypatch.setattr(search_module, "_iter_events", _fake_events)

        results = search_module.search_all("ref 1:1", scope=["references"])

        assert any(r["match_in"] == "references" and r["reference"] == "Ref 1:1" for r in results)

    def test_tags_scope_matches_character_tags(self, monkeypatch) -> None:
        monkeypatch.setattr(search_module, "_iter_characters", _fake_characters)
        monkeypatch.setattr(search_module, "_iter_events", _fake_events)

        results = search_module.search_all("featured", scope=["tags"])

        # search_all currently inspects tags on characters, not on events.
        assert any(r["match_in"] == "tags" and r["type"] == "character" for r in results)

    def test_accounts_and_notes_scopes(self, monkeypatch) -> None:
        monkeypatch.setattr(search_module, "_iter_characters", _fake_characters)
        monkeypatch.setattr(search_module, "_iter_events", _fake_events)

        results_accounts = search_module.search_all("keyword", scope=["accounts"])
        assert any(r["match_in"] == "accounts" for r in results_accounts)

        results_notes = search_module.search_all("important", scope=["notes"])
        assert any(r["match_in"] == "notes" for r in results_notes)

    def test_empty_scope_searches_all_domains(self, monkeypatch) -> None:
        monkeypatch.setattr(search_module, "_iter_characters", _fake_characters)
        monkeypatch.setattr(search_module, "_iter_events", _fake_events)

        results = search_module.search_all("featured")

        # Should include at least one tag-based hit when scope is omitted
        assert any(r["match_in"] == "tags" for r in results)
