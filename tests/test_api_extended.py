"""Extended API tests to improve coverage of bce/api.py."""

from __future__ import annotations

from pathlib import Path

import pytest

from bce import api
from bce.config import BceConfig, set_default_config, reset_default_config


class TestBuildAllDossiers:
    """Test build_all_*_dossiers functions."""

    def test_build_all_character_dossiers(self):
        """build_all_character_dossiers should return list of all character dossiers."""
        dossiers = api.build_all_character_dossiers()

        assert isinstance(dossiers, list)
        assert len(dossiers) > 0

        # Verify dossier structure
        for dossier in dossiers:
            assert isinstance(dossier, dict)
            assert "id" in dossier
            assert "canonical_name" in dossier
            assert "traits_by_source" in dossier
            assert "trait_conflicts" in dossier

        # Verify specific characters are included
        jesus_dossier = next((d for d in dossiers if d["id"] == "jesus"), None)
        assert jesus_dossier is not None
        assert jesus_dossier["canonical_name"] == "Jesus of Nazareth"

    def test_build_all_event_dossiers(self):
        """build_all_event_dossiers should return list of all event dossiers."""
        dossiers = api.build_all_event_dossiers()

        assert isinstance(dossiers, list)
        assert len(dossiers) > 0

        # Verify dossier structure
        for dossier in dossiers:
            assert isinstance(dossier, dict)
            assert "id" in dossier
            assert "label" in dossier
            assert "accounts" in dossier
            assert "account_conflicts" in dossier

        # Verify specific events are included
        crucifixion_dossier = next((d for d in dossiers if d["id"] == "crucifixion"), None)
        assert crucifixion_dossier is not None
        assert "Crucifixion" in crucifixion_dossier["label"]


class TestCSVExport:
    """Test CSV export functions."""

    def test_export_characters_csv(self, tmp_path: Path):
        """export_characters_csv should create a CSV file."""
        output_file = tmp_path / "characters.csv"

        api.export_characters_csv(str(output_file))

        assert output_file.exists()
        content = output_file.read_text()

        # Verify CSV has header and data
        lines = content.strip().split("\n")
        assert len(lines) > 1  # Header + at least one row

        # Verify header contains expected columns
        header = lines[0]
        assert "id" in header.lower()
        assert "canonical_name" in header.lower()

        # Verify Jesus is in the export
        assert any("jesus" in line.lower() for line in lines[1:])

    def test_export_characters_csv_with_include_fields(self, tmp_path: Path):
        """export_characters_csv with include_fields should work."""
        output_file = tmp_path / "characters_subset.csv"

        api.export_characters_csv(str(output_file), include_fields=["id", "canonical_name"])

        assert output_file.exists()
        content = output_file.read_text()

        lines = content.strip().split("\n")
        assert len(lines) > 1

    def test_export_events_csv(self, tmp_path: Path):
        """export_events_csv should create a CSV file."""
        output_file = tmp_path / "events.csv"

        api.export_events_csv(str(output_file))

        assert output_file.exists()
        content = output_file.read_text()

        # Verify CSV has header and data
        lines = content.strip().split("\n")
        assert len(lines) > 1  # Header + at least one row

        # Verify header contains expected columns
        header = lines[0]
        assert "id" in header.lower()
        assert "label" in header.lower()

        # Verify crucifixion is in the export
        assert any("crucifixion" in line.lower() for line in lines[1:])

    def test_export_events_csv_with_include_fields(self, tmp_path: Path):
        """export_events_csv with include_fields should work."""
        output_file = tmp_path / "events_subset.csv"

        api.export_events_csv(str(output_file), include_fields=["id", "label"])

        assert output_file.exists()
        content = output_file.read_text()

        lines = content.strip().split("\n")
        assert len(lines) > 1


class TestAIFeaturesDisabled:
    """Test AI features when disabled (default state)."""

    def test_analyze_semantic_contradictions_requires_ai_enabled(self):
        """analyze_semantic_contradictions should raise error when AI disabled."""
        from bce.exceptions import ConfigurationError

        with pytest.raises(ConfigurationError, match="AI features are disabled"):
            api.analyze_semantic_contradictions("jesus")

    def test_audit_character_completeness_requires_ai_enabled(self):
        """audit_character_completeness should raise error when AI disabled."""
        from bce.exceptions import ConfigurationError

        with pytest.raises(ConfigurationError, match="AI features are disabled"):
            api.audit_character_completeness("jesus")

    def test_audit_character_completeness_all_requires_ai_enabled(self):
        """audit_character_completeness with no char_id should raise error when AI disabled."""
        from bce.exceptions import ConfigurationError

        with pytest.raises(ConfigurationError, match="AI features are disabled"):
            api.audit_character_completeness(None)

    def test_get_validation_suggestions_requires_ai_enabled(self):
        """get_validation_suggestions should raise error when AI disabled."""
        from bce.exceptions import ConfigurationError

        with pytest.raises(ConfigurationError, match="AI features are disabled"):
            api.get_validation_suggestions()

    def test_semantic_search_requires_ai_enabled(self):
        """semantic_search should raise error when AI disabled."""
        from bce.exceptions import ConfigurationError

        with pytest.raises(ConfigurationError, match="AI features are disabled"):
            api.semantic_search("test query")

    def test_find_similar_characters_requires_ai_enabled(self):
        """find_similar_characters should raise error when AI disabled."""
        from bce.exceptions import ConfigurationError

        with pytest.raises(ConfigurationError, match="AI features are disabled"):
            api.find_similar_characters("jesus")

    def test_find_thematic_clusters_requires_ai_enabled(self):
        """find_thematic_clusters should raise error when AI disabled."""
        from bce.exceptions import ConfigurationError

        with pytest.raises(ConfigurationError, match="AI features are disabled"):
            api.find_thematic_clusters()

    def test_find_thematic_clusters_events_requires_ai_enabled(self):
        """find_thematic_clusters for events should raise error when AI disabled."""
        from bce.exceptions import ConfigurationError

        with pytest.raises(ConfigurationError, match="AI features are disabled"):
            api.find_thematic_clusters(entity_type="events")

    def test_find_thematic_clusters_invalid_entity_type(self):
        """find_thematic_clusters with invalid entity_type should raise ValueError."""
        # This should raise ValueError even before checking AI features
        with pytest.raises(ValueError, match="entity_type must be"):
            api.find_thematic_clusters(entity_type="invalid")
