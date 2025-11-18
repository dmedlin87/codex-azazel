"""
Comprehensive tests for AI cache and embeddings modules.

This test suite focuses on:
- bce/ai/cache.py: AIResultCache, CachedResult, cache invalidation
- bce/ai/embeddings.py: EmbeddingCache, embedding functions, similarity
"""

from __future__ import annotations

import json
import os
import pickle
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from bce.config import BceConfig, set_default_config, reset_default_config
from bce.exceptions import ConfigurationError


# ============================================================================
# Tests for bce/ai/cache.py
# ============================================================================


class TestCachedResult:
    """Tests for CachedResult dataclass."""

    def test_cached_result_creation(self):
        """Test creating a CachedResult instance."""
        from bce.ai.cache import CachedResult

        result = CachedResult(
            result={"data": "test"},
            timestamp=1234567890.0,
            model_name="test-model",
            metadata={"key": "value"},
        )

        assert result.result == {"data": "test"}
        assert result.timestamp == 1234567890.0
        assert result.model_name == "test-model"
        assert result.metadata == {"key": "value"}

    def test_cached_result_defaults(self):
        """Test default values for CachedResult."""
        from bce.ai.cache import CachedResult

        result = CachedResult(result="test")

        assert result.result == "test"
        assert isinstance(result.timestamp, float)
        assert result.model_name == ""
        assert result.metadata == {}

    def test_is_expired_fresh(self):
        """Test is_expired for fresh result."""
        from bce.ai.cache import CachedResult

        result = CachedResult(result="test", timestamp=time.time())
        assert not result.is_expired(max_age_seconds=3600)

    def test_is_expired_old(self):
        """Test is_expired for expired result."""
        from bce.ai.cache import CachedResult

        old_timestamp = time.time() - 7200  # 2 hours ago
        result = CachedResult(result="test", timestamp=old_timestamp)
        assert result.is_expired(max_age_seconds=3600)  # 1 hour max age

    def test_is_expired_exact_boundary(self):
        """Test is_expired at exact boundary."""
        from bce.ai.cache import CachedResult

        timestamp = time.time() - 3600
        result = CachedResult(result="test", timestamp=timestamp)
        # At exact boundary, should be expired (> not >=)
        assert result.is_expired(max_age_seconds=3600)

    def test_to_dict(self):
        """Test conversion to dictionary."""
        from bce.ai.cache import CachedResult

        result = CachedResult(
            result={"nested": "data"},
            timestamp=1234567890.0,
            model_name="model-v1",
            metadata={"version": 1},
        )

        data = result.to_dict()

        assert data == {
            "result": {"nested": "data"},
            "timestamp": 1234567890.0,
            "model_name": "model-v1",
            "metadata": {"version": 1},
        }

    def test_from_dict(self):
        """Test creation from dictionary."""
        from bce.ai.cache import CachedResult

        data = {
            "result": ["list", "data"],
            "timestamp": 9876543210.0,
            "model_name": "test-model",
            "metadata": {"info": "value"},
        }

        result = CachedResult.from_dict(data)

        assert result.result == ["list", "data"]
        assert result.timestamp == 9876543210.0
        assert result.model_name == "test-model"
        assert result.metadata == {"info": "value"}

    def test_from_dict_missing_optional_fields(self):
        """Test from_dict with missing optional fields."""
        from bce.ai.cache import CachedResult

        data = {
            "result": "test",
            "timestamp": 1234567890.0,
        }

        result = CachedResult.from_dict(data)

        assert result.result == "test"
        assert result.timestamp == 1234567890.0
        assert result.model_name == ""
        assert result.metadata == {}

    def test_roundtrip_serialization(self):
        """Test to_dict/from_dict roundtrip."""
        from bce.ai.cache import CachedResult

        original = CachedResult(
            result={"complex": ["nested", "data"]},
            timestamp=1234567890.5,
            model_name="model-name",
            metadata={"key1": "val1", "key2": 42},
        )

        data = original.to_dict()
        restored = CachedResult.from_dict(data)

        assert restored.result == original.result
        assert restored.timestamp == original.timestamp
        assert restored.model_name == original.model_name
        assert restored.metadata == original.metadata


class TestAIResultCache:
    """Tests for AIResultCache class."""

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

    def test_cache_initialization(self):
        """Test cache initialization creates necessary directories."""
        from bce.ai.cache import AIResultCache

        cache = AIResultCache("test_cache")

        assert cache.cache_name == "test_cache"
        assert cache.max_age_seconds == 86400  # Default 24 hours
        assert cache.cache_dir.exists()
        assert cache.cache_file.name == "test_cache.json"

    def test_cache_custom_max_age(self):
        """Test cache with custom max age."""
        from bce.ai.cache import AIResultCache

        cache = AIResultCache("test_cache", max_age_seconds=3600)
        assert cache.max_age_seconds == 3600

    def test_set_and_get(self):
        """Test setting and getting cached results."""
        from bce.ai.cache import AIResultCache

        cache = AIResultCache("test_cache")
        cache.set("key1", {"data": "value"}, model_name="test-model")

        result = cache.get("key1")
        assert result == {"data": "value"}

    def test_get_nonexistent_key(self):
        """Test getting non-existent key returns None."""
        from bce.ai.cache import AIResultCache

        cache = AIResultCache("test_cache")
        result = cache.get("nonexistent")
        assert result is None

    def test_get_expired_entry(self):
        """Test getting expired entry returns None and removes it."""
        from bce.ai.cache import AIResultCache, CachedResult

        cache = AIResultCache("test_cache", max_age_seconds=1)

        # Manually insert an old entry
        old_timestamp = time.time() - 10
        cache._cache["old_key"] = CachedResult(
            result="old_data", timestamp=old_timestamp
        )
        cache._save_cache()

        # Get should return None and remove the entry
        result = cache.get("old_key")
        assert result is None
        assert "old_key" not in cache._cache

    def test_set_with_metadata(self):
        """Test setting result with metadata."""
        from bce.ai.cache import AIResultCache

        cache = AIResultCache("test_cache")
        cache.set(
            "key1",
            "result",
            model_name="model-v1",
            metadata={"version": 1, "source": "test"},
        )

        # Verify metadata is stored
        cached_result = cache._cache["key1"]
        assert cached_result.model_name == "model-v1"
        assert cached_result.metadata == {"version": 1, "source": "test"}

    def test_invalidate(self):
        """Test invalidating specific key."""
        from bce.ai.cache import AIResultCache

        cache = AIResultCache("test_cache")
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        cache.invalidate("key1")

        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"

    def test_invalidate_nonexistent(self):
        """Test invalidating non-existent key doesn't error."""
        from bce.ai.cache import AIResultCache

        cache = AIResultCache("test_cache")
        cache.invalidate("nonexistent")  # Should not raise

    def test_clear(self):
        """Test clearing all cached results."""
        from bce.ai.cache import AIResultCache

        cache = AIResultCache("test_cache")
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        cache.clear()

        assert cache.size() == 0
        assert not cache.cache_file.exists()

    def test_size(self):
        """Test getting cache size."""
        from bce.ai.cache import AIResultCache

        cache = AIResultCache("test_cache")
        assert cache.size() == 0

        cache.set("key1", "value1")
        assert cache.size() == 1

        cache.set("key2", "value2")
        assert cache.size() == 2

        cache.invalidate("key1")
        assert cache.size() == 1

    def test_prune_expired_removes_old_entries(self):
        """Test prune_expired removes expired entries."""
        from bce.ai.cache import AIResultCache, CachedResult

        cache = AIResultCache("test_cache", max_age_seconds=1)

        # Add fresh entry
        cache.set("fresh", "value1")

        # Add old entries manually
        old_timestamp = time.time() - 10
        cache._cache["old1"] = CachedResult(result="old_value1", timestamp=old_timestamp)
        cache._cache["old2"] = CachedResult(result="old_value2", timestamp=old_timestamp)

        removed = cache.prune_expired()

        assert removed == 2
        assert cache.size() == 1
        assert cache.get("fresh") == "value1"

    def test_prune_expired_no_expired_entries(self):
        """Test prune_expired with no expired entries."""
        from bce.ai.cache import AIResultCache

        cache = AIResultCache("test_cache", max_age_seconds=3600)
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        removed = cache.prune_expired()

        assert removed == 0
        assert cache.size() == 2

    def test_cache_persistence(self):
        """Test cache persists across instances."""
        from bce.ai.cache import AIResultCache

        # Create cache and add data
        cache1 = AIResultCache("persistent_cache")
        cache1.set("key1", {"data": "persisted"})

        # Create new instance with same name
        cache2 = AIResultCache("persistent_cache")
        result = cache2.get("key1")

        assert result == {"data": "persisted"}

    def test_corrupted_cache_file_recovers(self):
        """Test recovery from corrupted cache file."""
        from bce.ai.cache import AIResultCache

        cache = AIResultCache("test_cache")
        cache.set("key1", "value1")

        # Corrupt the cache file
        with open(cache.cache_file, "w") as f:
            f.write("not valid json {{{")

        # Should recover and start fresh
        cache2 = AIResultCache("test_cache")
        assert cache2.size() == 0

    def test_save_and_load_cache(self):
        """Test internal save and load methods."""
        from bce.ai.cache import AIResultCache

        cache = AIResultCache("test_cache")
        cache.set("key1", "value1")
        cache.set("key2", {"nested": "data"})

        # Manually reload
        cache._load_cache()

        assert cache.get("key1") == "value1"
        assert cache.get("key2") == {"nested": "data"}


class TestCacheModuleFunctions:
    """Tests for module-level cache functions."""

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

    def test_invalidate_character_caches(self):
        """Test invalidating character-related caches."""
        from bce.ai.cache import AIResultCache, invalidate_character_caches

        # Create caches and add data
        cache1 = AIResultCache("semantic_contradictions")
        cache1.set("jesus", {"data": "test1"})

        cache2 = AIResultCache("completeness_audit")
        cache2.set("jesus", {"data": "test2"})

        cache3 = AIResultCache("validation_suggestions")
        cache3.set("jesus", {"data": "test3"})

        # Invalidate character caches
        invalidate_character_caches("jesus")

        # Need to reload caches to see the changes from disk
        cache1_reload = AIResultCache("semantic_contradictions")
        cache2_reload = AIResultCache("completeness_audit")
        cache3_reload = AIResultCache("validation_suggestions")

        # Check all caches cleared for this character
        assert cache1_reload.get("jesus") is None
        assert cache2_reload.get("jesus") is None
        assert cache3_reload.get("jesus") is None

    def test_invalidate_event_caches(self):
        """Test invalidating event-related caches."""
        from bce.ai.cache import AIResultCache, invalidate_event_caches

        # Create caches and add data
        cache1 = AIResultCache("semantic_contradictions")
        cache1.set("crucifixion", {"data": "test1"})

        cache2 = AIResultCache("parallel_detection")
        cache2.set("crucifixion", {"data": "test2"})

        # Invalidate event caches
        invalidate_event_caches("crucifixion")

        # Need to reload caches to see the changes from disk
        cache1_reload = AIResultCache("semantic_contradictions")
        cache2_reload = AIResultCache("parallel_detection")

        # Check caches cleared
        assert cache1_reload.get("crucifixion") is None
        assert cache2_reload.get("crucifixion") is None

    def test_clear_all_ai_caches(self):
        """Test clearing all AI caches."""
        from bce.ai.cache import AIResultCache, clear_all_ai_caches

        # Create multiple caches with data
        cache1 = AIResultCache("cache1")
        cache1.set("key1", "value1")

        cache2 = AIResultCache("cache2")
        cache2.set("key2", "value2")

        # Also create some pickle and json files directly
        cache_dir = self.config.ai_cache_dir
        (cache_dir / "test.pkl").write_bytes(pickle.dumps({"test": "data"}))
        (cache_dir / "test.json").write_text('{"test": "data"}')

        # Clear all caches
        clear_all_ai_caches()

        # Check files are removed
        assert not (cache_dir / "test.pkl").exists()
        assert not (cache_dir / "test.json").exists()

    def test_clear_all_ai_caches_nested_directories(self):
        """Test clearing caches in nested directories."""
        from bce.ai.cache import clear_all_ai_caches

        cache_dir = self.config.ai_cache_dir
        nested_dir = cache_dir / "nested" / "deep"
        nested_dir.mkdir(parents=True, exist_ok=True)

        # Create files in nested directories
        (nested_dir / "nested.pkl").write_bytes(pickle.dumps({"data": "test"}))
        (nested_dir / "nested.json").write_text('{"data": "test"}')

        clear_all_ai_caches()

        # Check nested files are removed
        assert not (nested_dir / "nested.pkl").exists()
        assert not (nested_dir / "nested.json").exists()


class TestCachedAnalysisDecorator:
    """Tests for cached_analysis decorator."""

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

    def test_decorator_caches_result(self):
        """Test decorator caches function results."""
        from bce.ai.cache import cached_analysis

        call_count = 0

        @cached_analysis(ttl_hours=1, namespace="test_ns")
        def expensive_function(x, y):
            nonlocal call_count
            call_count += 1
            return x + y

        # First call
        result1 = expensive_function(1, 2)
        assert result1 == 3
        assert call_count == 1

        # Second call should use cache
        result2 = expensive_function(1, 2)
        assert result2 == 3
        assert call_count == 1  # Not called again

    def test_decorator_different_args(self):
        """Test decorator with different arguments."""
        from bce.ai.cache import cached_analysis

        call_count = 0

        @cached_analysis(ttl_hours=1, namespace="test_ns")
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count == 1

        # Different args should call function again
        result2 = expensive_function(10)
        assert result2 == 20
        assert call_count == 2

    def test_decorator_with_kwargs(self):
        """Test decorator with keyword arguments."""
        from bce.ai.cache import cached_analysis

        call_count = 0

        @cached_analysis(ttl_hours=1, namespace="test_ns")
        def expensive_function(x, y=10):
            nonlocal call_count
            call_count += 1
            return x + y

        result1 = expensive_function(5, y=20)
        assert result1 == 25
        assert call_count == 1

        # Same kwargs should use cache
        result2 = expensive_function(5, y=20)
        assert result2 == 25
        assert call_count == 1

    def test_decorator_custom_ttl(self):
        """Test decorator with custom TTL."""
        from bce.ai.cache import cached_analysis

        @cached_analysis(ttl_hours=0.0001, namespace="test_ns")  # Very short TTL
        def expensive_function(x):
            return x * 2

        result1 = expensive_function(5)
        assert result1 == 10

        # Wait for expiration
        time.sleep(0.5)

        # Should compute again (though we can't easily verify without call count)
        result2 = expensive_function(5)
        assert result2 == 10

    def test_decorator_default_namespace(self):
        """Test decorator uses default namespace."""
        from bce.ai.cache import cached_analysis

        @cached_analysis(ttl_hours=1)  # No namespace specified
        def expensive_function(x):
            return x * 2

        result = expensive_function(5)
        assert result == 10


# ============================================================================
# Tests for bce/ai/embeddings.py
# ============================================================================


class TestEmbeddingLazyImports:
    """Tests for lazy import functions."""

    def setup_method(self):
        """Set up test fixtures."""
        reset_default_config()

    def teardown_method(self):
        """Clean up after tests."""
        reset_default_config()

    def test_get_numpy_imports_numpy(self):
        """Test _get_numpy imports numpy."""
        np = pytest.importorskip("numpy")
        from bce.ai import embeddings

        # Reset global
        embeddings._np = None

        np_loaded = embeddings._get_numpy()
        assert np_loaded is not None
        assert hasattr(np_loaded, "array")

    def test_get_numpy_caches_import(self):
        """Test _get_numpy caches the import."""
        pytest.importorskip("numpy")
        from bce.ai import embeddings

        embeddings._np = None

        np1 = embeddings._get_numpy()
        np2 = embeddings._get_numpy()

        assert np1 is np2

    def test_get_numpy_missing_raises_import_error(self):
        """Test _get_numpy raises ImportError if numpy missing."""
        from bce.ai import embeddings

        embeddings._np = None

        with patch.dict("sys.modules", {"numpy": None}):
            with pytest.raises(ImportError, match="numpy is required"):
                embeddings._get_numpy()

    def test_get_model_requires_ai_enabled(self):
        """Test _get_model requires AI features enabled."""
        pytest.importorskip("numpy")
        from bce.ai import embeddings

        config = BceConfig(enable_ai_features=False)
        set_default_config(config)

        embeddings._model = None

        with pytest.raises(ConfigurationError, match="AI features are disabled"):
            embeddings._get_model()

    def test_get_model_missing_transformers_raises_error(self):
        """Test _get_model raises ImportError if transformers missing."""
        from bce.ai import embeddings

        temp_dir = tempfile.mkdtemp()
        config = BceConfig(
            data_root=Path(temp_dir), enable_ai_features=True
        )
        set_default_config(config)

        embeddings._model = None

        with patch.dict("sys.modules", {"sentence_transformers": None}):
            with pytest.raises(ImportError, match="sentence-transformers is required"):
                embeddings._get_model()

        import shutil

        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_get_model_caches_model(self):
        """Test _get_model caches the model instance."""
        pytest.importorskip("numpy")
        from bce.ai import embeddings

        temp_dir = tempfile.mkdtemp()
        config = BceConfig(
            data_root=Path(temp_dir), enable_ai_features=True
        )
        set_default_config(config)

        # Mock SentenceTransformer
        mock_model = MagicMock()
        mock_transformer_class = MagicMock(return_value=mock_model)

        embeddings._model = None

        with patch(
            "bce.ai.embeddings.SentenceTransformer", mock_transformer_class
        ):
            model1 = embeddings._get_model()
            model2 = embeddings._get_model()

            assert model1 is model2
            assert mock_transformer_class.call_count == 1

        import shutil

        shutil.rmtree(temp_dir, ignore_errors=True)


class TestEmbeddingFunctions:
    """Tests for embedding generation functions."""

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

    def test_embed_text_requires_ai_enabled(self):
        """Test embed_text requires AI features enabled."""
        from bce.ai.embeddings import embed_text

        config = BceConfig(enable_ai_features=False)
        set_default_config(config)

        with pytest.raises(ConfigurationError, match="AI features are disabled"):
            embed_text("test")

    def test_embed_text_calls_model(self):
        """Test embed_text calls the model."""
        from bce.ai.embeddings import embed_text

        mock_model = MagicMock()
        mock_model.encode.return_value = [0.1, 0.2, 0.3]

        with patch("bce.ai.embeddings._get_model", return_value=mock_model):
            result = embed_text("test text")

            mock_model.encode.assert_called_once_with("test text", convert_to_numpy=True)
            assert result == [0.1, 0.2, 0.3]

    def test_embed_texts_requires_ai_enabled(self):
        """Test embed_texts requires AI features enabled."""
        from bce.ai.embeddings import embed_texts

        config = BceConfig(enable_ai_features=False)
        set_default_config(config)

        with pytest.raises(ConfigurationError, match="AI features are disabled"):
            embed_texts(["test1", "test2"])

    def test_embed_texts_calls_model(self):
        """Test embed_texts calls the model with list."""
        from bce.ai.embeddings import embed_texts

        mock_model = MagicMock()
        mock_model.encode.return_value = [[0.1, 0.2], [0.3, 0.4]]

        with patch("bce.ai.embeddings._get_model", return_value=mock_model):
            result = embed_texts(["text1", "text2"])

            mock_model.encode.assert_called_once_with(
                ["text1", "text2"], convert_to_numpy=True
            )
            assert result == [[0.1, 0.2], [0.3, 0.4]]


class TestSimilarityFunctions:
    """Tests for similarity computation functions."""

    def test_cosine_similarity_identical_vectors(self):
        """Test cosine similarity of identical vectors is 1."""
        np = pytest.importorskip("numpy")
        from bce.ai.embeddings import cosine_similarity

        vec = np.array([1.0, 2.0, 3.0])
        similarity = cosine_similarity(vec, vec)

        assert abs(similarity - 1.0) < 1e-6

    def test_cosine_similarity_orthogonal_vectors(self):
        """Test cosine similarity of orthogonal vectors is 0."""
        np = pytest.importorskip("numpy")
        from bce.ai.embeddings import cosine_similarity

        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([0.0, 1.0, 0.0])
        similarity = cosine_similarity(vec1, vec2)

        assert abs(similarity - 0.0) < 1e-6

    def test_cosine_similarity_opposite_vectors(self):
        """Test cosine similarity of opposite vectors is -1."""
        np = pytest.importorskip("numpy")
        from bce.ai.embeddings import cosine_similarity

        vec1 = np.array([1.0, 2.0, 3.0])
        vec2 = np.array([-1.0, -2.0, -3.0])
        similarity = cosine_similarity(vec1, vec2)

        assert abs(similarity - (-1.0)) < 1e-6

    def test_cosine_similarity_zero_vector(self):
        """Test cosine similarity with zero vector returns 0."""
        np = pytest.importorskip("numpy")
        from bce.ai.embeddings import cosine_similarity

        vec1 = np.array([1.0, 2.0, 3.0])
        vec2 = np.array([0.0, 0.0, 0.0])
        similarity = cosine_similarity(vec1, vec2)

        assert similarity == 0.0

    def test_cosine_similarity_both_zero_vectors(self):
        """Test cosine similarity with both zero vectors returns 0."""
        np = pytest.importorskip("numpy")
        from bce.ai.embeddings import cosine_similarity

        vec1 = np.array([0.0, 0.0, 0.0])
        vec2 = np.array([0.0, 0.0, 0.0])
        similarity = cosine_similarity(vec1, vec2)

        assert similarity == 0.0

    def test_compute_similarity_matrix_shape(self):
        """Test compute_similarity_matrix returns correct shape."""
        np = pytest.importorskip("numpy")
        from bce.ai.embeddings import compute_similarity_matrix

        embeddings = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
        matrix = compute_similarity_matrix(embeddings)

        assert matrix.shape == (3, 3)

    def test_compute_similarity_matrix_diagonal_is_one(self):
        """Test similarity matrix diagonal is 1 (self-similarity)."""
        np = pytest.importorskip("numpy")
        from bce.ai.embeddings import compute_similarity_matrix

        embeddings = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
        matrix = compute_similarity_matrix(embeddings)

        assert abs(matrix[0, 0] - 1.0) < 1e-6
        assert abs(matrix[1, 1] - 1.0) < 1e-6
        assert abs(matrix[2, 2] - 1.0) < 1e-6

    def test_compute_similarity_matrix_symmetric(self):
        """Test similarity matrix is symmetric."""
        np = pytest.importorskip("numpy")
        from bce.ai.embeddings import compute_similarity_matrix

        embeddings = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
        matrix = compute_similarity_matrix(embeddings)

        assert abs(matrix[0, 1] - matrix[1, 0]) < 1e-6
        assert abs(matrix[0, 2] - matrix[2, 0]) < 1e-6
        assert abs(matrix[1, 2] - matrix[2, 1]) < 1e-6

    def test_compute_similarity_matrix_with_zero_vectors(self):
        """Test similarity matrix handles zero vectors."""
        np = pytest.importorskip("numpy")
        from bce.ai.embeddings import compute_similarity_matrix

        embeddings = np.array([[1.0, 2.0], [0.0, 0.0], [3.0, 4.0]])
        matrix = compute_similarity_matrix(embeddings)

        # Zero vector should have 0 similarity with others (except itself)
        assert abs(matrix[1, 1] - 1.0) < 1e-6  # Self-similarity handled
        # Other similarities involving zero vector should be 0
        assert abs(matrix[0, 1]) < 1e-6
        assert abs(matrix[1, 2]) < 1e-6


class TestEmbeddingCache:
    """Tests for EmbeddingCache class."""

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

    def test_embedding_cache_initialization(self):
        """Test embedding cache initialization."""
        from bce.ai.embeddings import EmbeddingCache

        cache = EmbeddingCache("test_embeddings")

        assert cache.cache_name == "test_embeddings"
        assert cache.cache_dir.exists()
        assert cache.cache_file.name == "test_embeddings.pkl"

    def test_hash_text_consistent(self):
        """Test _hash_text produces consistent hashes."""
        from bce.ai.embeddings import EmbeddingCache

        cache = EmbeddingCache("test_cache")

        hash1 = cache._hash_text("test text")
        hash2 = cache._hash_text("test text")

        assert hash1 == hash2

    def test_hash_text_different_for_different_text(self):
        """Test _hash_text produces different hashes for different text."""
        from bce.ai.embeddings import EmbeddingCache

        cache = EmbeddingCache("test_cache")

        hash1 = cache._hash_text("text1")
        hash2 = cache._hash_text("text2")

        assert hash1 != hash2

    def test_set_and_get(self):
        """Test setting and getting embeddings."""
        np = pytest.importorskip("numpy")
        from bce.ai.embeddings import EmbeddingCache

        cache = EmbeddingCache("test_cache")
        embedding = np.array([0.1, 0.2, 0.3])

        cache.set("test text", embedding)
        retrieved = cache.get("test text")

        assert np.array_equal(retrieved, embedding)

    def test_get_nonexistent_returns_none(self):
        """Test getting non-existent embedding returns None."""
        from bce.ai.embeddings import EmbeddingCache

        cache = EmbeddingCache("test_cache")
        result = cache.get("nonexistent text")

        assert result is None

    def test_get_or_compute_cached(self):
        """Test get_or_compute returns cached embedding."""
        np = pytest.importorskip("numpy")
        from bce.ai.embeddings import EmbeddingCache

        cache = EmbeddingCache("test_cache")
        embedding = np.array([0.1, 0.2, 0.3])
        cache.set("test text", embedding)

        # Should return cached value without calling embed_text
        with patch("bce.ai.embeddings.embed_text") as mock_embed:
            result = cache.get_or_compute("test text")
            assert np.array_equal(result, embedding)
            mock_embed.assert_not_called()

    def test_get_or_compute_computes_missing(self):
        """Test get_or_compute computes and caches missing embedding."""
        np = pytest.importorskip("numpy")
        from bce.ai.embeddings import EmbeddingCache

        cache = EmbeddingCache("test_cache")
        expected_embedding = np.array([0.5, 0.6, 0.7])

        with patch(
            "bce.ai.embeddings.embed_text", return_value=expected_embedding
        ) as mock_embed:
            result = cache.get_or_compute("new text")

            mock_embed.assert_called_once_with("new text")
            assert np.array_equal(result, expected_embedding)

            # Should now be cached
            cached = cache.get("new text")
            assert np.array_equal(cached, expected_embedding)

    def test_get_or_compute_batch_all_cached(self):
        """Test get_or_compute_batch with all embeddings cached."""
        np = pytest.importorskip("numpy")
        from bce.ai.embeddings import EmbeddingCache

        cache = EmbeddingCache("test_cache")
        emb1 = np.array([0.1, 0.2])
        emb2 = np.array([0.3, 0.4])

        cache.set("text1", emb1)
        cache.set("text2", emb2)

        with patch("bce.ai.embeddings.embed_texts") as mock_embed:
            result = cache.get_or_compute_batch(["text1", "text2"])

            mock_embed.assert_not_called()
            assert len(result) == 2
            assert np.array_equal(result[0], emb1)
            assert np.array_equal(result[1], emb2)

    def test_get_or_compute_batch_mixed(self):
        """Test get_or_compute_batch with mixed cached/uncached."""
        np = pytest.importorskip("numpy")
        from bce.ai.embeddings import EmbeddingCache

        cache = EmbeddingCache("test_cache")
        cached_emb = np.array([0.1, 0.2])
        cache.set("cached_text", cached_emb)

        new_emb = np.array([0.3, 0.4])

        with patch(
            "bce.ai.embeddings.embed_texts", return_value=np.array([new_emb])
        ) as mock_embed:
            result = cache.get_or_compute_batch(["cached_text", "new_text"])

            mock_embed.assert_called_once_with(["new_text"])
            assert len(result) == 2
            assert np.array_equal(result[0], cached_emb)
            assert np.array_equal(result[1], new_emb)

    def test_get_or_compute_batch_all_new(self):
        """Test get_or_compute_batch with all new embeddings."""
        np = pytest.importorskip("numpy")
        from bce.ai.embeddings import EmbeddingCache

        cache = EmbeddingCache("test_cache")
        new_embs = np.array([[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]])

        with patch(
            "bce.ai.embeddings.embed_texts", return_value=new_embs
        ) as mock_embed:
            result = cache.get_or_compute_batch(["text1", "text2", "text3"])

            mock_embed.assert_called_once_with(["text1", "text2", "text3"])
            assert len(result) == 3

    def test_clear(self):
        """Test clearing embedding cache."""
        np = pytest.importorskip("numpy")
        from bce.ai.embeddings import EmbeddingCache

        cache = EmbeddingCache("test_cache")
        cache.set("text1", np.array([0.1, 0.2]))
        cache.set("text2", np.array([0.3, 0.4]))

        cache.clear()

        assert cache.size() == 0
        assert not cache.cache_file.exists()

    def test_size(self):
        """Test getting cache size."""
        np = pytest.importorskip("numpy")
        from bce.ai.embeddings import EmbeddingCache

        cache = EmbeddingCache("test_cache")
        assert cache.size() == 0

        cache.set("text1", np.array([0.1, 0.2]))
        assert cache.size() == 1

        cache.set("text2", np.array([0.3, 0.4]))
        assert cache.size() == 2

    def test_persistence(self):
        """Test embedding cache persists across instances."""
        np = pytest.importorskip("numpy")
        from bce.ai.embeddings import EmbeddingCache

        embedding = np.array([0.1, 0.2, 0.3])

        # Create cache and add data
        cache1 = EmbeddingCache("persistent_cache")
        cache1.set("test text", embedding)

        # Create new instance
        cache2 = EmbeddingCache("persistent_cache")
        retrieved = cache2.get("test text")

        assert np.array_equal(retrieved, embedding)

    def test_corrupted_cache_recovers(self):
        """Test recovery from corrupted cache file."""
        np = pytest.importorskip("numpy")
        from bce.ai.embeddings import EmbeddingCache

        cache = EmbeddingCache("test_cache")
        cache.set("text", np.array([0.1, 0.2]))

        # Corrupt the cache file
        with open(cache.cache_file, "w") as f:
            f.write("corrupted data")

        # Should recover and start fresh
        cache2 = EmbeddingCache("test_cache")
        assert cache2.size() == 0
