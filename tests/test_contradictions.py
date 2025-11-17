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


class TestEdgeCases:
    """Test edge cases in contradiction detection."""

    def test_compare_character_with_single_source(self):
        """Character with single source should have no conflicts."""
        from bce import storage, queries
        from bce.models import Character, SourceProfile

        # Use temp data root
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            storage.configure_data_root(Path(tmpdir))
            try:
                # Create character with single source
                char = Character(
                    id="single_source",
                    canonical_name="Test",
                    source_profiles=[
                        SourceProfile(
                            source_id="only_source",
                            traits={"trait1": "value1", "trait2": "value2"}
                        )
                    ]
                )
                storage.save_character(char)

                # Should have comparison data
                comparison = contradictions.compare_character_sources("single_source")
                assert len(comparison) == 2

                # But no conflicts (all traits have only one source)
                conflicts = contradictions.find_trait_conflicts("single_source")
                assert len(conflicts) == 0

            finally:
                storage.reset_data_root()

    def test_find_trait_conflicts_all_same_values(self):
        """Traits with same values across sources should not conflict."""
        from bce import storage
        from bce.models import Character, SourceProfile

        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            storage.configure_data_root(Path(tmpdir))
            try:
                # Create character where all sources agree
                char = Character(
                    id="agreement",
                    canonical_name="Test",
                    source_profiles=[
                        SourceProfile(
                            source_id="source1",
                            traits={"role": "teacher", "origin": "Galilee"}
                        ),
                        SourceProfile(
                            source_id="source2",
                            traits={"role": "teacher", "origin": "Galilee"}
                        )
                    ]
                )
                storage.save_character(char)

                # Should have comparison data
                comparison = contradictions.compare_character_sources("agreement")
                assert len(comparison) == 2

                # But no conflicts (all values agree)
                conflicts = contradictions.find_trait_conflicts("agreement")
                assert len(conflicts) == 0

            finally:
                storage.reset_data_root()

    def test_find_trait_conflicts_with_empty_trait_values(self):
        """Empty trait values should be handled gracefully."""
        from bce import storage
        from bce.models import Character, SourceProfile

        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            storage.configure_data_root(Path(tmpdir))
            try:
                # Create character with empty trait values
                char = Character(
                    id="empty_traits",
                    canonical_name="Test",
                    source_profiles=[
                        SourceProfile(
                            source_id="source1",
                            traits={"role": "teacher", "origin": ""}
                        ),
                        SourceProfile(
                            source_id="source2",
                            traits={"role": "prophet", "origin": ""}
                        )
                    ]
                )
                storage.save_character(char)

                # Empty values should be filtered out
                conflicts = contradictions.find_trait_conflicts("empty_traits")

                # Only "role" should conflict (has non-empty differing values)
                assert "role" in conflicts
                # "origin" shouldn't conflict (both empty)
                assert "origin" not in conflicts

            finally:
                storage.reset_data_root()

    def test_event_conflicts_with_identical_accounts(self):
        """Events with identical accounts should show no conflicts."""
        from bce import storage
        from bce.models import Event, EventAccount

        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            storage.configure_data_root(Path(tmpdir))
            try:
                # Create event with identical accounts
                event = Event(
                    id="identical",
                    label="Test",
                    participants=["test"],
                    accounts=[
                        EventAccount(
                            source_id="source1",
                            reference="Ref 1:1",
                            summary="Same summary"
                        ),
                        EventAccount(
                            source_id="source2",
                            reference="Ref 1:1",
                            summary="Same summary"
                        )
                    ]
                )
                storage.save_event(event)

                conflicts = contradictions.find_events_with_conflicting_accounts("identical")
                assert len(conflicts) == 0

            finally:
                storage.reset_data_root()

    def test_event_conflicts_with_missing_fields(self):
        """Event accounts with missing optional fields shouldn't cause errors."""
        from bce import storage
        from bce.models import Event, EventAccount

        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            storage.configure_data_root(Path(tmpdir))
            try:
                # Create event with some accounts missing notes
                event = Event(
                    id="partial",
                    label="Test",
                    participants=["test"],
                    accounts=[
                        EventAccount(
                            source_id="source1",
                            reference="Ref 1:1",
                            summary="Summary 1",
                            notes="Has notes"
                        ),
                        EventAccount(
                            source_id="source2",
                            reference="Ref 2:2",
                            summary="Summary 2"
                            # No notes
                        )
                    ]
                )
                storage.save_event(event)

                # Should not raise an error
                conflicts = contradictions.find_events_with_conflicting_accounts("partial")

                # Should find conflicts in summary and reference
                assert "summary" in conflicts or "reference" in conflicts

            finally:
                storage.reset_data_root()

    def test_character_with_no_traits(self):
        """Character with source profiles but no traits."""
        from bce import storage
        from bce.models import Character, SourceProfile

        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            storage.configure_data_root(Path(tmpdir))
            try:
                char = Character(
                    id="no_traits",
                    canonical_name="Test",
                    source_profiles=[
                        SourceProfile(source_id="source1", traits={}),
                        SourceProfile(source_id="source2", traits={})
                    ]
                )
                storage.save_character(char)

                comparison = contradictions.compare_character_sources("no_traits")
                assert comparison == {}

                conflicts = contradictions.find_trait_conflicts("no_traits")
                assert conflicts == {}

            finally:
                storage.reset_data_root()

    def test_compare_returns_all_traits_across_sources(self):
        """compare_character_sources should include traits from all sources."""
        from bce import storage
        from bce.models import Character, SourceProfile

        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            storage.configure_data_root(Path(tmpdir))
            try:
                char = Character(
                    id="multi_trait",
                    canonical_name="Test",
                    source_profiles=[
                        SourceProfile(
                            source_id="source1",
                            traits={"trait1": "value1", "trait2": "value2"}
                        ),
                        SourceProfile(
                            source_id="source2",
                            traits={"trait2": "value2", "trait3": "value3"}
                        )
                    ]
                )
                storage.save_character(char)

                comparison = contradictions.compare_character_sources("multi_trait")

                # Should have all three traits
                assert "trait1" in comparison
                assert "trait2" in comparison
                assert "trait3" in comparison

                # trait1 only in source1
                assert "source1" in comparison["trait1"]
                assert "source2" not in comparison["trait1"]

                # trait3 only in source2
                assert "source2" in comparison["trait3"]
                assert "source1" not in comparison["trait3"]

                # trait2 in both
                assert "source1" in comparison["trait2"]
                assert "source2" in comparison["trait2"]

            finally:
                storage.reset_data_root()
