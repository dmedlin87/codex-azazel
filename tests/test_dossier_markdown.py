from __future__ import annotations

from bce import queries
from bce.dossiers import build_character_dossier
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
