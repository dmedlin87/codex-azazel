from __future__ import annotations

from bce import dossiers


def test_build_character_dossier_basic() -> None:
    d = dossiers.build_character_dossier("jesus")

    for key in (
        "id",
        "canonical_name",
        "aliases",
        "roles",
        "source_ids",
        "source_metadata",
        "traits_by_source",
        "trait_conflicts",
        "claim_graph",
    ):
        assert key in d

    assert d["id"] == "jesus"
    assert isinstance(d["source_ids"], list)
    assert isinstance(d["traits_by_source"], dict)


def test_character_dossier_includes_source_metadata_for_known_sources() -> None:
    """Character dossier should include source metadata for known sources."""
    d = dossiers.build_character_dossier("jesus")

    assert "source_metadata" in d
    meta = d["source_metadata"]
    assert isinstance(meta, dict)
    # At least Mark should have metadata defined in sources.json
    assert "mark" in meta
    assert isinstance(meta["mark"], dict)
    assert "date_range" in meta["mark"]


def test_build_event_dossier_basic() -> None:
    d = dossiers.build_event_dossier("crucifixion")

    for key in ("id", "label", "participants", "accounts", "account_conflicts"):
        assert key in d
    assert "claim_graph" in d

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


class TestDossierEdgeCases:
    """Test edge cases in dossier building."""

    def test_build_character_dossier_preserves_all_fields(self):
        """Character dossier should preserve all fields from original."""
        from bce import storage
        from bce.models import Character, SourceProfile

        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            storage.configure_data_root(Path(tmpdir))
            try:
                char = Character(
                    id="full_char",
                    canonical_name="Full Character",
                    aliases=["Alias1", "Alias2"],
                    roles=["Role1", "Role2"],
                    source_profiles=[
                        SourceProfile(
                            source_id="source1",
                            traits={"trait1": "value1"},
                            references=["Ref 1:1"]
                        )
                    ]
                )
                storage.save_character(char)

                dossier = dossiers.build_character_dossier("full_char")

                # All fields should be present
                assert dossier["id"] == "full_char"
                assert dossier["canonical_name"] == "Full Character"
                assert "Alias1" in dossier["aliases"]
                assert "Role1" in dossier["roles"]
                assert "source1" in dossier["source_ids"]
                assert "source1" in dossier["traits_by_source"]
                assert "source1" in dossier["references_by_source"]

            finally:
                storage.reset_data_root()

    def test_build_character_dossier_with_minimal_data(self):
        """Character with only required fields should build dossier."""
        from bce import storage
        from bce.models import Character

        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            storage.configure_data_root(Path(tmpdir))
            try:
                char = Character(
                    id="minimal",
                    canonical_name="Minimal"
                    # No aliases, roles, or source_profiles
                )
                storage.save_character(char)

                dossier = dossiers.build_character_dossier("minimal")

                assert dossier["id"] == "minimal"
                assert dossier["canonical_name"] == "Minimal"
                assert dossier["aliases"] == []
                assert dossier["roles"] == []
                assert dossier["source_ids"] == []
                assert dossier["traits_by_source"] == {}
                assert dossier["trait_conflicts"] == {}
                assert dossier["claim_graph"]["claims"] == []
                assert dossier["claim_graph"]["conflicts"] == []

            finally:
                storage.reset_data_root()

    def test_build_event_dossier_preserves_all_fields(self):
        """Event dossier should preserve all fields from original."""
        from bce import storage
        from bce.models import Event, EventAccount

        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            storage.configure_data_root(Path(tmpdir))
            try:
                event = Event(
                    id="full_event",
                    label="Full Event",
                    participants=["char1", "char2"],
                    accounts=[
                        EventAccount(
                            source_id="source1",
                            reference="Ref 1:1",
                            summary="Summary",
                            notes="Notes"
                        )
                    ]
                )
                storage.save_event(event)

                dossier = dossiers.build_event_dossier("full_event")

                assert dossier["id"] == "full_event"
                assert dossier["label"] == "Full Event"
                assert "char1" in dossier["participants"]
                assert len(dossier["accounts"]) == 1
                assert dossier["accounts"][0]["source_id"] == "source1"
                assert dossier["accounts"][0]["notes"] == "Notes"

            finally:
                storage.reset_data_root()

    def test_build_event_dossier_with_minimal_data(self):
        """Event with only required fields should build dossier."""
        from bce import storage
        from bce.models import Event

        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            storage.configure_data_root(Path(tmpdir))
            try:
                event = Event(
                    id="minimal_event",
                    label="Minimal"
                    # No participants or accounts
                )
                storage.save_event(event)

                dossier = dossiers.build_event_dossier("minimal_event")

                assert dossier["id"] == "minimal_event"
                assert dossier["label"] == "Minimal"
                assert dossier["participants"] == []
                assert dossier["accounts"] == []
                assert dossier["account_conflicts"] == {}
                assert dossier["claim_graph"]["claims"] == []
                assert dossier["claim_graph"]["conflicts"] == []

            finally:
                storage.reset_data_root()

    def test_build_all_character_dossiers_returns_list(self):
        """build_all_character_dossiers should return list of all dossiers."""
        all_dossiers = dossiers.build_all_character_dossiers()

        # Should be a list
        assert isinstance(all_dossiers, list)

        # Each item should be a dict with required fields
        for dossier in all_dossiers:
            assert isinstance(dossier, dict)
            assert "id" in dossier
            assert "canonical_name" in dossier

    def test_build_all_event_dossiers_returns_list(self):
        """build_all_event_dossiers should return list of all dossiers."""
        all_dossiers = dossiers.build_all_event_dossiers()

        # Should be a list
        assert isinstance(all_dossiers, list)

        # Each item should be a dict with required fields
        for dossier in all_dossiers:
            assert isinstance(dossier, dict)
            assert "id" in dossier
            assert "label" in dossier

    def test_character_dossier_includes_trait_comparison(self):
        """Character dossier should include trait comparison."""
        dossier = dossiers.build_character_dossier("jesus")

        assert "trait_comparison" in dossier
        assert isinstance(dossier["trait_comparison"], dict)

    def test_character_dossier_includes_trait_conflicts(self):
        """Character dossier should include trait conflicts."""
        dossier = dossiers.build_character_dossier("jesus")

        assert "trait_conflicts" in dossier
        assert isinstance(dossier["trait_conflicts"], dict)

    def test_event_dossier_includes_account_conflicts(self):
        """Event dossier should include account conflicts."""
        dossier = dossiers.build_event_dossier("crucifixion")

        assert "account_conflicts" in dossier
        assert isinstance(dossier["account_conflicts"], dict)

    def test_dossier_serialization_to_json(self):
        """Dossiers should be JSON-serializable."""
        import json

        char_dossier = dossiers.build_character_dossier("jesus")
        event_dossier = dossiers.build_event_dossier("crucifixion")

        # Should not raise an error
        char_json = json.dumps(char_dossier)
        event_json = json.dumps(event_dossier)

        # Should be able to parse back
        parsed_char = json.loads(char_json)
        parsed_event = json.loads(event_json)

        assert parsed_char["id"] == "jesus"
        assert parsed_event["id"] == "crucifixion"

    def test_character_dossier_includes_relationships(self) -> None:
        dossier = dossiers.build_character_dossier("paul")

        assert "relationships" in dossier
        relationships = dossier["relationships"]
        assert isinstance(relationships, list)
        assert relationships, "expected at least one relationship for paul"

        first = relationships[0]
        assert isinstance(first, dict)
        assert "character_id" in first
        assert "type" in first
        assert "sources" in first
        assert "references" in first
        assert "notes" in first

    def test_event_dossier_includes_parallels(self) -> None:
        dossier = dossiers.build_event_dossier("empty_tomb")

        assert "parallels" in dossier
        parallels = dossier["parallels"]
        assert isinstance(parallels, list)
        assert parallels, "expected at least one parallels entry for empty_tomb"

        entry = parallels[0]
        assert isinstance(entry, dict)
        assert "sources" in entry
        assert "references" in entry
        assert isinstance(entry["sources"], list)
        assert isinstance(entry["references"], dict)
