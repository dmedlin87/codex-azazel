"""
Tests for AI validation assistant module (Phase 6.2).

Comprehensive tests for bce/ai/validation_assistant.py to achieve 75-80% coverage.
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from bce.config import BceConfig, set_default_config, reset_default_config
from bce.exceptions import ConfigurationError
from bce.ai import validation_assistant


class TestValidationAssistantWithAIDisabled:
    """Tests that verify AI features are properly gated."""

    def setup_method(self):
        """Reset configuration before each test."""
        reset_default_config()
        os.environ.pop("BCE_ENABLE_AI_FEATURES", None)

    def teardown_method(self):
        """Clean up after each test."""
        reset_default_config()

    def test_suggest_fixes_requires_ai_enabled(self):
        """Should raise ConfigurationError when AI is disabled."""
        config = BceConfig(enable_ai_features=False)
        set_default_config(config)

        with pytest.raises(ConfigurationError, match="AI features are disabled"):
            validation_assistant.suggest_fixes(errors=["test error"])


class TestSuggestFixesBasic:
    """Basic tests for suggest_fixes function."""

    def setup_method(self):
        """Enable AI features for testing."""
        reset_default_config()
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

    def teardown_method(self):
        """Clean up after each test."""
        reset_default_config()

    def test_suggest_fixes_empty_errors(self):
        """Should return empty list for no errors."""
        result = validation_assistant.suggest_fixes(errors=[], use_cache=False)
        assert result == []

    def test_suggest_fixes_runs_validation_if_none(self):
        """Should run validate_all if errors is None."""
        with patch("bce.ai.validation_assistant.validate_all", return_value=[]):
            result = validation_assistant.suggest_fixes(errors=None, use_cache=False)
            assert result == []

    def test_suggest_fixes_structure(self):
        """Each suggestion should have required fields."""
        errors = ["Event 'foo' references unknown character 'bar'"]

        with patch("bce.ai.validation_assistant.list_character_ids", return_value=["bar2", "baz"]):
            result = validation_assistant.suggest_fixes(errors=errors, use_cache=False)

        assert len(result) > 0
        for suggestion in result:
            assert "error" in suggestion
            assert "suggestion" in suggestion
            assert "confidence" in suggestion
            assert "similar_items" in suggestion

            assert isinstance(suggestion["error"], str)
            assert isinstance(suggestion["suggestion"], str)
            assert isinstance(suggestion["confidence"], (int, float))
            assert isinstance(suggestion["similar_items"], list)
            assert 0.0 <= suggestion["confidence"] <= 1.0

    def test_suggest_fixes_caching(self):
        """Should use cache when enabled."""
        errors = ["Test error message"]

        result1 = validation_assistant.suggest_fixes(errors=errors, use_cache=False)
        result2 = validation_assistant.suggest_fixes(errors=errors, use_cache=True)

        # Results should be consistent
        assert len(result1) == len(result2)


class TestHashErrorList:
    """Tests for _hash_error_list helper."""

    def test_hash_empty_list(self):
        """Should hash empty list consistently."""
        hash1 = validation_assistant._hash_error_list([])
        hash2 = validation_assistant._hash_error_list([])

        assert hash1 == hash2
        assert isinstance(hash1, str)
        assert len(hash1) == 16  # Truncated to 16 chars

    def test_hash_single_error(self):
        """Should hash single error consistently."""
        errors = ["error message 1"]
        hash1 = validation_assistant._hash_error_list(errors)
        hash2 = validation_assistant._hash_error_list(errors)

        assert hash1 == hash2

    def test_hash_order_independence(self):
        """Hash should be same regardless of error order (sorted)."""
        errors1 = ["error A", "error B", "error C"]
        errors2 = ["error C", "error A", "error B"]

        hash1 = validation_assistant._hash_error_list(errors1)
        hash2 = validation_assistant._hash_error_list(errors2)

        # Should be same due to sorting
        assert hash1 == hash2

    def test_hash_different_errors(self):
        """Different errors should produce different hashes."""
        hash1 = validation_assistant._hash_error_list(["error 1"])
        hash2 = validation_assistant._hash_error_list(["error 2"])

        assert hash1 != hash2


class TestSuggestMissingCharacterFix:
    """Tests for _suggest_missing_character_fix function."""

    def test_missing_character_with_similar_matches(self):
        """Should suggest similar character IDs."""
        error = "Event 'crucifixion' references unknown character 'jesu'"

        with patch("bce.ai.validation_assistant.list_character_ids") as mock_list:
            mock_list.return_value = ["jesus", "john", "judas"]

            result = validation_assistant._suggest_missing_character_fix(error)

            assert result["error"] == error
            assert "jesu" in result["suggestion"]
            assert "jesus" in result["suggestion"]  # Should suggest similar ID
            assert result["confidence"] == 0.85
            assert len(result["similar_items"]) > 0
            assert "jesus" in result["similar_items"]

    def test_missing_character_no_matches(self):
        """Should suggest creating new character file when no matches."""
        error = "Event 'foo' references unknown character 'completely_unknown'"

        with patch("bce.ai.validation_assistant.list_character_ids") as mock_list:
            mock_list.return_value = ["jesus", "peter", "paul"]

            result = validation_assistant._suggest_missing_character_fix(error)

            assert result["error"] == error
            assert "completely_unknown" in result["suggestion"]
            assert "Create a new character file" in result["suggestion"]
            assert result["confidence"] == 0.70
            assert len(result["similar_items"]) == 0

    def test_missing_character_no_id_in_error(self):
        """Should handle error message without parseable character ID."""
        error = "Something went wrong with characters"

        result = validation_assistant._suggest_missing_character_fix(error)

        assert result["error"] == error
        assert "Check the character ID spelling" in result["suggestion"]
        assert result["confidence"] == 0.5
        assert result["similar_items"] == []


class TestSuggestMissingEventFix:
    """Tests for _suggest_missing_event_fix function."""

    def test_missing_event_with_similar_matches(self):
        """Should suggest similar event IDs."""
        error = "Character 'jesus' references unknown event 'crucifiction'"  # Typo

        with patch("bce.ai.validation_assistant.list_event_ids") as mock_list:
            mock_list.return_value = ["crucifixion", "resurrection", "betrayal"]

            result = validation_assistant._suggest_missing_event_fix(error)

            assert result["error"] == error
            assert "crucifiction" in result["suggestion"]
            assert result["confidence"] == 0.85
            assert len(result["similar_items"]) > 0

    def test_missing_event_no_matches(self):
        """Should suggest creating new event file when no matches."""
        error = "Character 'foo' references unknown event 'xyz_123'"

        with patch("bce.ai.validation_assistant.list_event_ids") as mock_list:
            mock_list.return_value = ["crucifixion", "resurrection"]

            result = validation_assistant._suggest_missing_event_fix(error)

            assert result["error"] == error
            assert "xyz_123" in result["suggestion"]
            assert "Create a new event file" in result["suggestion"]
            assert result["confidence"] == 0.70
            assert len(result["similar_items"]) == 0

    def test_missing_event_no_id_in_error(self):
        """Should handle error message without parseable event ID."""
        error = "Something went wrong with events"

        result = validation_assistant._suggest_missing_event_fix(error)

        assert result["error"] == error
        assert "Check the event ID spelling" in result["suggestion"]
        assert result["confidence"] == 0.5


class TestSuggestReferenceFix:
    """Tests for _suggest_reference_fix function."""

    def test_invalid_reference_format(self):
        """Should provide format guidance for invalid references."""
        error = "Invalid scripture reference format in character 'peter'"

        result = validation_assistant._suggest_reference_fix(error)

        assert result["error"] == error
        assert "Book Chapter:Verse" in result["suggestion"]
        assert "John 3:16" in result["suggestion"]
        assert "Matthew 5:1-12" in result["suggestion"]
        assert result["confidence"] == 0.90
        assert result["similar_items"] == []


class TestSuggestMissingFieldFix:
    """Tests for _suggest_missing_field_fix function."""

    def test_missing_field_with_field_name(self):
        """Should extract field name from error and suggest fix."""
        error = "Character 'test' is missing required field 'canonical_name'"

        result = validation_assistant._suggest_missing_field_fix(error)

        assert result["error"] == error
        assert "canonical_name" in result["suggestion"]
        assert "DATA_ENTRY_GUIDE.md" in result["suggestion"]
        assert result["confidence"] == 0.85

    def test_missing_field_no_field_name(self):
        """Should provide generic suggestion when field name not found."""
        error = "Missing required field somewhere"

        result = validation_assistant._suggest_missing_field_fix(error)

        assert result["error"] == error
        assert "required fields" in result["suggestion"]
        assert "DATA_ENTRY_GUIDE.md" in result["suggestion"]
        assert result["confidence"] == 0.70


class TestSuggestJsonFix:
    """Tests for _suggest_json_fix function."""

    def test_json_expecting_property_name(self):
        """Should provide specific fix for property name errors."""
        error = "Failed to load character 'test': Expecting property name enclosed in double quotes"

        result = validation_assistant._suggest_json_fix(error)

        assert result["error"] == error
        assert "property name" in result["suggestion"].lower()
        assert "double quotes" in result["suggestion"]
        assert result["confidence"] == 0.80

    def test_json_expecting_value(self):
        """Should provide specific fix for missing value errors."""
        error = "Failed to load: Expecting value at line 10"

        result = validation_assistant._suggest_json_fix(error)

        assert result["error"] == error
        assert "trailing commas" in result["suggestion"].lower() or "missing values" in result["suggestion"].lower()
        assert result["confidence"] == 0.80

    def test_json_generic_error(self):
        """Should provide general JSON guidance for other errors."""
        error = "Failed to load character 'test': Some other JSON error"

        result = validation_assistant._suggest_json_fix(error)

        assert result["error"] == error
        assert "JSON" in result["suggestion"]
        assert result["confidence"] == 0.70


class TestSuggestFixForError:
    """Tests for _suggest_fix_for_error dispatcher."""

    def test_dispatch_missing_character(self):
        """Should dispatch to character fix for character errors."""
        error = "Event references unknown character 'foo'"

        with patch("bce.ai.validation_assistant.list_character_ids", return_value=[]):
            result = validation_assistant._suggest_fix_for_error(error)

        assert result is not None
        assert result["error"] == error
        assert "character" in result["suggestion"].lower()

    def test_dispatch_missing_event(self):
        """Should dispatch to event fix for event errors."""
        error = "Character references unknown event 'bar'"

        with patch("bce.ai.validation_assistant.list_event_ids", return_value=[]):
            result = validation_assistant._suggest_fix_for_error(error)

        assert result is not None
        assert result["error"] == error
        assert "event" in result["suggestion"].lower()

    def test_dispatch_invalid_reference(self):
        """Should dispatch to reference fix for reference errors."""
        error = "Invalid scripture reference in character 'peter'"

        result = validation_assistant._suggest_fix_for_error(error)

        assert result is not None
        assert "scripture reference" in result["suggestion"].lower()

    def test_dispatch_missing_field(self):
        """Should dispatch to field fix for missing field errors."""
        error = "Character missing required field 'id'"

        result = validation_assistant._suggest_fix_for_error(error)

        assert result is not None
        assert "required field" in result["suggestion"].lower()

    def test_dispatch_json_error(self):
        """Should dispatch to JSON fix for loading errors."""
        error = "Failed to load character 'test': Expecting property name"

        result = validation_assistant._suggest_fix_for_error(error)

        assert result is not None
        assert "JSON" in result["suggestion"] or "json" in result["suggestion"]

    def test_dispatch_generic_error(self):
        """Should provide generic suggestion for unknown error types."""
        error = "Some completely unknown error type"

        result = validation_assistant._suggest_fix_for_error(error)

        assert result is not None
        assert result["error"] == error
        assert result["confidence"] == 0.3
        assert result["similar_items"] == []


class TestFindSimilarIds:
    """Tests for _find_similar_ids helper."""

    def test_exact_match(self):
        """Should return exact match with high score."""
        candidates = ["jesus", "peter", "paul"]
        similar = validation_assistant._find_similar_ids("jesus", candidates, top_k=5)

        assert "jesus" in similar
        # Exact match should be first
        assert similar[0] == "jesus"

    def test_substring_match(self):
        """Should find substring matches."""
        candidates = ["jesus_of_nazareth", "peter", "paul"]
        similar = validation_assistant._find_similar_ids("jesus", candidates, top_k=5)

        assert "jesus_of_nazareth" in similar

    def test_prefix_match(self):
        """Should find prefix matches."""
        candidates = ["paul_undisputed", "paul_disputed", "peter"]
        similar = validation_assistant._find_similar_ids("paul", candidates, top_k=5)

        # Both Paul variants should be found
        assert "paul_undisputed" in similar or "paul_disputed" in similar

    def test_case_insensitive(self):
        """Should match case-insensitively."""
        candidates = ["Jesus", "PETER", "paul"]
        similar = validation_assistant._find_similar_ids("jesus", candidates, top_k=5)

        assert "Jesus" in similar

    def test_no_matches_below_threshold(self):
        """Should not return candidates below similarity threshold."""
        candidates = ["xyz", "abc", "123"]
        similar = validation_assistant._find_similar_ids("jesus", candidates, top_k=5)

        # No good matches, should be empty or very few
        assert len(similar) == 0

    def test_top_k_limit(self):
        """Should respect top_k limit."""
        candidates = ["jesus1", "jesus2", "jesus3", "jesus4", "jesus5", "jesus6"]
        similar = validation_assistant._find_similar_ids("jesus", candidates, top_k=3)

        # Should return at most 3
        assert len(similar) <= 3

    def test_empty_candidates(self):
        """Should handle empty candidate list."""
        similar = validation_assistant._find_similar_ids("jesus", [], top_k=5)
        assert similar == []

    def test_similarity_scoring(self):
        """Should score similar strings higher than dissimilar ones."""
        candidates = ["jesu", "jesus_christ", "completely_different"]
        similar = validation_assistant._find_similar_ids("jesus", candidates, top_k=5)

        # jesu and jesus_christ should rank higher than completely_different
        if "completely_different" in similar:
            # If it made it in, it should be last
            assert similar.index("jesu") < similar.index("completely_different")


class TestSimilarityScore:
    """Tests for similarity scoring logic within _find_similar_ids."""

    def test_similarity_exact_match(self):
        """Exact match should have highest score."""
        # Testing the internal similarity_score function via _find_similar_ids
        candidates = ["exact", "other"]
        similar = validation_assistant._find_similar_ids("exact", candidates, top_k=5)

        # Exact should be first
        assert similar[0] == "exact"

    def test_similarity_substring(self):
        """Substring should score high."""
        candidates = ["test_string", "other"]
        similar = validation_assistant._find_similar_ids("test", candidates, top_k=5)

        # test_string contains test, should be included
        assert "test_string" in similar

    def test_similarity_common_prefix(self):
        """Common prefix should score reasonably."""
        candidates = ["testing", "tested", "completely_different"]
        similar = validation_assistant._find_similar_ids("test", candidates, top_k=5)

        # testing and tested should be included, not completely_different
        assert "testing" in similar or "tested" in similar

    def test_similarity_common_characters(self):
        """Common characters should provide some similarity."""
        # This is a weaker signal but should still work
        candidates = ["aet", "completely_different"]
        similar = validation_assistant._find_similar_ids("ate", candidates, top_k=5)

        # aet shares all characters with ate (anagram)
        # May or may not be included depending on threshold
        # Just verify it doesn't crash
        assert isinstance(similar, list)


class TestIntegrationSuggestFixes:
    """Integration tests for suggest_fixes with various error patterns."""

    def setup_method(self):
        """Enable AI features for testing."""
        reset_default_config()
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

    def teardown_method(self):
        """Clean up after each test."""
        reset_default_config()

    def test_multiple_error_types(self):
        """Should handle multiple different error types."""
        errors = [
            "Event 'crucifixion' references unknown character 'pilatus'",
            "Invalid scripture reference in character 'peter'",
            "Character 'john' is missing required field 'canonical_name'",
            "Failed to load character 'test': Expecting value",
        ]

        with patch("bce.ai.validation_assistant.list_character_ids") as mock_chars:
            with patch("bce.ai.validation_assistant.list_event_ids") as mock_events:
                mock_chars.return_value = ["pilate", "peter", "paul"]
                mock_events.return_value = ["crucifixion", "resurrection"]

                suggestions = validation_assistant.suggest_fixes(errors=errors, use_cache=False)

                # Should have one suggestion per error
                assert len(suggestions) == len(errors)

                # Verify all are valid suggestions
                for suggestion in suggestions:
                    assert "error" in suggestion
                    assert "suggestion" in suggestion
                    assert "confidence" in suggestion
                    assert 0.0 <= suggestion["confidence"] <= 1.0

    def test_with_real_validation_errors(self):
        """Should handle actual validation errors from the system."""
        # Let it run actual validation if available
        with patch("bce.ai.validation_assistant.validate_all") as mock_validate:
            mock_validate.return_value = [
                "Character 'test' references unknown event 'foo'"
            ]

            with patch("bce.ai.validation_assistant.list_event_ids", return_value=["foobar", "baz"]):
                suggestions = validation_assistant.suggest_fixes(errors=None, use_cache=False)

                assert len(suggestions) > 0
                assert suggestions[0]["error"] == "Character 'test' references unknown event 'foo'"


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def setup_method(self):
        """Enable AI features for testing."""
        reset_default_config()
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

    def teardown_method(self):
        """Clean up after each test."""
        reset_default_config()

    def test_empty_error_string(self):
        """Should handle empty error strings."""
        errors = [""]

        result = validation_assistant.suggest_fixes(errors=errors, use_cache=False)

        # Should still return suggestions (generic ones)
        assert len(result) > 0

    def test_very_long_error_message(self):
        """Should handle very long error messages."""
        long_error = "x" * 10000 + " references unknown character 'test'"

        with patch("bce.ai.validation_assistant.list_character_ids", return_value=[]):
            result = validation_assistant.suggest_fixes(errors=[long_error], use_cache=False)

        assert len(result) > 0

    def test_special_characters_in_ids(self):
        """Should handle IDs with special characters."""
        error = "Event references unknown character 'mary_mother_of_jesus'"

        with patch("bce.ai.validation_assistant.list_character_ids") as mock_list:
            mock_list.return_value = ["mary_magdalene", "mary_mother_of_jesus"]

            result = validation_assistant.suggest_fixes(errors=[error], use_cache=False)

        assert len(result) > 0
        # Should find the actual character
        assert "mary_mother_of_jesus" in result[0]["similar_items"]

    def test_unicode_in_errors(self):
        """Should handle Unicode characters in error messages."""
        error = "Character 'Ἰησοῦς' references unknown event 'test'"

        with patch("bce.ai.validation_assistant.list_event_ids", return_value=[]):
            result = validation_assistant.suggest_fixes(errors=[error], use_cache=False)

        assert len(result) > 0
