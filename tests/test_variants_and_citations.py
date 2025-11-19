"""Tests for textual variants and citations features."""

from __future__ import annotations

import pytest
from bce.models import (
    TextualVariant,
    SourceProfile,
    EventAccount,
    Character,
    Event,
    STANDARD_TRAIT_KEYS,
)
from bce import storage, queries, dossiers, validation


class TestTextualVariant:
    """Tests for TextualVariant model."""

    def test_textual_variant_creation(self):
        """Test creating a TextualVariant."""
        variant = TextualVariant(
            manuscript_family="LXX",
            reading="sons of God",
            significance="Reflects divine council imagery",
        )
        assert variant.manuscript_family == "LXX"
        assert variant.reading == "sons of God"
        assert variant.significance == "Reflects divine council imagery"

    def test_textual_variant_requires_all_fields(self):
        """Test that TextualVariant requires all fields to be non-empty."""
        # Test empty manuscript_family
        with pytest.raises(ValueError, match="manuscript_family cannot be empty"):
            TextualVariant(
                manuscript_family="",
                reading="test",
                significance="test",
            )

        # Test empty reading
        with pytest.raises(ValueError, match="reading cannot be empty"):
            TextualVariant(
                manuscript_family="MT",
                reading="",
                significance="test",
            )

        # Test empty significance
        with pytest.raises(ValueError, match="significance cannot be empty"):
            TextualVariant(
                manuscript_family="MT",
                reading="test",
                significance="",
            )


class TestSourceProfileVariantsAndCitations:
    """Tests for SourceProfile with variants and citations."""

    def test_source_profile_with_variants(self):
        """Test SourceProfile with textual variants."""
        variant = TextualVariant(
            manuscript_family="LXX",
            reading="sons of God",
            significance="Divine council imagery",
        )
        profile = SourceProfile(
            source_id="septuagint",
            traits={"portrayal": "Test"},
            references=["Genesis 6:2"],
            variants=[variant],
            citations=["Meier1994"],
        )

        assert len(profile.variants) == 1
        assert profile.variants[0].manuscript_family == "LXX"
        assert len(profile.citations) == 1
        assert profile.citations[0] == "Meier1994"

    def test_source_profile_defaults(self):
        """Test SourceProfile default values for new fields."""
        profile = SourceProfile(source_id="test")
        assert profile.variants == []
        assert profile.citations == []


class TestEventAccountVariants:
    """Tests for EventAccount with variants."""

    def test_event_account_with_variants(self):
        """Test EventAccount with textual variants."""
        variant = TextualVariant(
            manuscript_family="P46",
            reading="alternative reading",
            significance="Pauline textual tradition",
        )
        account = EventAccount(
            source_id="paul",
            reference="1 Corinthians 15:3-8",
            summary="Resurrection appearance list",
            variants=[variant],
        )

        assert len(account.variants) == 1
        assert account.variants[0].manuscript_family == "P46"

    def test_event_account_defaults(self):
        """Test EventAccount default values for variants."""
        account = EventAccount(
            source_id="mark",
            reference="Mark 16:1-8",
            summary="Empty tomb",
        )
        assert account.variants == []


class TestEventCitations:
    """Tests for Event with citations."""

    def test_event_with_citations(self):
        """Test Event with citations."""
        event = Event(
            id="test_event",
            label="Test Event",
            citations=["Brown1994", "Crossan1995"],
        )

        assert len(event.citations) == 2
        assert "Brown1994" in event.citations

    def test_event_defaults(self):
        """Test Event default values for citations."""
        event = Event(id="test", label="Test")
        assert event.citations == []


class TestStorageSerialization:
    """Tests for storage serialization/deserialization of new fields."""

    def test_character_with_variants_roundtrip(self, tmp_path):
        """Test saving and loading a character with variants and citations."""
        from bce.config import BceConfig

        # Create test character with variants and citations
        variant = TextualVariant(
            manuscript_family="LXX",
            reading="test reading",
            significance="test significance",
        )
        profile = SourceProfile(
            source_id="test_source",
            traits={"mission_focus": "test"},
            references=["Test 1:1"],
            variants=[variant],
            citations=["TestCitation2024"],
        )
        char = Character(
            id="test_char",
            canonical_name="Test Character",
            source_profiles=[profile],
        )

        # Set up temp storage
        data_root = tmp_path / "data"
        char_dir = data_root / "characters"
        char_dir.mkdir(parents=True)
        (data_root / "events").mkdir(parents=True)

        config = BceConfig(data_root=data_root)
        store = storage.StorageManager(config)

        # Save and reload
        store.save_character(char)
        loaded = store.load_character("test_char")

        # Verify variants
        assert len(loaded.source_profiles) == 1
        assert len(loaded.source_profiles[0].variants) == 1
        v = loaded.source_profiles[0].variants[0]
        assert v.manuscript_family == "LXX"
        assert v.reading == "test reading"
        assert v.significance == "test significance"

        # Verify citations
        assert len(loaded.source_profiles[0].citations) == 1
        assert loaded.source_profiles[0].citations[0] == "TestCitation2024"

    def test_event_with_variants_roundtrip(self, tmp_path):
        """Test saving and loading an event with variants and citations."""
        from bce.config import BceConfig

        # Create test event with variants and citations
        variant = TextualVariant(
            manuscript_family="P46",
            reading="variant text",
            significance="important difference",
        )
        account = EventAccount(
            source_id="paul",
            reference="1 Cor 15:3",
            summary="Test summary",
            variants=[variant],
        )
        event = Event(
            id="test_event",
            label="Test Event",
            accounts=[account],
            citations=["Citation1", "Citation2"],
        )

        # Set up temp storage
        data_root = tmp_path / "data"
        event_dir = data_root / "events"
        event_dir.mkdir(parents=True)
        (data_root / "characters").mkdir(parents=True)

        config = BceConfig(data_root=data_root)
        store = storage.StorageManager(config)

        # Save and reload
        store.save_event(event)
        loaded = store.load_event("test_event")

        # Verify account variants
        assert len(loaded.accounts) == 1
        assert len(loaded.accounts[0].variants) == 1
        v = loaded.accounts[0].variants[0]
        assert v.manuscript_family == "P46"
        assert v.reading == "variant text"

        # Verify event citations
        assert len(loaded.citations) == 2
        assert "Citation1" in loaded.citations


class TestDossierIntegration:
    """Tests for dossier integration with new fields."""

    def test_character_dossier_includes_variants_and_citations(self, tmp_path):
        """Test that character dossiers include variants and citations."""
        from bce.config import BceConfig, set_default_config

        # Create test character
        variant = TextualVariant(
            manuscript_family="MT",
            reading="masoretic reading",
            significance="traditional text",
        )
        profile = SourceProfile(
            source_id="hebrew",
            traits={"portrayal": "test"},
            references=["Gen 1:1"],
            variants=[variant],
            citations=["Scholarly2024"],
        )
        char = Character(
            id="test_dossier_char",
            canonical_name="Test Dossier",
            source_profiles=[profile],
        )

        # Set up storage
        data_root = tmp_path / "data"
        char_dir = data_root / "characters"
        char_dir.mkdir(parents=True)
        (data_root / "events").mkdir(parents=True)

        config = BceConfig(data_root=data_root)
        store = storage.StorageManager(config)
        set_default_config(config)

        store.save_character(char)

        # Build dossier
        dossier = dossiers.build_character_dossier("test_dossier_char")

        # Verify variants_by_source
        assert "variants_by_source" in dossier
        assert "hebrew" in dossier["variants_by_source"]
        variants = dossier["variants_by_source"]["hebrew"]
        assert len(variants) == 1
        assert variants[0]["manuscript_family"] == "MT"

        # Verify citations_by_source
        assert "citations_by_source" in dossier
        assert "hebrew" in dossier["citations_by_source"]
        assert "Scholarly2024" in dossier["citations_by_source"]["hebrew"]

    def test_event_dossier_includes_variants_and_citations(self, tmp_path):
        """Test that event dossiers include variants and citations."""
        from bce.config import BceConfig, set_default_config, reset_default_config

        # Create test event
        variant = TextualVariant(
            manuscript_family="Codex Sinaiticus",
            reading="sinaiticus reading",
            significance="early manuscript",
        )
        account = EventAccount(
            source_id="john",
            reference="John 21:1-14",
            summary="Post-resurrection appearance",
            variants=[variant],
        )
        event = Event(
            id="test_dossier_event2",  # Use unique ID
            label="Test Event Dossier",
            accounts=[account],
            citations=["Brown1970"],
        )

        # Set up storage
        data_root = tmp_path / "data"
        event_dir = data_root / "events"
        event_dir.mkdir(parents=True)
        (data_root / "characters").mkdir(parents=True)

        config = BceConfig(data_root=data_root)
        set_default_config(config)
        storage._reset_default_storage()  # Force reset storage manager
        queries.clear_cache()  # Clear query cache

        try:
            # Use storage module-level functions that respect default config
            storage.save_event(event)

            # Build dossier
            dossier = dossiers.build_event_dossier("test_dossier_event2")

            # Verify account variants
            assert len(dossier["accounts"]) == 1
            assert "variants" in dossier["accounts"][0]
            assert len(dossier["accounts"][0]["variants"]) == 1
            assert dossier["accounts"][0]["variants"][0]["manuscript_family"] == "Codex Sinaiticus"

            # Verify event citations
            assert "citations" in dossier
            assert "Brown1970" in dossier["citations"]
        finally:
            # Clean up
            reset_default_config()
            storage._reset_default_storage()
            queries.clear_cache()


class TestTraitKeyValidation:
    """Tests for trait key vocabulary validation."""

    def test_standard_trait_keys_exist(self):
        """Test that standard trait keys constant exists and has content."""
        assert len(STANDARD_TRAIT_KEYS) > 0
        # Check for some expected keys
        assert "mission_focus" in STANDARD_TRAIT_KEYS
        assert "eschatology" in STANDARD_TRAIT_KEYS
        assert "miracles" in STANDARD_TRAIT_KEYS

    def test_validation_warns_on_nonstandard_keys(self, tmp_path):
        """Test that validation warns on non-standard trait keys."""
        from bce.config import BceConfig, set_default_config, reset_default_config

        # Create character with non-standard trait key
        profile = SourceProfile(
            source_id="test",
            traits={"nonstandard_key": "value"},  # Not in STANDARD_TRAIT_KEYS
            references=["Test 1:1"],
        )
        char = Character(
            id="test_nonstandard",
            canonical_name="Test",
            source_profiles=[profile],
        )

        # Set up storage
        data_root = tmp_path / "data"
        char_dir = data_root / "characters"
        char_dir.mkdir(parents=True)
        (data_root / "events").mkdir(parents=True)

        config = BceConfig(data_root=data_root)
        set_default_config(config)
        storage._reset_default_storage()  # Force reset storage manager
        queries.clear_cache()  # Clear query cache

        try:
            # Use storage module-level functions
            storage.save_character(char)

            # Run validation
            errors = validation.validate_all()

            # Should have a warning about non-standard key
            warnings = [e for e in errors if "[WARNING]" in e and "nonstandard_key" in e]
            assert len(warnings) > 0, f"Expected warnings but got: {errors}"
        finally:
            # Clean up
            reset_default_config()
            storage._reset_default_storage()
            queries.clear_cache()

    def test_validation_accepts_standard_keys(self, tmp_path):
        """Test that validation accepts standard trait keys without warnings."""
        from bce.config import BceConfig, set_default_config

        # Create character with standard trait keys
        profile = SourceProfile(
            source_id="test",
            traits={
                "mission_focus": "test mission",
                "eschatology": "test eschatology",
            },
            references=["Test 1:1"],
        )
        char = Character(
            id="test_standard",
            canonical_name="Test",
            source_profiles=[profile],
        )

        # Set up storage
        data_root = tmp_path / "data"
        char_dir = data_root / "characters"
        char_dir.mkdir(parents=True)
        (data_root / "events").mkdir(parents=True)

        config = BceConfig(data_root=data_root)
        store = storage.StorageManager(config)
        set_default_config(config)

        store.save_character(char)

        # Run validation
        errors = validation.validate_all()

        # Should not have warnings about standard keys
        warnings = [
            e for e in errors
            if "[WARNING]" in e and ("mission_focus" in e or "eschatology" in e)
        ]
        assert len(warnings) == 0


class TestCrossReferenceValidation:
    """Test that cross-reference validation is integrated into validate_all."""

    def test_validate_all_includes_cross_references(self):
        """Test that validate_all now includes cross-reference validation."""
        # This is a smoke test to ensure cross-reference validation runs
        # The actual character/event validation is tested elsewhere
        errors = validation.validate_all()
        # Should not raise an exception
        assert isinstance(errors, list)
