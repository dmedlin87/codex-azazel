from __future__ import annotations

from bce import dossiers
from bce.export import dossier_to_markdown, dossiers_to_markdown


def test_dossier_to_markdown_character_basic() -> None:
    d = dossiers.build_character_dossier("jesus")

    md = dossier_to_markdown(d)

    assert isinstance(md, str)
    assert md.strip(), "expected non-empty markdown output"

    # ID and canonical name should be present.
    assert d["id"] in md
    assert d["canonical_name"] in md

    # At least one section heading derived from character-specific data.
    assert "## Traits by source" in md or "## Aliases" in md or "## Roles" in md


def test_dossier_to_markdown_event_basic() -> None:
    d = dossiers.build_event_dossier("crucifixion")

    md = dossier_to_markdown(d)

    assert isinstance(md, str)
    assert md.strip(), "expected non-empty markdown output"

    # ID and event label should be present.
    assert d["id"] in md
    assert d["label"] in md

    # Expect at least one event-oriented section heading.
    assert "## Accounts" in md or "## Participants" in md


def test_dossiers_to_markdown_multiple() -> None:
    char = dossiers.build_character_dossier("jesus")
    event = dossiers.build_event_dossier("crucifixion")

    all_md = dossiers_to_markdown({char["id"]: char, event["id"]: event})

    assert isinstance(all_md, str)
    assert all_md.strip(), "expected non-empty combined markdown output"

    # Both IDs should appear in the combined output.
    assert char["id"] in all_md
    assert event["id"] in all_md

    # Delimiter between blocks should be present at least once.
    assert "---" in all_md


# Edge case tests for markdown export


def test_dossier_with_no_title_uses_id_as_fallback() -> None:
    """Dossier with no canonical_name/label uses id as title."""
    dossier = {"id": "test", "some_other_field": "value"}
    md = dossier_to_markdown(dossier)

    # "id" is in the title_key_candidates list, so it becomes the title
    assert "# test" in md
    assert "ID: test" in md


def test_dossier_with_empty_title_fields_uses_id() -> None:
    """Dossier with empty canonical_name/label/title uses id."""
    dossier = {
        "id": "test",
        "canonical_name": "",
        "label": "",
        "title": "",
    }
    md = dossier_to_markdown(dossier)

    # Empty strings are skipped, so falls back to "id"
    assert "# test" in md


def test_dossier_with_truly_no_title_uses_unknown() -> None:
    """Dossier with no title fields at all should use <unknown>."""
    dossier = {"some_field": "value"}  # No id, canonical_name, label, title, or name
    md = dossier_to_markdown(dossier)

    assert "# <unknown>" in md
    assert "ID:" not in md


def test_dossier_with_no_id() -> None:
    """Dossier with no ID should not include ID line."""
    dossier = {"canonical_name": "Test Character"}
    md = dossier_to_markdown(dossier)

    assert "# Test Character" in md
    assert "ID:" not in md


def test_dossier_with_empty_id() -> None:
    """Dossier with empty ID should not include ID line."""
    dossier = {"canonical_name": "Test Character", "id": ""}
    md = dossier_to_markdown(dossier)

    assert "ID:" not in md


def test_dossier_with_summary() -> None:
    """Dossier with summary should include it."""
    dossier = {
        "id": "test",
        "canonical_name": "Test",
        "summary": "This is a test summary.",
    }
    md = dossier_to_markdown(dossier)

    assert "This is a test summary." in md


def test_dossier_with_description() -> None:
    """Dossier with description should include it."""
    dossier = {
        "id": "test",
        "canonical_name": "Test",
        "description": "This is a test description.",
    }
    md = dossier_to_markdown(dossier)

    assert "This is a test description." in md


def test_dossier_with_empty_summary() -> None:
    """Dossier with empty summary should skip it."""
    dossier = {
        "id": "test",
        "canonical_name": "Test",
        "summary": "   ",
    }
    md = dossier_to_markdown(dossier)
    lines = md.split("\n")

    # Should not have extra blank lines from empty summary
    assert len([line for line in lines if line.strip()]) >= 2


def test_dossier_with_empty_aliases_list() -> None:
    """Dossier with empty aliases list should skip aliases section."""
    dossier = {
        "id": "test",
        "canonical_name": "Test",
        "aliases": [],
    }
    md = dossier_to_markdown(dossier)

    assert "## Aliases" not in md


def test_dossier_with_aliases_containing_empty_strings() -> None:
    """Aliases with empty strings should be filtered out."""
    dossier = {
        "id": "test",
        "canonical_name": "Test",
        "aliases": ["Valid Alias", "", "  ", "Another Valid"],
    }
    md = dossier_to_markdown(dossier)

    assert "Valid Alias" in md
    assert "Another Valid" in md
    # Should only have valid aliases
    alias_section = md.split("## Aliases")[1].split("##")[0]
    bullet_points = [line for line in alias_section.split("\n") if line.startswith("- ")]
    assert len(bullet_points) == 2


def test_dossier_with_empty_roles_list() -> None:
    """Dossier with empty roles list should skip roles section."""
    dossier = {
        "id": "test",
        "canonical_name": "Test",
        "roles": [],
    }
    md = dossier_to_markdown(dossier)

    assert "## Roles" not in md


def test_dossier_with_empty_participants_list() -> None:
    """Dossier with empty participants list should skip section."""
    dossier = {
        "id": "test",
        "label": "Test Event",
        "participants": [],
    }
    md = dossier_to_markdown(dossier)

    assert "## Participants" not in md


def test_dossier_with_empty_accounts_list() -> None:
    """Dossier with empty accounts list should skip accounts section."""
    dossier = {
        "id": "test",
        "label": "Test Event",
        "accounts": [],
    }
    md = dossier_to_markdown(dossier)

    assert "## Accounts" not in md


def test_dossier_with_accounts_missing_fields() -> None:
    """Accounts with missing fields should handle gracefully."""
    dossier = {
        "id": "test",
        "label": "Test Event",
        "accounts": [
            {"source_id": "mark"},
            {"reference": "Mark 1:1"},
            {"summary": "Test summary"},
            {},  # Empty account
        ],
    }
    md = dossier_to_markdown(dossier)

    assert "## Accounts" in md
    assert "source=mark" in md
    assert "ref=Mark 1:1" in md
    assert "summary=Test summary" in md


def test_dossier_with_malformed_traits_by_source() -> None:
    """Malformed traits_by_source should be handled gracefully."""
    dossier = {
        "id": "test",
        "canonical_name": "Test",
        "traits_by_source": {
            "valid_source": {"trait1": "value1"},
            123: {"trait2": "value2"},  # Invalid key (not string)
            "source_with_non_dict": "not a dict",  # Invalid value
        },
    }
    md = dossier_to_markdown(dossier)

    assert "## Traits by source" in md
    assert "valid_source" in md
    assert "trait1=value1" in md


def test_dossier_with_empty_traits_by_source() -> None:
    """Empty traits_by_source dict still renders section header."""
    dossier = {
        "id": "test",
        "canonical_name": "Test",
        "traits_by_source": {},
    }
    md = dossier_to_markdown(dossier)

    # The implementation renders the header even for empty dict
    assert "## Traits by source" in md
    # But should have no bullet points
    section = md.split("## Traits by source")[1].split("##")[0] if "##" in md.split("## Traits by source")[1] else md.split("## Traits by source")[1]
    assert "- " not in section


def test_dossier_with_references_by_source() -> None:
    """references_by_source should be rendered correctly."""
    dossier = {
        "id": "test",
        "canonical_name": "Test",
        "references_by_source": {
            "mark": ["Mark 1:1", "Mark 2:2"],
            "matthew": ["Matt 1:1"],
        },
    }
    md = dossier_to_markdown(dossier)

    assert "## References by source" in md
    assert "mark:" in md
    assert "Mark 1:1" in md
    assert "Mark 2:2" in md
    assert "matthew:" in md


def test_dossier_with_empty_references_list() -> None:
    """references_by_source with empty lists should skip that source."""
    dossier = {
        "id": "test",
        "canonical_name": "Test",
        "references_by_source": {
            "mark": ["Mark 1:1"],
            "empty_source": [],
        },
    }
    md = dossier_to_markdown(dossier)

    assert "mark:" in md
    assert "empty_source:" not in md


def test_dossier_with_trait_comparison() -> None:
    """trait_comparison should be rendered as nested mapping."""
    dossier = {
        "id": "test",
        "canonical_name": "Test",
        "trait_comparison": {
            "trait1": {"mark": "value1", "matthew": "value2"},
        },
    }
    md = dossier_to_markdown(dossier)

    assert "## Trait comparison" in md
    assert "trait1:" in md
    assert "mark=value1" in md
    assert "matthew=value2" in md


def test_dossier_with_trait_conflicts() -> None:
    """trait_conflicts should be rendered as nested mapping."""
    dossier = {
        "id": "test",
        "canonical_name": "Test",
        "trait_conflicts": {
            "conflict_trait": {"mark": "val1", "matthew": "val2"},
        },
    }
    md = dossier_to_markdown(dossier)

    assert "## Trait conflicts" in md
    assert "conflict_trait:" in md


def test_dossier_with_trait_conflict_summaries() -> None:
    """trait_conflict_summaries should be rendered when present."""

    dossier = {
        "id": "test",
        "canonical_name": "Test",
        "trait_conflict_summaries": {
            "trait1": {
                "severity": "medium",
                "category": "narrative",
                "distinct_values": ["a", "b"],
            }
        },
    }
    md = dossier_to_markdown(dossier)

    assert "## Trait conflict summaries" in md
    assert "trait1:" in md
    assert "severity=medium" in md


def test_dossier_with_account_conflicts() -> None:
    """account_conflicts should be rendered as nested mapping."""
    dossier = {
        "id": "test",
        "label": "Test Event",
        "account_conflicts": {
            "field1": {"mark": "version1", "john": "version2"},
        },
    }
    md = dossier_to_markdown(dossier)

    assert "## Account conflicts" in md
    assert "field1:" in md


def test_dossier_with_account_conflict_summaries() -> None:
    """account_conflict_summaries should be rendered when present."""

    dossier = {
        "id": "test",
        "label": "Test Event",
        "account_conflict_summaries": {
            "summary": {
                "severity": "high",
                "category": "narrative",
                "distinct_values": ["x", "y", "z"],
            }
        },
    }
    md = dossier_to_markdown(dossier)

    assert "## Account conflict summaries" in md
    assert "summary:" in md
    assert "severity=high" in md


def test_dossiers_to_markdown_with_empty_dict() -> None:
    """dossiers_to_markdown with empty dict should return empty string."""
    md = dossiers_to_markdown({})

    assert md == ""


def test_dossiers_to_markdown_with_non_dict_values() -> None:
    """dossiers_to_markdown should skip non-dict values."""
    dossier = {"id": "test", "canonical_name": "Test"}
    result = dossiers_to_markdown({
        "valid": dossier,
        "invalid": "not a dict",
        "also_invalid": 123,
    })

    assert "Test" in result
    # Should only have one dossier rendered
    assert result.count("# ") == 1
