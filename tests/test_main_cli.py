"""Tests for the main bce CLI (bce.cli module).

These tests verify the primary user-facing CLI registered as 'bce' command.
"""

from __future__ import annotations

import pytest
from bce.cli import main


class TestCharacterCommand:
    """Test 'bce character' command."""

    def test_character_markdown_output(self, capsys):
        """character command should output markdown for valid ID."""
        exit_code = main(["character", "jesus", "--format", "markdown"])
        captured = capsys.readouterr()

        assert exit_code == 0
        # Should contain markdown headers
        assert "# Jesus of Nazareth" in captured.out
        assert "ID: jesus" in captured.out
        # Should contain some source information
        assert "source" in captured.out.lower()

    def test_character_markdown_with_short_flag(self, capsys):
        """character command should accept -f short flag."""
        exit_code = main(["character", "paul", "-f", "markdown"])
        captured = capsys.readouterr()

        assert exit_code == 0
        assert "# " in captured.out  # Should have markdown header
        assert "paul" in captured.out.lower()

    def test_character_default_format(self, capsys):
        """character command should default to markdown format."""
        exit_code = main(["character", "peter"])
        captured = capsys.readouterr()

        assert exit_code == 0
        # Should output markdown by default
        assert "# " in captured.out

    def test_character_not_found(self, capsys):
        """character command with invalid ID should return exit code 1."""
        exit_code = main(["character", "nonexistent-character"])
        captured = capsys.readouterr()

        assert exit_code == 1
        # Should print error to stderr
        assert "Error:" in captured.err
        assert "not found" in captured.err

    def test_character_with_all_data_characters(self, capsys):
        """Test all known characters can be loaded."""
        known_chars = ["jesus", "paul", "peter", "judas", "pilate"]

        for char_id in known_chars:
            exit_code = main(["character", char_id, "--format", "markdown"])
            captured = capsys.readouterr()

            assert exit_code == 0, f"Failed to load character: {char_id}"
            assert "# " in captured.out, f"No markdown header for {char_id}"


class TestEventCommand:
    """Test 'bce event' command."""

    def test_event_markdown_output(self, capsys):
        """event command should output markdown for valid ID."""
        exit_code = main(["event", "crucifixion", "--format", "markdown"])
        captured = capsys.readouterr()

        assert exit_code == 0
        # Should contain markdown headers
        assert "# " in captured.out
        assert "ID: crucifixion" in captured.out

    def test_event_markdown_with_short_flag(self, capsys):
        """event command should accept -f short flag."""
        exit_code = main(["event", "betrayal", "-f", "markdown"])
        captured = capsys.readouterr()

        assert exit_code == 0
        assert "# " in captured.out  # Should have markdown header

    def test_event_default_format(self, capsys):
        """event command should default to markdown format."""
        exit_code = main(["event", "damascus_road"])
        captured = capsys.readouterr()

        assert exit_code == 0
        # Should output markdown by default
        assert "# " in captured.out

    def test_event_not_found(self, capsys):
        """event command with invalid ID should return exit code 1."""
        exit_code = main(["event", "nonexistent-event"])
        captured = capsys.readouterr()

        assert exit_code == 1
        # Should print error to stderr
        assert "Error:" in captured.err
        assert "not found" in captured.err

    def test_event_with_all_data_events(self, capsys):
        """Test all known events can be loaded."""
        known_events = [
            "crucifixion",
            "betrayal",
            "damascus_road",
            "resurrection_appearance",
            "trial_before_pilate"
        ]

        for event_id in known_events:
            exit_code = main(["event", event_id, "--format", "markdown"])
            captured = capsys.readouterr()

            assert exit_code == 0, f"Failed to load event: {event_id}"
            assert "# " in captured.out, f"No markdown header for {event_id}"


class TestArgumentParsing:
    """Test argument parsing and validation."""

    def test_help_displays_for_character(self, capsys):
        """Help should be available via --help."""
        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])

        assert exc_info.value.code == 0

    def test_invalid_kind_argument(self, capsys):
        """Invalid kind argument should fail."""
        with pytest.raises(SystemExit) as exc_info:
            main(["invalid_kind", "some_id"])

        # argparse exits with code 2 for invalid arguments
        assert exc_info.value.code == 2

    def test_missing_id_argument(self, capsys):
        """Missing ID argument should fail."""
        with pytest.raises(SystemExit) as exc_info:
            main(["character"])

        # argparse exits with code 2 for missing arguments
        assert exc_info.value.code == 2

    def test_no_arguments(self, capsys):
        """No arguments should display help and fail."""
        with pytest.raises(SystemExit) as exc_info:
            main([])

        # argparse exits with code 2 for missing arguments
        assert exc_info.value.code == 2


class TestErrorHandling:
    """Test error handling for edge cases."""

    def test_character_file_not_found_error(self, capsys):
        """FileNotFoundError should be caught and reported."""
        exit_code = main(["character", "missing"])
        captured = capsys.readouterr()

        assert exit_code == 1
        assert "Error:" in captured.err

    def test_event_file_not_found_error(self, capsys):
        """FileNotFoundError should be caught and reported."""
        exit_code = main(["event", "missing"])
        captured = capsys.readouterr()

        assert exit_code == 1
        assert "Error:" in captured.err

    def test_empty_id_string(self, capsys):
        """Empty ID string should be handled."""
        exit_code = main(["character", ""])
        captured = capsys.readouterr()

        assert exit_code == 1
        assert "Error:" in captured.err
