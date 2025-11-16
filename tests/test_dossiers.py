from __future__ import annotations

from bce import dossiers


def test_build_character_dossier_basic() -> None:
    d = dossiers.build_character_dossier("jesus")

    for key in ("id", "canonical_name", "aliases", "roles", "source_ids", "traits_by_source", "trait_conflicts"):
        assert key in d

    assert d["id"] == "jesus"
    assert isinstance(d["source_ids"], list)
    assert isinstance(d["traits_by_source"], dict)


def test_build_event_dossier_basic() -> None:
    d = dossiers.build_event_dossier("crucifixion")

    for key in ("id", "label", "participants", "accounts", "account_conflicts"):
        assert key in d

    assert "jesus" in d["participants"]
    assert isinstance(d["accounts"], list)
    assert isinstance(d["account_conflicts"], dict)


def test_build_all_character_dossiers_basic() -> None:
    all_dossiers = dossiers.build_all_character_dossiers()
    assert isinstance(all_dossiers, list)
    assert all_dossiers, "expected at least one character dossier"

    for d in all_dossiers:
        assert isinstance(d, dict)
        # basic shape checks
        assert "id" in d
        assert "canonical_name" in d
        assert "traits_by_source" in d


def test_build_all_event_dossiers_basic() -> None:
    all_dossiers = dossiers.build_all_event_dossiers()
    assert isinstance(all_dossiers, list)
    assert all_dossiers, "expected at least one event dossier"

    for d in all_dossiers:
        assert isinstance(d, dict)
        # basic shape checks
        assert "id" in d
        assert "label" in d
        assert "accounts" in d
