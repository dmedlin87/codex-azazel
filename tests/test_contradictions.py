"""Tests for bce.contradictions module.

These tests focus on the public API shape and invariants, not specific content.
"""

import pytest
from bce import contradictions


class TestCharacterContradictions:
    """Test character-level contradiction helpers."""

    def test_compare_character_sources_returns_dict(self):
        """compare_character_sources should return a dict with proper structure."""
        result = contradictions.compare_character_sources("jesus")
        
        # Should return a dict
        assert isinstance(result, dict)
        
        # Should have traits as keys
        assert len(result) > 0
        
        # Each trait should map to source_id -> value
        for trait, source_map in result.items():
            assert isinstance(source_map, dict)
            assert len(source_map) > 0
            
            # Each source mapping should have string keys and values
            for source_id, value in source_map.items():
                assert isinstance(source_id, str)
                assert isinstance(value, str)

    def test_compare_character_sources_has_multiple_sources(self):
        """Jesus data should have entries for multiple sources."""
        result = contradictions.compare_character_sources("jesus")
        
        # Should have at least 2 distinct sources
        all_sources = set()
        for source_map in result.values():
            all_sources.update(source_map.keys())
        
        assert len(all_sources) >= 2
        assert "mark" in all_sources
        assert "matthew" in all_sources

    def test_find_trait_conflicts_returns_dict(self):
        """find_trait_conflicts should return a dict with proper structure."""
        result = contradictions.find_trait_conflicts("jesus")
        
        # Should return a dict
        assert isinstance(result, dict)
        
        # Each conflicting trait should map to source_id -> value
        for trait, source_map in result.items():
            assert isinstance(source_map, dict)
            assert len(source_map) >= 2  # Conflicts need at least 2 sources
            
            # Each source mapping should have string keys and values
            for source_id, value in source_map.items():
                assert isinstance(source_id, str)
                assert isinstance(value, str)

    def test_find_trait_conflicts_identifies_differences(self):
        """Should find at least one trait with differing values."""
        result = contradictions.find_trait_conflicts("jesus")
        
        # Should find some conflicts (Jesus has different birth narratives, etc.)
        assert len(result) > 0
        
        # Verify that conflicts actually have different values
        for trait, source_map in result.items():
            values = set(source_map.values())
            assert len(values) >= 2, f"Trait {trait} should have conflicting values"


class TestEventContradictions:
    """Test event-level contradiction helpers."""

    def test_find_events_with_conflicting_accounts_returns_dict(self):
        """find_events_with_conflicting_accounts should return a dict with proper structure."""
        result = contradictions.find_events_with_conflicting_accounts("crucifixion")
        
        # Should return a dict
        assert isinstance(result, dict)
        
        # Each conflicting field should map to source_id -> value
        for field, source_map in result.items():
            assert isinstance(source_map, dict)
            assert len(source_map) >= 2  # Conflicts need at least 2 sources
            
            # Each source mapping should have string keys and values
            for source_id, value in source_map.items():
                assert isinstance(source_id, str)
                assert isinstance(value, str)

    def test_find_events_with_conflicting_accounts_has_multiple_sources(self):
        """Crucifixion data should have entries for multiple sources."""
        result = contradictions.find_events_with_conflicting_accounts("crucifixion")
        
        # Should have at least 2 distinct sources
        all_sources = set()
        for source_map in result.values():
            all_sources.update(source_map.keys())
        
        assert len(all_sources) >= 2
        assert "mark" in all_sources
        assert "john" in all_sources

    def test_find_events_with_conflicting_accounts_identifies_differences(self):
        """Should find at least one field with differing values."""
        result = contradictions.find_events_with_conflicting_accounts("crucifixion")
        
        # Should find some conflicts (crucifixion accounts differ in details)
        assert len(result) > 0
        
        # Verify that conflicts actually have different values
        for field, source_map in result.items():
            values = set(source_map.values())
            assert len(values) >= 2, f"Field {field} should have conflicting values"


class TestAPIInvariants:
    """Test general API invariants and error handling."""

    def test_nonexistent_character_raises_error(self):
        """Should handle nonexistent character IDs gracefully."""
        with pytest.raises(Exception):  # Should raise some kind of error
            contradictions.compare_character_sources("nonexistent")

    def test_nonexistent_event_raises_error(self):
        """Should handle nonexistent event IDs gracefully."""
        with pytest.raises(Exception):  # Should raise some kind of error
            contradictions.find_events_with_conflicting_accounts("nonexistent")

    def test_conflicts_is_subset_of_comparison(self):
        """Trait conflicts should be a subset of full comparison."""
        full_comparison = contradictions.compare_character_sources("jesus")
        conflicts = contradictions.find_trait_conflicts("jesus")
        
        # All conflicted traits should exist in full comparison
        assert set(conflicts.keys()).issubset(set(full_comparison.keys()))
        
        # For each conflicted trait, the source mappings should match
        for trait in conflicts:
            assert conflicts[trait] == full_comparison[trait]
