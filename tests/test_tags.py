from __future__ import annotations

from bce import queries


def test_list_characters_with_tag_resurrection() -> None:
    ids = queries.list_characters_with_tag("resurrection")

    assert "jesus" in ids


def test_list_events_with_tag_resurrection() -> None:
    ids = queries.list_events_with_tag("resurrection")

    assert "empty_tomb" in ids
