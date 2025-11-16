"""Tests for CLI functionality.

These tests use the main() function directly instead of subprocesses
to test CLI behavior in a controlled way.
"""

import json
import pytest
from dev_cli import main


class TestListCommands:
    """Test list-* commands."""

    def test_list_chars(self, capsys):
        """list-chars should return exit code 0 and list character IDs."""
        exit_code = main(["list-chars"])
        captured = capsys.readouterr()
        
        assert exit_code == 0
        assert "jesus" in captured.out
        # Should have multiple characters
        lines = [line.strip() for line in captured.out.strip().split('\n') if line.strip()]
        assert len(lines) >= 3  # At least jesus, paul, peter, etc.

    def test_list_events(self, capsys):
        """list-events should return exit code 0 and list event IDs."""
        exit_code = main(["list-events"])
        captured = capsys.readouterr()
        
        assert exit_code == 0
        assert "crucifixion" in captured.out
        # Should have multiple events
        lines = [line.strip() for line in captured.out.strip().split('\n') if line.strip()]
        assert len(lines) >= 3  # At least crucifixion, betrayal, etc.


class TestShowCommands:
    """Test show-* commands."""

    def test_show_char(self, capsys):
        """show-char should return exit code 0 and display character JSON."""
        exit_code = main(["show-char", "jesus"])
        captured = capsys.readouterr()
        
        assert exit_code == 0
        # Should contain key character fields
        assert '"id": "jesus"' in captured.out
        assert '"canonical_name": "Jesus of Nazareth"' in captured.out
        assert '"source_profiles"' in captured.out
        
        # Should be valid JSON
        data = json.loads(captured.out)
        assert data["id"] == "jesus"
        assert "canonical_name" in data
        assert "source_profiles" in data

    def test_show_event(self, capsys):
        """show-event should return exit code 0 and display event JSON."""
        exit_code = main(["show-event", "crucifixion"])
        captured = capsys.readouterr()
        
        assert exit_code == 0
        # Should contain key event fields
        assert '"id": "crucifixion"' in captured.out
        assert '"label": "Crucifixion of Jesus"' in captured.out
        assert '"accounts"' in captured.out
        
        # Should be valid JSON
        data = json.loads(captured.out)
        assert data["id"] == "crucifixion"
        assert "label" in data
        assert "accounts" in data


class TestExportCommands:
    """Test export-* commands."""

    def test_export_chars(self, tmp_path, capsys):
        """export-chars should create a JSON file with character data."""
        target = tmp_path / "chars.json"
        exit_code = main(["export-chars", str(target)])
        captured = capsys.readouterr()
        
        assert exit_code == 0
        assert target.exists()
        
        # Should contain exported data
        data = json.load(target.open())
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Should contain Jesus and other known characters
        char_ids = [char["id"] for char in data]
        assert "jesus" in char_ids
        
        # Should print confirmation message
        assert "Exported characters to" in captured.out

    def test_export_events(self, tmp_path, capsys):
        """export-events should create a JSON file with event data."""
        target = tmp_path / "events.json"
        exit_code = main(["export-events", str(target)])
        captured = capsys.readouterr()
        
        assert exit_code == 0
        assert target.exists()
        
        # Should contain exported data
        data = json.load(target.open())
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Should contain crucifixion and other known events
        event_ids = [event["id"] for event in data]
        assert "crucifixion" in event_ids
        
        # Should print confirmation message
        assert "Exported events to" in captured.out


class TestErrorHandling:
    """Test error handling for invalid inputs."""

    def test_show_char_unknown_id(self, capsys):
        """show-char with unknown ID should return non-zero exit code."""
        exit_code = main(["show-char", "not-a-real-id"])
        captured = capsys.readouterr()
        
        assert exit_code != 0
        # Should print error message
        assert "Error:" in captured.err

    def test_show_event_unknown_id(self, capsys):
        """show-event with unknown ID should return non-zero exit code."""
        exit_code = main(["show-event", "not-a-real-id"])
        captured = capsys.readouterr()
        
        assert exit_code != 0
        # Should print error message
        assert "Error:" in captured.err

    def test_invalid_command(self, capsys):
        """Invalid command should return non-zero exit code."""
        exit_code = main(["not-a-command"])
        captured = capsys.readouterr()
        
        assert exit_code != 0
        # argparse should show error message
        assert "invalid choice" in captured.err.lower()


class TestAdditionalCommands:
    """Test additional dossier commands that exist but aren't in README."""

    def test_show_char_dossier(self, capsys):
        """show-char-dossier should work and return structured dossier."""
        exit_code = main(["show-char-dossier", "jesus"])
        captured = capsys.readouterr()
        
        assert exit_code == 0
        # Should be valid JSON
        data = json.loads(captured.out)
        assert isinstance(data, dict)
        assert len(data) > 0

    def test_show_event_dossier(self, capsys):
        """show-event-dossier should work and return structured dossier."""
        exit_code = main(["show-event-dossier", "crucifixion"])
        captured = capsys.readouterr()
        
        assert exit_code == 0
        # Should be valid JSON
        data = json.loads(captured.out)
        assert isinstance(data, dict)
        assert len(data) > 0
