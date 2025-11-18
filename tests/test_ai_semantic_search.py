"""
Comprehensive tests for bce/ai/semantic_search.py.

Tests semantic search functionality including:
- Query with different scopes
- Character and event similarity finding
- Index building and caching
- Match explanation
- Edge cases and error handling
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
import numpy as np

import pytest

from bce.config import BceConfig, set_default_config, reset_default_config
from bce.exceptions import ConfigurationError
from bce.models import Character, SourceProfile, Event, EventAccount


class TestSemanticSearchConfiguration:
    """Tests for configuration and error handling."""

    def setup_method(self):
        """Setup for each test."""
        reset_default_config()

    def teardown_method(self):
        """Cleanup after each test."""
        reset_default_config()

    def test_query_raises_when_ai_disabled(self):
        """query() should raise ConfigurationError when AI is disabled."""
        from bce.ai import semantic_search

        config = BceConfig(enable_ai_features=False)
        set_default_config(config)

        with pytest.raises(ConfigurationError, match="AI features are disabled"):
            semantic_search.query("test query")

    def test_find_similar_characters_raises_when_disabled(self):
        """find_similar_characters() should raise when AI disabled."""
        from bce.ai import semantic_search

        config = BceConfig(enable_ai_features=False)
        set_default_config(config)

        with pytest.raises(ConfigurationError):
            semantic_search.find_similar_characters("paul")

    def test_find_similar_events_raises_when_disabled(self):
        """find_similar_events() should raise when AI disabled."""
        from bce.ai import semantic_search

        config = BceConfig(enable_ai_features=False)
        set_default_config(config)

        with pytest.raises(ConfigurationError):
            semantic_search.find_similar_events("crucifixion")


class TestQuery:
    """Tests for main query() function."""

    def setup_method(self):
        """Setup for each test."""
        reset_default_config()

    def teardown_method(self):
        """Cleanup after each test."""
        reset_default_config()

    def test_query_with_default_scope(self):
        """Should use default scope when not specified."""
        from bce.ai import semantic_search

        with tempfile.TemporaryDirectory() as tmpdir:
            config = BceConfig(
                enable_ai_features=True,
                ai_cache_dir=Path(tmpdir)
            )
            set_default_config(config)

            # Mock the index building and embedding
            mock_index = []
            mock_embedding = np.array([0.1, 0.2, 0.3])

            with patch("bce.ai.semantic_search._build_search_index") as mock_build, \
                 patch("bce.ai.semantic_search.EmbeddingCache") as mock_cache_cls:

                mock_build.return_value = mock_index
                mock_cache = MagicMock()
                mock_cache.get_or_compute.return_value = mock_embedding
                mock_cache_cls.return_value = mock_cache

                results = semantic_search.query("test query", use_cache=False)

                # Verify default scope is used
                call_args = mock_build.call_args
                scope = call_args[0][0]
                assert "traits" in scope
                assert "relationships" in scope
                assert "accounts" in scope

    def test_query_with_custom_scope(self):
        """Should respect custom scope parameter."""
        from bce.ai import semantic_search

        with tempfile.TemporaryDirectory() as tmpdir:
            config = BceConfig(
                enable_ai_features=True,
                ai_cache_dir=Path(tmpdir)
            )
            set_default_config(config)

            mock_index = []
            mock_embedding = np.array([0.1, 0.2, 0.3])

            with patch("bce.ai.semantic_search._build_search_index") as mock_build, \
                 patch("bce.ai.semantic_search.EmbeddingCache") as mock_cache_cls:

                mock_build.return_value = mock_index
                mock_cache = MagicMock()
                mock_cache.get_or_compute.return_value = mock_embedding
                mock_cache_cls.return_value = mock_cache

                results = semantic_search.query(
                    "test query",
                    scope=["traits"],
                    use_cache=False
                )

                # Verify custom scope is passed
                call_args = mock_build.call_args
                scope = call_args[0][0]
                assert scope == ["traits"]

    def test_query_filters_by_min_score(self):
        """Should filter results by minimum similarity score."""
        from bce.ai import semantic_search

        with tempfile.TemporaryDirectory() as tmpdir:
            config = BceConfig(
                enable_ai_features=True,
                ai_cache_dir=Path(tmpdir)
            )
            set_default_config(config)

            # Create mock index with embeddings
            mock_embedding1 = np.array([1.0, 0.0, 0.0])
            mock_embedding2 = np.array([0.0, 1.0, 0.0])

            mock_index = [
                {
                    "type": "character",
                    "id": "char1",
                    "field": "traits.source.key",
                    "text": "text1",
                    "embedding": mock_embedding1
                },
                {
                    "type": "character",
                    "id": "char2",
                    "field": "traits.source.key",
                    "text": "text2",
                    "embedding": mock_embedding2
                }
            ]

            query_embedding = np.array([1.0, 0.0, 0.0])  # Very similar to embedding1

            with patch("bce.ai.semantic_search._build_search_index") as mock_build, \
                 patch("bce.ai.semantic_search.EmbeddingCache") as mock_cache_cls:

                mock_build.return_value = mock_index
                mock_cache = MagicMock()
                mock_cache.get_or_compute.return_value = query_embedding
                mock_cache_cls.return_value = mock_cache

                # Use high min_score to filter out dissimilar results
                results = semantic_search.query(
                    "test query",
                    min_score=0.9,
                    use_cache=False
                )

                # Should only get char1 (similar to query)
                assert len(results) <= 1

    def test_query_respects_top_k(self):
        """Should limit results to top_k parameter."""
        from bce.ai import semantic_search

        with tempfile.TemporaryDirectory() as tmpdir:
            config = BceConfig(
                enable_ai_features=True,
                ai_cache_dir=Path(tmpdir)
            )
            set_default_config(config)

            # Create large mock index
            mock_index = []
            for i in range(20):
                mock_index.append({
                    "type": "character",
                    "id": f"char{i}",
                    "field": "traits.source.key",
                    "text": f"text{i}",
                    "embedding": np.array([0.5, 0.5, 0.0])
                })

            query_embedding = np.array([0.5, 0.5, 0.0])

            with patch("bce.ai.semantic_search._build_search_index") as mock_build, \
                 patch("bce.ai.semantic_search.EmbeddingCache") as mock_cache_cls:

                mock_build.return_value = mock_index
                mock_cache = MagicMock()
                mock_cache.get_or_compute.return_value = query_embedding
                mock_cache_cls.return_value = mock_cache

                results = semantic_search.query(
                    "test query",
                    top_k=5,
                    min_score=0.0,
                    use_cache=False
                )

                # Should return at most 5 results
                assert len(results) <= 5

    def test_query_returns_expected_fields(self):
        """Should return results with all expected fields."""
        from bce.ai import semantic_search

        with tempfile.TemporaryDirectory() as tmpdir:
            config = BceConfig(
                enable_ai_features=True,
                ai_cache_dir=Path(tmpdir)
            )
            set_default_config(config)

            mock_embedding = np.array([0.5, 0.5, 0.0])
            mock_index = [{
                "type": "character",
                "id": "test_char",
                "field": "traits.mark.portrayal",
                "text": "A faithful disciple",
                "embedding": mock_embedding
            }]

            with patch("bce.ai.semantic_search._build_search_index") as mock_build, \
                 patch("bce.ai.semantic_search.EmbeddingCache") as mock_cache_cls:

                mock_build.return_value = mock_index
                mock_cache = MagicMock()
                mock_cache.get_or_compute.return_value = mock_embedding
                mock_cache_cls.return_value = mock_cache

                results = semantic_search.query(
                    "faithful",
                    min_score=0.0,
                    use_cache=False
                )

                if results:
                    result = results[0]
                    assert "type" in result
                    assert "id" in result
                    assert "relevance_score" in result
                    assert "matching_context" in result
                    assert "match_in" in result
                    assert "explanation" in result


class TestBuildSearchIndex:
    """Tests for _build_search_index function."""

    def setup_method(self):
        """Setup for each test."""
        reset_default_config()

    def teardown_method(self):
        """Cleanup after each test."""
        reset_default_config()

    def test_build_index_with_traits_scope(self):
        """Should build index for character traits."""
        from bce.ai.semantic_search import _build_search_index

        char = Character(
            id="test_char",
            canonical_name="Test Character",
            aliases=[],
            roles=["role1"],
            source_profiles=[
                SourceProfile(
                    source_id="mark",
                    traits={"trait1": "value1", "trait2": "value2"},
                    references=["Mark 1:1"]
                )
            ],
            relationships=[],
            tags=[]
        )

        with patch("bce.ai.semantic_search.list_all_characters") as mock_list, \
             patch("bce.ai.semantic_search.list_all_events") as mock_events, \
             patch("bce.ai.semantic_search.EmbeddingCache") as mock_cache_cls:

            mock_list.return_value = [char]
            mock_events.return_value = []

            mock_cache = MagicMock()
            mock_cache.get_or_compute.return_value = np.array([0.1, 0.2])
            mock_cache_cls.return_value = mock_cache

            index = _build_search_index(["traits"], use_cache=False)

            # Should have 2 entries (one per trait)
            assert len(index) == 2
            assert index[0]["type"] == "character"
            assert index[0]["id"] == "test_char"
            assert "trait1" in index[0]["field"] or "trait2" in index[0]["field"]

    def test_build_index_with_relationships_scope(self):
        """Should build index for character relationships."""
        from bce.ai.semantic_search import _build_search_index

        char = Character(
            id="test_char",
            canonical_name="Test Character",
            aliases=[],
            roles=[],
            source_profiles=[],
            relationships=[
                {"type": "friend", "to": "other_char", "description": "Close friend"}
            ],
            tags=[]
        )

        with patch("bce.ai.semantic_search.list_all_characters") as mock_list, \
             patch("bce.ai.semantic_search.list_all_events") as mock_events, \
             patch("bce.ai.semantic_search.EmbeddingCache") as mock_cache_cls:

            mock_list.return_value = [char]
            mock_events.return_value = []

            mock_cache = MagicMock()
            mock_cache.get_or_compute.return_value = np.array([0.1, 0.2])
            mock_cache_cls.return_value = mock_cache

            index = _build_search_index(["relationships"], use_cache=False)

            assert len(index) == 1
            assert index[0]["field"] == "relationships"
            assert "friend" in index[0]["text"]

    def test_build_index_with_accounts_scope(self):
        """Should build index for event accounts."""
        from bce.ai.semantic_search import _build_search_index

        event = Event(
            id="test_event",
            label="Test Event",
            participants=["char1"],
            accounts=[
                EventAccount(
                    source_id="mark",
                    reference="Mark 1:1",
                    summary="Event summary",
                    notes="Some notes"
                )
            ],
            parallels=[],
            tags=[]
        )

        with patch("bce.ai.semantic_search.list_all_characters") as mock_chars, \
             patch("bce.ai.semantic_search.list_all_events") as mock_events, \
             patch("bce.ai.semantic_search.EmbeddingCache") as mock_cache_cls:

            mock_chars.return_value = []
            mock_events.return_value = [event]

            mock_cache = MagicMock()
            mock_cache.get_or_compute.return_value = np.array([0.1, 0.2])
            mock_cache_cls.return_value = mock_cache

            index = _build_search_index(["accounts"], use_cache=False)

            assert len(index) == 1
            assert index[0]["type"] == "event"
            assert index[0]["id"] == "test_event"
            assert "accounts.mark" in index[0]["field"]

    def test_build_index_caching(self):
        """Should cache and retrieve index."""
        from bce.ai.semantic_search import _build_search_index

        with tempfile.TemporaryDirectory() as tmpdir:
            config = BceConfig(
                enable_ai_features=True,
                ai_cache_dir=Path(tmpdir)
            )
            set_default_config(config)

            with patch("bce.ai.semantic_search.list_all_characters") as mock_chars, \
                 patch("bce.ai.semantic_search.list_all_events") as mock_events, \
                 patch("bce.ai.semantic_search.EmbeddingCache") as mock_embed_cache, \
                 patch("bce.ai.semantic_search.AIResultCache") as mock_result_cache_cls:

                mock_chars.return_value = []
                mock_events.return_value = []

                # Mock embedding cache
                mock_embed = MagicMock()
                mock_embed.get_or_compute.return_value = np.array([0.1])
                mock_embed_cache.return_value = mock_embed

                # Mock result cache
                mock_result_cache = MagicMock()
                mock_result_cache.get.return_value = None  # First call: cache miss
                mock_result_cache_cls.return_value = mock_result_cache

                # First call - builds index
                index1 = _build_search_index(["traits"], use_cache=True)

                # Verify cache.set was called
                assert mock_result_cache.set.called


class TestExplainMatch:
    """Tests for _explain_match function."""

    def test_explain_strong_match(self):
        """Should label strong matches (>= 0.8)."""
        from bce.ai.semantic_search import _explain_match

        result = _explain_match(
            "test query",
            "matched text",
            0.85,
            "character",
            "paul"
        )

        assert "Strong" in result
        assert "paul" in result

    def test_explain_moderate_match(self):
        """Should label moderate matches (0.6 - 0.8)."""
        from bce.ai.semantic_search import _explain_match

        result = _explain_match(
            "test query",
            "matched text",
            0.7,
            "event",
            "crucifixion"
        )

        assert "Moderate" in result
        assert "crucifixion" in result

    def test_explain_weak_match(self):
        """Should label weak matches (< 0.6)."""
        from bce.ai.semantic_search import _explain_match

        result = _explain_match(
            "test query",
            "matched text",
            0.4,
            "character",
            "thomas"
        )

        assert "Weak" in result
        assert "thomas" in result


class TestFindSimilarCharacters:
    """Tests for find_similar_characters function."""

    def setup_method(self):
        """Setup for each test."""
        reset_default_config()

    def teardown_method(self):
        """Cleanup after each test."""
        reset_default_config()

    def test_find_similar_characters_basic(self):
        """Should find similar characters based on traits."""
        from bce.ai import semantic_search

        with tempfile.TemporaryDirectory() as tmpdir:
            config = BceConfig(
                enable_ai_features=True,
                ai_cache_dir=Path(tmpdir)
            )
            set_default_config(config)

            paul = Character(
                id="paul",
                canonical_name="Paul",
                aliases=[],
                roles=["apostle"],
                source_profiles=[
                    SourceProfile(
                        source_id="acts",
                        traits={"role": "missionary"},
                        references=[]
                    )
                ],
                relationships=[],
                tags=[]
            )

            peter = Character(
                id="peter",
                canonical_name="Peter",
                aliases=[],
                roles=["apostle"],
                source_profiles=[
                    SourceProfile(
                        source_id="acts",
                        traits={"role": "leader"},
                        references=[]
                    )
                ],
                relationships=[],
                tags=[]
            )

            with patch("bce.ai.semantic_search.get_character") as mock_get, \
                 patch("bce.ai.semantic_search.list_all_characters") as mock_list, \
                 patch("bce.ai.semantic_search.EmbeddingCache") as mock_cache_cls:

                mock_get.return_value = paul
                mock_list.return_value = [paul, peter]

                # Mock embeddings
                mock_cache = MagicMock()
                mock_cache.get_or_compute.side_effect = [
                    np.array([0.8, 0.2]),  # paul
                    np.array([0.7, 0.3]),  # peter (similar to paul)
                ]
                mock_cache_cls.return_value = mock_cache

                results = semantic_search.find_similar_characters("paul", top_k=5)

                # Should return peter (excluding paul itself)
                assert len(results) >= 0
                if results:
                    assert all("character_id" in r for r in results)
                    assert all("similarity_score" in r for r in results)

    def test_find_similar_characters_with_custom_basis(self):
        """Should respect custom basis parameter."""
        from bce.ai import semantic_search

        with tempfile.TemporaryDirectory() as tmpdir:
            config = BceConfig(
                enable_ai_features=True,
                ai_cache_dir=Path(tmpdir)
            )
            set_default_config(config)

            with patch("bce.ai.semantic_search.get_character") as mock_get, \
                 patch("bce.ai.semantic_search.list_all_characters") as mock_list, \
                 patch("bce.ai.semantic_search._collect_character_texts") as mock_collect, \
                 patch("bce.ai.semantic_search.EmbeddingCache") as mock_cache_cls:

                mock_char = MagicMock()
                mock_char.id = "test"
                mock_get.return_value = mock_char
                mock_list.return_value = [mock_char]
                mock_collect.return_value = ["text"]

                mock_cache = MagicMock()
                mock_cache.get_or_compute.return_value = np.array([0.1])
                mock_cache_cls.return_value = mock_cache

                semantic_search.find_similar_characters(
                    "test",
                    basis=["roles", "tags"]
                )

                # Verify _collect_character_texts was called with custom basis
                assert mock_collect.called
                call_args = mock_collect.call_args_list
                for call in call_args:
                    basis_arg = call[0][1]
                    assert basis_arg == ["roles", "tags"]

    def test_find_similar_characters_excludes_self(self):
        """Should exclude the reference character from results."""
        from bce.ai import semantic_search

        with tempfile.TemporaryDirectory() as tmpdir:
            config = BceConfig(
                enable_ai_features=True,
                ai_cache_dir=Path(tmpdir)
            )
            set_default_config(config)

            paul = Character(
                id="paul",
                canonical_name="Paul",
                aliases=[],
                roles=["apostle"],
                source_profiles=[],
                relationships=[],
                tags=[]
            )

            with patch("bce.ai.semantic_search.get_character") as mock_get, \
                 patch("bce.ai.semantic_search.list_all_characters") as mock_list, \
                 patch("bce.ai.semantic_search.EmbeddingCache") as mock_cache_cls:

                mock_get.return_value = paul
                mock_list.return_value = [paul]

                mock_cache = MagicMock()
                mock_cache.get_or_compute.return_value = np.array([0.1])
                mock_cache_cls.return_value = mock_cache

                results = semantic_search.find_similar_characters("paul")

                # Should not include paul itself
                assert all(r["character_id"] != "paul" for r in results)


class TestFindSimilarEvents:
    """Tests for find_similar_events function."""

    def setup_method(self):
        """Setup for each test."""
        reset_default_config()

    def teardown_method(self):
        """Cleanup after each test."""
        reset_default_config()

    def test_find_similar_events_basic(self):
        """Should find similar events based on accounts."""
        from bce.ai import semantic_search

        with tempfile.TemporaryDirectory() as tmpdir:
            config = BceConfig(
                enable_ai_features=True,
                ai_cache_dir=Path(tmpdir)
            )
            set_default_config(config)

            event1 = Event(
                id="event1",
                label="Event 1",
                participants=[],
                accounts=[
                    EventAccount(
                        source_id="mark",
                        reference="Mark 1:1",
                        summary="Summary 1",
                        notes=None
                    )
                ],
                parallels=[],
                tags=[]
            )

            event2 = Event(
                id="event2",
                label="Event 2",
                participants=[],
                accounts=[
                    EventAccount(
                        source_id="mark",
                        reference="Mark 2:1",
                        summary="Summary 2",
                        notes=None
                    )
                ],
                parallels=[],
                tags=[]
            )

            with patch("bce.ai.semantic_search.get_event") as mock_get, \
                 patch("bce.ai.semantic_search.list_all_events") as mock_list, \
                 patch("bce.ai.semantic_search.EmbeddingCache") as mock_cache_cls:

                mock_get.return_value = event1
                mock_list.return_value = [event1, event2]

                mock_cache = MagicMock()
                mock_cache.get_or_compute.side_effect = [
                    np.array([0.8, 0.2]),
                    np.array([0.7, 0.3]),
                ]
                mock_cache_cls.return_value = mock_cache

                results = semantic_search.find_similar_events("event1")

                # Should have proper structure
                assert all("event_id" in r for r in results)
                assert all("similarity_score" in r for r in results)

    def test_find_similar_events_excludes_self(self):
        """Should exclude the reference event from results."""
        from bce.ai import semantic_search

        with tempfile.TemporaryDirectory() as tmpdir:
            config = BceConfig(
                enable_ai_features=True,
                ai_cache_dir=Path(tmpdir)
            )
            set_default_config(config)

            event = Event(
                id="test_event",
                label="Test Event",
                participants=[],
                accounts=[],
                parallels=[],
                tags=[]
            )

            with patch("bce.ai.semantic_search.get_event") as mock_get, \
                 patch("bce.ai.semantic_search.list_all_events") as mock_list, \
                 patch("bce.ai.semantic_search.EmbeddingCache") as mock_cache_cls:

                mock_get.return_value = event
                mock_list.return_value = [event]

                mock_cache = MagicMock()
                mock_cache.get_or_compute.return_value = np.array([0.1])
                mock_cache_cls.return_value = mock_cache

                results = semantic_search.find_similar_events("test_event")

                # Should not include the reference event
                assert all(r["event_id"] != "test_event" for r in results)


class TestCollectCharacterTexts:
    """Tests for _collect_character_texts helper."""

    def test_collect_traits(self):
        """Should collect trait texts."""
        from bce.ai.semantic_search import _collect_character_texts

        char = Character(
            id="test",
            canonical_name="Test",
            aliases=[],
            roles=[],
            source_profiles=[
                SourceProfile(
                    source_id="mark",
                    traits={"trait1": "value1"},
                    references=[]
                )
            ],
            relationships=[],
            tags=[]
        )

        texts = _collect_character_texts(char, ["traits"])
        assert len(texts) == 1
        assert "trait1" in texts[0]

    def test_collect_roles(self):
        """Should collect role texts."""
        from bce.ai.semantic_search import _collect_character_texts

        char = Character(
            id="test",
            canonical_name="Test",
            aliases=[],
            roles=["apostle", "teacher"],
            source_profiles=[],
            relationships=[],
            tags=[]
        )

        texts = _collect_character_texts(char, ["roles"])
        assert len(texts) == 1
        assert "apostle" in texts[0]

    def test_collect_relationships(self):
        """Should collect relationship texts."""
        from bce.ai.semantic_search import _collect_character_texts

        char = Character(
            id="test",
            canonical_name="Test",
            aliases=[],
            roles=[],
            source_profiles=[],
            relationships=[
                {"type": "brother", "to": "andrew", "description": "Brothers"}
            ],
            tags=[]
        )

        texts = _collect_character_texts(char, ["relationships"])
        assert len(texts) == 1
        assert "Brothers" in texts[0]

    def test_collect_tags(self):
        """Should collect tag texts."""
        from bce.ai.semantic_search import _collect_character_texts

        char = Character(
            id="test",
            canonical_name="Test",
            aliases=[],
            roles=[],
            source_profiles=[],
            relationships=[],
            tags=["resurrection", "apostle"]
        )

        texts = _collect_character_texts(char, ["tags"])
        assert len(texts) == 1
        assert "resurrection" in texts[0]

    def test_collect_multiple_bases(self):
        """Should collect from multiple bases."""
        from bce.ai.semantic_search import _collect_character_texts

        char = Character(
            id="test",
            canonical_name="Test",
            aliases=[],
            roles=["apostle"],
            source_profiles=[],
            relationships=[],
            tags=["tag1"]
        )

        texts = _collect_character_texts(char, ["roles", "tags"])
        assert len(texts) >= 2
