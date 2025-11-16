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
