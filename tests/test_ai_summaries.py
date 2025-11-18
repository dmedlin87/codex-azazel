"""
Comprehensive tests for bce/ai/summaries.py.

Tests summary generation functionality including:
- Character summaries (academic, accessible, technical styles)
- Event summaries (academic, accessible, technical styles)
- Helper functions (formatting, trimming, etc.)
- Edge cases (empty dossiers, missing fields, etc.)
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from bce.config import BceConfig, set_default_config, reset_default_config
from bce.exceptions import ConfigurationError


class TestSummariesConfiguration:
    """Tests for configuration and error handling."""

    def setup_method(self):
        """Setup for each test."""
        reset_default_config()

    def teardown_method(self):
        """Cleanup after each test."""
        reset_default_config()

    def test_generate_character_summary_raises_when_disabled(self):
        """Should raise ConfigurationError when AI is disabled."""
        from bce.ai import summaries

        config = BceConfig(enable_ai_features=False)
        set_default_config(config)

        fake_dossier = {
            "identity": {"id": "test", "canonical_name": "Test"}
        }

        with pytest.raises(ConfigurationError, match="AI features are disabled"):
            summaries.generate_character_summary(fake_dossier)

    def test_generate_event_summary_raises_when_disabled(self):
        """Should raise ConfigurationError when AI is disabled."""
        from bce.ai import summaries

        config = BceConfig(enable_ai_features=False)
        set_default_config(config)

        fake_dossier = {
            "identity": {"id": "test", "label": "Test Event"}
        }

        with pytest.raises(ConfigurationError):
            summaries.generate_event_summary(fake_dossier)

    def test_invalid_style_raises_error(self):
        """Should raise ValueError for invalid style."""
        from bce.ai import summaries

        with tempfile.TemporaryDirectory() as tmpdir:
            config = BceConfig(
                enable_ai_features=True,
                ai_cache_dir=Path(tmpdir)
            )
            set_default_config(config)

            fake_dossier = {
                "identity": {"id": "test", "canonical_name": "Test"}
            }

            with pytest.raises(ValueError, match="Unknown style"):
                summaries.generate_character_summary(fake_dossier, style="invalid")


class TestGenerateCharacterSummary:
    """Tests for generate_character_summary function."""

    def setup_method(self):
        """Setup for each test."""
        reset_default_config()

    def teardown_method(self):
        """Cleanup after each test."""
        reset_default_config()

    def test_generate_academic_style(self):
        """Should generate academic-style summary."""
        from bce.ai import summaries

        with tempfile.TemporaryDirectory() as tmpdir:
            config = BceConfig(
                enable_ai_features=True,
                ai_cache_dir=Path(tmpdir)
            )
            set_default_config(config)

            dossier = {
                "identity": {
                    "id": "paul",
                    "canonical_name": "Paul",
                    "roles": ["apostle", "missionary"],
                    "tags": ["conversion"]
                },
                "traits_by_source": {
                    "acts": {"conversion": "Damascus road"},
                    "paul_undisputed": {"authority": "Apostolic"}
                },
                "all_traits": {
                    "conversion": {"acts": "Damascus road"},
                    "authority": {"paul_undisputed": "Apostolic"}
                },
                "all_references": ["Acts 9:1", "Gal 1:1"],
                "conflicts": {},
                "relationships": []
            }

            summary = summaries.generate_character_summary(
                dossier,
                style="academic"
            )

            assert "Paul" in summary
            assert isinstance(summary, str)
            assert len(summary) > 0

    def test_generate_accessible_style(self):
        """Should generate accessible-style summary."""
        from bce.ai import summaries

        with tempfile.TemporaryDirectory() as tmpdir:
            config = BceConfig(
                enable_ai_features=True,
                ai_cache_dir=Path(tmpdir)
            )
            set_default_config(config)

            dossier = {
                "identity": {
                    "id": "peter",
                    "canonical_name": "Peter",
                    "roles": ["apostle"],
                    "tags": []
                },
                "traits_by_source": {
                    "mark": {"role": "disciple"}
                },
                "all_traits": {"role": {"mark": "disciple"}},
                "all_references": [],
                "conflicts": {},
                "relationships": []
            }

            summary = summaries.generate_character_summary(
                dossier,
                style="accessible"
            )

            assert "Peter" in summary
            assert "is known as" in summary or "is" in summary

    def test_generate_technical_style(self):
        """Should generate technical-style summary."""
        from bce.ai import summaries

        with tempfile.TemporaryDirectory() as tmpdir:
            config = BceConfig(
                enable_ai_features=True,
                ai_cache_dir=Path(tmpdir)
            )
            set_default_config(config)

            dossier = {
                "identity": {
                    "id": "john",
                    "canonical_name": "John",
                    "roles": ["apostle"],
                    "tags": ["disciple", "beloved"]
                },
                "traits_by_source": {
                    "john": {"identity": "beloved disciple"}
                },
                "all_traits": {"identity": {"john": "beloved disciple"}},
                "all_references": ["John 13:23"],
                "conflicts": {},
                "relationships": []
            }

            summary = summaries.generate_character_summary(
                dossier,
                style="technical"
            )

            assert "Character ID:" in summary
            assert "john" in summary.lower()

    def test_respects_max_words(self):
        """Should respect max_words parameter."""
        from bce.ai import summaries

        with tempfile.TemporaryDirectory() as tmpdir:
            config = BceConfig(
                enable_ai_features=True,
                ai_cache_dir=Path(tmpdir)
            )
            set_default_config(config)

            dossier = {
                "identity": {
                    "id": "paul",
                    "canonical_name": "Paul the Apostle",
                    "roles": ["apostle", "missionary", "teacher", "writer"],
                    "tags": ["conversion", "resurrection", "theology"]
                },
                "traits_by_source": {
                    "acts": {"conversion": "Damascus road conversion"},
                    "paul_undisputed": {
                        "authority": "Apostolic authority",
                        "theology": "Justification by faith"
                    }
                },
                "all_traits": {
                    "conversion": {"acts": "Damascus road"},
                    "authority": {"paul_undisputed": "Apostolic"}
                },
                "all_references": ["Acts 9:1-19", "Gal 1:1-24"],
                "conflicts": {},
                "relationships": [
                    {"type": "colleague", "to": "barnabas", "description": "Missionary companion"}
                ]
            }

            summary = summaries.generate_character_summary(
                dossier,
                max_words=50
            )

            word_count = len(summary.split())
            # Allow some tolerance for sentence boundary trimming
            assert word_count <= 60


class TestGenerateEventSummary:
    """Tests for generate_event_summary function."""

    def setup_method(self):
        """Setup for each test."""
        reset_default_config()

    def teardown_method(self):
        """Cleanup after each test."""
        reset_default_config()

    def test_generate_academic_event_summary(self):
        """Should generate academic-style event summary."""
        from bce.ai import summaries

        with tempfile.TemporaryDirectory() as tmpdir:
            config = BceConfig(
                enable_ai_features=True,
                ai_cache_dir=Path(tmpdir)
            )
            set_default_config(config)

            dossier = {
                "identity": {
                    "id": "crucifixion",
                    "label": "Crucifixion of Jesus",
                    "tags": ["passion", "death"]
                },
                "participants": ["jesus", "pilate", "mary"],
                "accounts": [
                    {
                        "source_id": "mark",
                        "reference": "Mark 15:1-47",
                        "summary": "Jesus crucified at Golgotha",
                        "notes": None
                    },
                    {
                        "source_id": "matthew",
                        "reference": "Matt 27:1-66",
                        "summary": "Jesus crucified with various signs",
                        "notes": None
                    }
                ],
                "parallels": [
                    {
                        "sources": ["mark", "matthew", "luke"],
                        "type": "synoptic_parallel"
                    }
                ],
                "conflicts": {}
            }

            summary = summaries.generate_event_summary(
                dossier,
                style="academic"
            )

            assert "Crucifixion" in summary
            assert isinstance(summary, str)

    def test_generate_accessible_event_summary(self):
        """Should generate accessible-style event summary."""
        from bce.ai import summaries

        with tempfile.TemporaryDirectory() as tmpdir:
            config = BceConfig(
                enable_ai_features=True,
                ai_cache_dir=Path(tmpdir)
            )
            set_default_config(config)

            dossier = {
                "identity": {
                    "id": "resurrection",
                    "label": "Resurrection Appearance",
                    "tags": ["resurrection"]
                },
                "participants": ["jesus", "mary_magdalene"],
                "accounts": [
                    {
                        "source_id": "john",
                        "reference": "John 20:11-18",
                        "summary": "Jesus appears to Mary in the garden",
                        "notes": None
                    }
                ],
                "parallels": [],
                "conflicts": {}
            }

            summary = summaries.generate_event_summary(
                dossier,
                style="accessible"
            )

            assert "resurrection appearance" in summary.lower()
            assert "john" in summary.lower()

    def test_generate_technical_event_summary(self):
        """Should generate technical-style event summary."""
        from bce.ai import summaries

        with tempfile.TemporaryDirectory() as tmpdir:
            config = BceConfig(
                enable_ai_features=True,
                ai_cache_dir=Path(tmpdir)
            )
            set_default_config(config)

            dossier = {
                "identity": {
                    "id": "baptism",
                    "label": "Baptism of Jesus",
                    "tags": ["ministry_start"]
                },
                "participants": ["jesus", "john_baptist"],
                "accounts": [
                    {
                        "source_id": "mark",
                        "reference": "Mark 1:9-11",
                        "summary": "Jesus baptized by John",
                        "notes": None
                    }
                ],
                "parallels": [],
                "conflicts": {}
            }

            summary = summaries.generate_event_summary(
                dossier,
                style="technical"
            )

            assert "Event ID:" in summary
            assert "baptism" in summary.lower()

    def test_event_summary_with_conflicts(self):
        """Should mention conflicts in summary."""
        from bce.ai import summaries

        with tempfile.TemporaryDirectory() as tmpdir:
            config = BceConfig(
                enable_ai_features=True,
                ai_cache_dir=Path(tmpdir)
            )
            set_default_config(config)

            dossier = {
                "identity": {
                    "id": "trial",
                    "label": "Trial Before Pilate",
                    "tags": []
                },
                "participants": ["jesus", "pilate"],
                "accounts": [
                    {
                        "source_id": "mark",
                        "reference": "Mark 15:1-15",
                        "summary": "Brief trial",
                        "notes": None
                    }
                ],
                "parallels": [],
                "conflicts": {
                    "trial_details": {"mark": "Brief", "john": "Extended"}
                }
            }

            summary = summaries.generate_event_summary(
                dossier,
                style="academic"
            )

            assert "diverge" in summary.lower() or "conflict" in summary.lower()


class TestAcademicCharacterSummary:
    """Tests for _generate_academic_character_summary."""

    def setup_method(self):
        """Setup for each test."""
        reset_default_config()

    def test_with_roles(self):
        """Should include roles in summary."""
        from bce.ai.summaries import _generate_academic_character_summary

        dossier = {
            "identity": {
                "id": "paul",
                "canonical_name": "Paul",
                "roles": ["apostle", "missionary"],
                "tags": []
            },
            "traits_by_source": {"acts": {}},
            "all_traits": {},
            "all_references": [],
            "conflicts": {},
            "relationships": []
        }

        summary = _generate_academic_character_summary(dossier, 200)
        assert "apostle" in summary.lower() or "missionary" in summary.lower()

    def test_without_roles(self):
        """Should handle missing roles gracefully."""
        from bce.ai.summaries import _generate_academic_character_summary

        dossier = {
            "identity": {
                "id": "unknown",
                "canonical_name": "Unknown Character",
                "roles": [],
                "tags": []
            },
            "traits_by_source": {},
            "all_traits": {},
            "all_references": [],
            "conflicts": {},
            "relationships": []
        }

        summary = _generate_academic_character_summary(dossier, 200)
        assert "significant figure" in summary.lower()

    def test_with_conflicts(self):
        """Should mention conflicts in summary."""
        from bce.ai.summaries import _generate_academic_character_summary

        dossier = {
            "identity": {
                "id": "judas",
                "canonical_name": "Judas",
                "roles": ["disciple"],
                "tags": []
            },
            "traits_by_source": {"mark": {}, "matthew": {}},
            "all_traits": {},
            "all_references": [],
            "conflicts": {
                "death_method": {
                    "values": {
                        "hanging": ["matthew"],
                        "falling": ["acts"]
                    }
                }
            },
            "relationships": []
        }

        summary = _generate_academic_character_summary(dossier, 200)
        assert "contradiction" in summary.lower()

    def test_with_relationships(self):
        """Should mention relationships in summary."""
        from bce.ai.summaries import _generate_academic_character_summary

        dossier = {
            "identity": {
                "id": "peter",
                "canonical_name": "Peter",
                "roles": ["apostle"],
                "tags": []
            },
            "traits_by_source": {},
            "all_traits": {},
            "all_references": [],
            "conflicts": {},
            "relationships": [
                {"type": "brother", "to": "andrew", "description": "Brothers"}
            ]
        }

        summary = _generate_academic_character_summary(dossier, 200)
        assert "relationship" in summary.lower() or "andrew" in summary.lower()


class TestAccessibleCharacterSummary:
    """Tests for _generate_accessible_character_summary."""

    def setup_method(self):
        """Setup for each test."""
        reset_default_config()

    def test_simple_language(self):
        """Should use simple, accessible language."""
        from bce.ai.summaries import _generate_accessible_character_summary

        dossier = {
            "identity": {
                "id": "peter",
                "canonical_name": "Peter",
                "roles": ["fisherman", "apostle"],
                "tags": []
            },
            "traits_by_source": {"mark": {}},
            "all_traits": {},
            "all_references": [],
            "conflicts": {},
            "relationships": []
        }

        summary = _generate_accessible_character_summary(dossier, 200)
        assert "Peter is" in summary
        assert "known as" in summary or "fisherman" in summary.lower()

    def test_mentions_sources_count(self):
        """Should mention number of sources."""
        from bce.ai.summaries import _generate_accessible_character_summary

        dossier = {
            "identity": {
                "id": "paul",
                "canonical_name": "Paul",
                "roles": ["apostle"],
                "tags": []
            },
            "traits_by_source": {
                "acts": {},
                "paul_undisputed": {},
                "mark": {}
            },
            "all_traits": {},
            "all_references": [],
            "conflicts": {},
            "relationships": []
        }

        summary = _generate_accessible_character_summary(dossier, 200)
        assert "3" in summary or "three" in summary.lower()


class TestTechnicalCharacterSummary:
    """Tests for _generate_technical_character_summary."""

    def setup_method(self):
        """Setup for each test."""
        reset_default_config()

    def test_includes_id(self):
        """Should include character ID."""
        from bce.ai.summaries import _generate_technical_character_summary

        dossier = {
            "identity": {
                "id": "paul",
                "canonical_name": "Paul",
                "roles": [],
                "tags": []
            },
            "traits_by_source": {},
            "all_traits": {},
            "all_references": [],
            "conflicts": {},
            "relationships": []
        }

        summary = _generate_technical_character_summary(dossier, 200)
        assert "Character ID:" in summary
        assert "paul" in summary

    def test_includes_counts(self):
        """Should include various counts."""
        from bce.ai.summaries import _generate_technical_character_summary

        dossier = {
            "identity": {
                "id": "jesus",
                "canonical_name": "Jesus",
                "roles": ["teacher"],
                "tags": ["messiah", "resurrection"]
            },
            "traits_by_source": {
                "mark": {},
                "john": {}
            },
            "all_traits": {"trait1": {}, "trait2": {}},
            "all_references": ["Mark 1:1", "John 1:1"],
            "conflicts": {"conflict1": {}},
            "relationships": [{"type": "friend", "to": "lazarus"}]
        }

        summary = _generate_technical_character_summary(dossier, 200)
        assert "Source profiles:" in summary
        assert "Total traits:" in summary
        assert "Scripture references:" in summary
        assert "Detected conflicts:" in summary
        assert "Relationships:" in summary


class TestEventSummaryFunctions:
    """Tests for event summary generation functions."""

    def setup_method(self):
        """Setup for each test."""
        reset_default_config()

    def test_academic_event_with_participants(self):
        """Should include participant count in academic summary."""
        from bce.ai.summaries import _generate_academic_event_summary

        dossier = {
            "identity": {
                "id": "feeding",
                "label": "Feeding of the 5000",
                "tags": []
            },
            "participants": ["jesus", "philip", "andrew"],
            "accounts": [],
            "parallels": [],
            "conflicts": {}
        }

        summary = _generate_academic_event_summary(dossier, 150)
        assert "3 participants" in summary or "3 participant" in summary

    def test_accessible_event_uses_first_account(self):
        """Should use first account summary in accessible style."""
        from bce.ai.summaries import _generate_accessible_event_summary

        dossier = {
            "identity": {
                "id": "transfiguration",
                "label": "Transfiguration",
                "tags": []
            },
            "participants": ["jesus", "peter", "james"],
            "accounts": [
                {
                    "source_id": "mark",
                    "reference": "Mark 9:2-8",
                    "summary": "Jesus transformed on a mountain",
                    "notes": None
                }
            ],
            "parallels": [],
            "conflicts": {}
        }

        summary = _generate_accessible_event_summary(dossier, 150)
        assert "transformed on a mountain" in summary.lower()

    def test_technical_event_shows_all_counts(self):
        """Should show all counts in technical summary."""
        from bce.ai.summaries import _generate_technical_event_summary

        dossier = {
            "identity": {
                "id": "pentecost",
                "label": "Pentecost",
                "tags": ["spirit", "tongues"]
            },
            "participants": ["peter", "john"],
            "accounts": [
                {"source_id": "acts", "reference": "Acts 2:1-41", "summary": "Spirit comes"}
            ],
            "parallels": [],
            "conflicts": {}
        }

        summary = _generate_technical_event_summary(dossier, 200)
        assert "Event ID:" in summary
        assert "Accounts:" in summary
        assert "Participants:" in summary
        assert "Tags:" in summary


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_format_source_list(self):
        """Should format source names properly."""
        from bce.ai.summaries import _format_source_list

        result = _format_source_list(["mark", "matthew", "luke"])
        assert "Mark" in result
        assert "Matthew" in result
        assert "Luke" in result

    def test_format_source_list_paul(self):
        """Should format Paul sources specially."""
        from bce.ai.summaries import _format_source_list

        result = _format_source_list(["paul_undisputed"])
        assert "Pauline epistles" in result or "pauline" in result.lower()

    def test_format_list_single_item(self):
        """Should format single item without conjunction."""
        from bce.ai.summaries import _format_list

        result = _format_list(["item1"], "and")
        assert result == "item1"

    def test_format_list_two_items(self):
        """Should format two items with conjunction."""
        from bce.ai.summaries import _format_list

        result = _format_list(["item1", "item2"], "and")
        assert result == "item1 and item2"

    def test_format_list_three_items(self):
        """Should format three items with Oxford comma."""
        from bce.ai.summaries import _format_list

        result = _format_list(["item1", "item2", "item3"], "and")
        assert "item1, item2, and item3" == result

    def test_format_list_empty(self):
        """Should handle empty list."""
        from bce.ai.summaries import _format_list

        result = _format_list([], "and")
        assert result == ""

    def test_extract_source_highlights(self):
        """Should extract distinctive trait highlights."""
        from bce.ai.summaries import _extract_source_highlights

        dossier = {
            "traits_by_source": {
                "john": {
                    "divine_claims": "I and the Father are one",
                    "other_trait": "value"
                }
            }
        }

        highlights = _extract_source_highlights(dossier)
        assert len(highlights) > 0
        # Should find the divine_claims trait
        assert any("divine claims" in h.lower() for h in highlights)

    def test_extract_source_highlights_empty(self):
        """Should handle empty traits gracefully."""
        from bce.ai.summaries import _extract_source_highlights

        dossier = {
            "traits_by_source": {}
        }

        highlights = _extract_source_highlights(dossier)
        assert highlights == []

    def test_trim_to_words_under_limit(self):
        """Should not trim text under word limit."""
        from bce.ai.summaries import _trim_to_words

        text = "This is a short text."
        result = _trim_to_words(text, 100)
        assert result == text

    def test_trim_to_words_over_limit(self):
        """Should trim text over word limit."""
        from bce.ai.summaries import _trim_to_words

        text = " ".join(["word"] * 100)
        result = _trim_to_words(text, 10)
        word_count = len(result.split())
        assert word_count <= 10

    def test_trim_to_words_at_sentence_boundary(self):
        """Should try to trim at sentence boundary."""
        from bce.ai.summaries import _trim_to_words

        text = "First sentence. " + " ".join(["word"] * 50)
        result = _trim_to_words(text, 10)
        # Should end with period if possible
        if "." in result:
            assert result.endswith(".")
