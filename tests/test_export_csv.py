"""Tests for bce.export_csv module.

Covers CSV export functionality for characters and events.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from bce import storage
from bce.export_csv import export_characters_csv, export_events_csv


class TestExportCharactersCsv:
    """Tests for export_characters_csv."""

    def test_creates_csv_with_default_columns(self, tmp_path: Path) -> None:
        """Should create a CSV file with default character columns."""
        output_file = tmp_path / "characters.csv"

        export_characters_csv(str(output_file))

        assert output_file.exists()

        with output_file.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            # Header should contain the default fields
            assert reader.fieldnames == [
                "id",
                "canonical_name",
                "aliases",
                "roles",
                "source_count",
            ]
            rows = list(reader)

        # Should have one row per stored character
        expected_ids = set(storage.list_character_ids())
        exported_ids = {row["id"] for row in rows}
        assert exported_ids == expected_ids

    def test_custom_fields_including_name_and_sources(self, tmp_path: Path) -> None:
        """Custom include_fields should control CSV columns, including alias 'name'."""
        output_file = tmp_path / "characters_custom.csv"
        include_fields = ["id", "name", "roles", "source_count", "sources"]

        export_characters_csv(str(output_file), include_fields=include_fields)

        with output_file.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            assert reader.fieldnames == include_fields
            rows = list(reader)

        assert rows, "expected at least one character row"

        # Verify that "name" maps to canonical_name for at least one character
        sample = rows[0]
        char = storage.load_character(sample["id"])
        assert sample["name"] == char.canonical_name

    def test_empty_character_list(self, tmp_path: Path) -> None:
        """Should handle empty character directory and still produce header-only CSV."""
        custom_root = tmp_path / "empty_data"
        storage.configure_data_root(custom_root)

        try:
            output_file = tmp_path / "empty_characters.csv"
            export_characters_csv(str(output_file))

            with output_file.open(newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            assert rows == []
        finally:
            storage.reset_data_root()

    def test_nested_directory_creation(self, tmp_path: Path) -> None:
        """Should create nested directories for character CSV output."""
        output_file = tmp_path / "exports" / "nested" / "characters.csv"

        export_characters_csv(str(output_file))

        assert output_file.exists()
        assert output_file.is_file()


class TestExportEventsCsv:
    """Tests for export_events_csv."""

    def test_creates_csv_with_default_columns(self, tmp_path: Path) -> None:
        """Should create a CSV file with default event columns."""
        output_file = tmp_path / "events.csv"

        export_events_csv(str(output_file))

        assert output_file.exists()

        with output_file.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            assert reader.fieldnames == [
                "id",
                "label",
                "participants",
                "participant_count",
                "account_count",
                "sources",
                "source_count",
            ]
            rows = list(reader)

        expected_ids = set(storage.list_event_ids())
        exported_ids = {row["id"] for row in rows}
        assert exported_ids == expected_ids

    def test_custom_fields_subset(self, tmp_path: Path) -> None:
        """Custom include_fields subset should control CSV columns for events."""
        output_file = tmp_path / "events_custom.csv"
        include_fields = ["id", "label", "account_count"]

        export_events_csv(str(output_file), include_fields=include_fields)

        with output_file.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            assert reader.fieldnames == include_fields
            rows = list(reader)

        assert rows, "expected at least one event row"
        # account_count should be numeric-as-string
        for row in rows:
            assert row["account_count"].isdigit()

    def test_empty_event_list(self, tmp_path: Path) -> None:
        """Should handle empty event directory and still produce header-only CSV."""
        custom_root = tmp_path / "empty_data"
        storage.configure_data_root(custom_root)

        try:
            output_file = tmp_path / "empty_events.csv"
            export_events_csv(str(output_file))

            with output_file.open(newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            assert rows == []
        finally:
            storage.reset_data_root()

    def test_nested_directory_creation(self, tmp_path: Path) -> None:
        """Should create nested directories for event CSV output."""
        output_file = tmp_path / "exports" / "nested" / "events.csv"

        export_events_csv(str(output_file))

        assert output_file.exists()
        assert output_file.is_file()
