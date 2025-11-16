from __future__ import annotations

from pathlib import Path

from bce import queries, storage
from bce.models import Character, Event


def test_configure_data_root(tmp_path: Path) -> None:
    custom_root = tmp_path / "custom_data"
    storage.configure_data_root(custom_root)
    try:
        assert storage.list_character_ids() == []
        character = Character(id="tmp", canonical_name="Temporary Character")
        storage.save_character(character)
        assert storage.list_character_ids() == ["tmp"]
    finally:
        storage.reset_data_root()

    ids = storage.list_character_ids()
    assert "jesus" in ids


def test_save_character_invalidates_query_cache(tmp_path: Path) -> None:
    custom_root = tmp_path / "custom_data_cache_char"
    storage.configure_data_root(custom_root)
    try:
        character = Character(id="cache_char", canonical_name="Original")
        storage.save_character(character)

        loaded = queries.get_character("cache_char")
        assert loaded.canonical_name == "Original"

        updated = Character(id="cache_char", canonical_name="Updated")
        storage.save_character(updated)

        refreshed = queries.get_character("cache_char")
        assert refreshed.canonical_name == "Updated"
    finally:
        storage.reset_data_root()


def test_save_event_invalidates_query_cache(tmp_path: Path) -> None:
    custom_root = tmp_path / "custom_data_cache_event"
    storage.configure_data_root(custom_root)
    try:
        event = Event(id="cache_event", label="Initial")
        storage.save_event(event)

        loaded = queries.get_event("cache_event")
        assert loaded.label == "Initial"

        updated = Event(id="cache_event", label="Changed")
        storage.save_event(updated)

        refreshed = queries.get_event("cache_event")
        assert refreshed.label == "Changed"
    finally:
        storage.reset_data_root()
