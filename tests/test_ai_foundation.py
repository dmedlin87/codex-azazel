"""
Tests for AI foundation modules (Phase 6.1).

Tests the core AI infrastructure: config, embeddings, cache, and models.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from bce.config import BceConfig, set_default_config, reset_default_config
from bce.exceptions import ConfigurationError


class TestAIConfiguration:
    """Tests for AI configuration in BceConfig."""

    def setup_method(self):
        """Reset configuration before each test."""
        reset_default_config()
        # Clear AI-related environment variables
        for key in [
            "BCE_ENABLE_AI_FEATURES",
            "BCE_AI_MODEL_BACKEND",
            "BCE_AI_CACHE_DIR",
            "BCE_EMBEDDING_MODEL",
        ]:
            os.environ.pop(key, None)

    def teardown_method(self):
        """Clean up after each test."""
        reset_default_config()

    def test_ai_features_disabled_by_default(self):
        """AI features should be disabled by default."""
        config = BceConfig()
        assert config.enable_ai_features is False

    def test_ai_features_enable_via_constructor(self):
        """Should enable AI features via constructor."""
        config = BceConfig(enable_ai_features=True)
        assert config.enable_ai_features is True

    def test_ai_features_enable_via_env(self):
        """Should enable AI features via environment variable."""
        os.environ["BCE_ENABLE_AI_FEATURES"] = "true"
        config = BceConfig()
        assert config.enable_ai_features is True

        os.environ["BCE_ENABLE_AI_FEATURES"] = "1"
        config = BceConfig()
        assert config.enable_ai_features is True

    def test_ai_backend_default(self):
        """AI backend should default to 'local'."""
        config = BceConfig()
        assert config.ai_model_backend == "local"

    def test_ai_backend_via_constructor(self):
        """Should set AI backend via constructor."""
        config = BceConfig(ai_model_backend="openai")
        assert config.ai_model_backend == "openai"

    def test_ai_backend_invalid(self):
        """Should raise error for invalid backend."""
        with pytest.raises(ConfigurationError, match="Invalid AI backend"):
            BceConfig(ai_model_backend="invalid")

    def test_ai_backend_via_env(self):
        """Should set AI backend via environment variable."""
        os.environ["BCE_AI_MODEL_BACKEND"] = "anthropic"
        config = BceConfig()
        assert config.ai_model_backend == "anthropic"

    def test_embedding_model_default(self):
        """Embedding model should have sensible default."""
        config = BceConfig()
        assert config.embedding_model == "all-MiniLM-L6-v2"

    def test_embedding_model_via_constructor(self):
        """Should set embedding model via constructor."""
        config = BceConfig(embedding_model="custom-model")
        assert config.embedding_model == "custom-model"

    def test_embedding_model_via_env(self):
        """Should set embedding model via environment variable."""
        os.environ["BCE_EMBEDDING_MODEL"] = "all-mpnet-base-v2"
        config = BceConfig()
        assert config.embedding_model == "all-mpnet-base-v2"

    def test_ai_cache_dir_default(self):
        """AI cache dir should default to data_root/ai_cache."""
        config = BceConfig()
        expected = config.data_root / "ai_cache"
        assert config.ai_cache_dir == expected

    def test_ai_cache_dir_via_constructor(self):
        """Should set AI cache dir via constructor."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "custom_cache"
            config = BceConfig(ai_cache_dir=cache_path)
            assert config.ai_cache_dir == cache_path

    def test_ai_cache_dir_via_env(self):
        """Should set AI cache dir via environment variable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ["BCE_AI_CACHE_DIR"] = tmpdir
            config = BceConfig()
            assert config.ai_cache_dir == Path(tmpdir)

    def test_repr_includes_ai_fields(self):
        """__repr__ should include AI configuration fields."""
        config = BceConfig(enable_ai_features=True, ai_model_backend="openai")
        repr_str = repr(config)
        assert "enable_ai_features=True" in repr_str
        assert "ai_model_backend=openai" in repr_str
        assert "embedding_model=" in repr_str


class TestAIConfigHelpers:
    """Tests for bce.ai.config helper functions."""

    def setup_method(self):
        """Setup for each test."""
        reset_default_config()

    def teardown_method(self):
        """Cleanup after each test."""
        reset_default_config()

    def test_ensure_ai_enabled_raises_when_disabled(self):
        """ensure_ai_enabled should raise when AI is disabled."""
        from bce.ai.config import ensure_ai_enabled

        config = BceConfig(enable_ai_features=False)
        set_default_config(config)

        with pytest.raises(ConfigurationError, match="AI features are disabled"):
            ensure_ai_enabled()

    def test_ensure_ai_enabled_passes_when_enabled(self):
        """ensure_ai_enabled should not raise when AI is enabled."""
        from bce.ai.config import ensure_ai_enabled

        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

        # Should not raise
        ensure_ai_enabled()

    def test_get_ai_cache_dir_creates_directory(self):
        """get_ai_cache_dir should create directory if it doesn't exist."""
        from bce.ai.config import get_ai_cache_dir

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "test_cache"
            config = BceConfig(ai_cache_dir=cache_path)
            set_default_config(config)

            result = get_ai_cache_dir()
            assert result == cache_path
            assert cache_path.exists()
            assert cache_path.is_dir()

    def test_get_embedding_model_name(self):
        """get_embedding_model_name should return configured model."""
        from bce.ai.config import get_embedding_model_name

        config = BceConfig(embedding_model="test-model")
        set_default_config(config)

        assert get_embedding_model_name() == "test-model"

    def test_get_ai_backend(self):
        """get_ai_backend should return configured backend."""
        from bce.ai.config import get_ai_backend

        config = BceConfig(ai_model_backend="anthropic")
        set_default_config(config)

        assert get_ai_backend() == "anthropic"

    def test_validate_api_key_openai_missing(self):
        """validate_api_key should raise if OpenAI key is missing."""
        from bce.ai.config import validate_api_key

        os.environ.pop("OPENAI_API_KEY", None)

        with pytest.raises(ConfigurationError, match="OPENAI_API_KEY"):
            validate_api_key("openai")

    def test_validate_api_key_openai_present(self):
        """validate_api_key should return key if present."""
        from bce.ai.config import validate_api_key

        os.environ["OPENAI_API_KEY"] = "sk-test-key"
        key = validate_api_key("openai")
        assert key == "sk-test-key"

        # Cleanup
        os.environ.pop("OPENAI_API_KEY")

    def test_validate_api_key_anthropic_missing(self):
        """validate_api_key should raise if Anthropic key is missing."""
        from bce.ai.config import validate_api_key

        os.environ.pop("ANTHROPIC_API_KEY", None)

        with pytest.raises(ConfigurationError, match="ANTHROPIC_API_KEY"):
            validate_api_key("anthropic")

    def test_validate_api_key_anthropic_present(self):
        """validate_api_key should return key if present."""
        from bce.ai.config import validate_api_key

        os.environ["ANTHROPIC_API_KEY"] = "sk-ant-test"
        key = validate_api_key("anthropic")
        assert key == "sk-ant-test"

        # Cleanup
        os.environ.pop("ANTHROPIC_API_KEY")

    def test_validate_api_key_local_returns_none(self):
        """validate_api_key should return None for local backend."""
        from bce.ai.config import validate_api_key

        key = validate_api_key("local")
        assert key is None


class TestAICache:
    """Tests for AI-specific caching."""

    def test_ai_result_cache_basic_operations(self):
        """Test basic cache operations."""
        from bce.ai.cache import AIResultCache

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir)
            config = BceConfig(ai_cache_dir=cache_path)
            set_default_config(config)

            cache = AIResultCache("test_cache")

            # Initially empty
            assert cache.get("key1") is None
            assert cache.size() == 0

            # Set and get
            cache.set("key1", {"result": "value1"}, model_name="test-model")
            result = cache.get("key1")
            assert result == {"result": "value1"}
            assert cache.size() == 1

            # Invalidate
            cache.invalidate("key1")
            assert cache.get("key1") is None
            assert cache.size() == 0

    def test_ai_result_cache_persistence(self):
        """Test cache persistence across instances."""
        from bce.ai.cache import AIResultCache

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir)
            config = BceConfig(ai_cache_dir=cache_path)
            set_default_config(config)

            # Create cache and add data
            cache1 = AIResultCache("persistent_cache")
            cache1.set("key1", {"data": "test"})

            # Create new cache instance
            cache2 = AIResultCache("persistent_cache")
            result = cache2.get("key1")
            assert result == {"data": "test"}

    def test_ai_result_cache_expiration(self):
        """Test cache expiration."""
        from bce.ai.cache import AIResultCache
        import time

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir)
            config = BceConfig(ai_cache_dir=cache_path)
            set_default_config(config)

            # Cache with 1 second max age
            cache = AIResultCache("expiring_cache", max_age_seconds=1)
            cache.set("key1", {"data": "test"})

            # Should be available immediately
            assert cache.get("key1") is not None

            # Wait for expiration
            time.sleep(1.1)

            # Should be expired
            assert cache.get("key1") is None

    def test_clear_all_ai_caches(self):
        """Test clearing all AI caches."""
        from bce.ai.cache import clear_all_ai_caches, AIResultCache

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir)
            config = BceConfig(ai_cache_dir=cache_path)
            set_default_config(config)

            # Create multiple caches
            cache1 = AIResultCache("cache1")
            cache2 = AIResultCache("cache2")
            cache1.set("key1", "value1")
            cache2.set("key2", "value2")

            # Clear all caches
            clear_all_ai_caches()

            # Verify caches are cleared
            cache1_new = AIResultCache("cache1")
            cache2_new = AIResultCache("cache2")
            assert cache1_new.get("key1") is None
            assert cache2_new.get("key2") is None


class TestEmbeddingCache:
    """Tests for embedding cache (requires sentence-transformers)."""

    @pytest.mark.skipif(
        os.getenv("SKIP_AI_TESTS") == "1",
        reason="Skipping AI tests (SKIP_AI_TESTS=1)",
    )
    def test_embedding_cache_basic(self):
        """Test basic embedding cache operations."""
        from bce.ai.embeddings import EmbeddingCache
        import numpy as np

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir)
            config = BceConfig(
                enable_ai_features=True, ai_cache_dir=cache_path
            )
            set_default_config(config)

            cache = EmbeddingCache("test_embeddings")

            # Initially no cached embedding
            assert cache.get("test text") is None

            # Cache an embedding
            embedding = np.array([0.1, 0.2, 0.3])
            cache.set("test text", embedding)

            # Retrieve cached embedding
            cached = cache.get("test text")
            assert cached is not None
            assert np.allclose(cached, embedding)

            # Size should be 1
            assert cache.size() == 1

            # Clear cache
            cache.clear()
            assert cache.size() == 0
            assert cache.get("test text") is None


class TestModelManager:
    """Tests for model manager."""

    def test_model_manager_singleton(self):
        """Test model manager singleton pattern."""
        from bce.ai.models import get_model_manager, reset_model_manager

        manager1 = get_model_manager()
        manager2 = get_model_manager()
        assert manager1 is manager2

        # Reset and get new instance
        reset_model_manager()
        manager3 = get_model_manager()
        assert manager3 is not manager1

    def test_model_manager_requires_ai_enabled(self):
        """Model manager should check if AI is enabled."""
        from bce.ai.models import get_model_manager

        config = BceConfig(enable_ai_features=False)
        set_default_config(config)

        manager = get_model_manager()

        with pytest.raises(ConfigurationError, match="AI features are disabled"):
            manager.get_embedding_model()
