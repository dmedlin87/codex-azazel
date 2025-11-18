"""
Comprehensive tests for AI clustering module.

This test suite focuses on:
- bce/ai/clustering.py: Character and event clustering, tag suggestions
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from bce.config import BceConfig, set_default_config, reset_default_config
from bce.exceptions import ConfigurationError


class TestFindCharacterClusters:
    """Tests for find_character_clusters function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = BceConfig(
            data_root=Path(self.temp_dir),
            enable_ai_features=True,
        )
        set_default_config(self.config)

    def teardown_method(self):
        """Clean up after tests."""
        reset_default_config()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_requires_ai_enabled(self):
        """Test that clustering requires AI features enabled."""
        from bce.ai.clustering import find_character_clusters

        config = BceConfig(enable_ai_features=False)
        set_default_config(config)

        with pytest.raises(ConfigurationError, match="AI features are disabled"):
            find_character_clusters()

    def test_requires_sklearn(self):
        """Test that clustering raises ImportError if sklearn is missing."""
        from bce.ai.clustering import find_character_clusters

        with patch.dict("sys.modules", {"sklearn": None, "sklearn.cluster": None}):
            with pytest.raises(ImportError, match="scikit-learn is required"):
                find_character_clusters(use_cache=False)

    def test_default_parameters(self):
        """Test clustering with default parameters."""
        pytest.importorskip("numpy")
        pytest.importorskip("sklearn")

        from bce.ai.clustering import find_character_clusters

        # Mock the dependencies
        mock_characters = self._create_mock_characters()
        mock_embeddings = self._create_mock_embeddings(len(mock_characters))

        with patch("bce.ai.clustering.list_all_characters", return_value=mock_characters):
            with patch("bce.ai.clustering.EmbeddingCache") as mock_cache_class:
                mock_cache = Mock()
                mock_cache.get_or_compute.side_effect = mock_embeddings
                mock_cache_class.return_value = mock_cache

                clusters = find_character_clusters(use_cache=False)

                assert isinstance(clusters, list)
                assert len(clusters) > 0

                # Verify cluster structure
                for cluster in clusters:
                    assert "cluster_id" in cluster
                    assert "label" in cluster
                    assert "members" in cluster
                    assert "member_names" in cluster
                    assert "representative_traits" in cluster
                    assert "confidence" in cluster
                    assert "size" in cluster
                    assert isinstance(cluster["members"], list)
                    assert isinstance(cluster["confidence"], float)
                    assert 0.0 <= cluster["confidence"] <= 1.0

    def test_custom_num_clusters(self):
        """Test clustering with custom number of clusters."""
        pytest.importorskip("numpy")
        pytest.importorskip("sklearn")

        from bce.ai.clustering import find_character_clusters

        mock_characters = self._create_mock_characters(count=15)
        mock_embeddings = self._create_mock_embeddings(15)

        with patch("bce.ai.clustering.list_all_characters", return_value=mock_characters):
            with patch("bce.ai.clustering.EmbeddingCache") as mock_cache_class:
                mock_cache = Mock()
                mock_cache.get_or_compute.side_effect = mock_embeddings
                mock_cache_class.return_value = mock_cache

                clusters = find_character_clusters(num_clusters=3, use_cache=False)

                # Should have at most 3 clusters (or fewer if data is insufficient)
                assert len(clusters) <= 3

    def test_custom_basis(self):
        """Test clustering with custom basis fields."""
        pytest.importorskip("numpy")
        pytest.importorskip("sklearn")

        from bce.ai.clustering import find_character_clusters

        mock_characters = self._create_mock_characters()
        mock_embeddings = self._create_mock_embeddings(len(mock_characters))

        with patch("bce.ai.clustering.list_all_characters", return_value=mock_characters):
            with patch("bce.ai.clustering.EmbeddingCache") as mock_cache_class:
                mock_cache = Mock()
                mock_cache.get_or_compute.side_effect = mock_embeddings
                mock_cache_class.return_value = mock_cache

                # Test with only traits
                clusters = find_character_clusters(basis=["traits"], use_cache=False)
                assert len(clusters) > 0

                # Reset mock
                mock_cache.get_or_compute.side_effect = mock_embeddings

                # Test with only tags
                clusters = find_character_clusters(basis=["tags"], use_cache=False)
                assert len(clusters) > 0

    def test_cache_usage(self):
        """Test that caching works correctly."""
        pytest.importorskip("numpy")
        pytest.importorskip("sklearn")

        from bce.ai.clustering import find_character_clusters

        mock_characters = self._create_mock_characters()
        mock_embeddings = self._create_mock_embeddings(len(mock_characters))

        # Mock the result cache
        with patch("bce.ai.clustering.AIResultCache") as mock_result_cache_class:
            mock_result_cache = Mock()
            mock_result_cache.get.return_value = None  # First call: cache miss
            mock_result_cache_class.return_value = mock_result_cache

            with patch("bce.ai.clustering.list_all_characters", return_value=mock_characters):
                with patch("bce.ai.clustering.EmbeddingCache") as mock_cache_class:
                    mock_cache = Mock()
                    mock_cache.get_or_compute.side_effect = mock_embeddings
                    mock_cache_class.return_value = mock_cache

                    # First call should compute and cache
                    clusters1 = find_character_clusters(use_cache=True)
                    assert mock_result_cache.set.called

                    # Reset mocks
                    mock_result_cache.reset_mock()
                    mock_result_cache.get.return_value = clusters1  # Cache hit

                    # Second call should use cache
                    clusters2 = find_character_clusters(use_cache=True)
                    assert clusters2 == clusters1
                    assert not mock_result_cache.set.called  # Should not save again

    def test_insufficient_characters_adjusts_clusters(self):
        """Test that num_clusters is adjusted when there are too few characters."""
        pytest.importorskip("numpy")
        pytest.importorskip("sklearn")

        from bce.ai.clustering import find_character_clusters

        # Only 3 characters
        mock_characters = self._create_mock_characters(count=3)
        mock_embeddings = self._create_mock_embeddings(3)

        with patch("bce.ai.clustering.list_all_characters", return_value=mock_characters):
            with patch("bce.ai.clustering.EmbeddingCache") as mock_cache_class:
                mock_cache = Mock()
                mock_cache.get_or_compute.side_effect = mock_embeddings
                mock_cache_class.return_value = mock_cache

                # Request 8 clusters but only have 3 characters
                clusters = find_character_clusters(num_clusters=8, use_cache=False)

                # Should have fewer clusters than requested
                assert len(clusters) < 8

    def test_clusters_sorted_by_size(self):
        """Test that clusters are sorted by size (descending)."""
        pytest.importorskip("numpy")
        pytest.importorskip("sklearn")

        from bce.ai.clustering import find_character_clusters

        mock_characters = self._create_mock_characters(count=15)
        mock_embeddings = self._create_mock_embeddings(15)

        with patch("bce.ai.clustering.list_all_characters", return_value=mock_characters):
            with patch("bce.ai.clustering.EmbeddingCache") as mock_cache_class:
                mock_cache = Mock()
                mock_cache.get_or_compute.side_effect = mock_embeddings
                mock_cache_class.return_value = mock_cache

                clusters = find_character_clusters(use_cache=False)

                # Verify clusters are sorted by size
                sizes = [c["size"] for c in clusters]
                assert sizes == sorted(sizes, reverse=True)

    def test_empty_text_characters_skipped(self):
        """Test that characters with no text content are skipped."""
        pytest.importorskip("numpy")
        pytest.importorskip("sklearn")

        from bce.ai.clustering import find_character_clusters
        from bce.models import Character

        # Create character with no traits, tags, or roles
        empty_char = Character(
            id="empty",
            canonical_name="Empty Character",
            aliases=[],
            roles=[],
            tags=[],
            source_profiles=[],
            relationships=[],
        )

        normal_chars = self._create_mock_characters(count=5)
        all_chars = [empty_char] + normal_chars
        mock_embeddings = self._create_mock_embeddings(5)  # Only for normal chars

        with patch("bce.ai.clustering.list_all_characters", return_value=all_chars):
            with patch("bce.ai.clustering.EmbeddingCache") as mock_cache_class:
                mock_cache = Mock()
                # Empty character should not call get_or_compute
                mock_cache.get_or_compute.side_effect = mock_embeddings
                mock_cache_class.return_value = mock_cache

                clusters = find_character_clusters(use_cache=False)

                # Empty character should not appear in any cluster
                all_members = []
                for cluster in clusters:
                    all_members.extend(cluster["members"])
                assert "empty" not in all_members

    # Helper methods
    def _create_mock_characters(self, count=10):
        """Create mock Character objects for testing."""
        from bce.models import Character, SourceProfile

        characters = []
        for i in range(count):
            char = Character(
                id=f"char_{i}",
                canonical_name=f"Character {i}",
                aliases=[f"Alias {i}"],
                roles=[f"role_{i % 3}"],  # Group characters by role
                tags=[f"tag_{i % 4}"],    # Group characters by tag
                source_profiles=[
                    SourceProfile(
                        source_id="test_source",
                        traits={"trait1": f"value_{i % 2}"},
                        references=["Test 1:1"],
                    )
                ],
                relationships=[],
            )
            characters.append(char)
        return characters

    def _create_mock_embeddings(self, count):
        """Create mock embeddings for testing."""
        import numpy as np

        # Create slightly varied embeddings to simulate real data
        embeddings = []
        for i in range(count):
            # Create embedding with some variation
            base = np.random.rand(384)  # Standard embedding size
            embeddings.append(base)
        return embeddings


class TestFindEventClusters:
    """Tests for find_event_clusters function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = BceConfig(
            data_root=Path(self.temp_dir),
            enable_ai_features=True,
        )
        set_default_config(self.config)

    def teardown_method(self):
        """Clean up after tests."""
        reset_default_config()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_requires_ai_enabled(self):
        """Test that event clustering requires AI features enabled."""
        from bce.ai.clustering import find_event_clusters

        config = BceConfig(enable_ai_features=False)
        set_default_config(config)

        with pytest.raises(ConfigurationError, match="AI features are disabled"):
            find_event_clusters()

    def test_requires_sklearn(self):
        """Test that event clustering raises ImportError if sklearn is missing."""
        from bce.ai.clustering import find_event_clusters

        with patch.dict("sys.modules", {"sklearn": None, "sklearn.cluster": None}):
            with pytest.raises(ImportError, match="scikit-learn is required"):
                find_event_clusters(use_cache=False)

    def test_default_parameters(self):
        """Test event clustering with default parameters."""
        pytest.importorskip("numpy")
        pytest.importorskip("sklearn")

        from bce.ai.clustering import find_event_clusters

        mock_events = self._create_mock_events()
        mock_embeddings = self._create_mock_embeddings(len(mock_events))

        with patch("bce.ai.clustering.list_all_events", return_value=mock_events):
            with patch("bce.ai.clustering.EmbeddingCache") as mock_cache_class:
                mock_cache = Mock()
                mock_cache.get_or_compute.side_effect = mock_embeddings
                mock_cache_class.return_value = mock_cache

                clusters = find_event_clusters(use_cache=False)

                assert isinstance(clusters, list)
                assert len(clusters) > 0

                # Verify cluster structure
                for cluster in clusters:
                    assert "cluster_id" in cluster
                    assert "label" in cluster
                    assert "members" in cluster
                    assert "member_labels" in cluster
                    assert "representative_traits" in cluster
                    assert "confidence" in cluster
                    assert "size" in cluster
                    assert cluster["cluster_id"].startswith("event_cluster_")

    def test_custom_num_clusters(self):
        """Test event clustering with custom number of clusters."""
        pytest.importorskip("numpy")
        pytest.importorskip("sklearn")

        from bce.ai.clustering import find_event_clusters

        mock_events = self._create_mock_events(count=10)
        mock_embeddings = self._create_mock_embeddings(10)

        with patch("bce.ai.clustering.list_all_events", return_value=mock_events):
            with patch("bce.ai.clustering.EmbeddingCache") as mock_cache_class:
                mock_cache = Mock()
                mock_cache.get_or_compute.side_effect = mock_embeddings
                mock_cache_class.return_value = mock_cache

                clusters = find_event_clusters(num_clusters=2, use_cache=False)

                # Should have at most 2 clusters
                assert len(clusters) <= 2

    def test_cache_usage(self):
        """Test that event clustering uses cache correctly."""
        pytest.importorskip("numpy")
        pytest.importorskip("sklearn")

        from bce.ai.clustering import find_event_clusters

        mock_events = self._create_mock_events()
        mock_embeddings = self._create_mock_embeddings(len(mock_events))

        with patch("bce.ai.clustering.AIResultCache") as mock_result_cache_class:
            mock_result_cache = Mock()
            mock_result_cache.get.return_value = None  # Cache miss
            mock_result_cache_class.return_value = mock_result_cache

            with patch("bce.ai.clustering.list_all_events", return_value=mock_events):
                with patch("bce.ai.clustering.EmbeddingCache") as mock_cache_class:
                    mock_cache = Mock()
                    mock_cache.get_or_compute.side_effect = mock_embeddings
                    mock_cache_class.return_value = mock_cache

                    # First call should compute and cache
                    clusters1 = find_event_clusters(use_cache=True)
                    assert mock_result_cache.set.called

                    # Simulate cache hit
                    mock_result_cache.reset_mock()
                    mock_result_cache.get.return_value = clusters1

                    # Second call should use cache
                    clusters2 = find_event_clusters(use_cache=True)
                    assert clusters2 == clusters1

    def test_insufficient_events_adjusts_clusters(self):
        """Test that num_clusters is adjusted when there are too few events."""
        pytest.importorskip("numpy")
        pytest.importorskip("sklearn")

        from bce.ai.clustering import find_event_clusters

        # Only 2 events
        mock_events = self._create_mock_events(count=2)
        mock_embeddings = self._create_mock_embeddings(2)

        with patch("bce.ai.clustering.list_all_events", return_value=mock_events):
            with patch("bce.ai.clustering.EmbeddingCache") as mock_cache_class:
                mock_cache = Mock()
                mock_cache.get_or_compute.side_effect = mock_embeddings
                mock_cache_class.return_value = mock_cache

                # Request 5 clusters but only have 2 events
                clusters = find_event_clusters(num_clusters=5, use_cache=False)

                # Should have fewer clusters than requested
                assert len(clusters) < 5

    def test_clusters_sorted_by_size(self):
        """Test that event clusters are sorted by size."""
        pytest.importorskip("numpy")
        pytest.importorskip("sklearn")

        from bce.ai.clustering import find_event_clusters

        mock_events = self._create_mock_events(count=10)
        mock_embeddings = self._create_mock_embeddings(10)

        with patch("bce.ai.clustering.list_all_events", return_value=mock_events):
            with patch("bce.ai.clustering.EmbeddingCache") as mock_cache_class:
                mock_cache = Mock()
                mock_cache.get_or_compute.side_effect = mock_embeddings
                mock_cache_class.return_value = mock_cache

                clusters = find_event_clusters(use_cache=False)

                # Verify clusters are sorted by size
                sizes = [c["size"] for c in clusters]
                assert sizes == sorted(sizes, reverse=True)

    # Helper methods
    def _create_mock_events(self, count=8):
        """Create mock Event objects for testing."""
        from bce.models import Event, EventAccount

        events = []
        for i in range(count):
            event = Event(
                id=f"event_{i}",
                label=f"Event {i}",
                participants=[f"char_{i}"],
                tags=[f"event_tag_{i % 3}"],
                accounts=[
                    EventAccount(
                        source_id="test_source",
                        reference="Test 1:1-10",
                        summary=f"Event {i} summary describing what happened",
                        notes=f"Additional notes for event {i}",
                    )
                ],
                parallels=[],
            )
            events.append(event)
        return events

    def _create_mock_embeddings(self, count):
        """Create mock embeddings for testing."""
        import numpy as np

        embeddings = []
        for i in range(count):
            base = np.random.rand(384)
            embeddings.append(base)
        return embeddings


class TestSuggestTagsFromClusters:
    """Tests for suggest_tags_from_clusters function."""

    def test_suggest_tags_basic(self):
        """Test basic tag suggestion from clusters."""
        from bce.ai.clustering import suggest_tags_from_clusters

        clusters = [
            {
                "cluster_id": "cluster_0",
                "label": "Apostles",
                "members": ["peter", "john", "james"],
                "representative_traits": ["apostle", "disciple", "follower"],
                "size": 3,
            },
            {
                "cluster_id": "cluster_1",
                "label": "Leaders",
                "members": ["paul", "barnabas"],
                "representative_traits": ["missionary", "teacher"],
                "size": 2,
            },
        ]

        suggestions = suggest_tags_from_clusters(clusters)

        assert "peter" in suggestions
        assert "john" in suggestions
        assert "paul" in suggestions

        # Check that suggested tags come from representative traits
        assert "apostle" in suggestions["peter"]
        assert "missionary" in suggestions["paul"]

    def test_suggest_tags_min_cluster_size(self):
        """Test that small clusters are filtered out."""
        from bce.ai.clustering import suggest_tags_from_clusters

        clusters = [
            {
                "cluster_id": "cluster_0",
                "label": "Large Group",
                "members": ["char1", "char2", "char3"],
                "representative_traits": ["tag1", "tag2"],
                "size": 3,
            },
            {
                "cluster_id": "cluster_1",
                "label": "Small Group",
                "members": ["char4"],
                "representative_traits": ["tag3"],
                "size": 1,
            },
        ]

        # With min_cluster_size=2, small cluster should be ignored
        suggestions = suggest_tags_from_clusters(clusters, min_cluster_size=2)

        assert "char1" in suggestions
        assert "char2" in suggestions
        assert "char3" in suggestions
        assert "char4" not in suggestions  # Too small cluster

    def test_suggest_tags_deduplication(self):
        """Test that suggested tags are deduplicated."""
        from bce.ai.clustering import suggest_tags_from_clusters

        # Character appears in multiple clusters with overlapping tags
        clusters = [
            {
                "cluster_id": "cluster_0",
                "label": "Group A",
                "members": ["char1"],
                "representative_traits": ["tag1", "tag2"],
                "size": 2,
            },
            {
                "cluster_id": "cluster_1",
                "label": "Group B",
                "members": ["char1"],
                "representative_traits": ["tag2", "tag3"],  # tag2 overlaps
                "size": 2,
            },
        ]

        suggestions = suggest_tags_from_clusters(clusters)

        # Should have all tags but no duplicates
        char1_tags = suggestions["char1"]
        assert "tag1" in char1_tags
        assert "tag2" in char1_tags
        assert "tag3" in char1_tags
        assert len(char1_tags) == 3  # No duplicates

    def test_suggest_tags_empty_clusters(self):
        """Test tag suggestion with empty cluster list."""
        from bce.ai.clustering import suggest_tags_from_clusters

        suggestions = suggest_tags_from_clusters([])

        assert suggestions == {}

    def test_suggest_tags_no_representative_traits(self):
        """Test clusters without representative traits."""
        from bce.ai.clustering import suggest_tags_from_clusters

        clusters = [
            {
                "cluster_id": "cluster_0",
                "label": "Group",
                "members": ["char1", "char2"],
                "representative_traits": [],  # No traits
                "size": 2,
            },
        ]

        suggestions = suggest_tags_from_clusters(clusters)

        # Characters should be in suggestions but with empty tag lists
        assert "char1" in suggestions
        assert suggestions["char1"] == []


class TestClusteringHelpers:
    """Tests for internal clustering helper functions."""

    def test_generate_cluster_label_with_traits(self):
        """Test cluster label generation with representative traits."""
        from bce.ai.clustering import _generate_cluster_label

        # With one trait
        label = _generate_cluster_label(
            member_names=["Peter", "John"],
            representative_traits=["apostle"],
            cluster_idx=0,
        )
        assert "Apostle" in label
        assert "Cluster" in label

        # With multiple traits
        label = _generate_cluster_label(
            member_names=["Paul", "Barnabas"],
            representative_traits=["missionary", "teacher"],
            cluster_idx=1,
        )
        assert "Missionary" in label
        assert "Teacher" in label
        assert "Figures" in label

    def test_generate_cluster_label_without_traits(self):
        """Test cluster label generation without representative traits."""
        from bce.ai.clustering import _generate_cluster_label

        label = _generate_cluster_label(
            member_names=["Character 1", "Character 2"],
            representative_traits=[],
            cluster_idx=2,
        )
        assert "Cluster 3" in label  # cluster_idx + 1

    def test_generate_cluster_label_handles_underscores(self):
        """Test that underscores in traits are replaced with spaces."""
        from bce.ai.clustering import _generate_cluster_label

        label = _generate_cluster_label(
            member_names=["Test"],
            representative_traits=["early_church_leader"],
            cluster_idx=0,
        )
        assert "Early Church Leader" in label
        assert "_" not in label

    def test_calculate_cluster_coherence_basic(self):
        """Test basic cluster coherence calculation."""
        np = pytest.importorskip("numpy")
        from bce.ai.clustering import _calculate_cluster_coherence

        # Create simple test data
        embeddings = np.array([
            [1.0, 0.0, 0.0],
            [0.9, 0.1, 0.0],
            [0.8, 0.2, 0.0],
        ])
        member_indices = [0, 1, 2]
        centroid = np.array([0.9, 0.1, 0.0])

        coherence = _calculate_cluster_coherence(embeddings, member_indices, centroid)

        assert isinstance(coherence, float)
        assert 0.0 <= coherence <= 1.0

    def test_calculate_cluster_coherence_empty_cluster(self):
        """Test coherence calculation with empty cluster."""
        np = pytest.importorskip("numpy")
        from bce.ai.clustering import _calculate_cluster_coherence

        embeddings = np.array([[1.0, 0.0], [0.0, 1.0]])
        member_indices = []  # Empty cluster
        centroid = np.array([0.5, 0.5])

        coherence = _calculate_cluster_coherence(embeddings, member_indices, centroid)

        assert coherence == 0.0

    def test_calculate_cluster_coherence_single_member(self):
        """Test coherence calculation with single member cluster."""
        np = pytest.importorskip("numpy")
        from bce.ai.clustering import _calculate_cluster_coherence

        embeddings = np.array([[1.0, 0.0], [0.0, 1.0]])
        member_indices = [0]
        centroid = np.array([1.0, 0.0])

        coherence = _calculate_cluster_coherence(embeddings, member_indices, centroid)

        assert isinstance(coherence, float)
        # Single member should have high similarity to itself
        assert coherence > 0.9


class TestClusteringIntegration:
    """Integration tests with minimal mocking."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = BceConfig(
            data_root=Path(self.temp_dir),
            enable_ai_features=True,
        )
        set_default_config(self.config)

    def teardown_method(self):
        """Clean up after tests."""
        reset_default_config()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_character_clustering_end_to_end(self):
        """Test character clustering with minimal mocking."""
        pytest.importorskip("numpy")
        pytest.importorskip("sklearn")

        from bce.ai.clustering import find_character_clusters
        from bce.models import Character, SourceProfile

        # Create realistic characters
        characters = [
            Character(
                id="peter",
                canonical_name="Peter",
                aliases=["Simon Peter"],
                roles=["apostle", "disciple"],
                tags=["leadership", "ministry"],
                source_profiles=[
                    SourceProfile(
                        source_id="mark",
                        traits={"role": "chief apostle", "personality": "impulsive"},
                        references=["Mark 1:16"],
                    )
                ],
                relationships=[],
            ),
            Character(
                id="john",
                canonical_name="John",
                aliases=["John the Apostle"],
                roles=["apostle", "disciple"],
                tags=["beloved", "ministry"],
                source_profiles=[
                    SourceProfile(
                        source_id="mark",
                        traits={"role": "beloved disciple"},
                        references=["Mark 1:19"],
                    )
                ],
                relationships=[],
            ),
            Character(
                id="paul",
                canonical_name="Paul",
                aliases=["Saul"],
                roles=["apostle", "missionary"],
                tags=["conversion", "letters"],
                source_profiles=[
                    SourceProfile(
                        source_id="acts",
                        traits={"role": "apostle to gentiles"},
                        references=["Acts 9:1"],
                    )
                ],
                relationships=[],
            ),
        ]

        # Mock embeddings (different enough to cluster separately)
        import numpy as np
        mock_embeddings = [
            np.array([1.0, 0.0, 0.0]),  # Peter
            np.array([0.9, 0.1, 0.0]),  # John (similar to Peter)
            np.array([0.0, 0.0, 1.0]),  # Paul (different)
        ]

        with patch("bce.ai.clustering.list_all_characters", return_value=characters):
            with patch("bce.ai.clustering.EmbeddingCache") as mock_cache_class:
                mock_cache = Mock()
                mock_cache.get_or_compute.side_effect = mock_embeddings
                mock_cache_class.return_value = mock_cache

                clusters = find_character_clusters(num_clusters=2, use_cache=False)

                # Should have 2 clusters
                assert len(clusters) == 2

                # All characters should be assigned
                all_members = []
                for cluster in clusters:
                    all_members.extend(cluster["members"])
                assert set(all_members) == {"peter", "john", "paul"}

                # Peter and John should likely be in same cluster (similar embeddings)
                # Paul should likely be in different cluster
                for cluster in clusters:
                    if "peter" in cluster["members"]:
                        # Peter and John should cluster together
                        assert "john" in cluster["members"]
                    if "paul" in cluster["members"]:
                        # Paul should be separate
                        assert "peter" not in cluster["members"]

    def test_event_clustering_end_to_end(self):
        """Test event clustering with minimal mocking."""
        pytest.importorskip("numpy")
        pytest.importorskip("sklearn")

        from bce.ai.clustering import find_event_clusters
        from bce.models import Event, EventAccount

        events = [
            Event(
                id="crucifixion",
                label="Crucifixion",
                participants=["jesus", "pilate"],
                tags=["passion", "death"],
                accounts=[
                    EventAccount(
                        source_id="mark",
                        reference="Mark 15:1-47",
                        summary="Jesus is crucified and dies",
                        notes="Emphasizes suffering",
                    )
                ],
                parallels=[],
            ),
            Event(
                id="resurrection",
                label="Resurrection",
                participants=["jesus"],
                tags=["passion", "resurrection"],
                accounts=[
                    EventAccount(
                        source_id="mark",
                        reference="Mark 16:1-8",
                        summary="Jesus rises from the dead",
                        notes="Women find empty tomb",
                    )
                ],
                parallels=[],
            ),
        ]

        import numpy as np
        mock_embeddings = [
            np.array([1.0, 0.0]),
            np.array([0.9, 0.1]),
        ]

        with patch("bce.ai.clustering.list_all_events", return_value=events):
            with patch("bce.ai.clustering.EmbeddingCache") as mock_cache_class:
                mock_cache = Mock()
                mock_cache.get_or_compute.side_effect = mock_embeddings
                mock_cache_class.return_value = mock_cache

                clusters = find_event_clusters(num_clusters=2, use_cache=False)

                # Should have clusters
                assert len(clusters) > 0

                # All events should be assigned
                all_members = []
                for cluster in clusters:
                    all_members.extend(cluster["members"])
                assert "crucifixion" in all_members
                assert "resurrection" in all_members
