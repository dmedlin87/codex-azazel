from __future__ import annotations

from bce import queries
from bce.dossiers import build_character_dossier, build_event_dossier
from bce.export import dossier_to_markdown


def test_character_dossier_to_markdown_smoke() -> None:
    ids = queries.list_character_ids()
    assert ids, "expected at least one character ID"
    char_id = ids[0]

    dossier = build_character_dossier(char_id)
    markdown = dossier_to_markdown(dossier)

    assert isinstance(markdown, str)
    assert markdown.strip(), "expected non-empty markdown output"


def test_event_account_notes_retain_markdown_output() -> None:
    """Event notes should be rendered when accounts include them."""
    dossier = {
        "id": "notes_event",
        "label": "Notes Event",
        "accounts": [
            {
                "source_id": "source-a",
                "reference": "Ref 1:1",
                "summary": "Summary",
                "notes": "  important context  ",
            }
        ],
    }

    markdown = dossier_to_markdown(dossier)

    assert "notes=important context" in markdown


def test_character_relationships_render_in_markdown() -> None:
    """Paul's relationships should appear in the markdown output."""
    # Paul is seeded with relationships in the sample data
    dossier = build_character_dossier("paul")
    markdown = dossier_to_markdown(dossier)

    assert "## Relationships" in markdown
    # At least one relationship should mention Barnabas
    assert "character_id=barnabas" in markdown


def test_event_parallels_render_in_markdown() -> None:
    """Crucifixion parallels should appear in the markdown output."""
    dossier = build_event_dossier("crucifixion")
    markdown = dossier_to_markdown(dossier)

    assert "## Parallels" in markdown
    assert "relationship=gospel_parallel" in markdown
