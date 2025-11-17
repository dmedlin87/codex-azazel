from __future__ import annotations

from bce.search import search_all


def test_search_traits_finds_jesus_resurrection() -> None:
    results = search_all("resurrection", scope=["traits"])

    assert any(r["type"] == "character" and r["id"] == "jesus" for r in results)


def test_search_accounts_finds_crucifixion() -> None:
    results = search_all("crucified", scope=["accounts"])

    assert any(r["type"] == "event" and r["id"] == "crucifixion" for r in results)
