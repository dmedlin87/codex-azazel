"""Tests for bce.export_citations module.

These tests exercise the citation export helper and lock in the basic
BibTeX-style behavior described in features.md.
"""

from __future__ import annotations

from typing import List

import pytest

from bce.export_citations import export_citations


class TestExportCitationsBibtex:
    """Tests for export_citations(format="bibtex")."""

    def test_returns_list_of_strings(self) -> None:
        entries = export_citations()

        assert isinstance(entries, list)
        assert entries, "expected at least one citation entry"
        assert all(isinstance(e, str) for e in entries)

    def test_basic_bibtex_shape(self) -> None:
        entries: List[str] = export_citations()

        # Each entry should be an @misc BibTeX record with a closing brace
        for entry in entries:
            lines = entry.strip().split("\n")
            assert lines[0].startswith("@misc{")
            assert entry.strip().endswith("}")

    def test_includes_known_ids_in_citations(self) -> None:
        """Citations should include references to known sources, characters, and events."""
        entries_text = "\n".join(export_citations())

        # Source IDs (from sources.json) should appear at least in keywords or note
        assert "mark" in entries_text or "Mark" in entries_text

        # Core character and event IDs should be referenced in notes/keywords
        assert "jesus" in entries_text
        assert "crucifixion" in entries_text

    def test_unsupported_format_raises(self) -> None:
        with pytest.raises(ValueError):
            export_citations(format="unknown-format")
