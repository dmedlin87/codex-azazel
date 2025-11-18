"""
Comprehensive tests for AI models module.

This test suite focuses on:
- bce/ai/models.py: ModelManager, model loading, backend management
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from bce.config import BceConfig, set_default_config, reset_default_config
from bce.exceptions import ConfigurationError


# ============================================================================
# Tests for bce/ai/models.py
# ============================================================================


class TestModelManager:
    """Tests for ModelManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = BceConfig(
            data_root=Path(self.temp_dir),
            enable_ai_features=True,
        )
        set_default_config(self.config)

        # Reset global manager
        from bce.ai.models import reset_model_manager

        reset_model_manager()

    def teardown_method(self):
        """Clean up after tests."""
        reset_default_config()

        from bce.ai.models import reset_model_manager

        reset_model_manager()

        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_model_manager_initialization(self):
        """Test ModelManager initialization."""
        from bce.ai.models import ModelManager

        manager = ModelManager()

        assert manager._local_model is None
        assert manager._api_client is None

    def test_get_embedding_model_requires_ai_enabled(self):
        """Test get_embedding_model requires AI features enabled."""
        from bce.ai.models import ModelManager

        config = BceConfig(enable_ai_features=False)
        set_default_config(config)

        manager = ModelManager()

        with pytest.raises(ConfigurationError, match="AI features are disabled"):
            manager.get_embedding_model()

    def test_get_embedding_model_missing_transformers(self):
        """Test get_embedding_model raises ImportError if transformers missing."""
        from bce.ai.models import ModelManager

        manager = ModelManager()

        with patch.dict("sys.modules", {"sentence_transformers": None}):
            with pytest.raises(ImportError, match="sentence-transformers is required"):
                manager.get_embedding_model()

    def test_get_embedding_model_loads_model(self):
        """Test get_embedding_model loads the model."""
        from bce.ai.models import ModelManager

        mock_model = MagicMock()
        mock_transformer_class = MagicMock(return_value=mock_model)

        manager = ModelManager()

        # Patch where it's imported (inside the method)
        with patch("sentence_transformers.SentenceTransformer", mock_transformer_class):
            result = manager.get_embedding_model()

            assert result is mock_model
            mock_transformer_class.assert_called_once()

            # Check it was called with correct args
            call_args = mock_transformer_class.call_args
            assert call_args[0][0] == "all-MiniLM-L6-v2"  # Default model
            assert "cache_folder" in call_args[1]

    def test_get_embedding_model_caches_model(self):
        """Test get_embedding_model caches the model instance."""
        from bce.ai.models import ModelManager
        import sys

        mock_model = MagicMock()
        mock_transformer_class = MagicMock(return_value=mock_model)

        # Create mock sentence_transformers module
        mock_st_module = MagicMock()
        mock_st_module.SentenceTransformer = mock_transformer_class

        manager = ModelManager()

        with patch.dict(sys.modules, {"sentence_transformers": mock_st_module}):
            model1 = manager.get_embedding_model()
            model2 = manager.get_embedding_model()

            assert model1 is model2
            assert manager._local_model is model1
            mock_transformer_class.assert_called_once()  # Only called once

    def test_get_llm_client_requires_ai_enabled(self):
        """Test get_llm_client requires AI features enabled."""
        from bce.ai.models import ModelManager

        config = BceConfig(enable_ai_features=False)
        set_default_config(config)

        manager = ModelManager()

        with pytest.raises(ConfigurationError, match="AI features are disabled"):
            manager.get_llm_client()

    def test_get_llm_client_default_backend(self):
        """Test get_llm_client uses default backend."""
        from bce.ai.models import ModelManager

        config = BceConfig(
            enable_ai_features=True, ai_model_backend="openai"
        )
        set_default_config(config)
        os.environ["OPENAI_API_KEY"] = "test-key"

        manager = ModelManager()
        mock_client = MagicMock()

        with patch("bce.ai.models.openai.OpenAI", return_value=mock_client):
            result = manager.get_llm_client()
            assert result is mock_client

        del os.environ["OPENAI_API_KEY"]

    def test_get_llm_client_explicit_backend(self):
        """Test get_llm_client with explicit backend override."""
        from bce.ai.models import ModelManager

        config = BceConfig(
            enable_ai_features=True, ai_model_backend="local"
        )
        set_default_config(config)
        os.environ["ANTHROPIC_API_KEY"] = "test-key"

        manager = ModelManager()
        mock_client = MagicMock()

        with patch("bce.ai.models.anthropic.Anthropic", return_value=mock_client):
            # Override default backend
            result = manager.get_llm_client(backend="anthropic")
            assert result is mock_client

        del os.environ["ANTHROPIC_API_KEY"]

    def test_get_llm_client_unknown_backend(self):
        """Test get_llm_client raises error for unknown backend."""
        from bce.ai.models import ModelManager

        manager = ModelManager()

        with pytest.raises(ConfigurationError, match="Unknown backend: invalid_backend"):
            manager.get_llm_client(backend="invalid_backend")

    def test_get_openai_client_missing_library(self):
        """Test _get_openai_client raises ImportError if openai missing."""
        from bce.ai.models import ModelManager

        manager = ModelManager()

        with patch.dict("sys.modules", {"openai": None}):
            with pytest.raises(ImportError, match="openai is required"):
                manager._get_openai_client()

    def test_get_openai_client_missing_api_key(self):
        """Test _get_openai_client raises error if API key missing."""
        from bce.ai.models import ModelManager

        # Ensure key is not set
        os.environ.pop("OPENAI_API_KEY", None)

        manager = ModelManager()
        mock_openai = MagicMock()

        with patch("bce.ai.models.openai", mock_openai):
            with pytest.raises(
                ConfigurationError, match="OpenAI backend requires OPENAI_API_KEY"
            ):
                manager._get_openai_client()

    def test_get_openai_client_success(self):
        """Test _get_openai_client successfully creates client."""
        from bce.ai.models import ModelManager

        os.environ["OPENAI_API_KEY"] = "test-openai-key"

        manager = ModelManager()
        mock_client = MagicMock()
        mock_openai = MagicMock()
        mock_openai.OpenAI = MagicMock(return_value=mock_client)

        with patch("bce.ai.models.openai", mock_openai):
            result = manager._get_openai_client()

            assert result is mock_client
            mock_openai.OpenAI.assert_called_once_with(api_key="test-openai-key")

        del os.environ["OPENAI_API_KEY"]

    def test_get_anthropic_client_missing_library(self):
        """Test _get_anthropic_client raises ImportError if anthropic missing."""
        from bce.ai.models import ModelManager

        manager = ModelManager()

        with patch.dict("sys.modules", {"anthropic": None}):
            with pytest.raises(ImportError, match="anthropic is required"):
                manager._get_anthropic_client()

    def test_get_anthropic_client_missing_api_key(self):
        """Test _get_anthropic_client raises error if API key missing."""
        from bce.ai.models import ModelManager

        # Ensure key is not set
        os.environ.pop("ANTHROPIC_API_KEY", None)

        manager = ModelManager()
        mock_anthropic = MagicMock()

        with patch("bce.ai.models.anthropic", mock_anthropic):
            with pytest.raises(
                ConfigurationError, match="Anthropic backend requires ANTHROPIC_API_KEY"
            ):
                manager._get_anthropic_client()

    def test_get_anthropic_client_success(self):
        """Test _get_anthropic_client successfully creates client."""
        from bce.ai.models import ModelManager

        os.environ["ANTHROPIC_API_KEY"] = "test-anthropic-key"

        manager = ModelManager()
        mock_client = MagicMock()
        mock_anthropic = MagicMock()
        mock_anthropic.Anthropic = MagicMock(return_value=mock_client)

        with patch("bce.ai.models.anthropic", mock_anthropic):
            result = manager._get_anthropic_client()

            assert result is mock_client
            mock_anthropic.Anthropic.assert_called_once_with(api_key="test-anthropic-key")

        del os.environ["ANTHROPIC_API_KEY"]

    def test_get_local_llm_client_not_implemented(self):
        """Test _get_local_llm_client raises NotImplementedError."""
        from bce.ai.models import ModelManager

        manager = ModelManager()

        with pytest.raises(NotImplementedError, match="Local LLM support is not yet implemented"):
            manager._get_local_llm_client()

    def test_reset_clears_models(self):
        """Test reset clears loaded models."""
        from bce.ai.models import ModelManager

        manager = ModelManager()
        mock_model = MagicMock()
        manager._local_model = mock_model
        manager._api_client = MagicMock()

        manager.reset()

        assert manager._local_model is None
        assert manager._api_client is None


class TestModelManagerGlobalInstance:
    """Tests for global model manager functions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = BceConfig(
            data_root=Path(self.temp_dir),
            enable_ai_features=True,
        )
        set_default_config(self.config)

        # Reset global manager
        from bce.ai.models import reset_model_manager

        reset_model_manager()

    def teardown_method(self):
        """Clean up after tests."""
        reset_default_config()

        from bce.ai.models import reset_model_manager

        reset_model_manager()

        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_get_model_manager_creates_singleton(self):
        """Test get_model_manager creates singleton instance."""
        from bce.ai.models import get_model_manager

        manager1 = get_model_manager()
        manager2 = get_model_manager()

        assert manager1 is manager2

    def test_get_model_manager_returns_model_manager(self):
        """Test get_model_manager returns ModelManager instance."""
        from bce.ai.models import get_model_manager, ModelManager

        manager = get_model_manager()

        assert isinstance(manager, ModelManager)

    def test_reset_model_manager_clears_singleton(self):
        """Test reset_model_manager clears the singleton."""
        from bce.ai.models import get_model_manager, reset_model_manager

        manager1 = get_model_manager()
        reset_model_manager()
        manager2 = get_model_manager()

        assert manager1 is not manager2

    def test_reset_model_manager_calls_reset(self):
        """Test reset_model_manager calls reset on existing manager."""
        from bce.ai.models import get_model_manager, reset_model_manager

        manager = get_model_manager()
        mock_model = MagicMock()
        manager._local_model = mock_model

        reset_model_manager()

        # The old manager should have been reset
        assert manager._local_model is None

    def test_reset_model_manager_when_none(self):
        """Test reset_model_manager when no manager exists."""
        from bce.ai.models import reset_model_manager

        # Should not raise
        reset_model_manager()


class TestModelManagerIntegration:
    """Integration tests for ModelManager with different backends."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = BceConfig(
            data_root=Path(self.temp_dir),
            enable_ai_features=True,
        )
        set_default_config(self.config)

        from bce.ai.models import reset_model_manager

        reset_model_manager()

    def teardown_method(self):
        """Clean up after tests."""
        reset_default_config()

        from bce.ai.models import reset_model_manager

        reset_model_manager()

        # Clean up env vars
        for key in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"]:
            os.environ.pop(key, None)

        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_multiple_backend_switches(self):
        """Test switching between different backends."""
        from bce.ai.models import ModelManager

        os.environ["OPENAI_API_KEY"] = "openai-key"
        os.environ["ANTHROPIC_API_KEY"] = "anthropic-key"

        manager = ModelManager()

        mock_openai_client = MagicMock()
        mock_anthropic_client = MagicMock()

        mock_openai = MagicMock()
        mock_openai.OpenAI = MagicMock(return_value=mock_openai_client)

        mock_anthropic = MagicMock()
        mock_anthropic.Anthropic = MagicMock(return_value=mock_anthropic_client)

        with patch("bce.ai.models.openai", mock_openai):
            with patch("bce.ai.models.anthropic", mock_anthropic):
                # Get OpenAI client
                client1 = manager.get_llm_client(backend="openai")
                assert client1 is mock_openai_client

                # Get Anthropic client
                client2 = manager.get_llm_client(backend="anthropic")
                assert client2 is mock_anthropic_client

    def test_embedding_model_and_llm_client_coexist(self):
        """Test that embedding model and LLM client can be used together."""
        from bce.ai.models import ModelManager

        os.environ["OPENAI_API_KEY"] = "test-key"

        manager = ModelManager()

        mock_embedding_model = MagicMock()
        mock_llm_client = MagicMock()

        mock_transformer = MagicMock(return_value=mock_embedding_model)
        mock_openai = MagicMock()
        mock_openai.OpenAI = MagicMock(return_value=mock_llm_client)

        with patch("bce.ai.models.SentenceTransformer", mock_transformer):
            with patch("bce.ai.models.openai", mock_openai):
                # Get embedding model
                emb_model = manager.get_embedding_model()
                assert emb_model is mock_embedding_model

                # Get LLM client
                llm_client = manager.get_llm_client(backend="openai")
                assert llm_client is mock_llm_client

                # Both should be cached
                assert manager._local_model is mock_embedding_model


class TestModelManagerErrorHandling:
    """Tests for error handling in ModelManager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = BceConfig(
            data_root=Path(self.temp_dir),
            enable_ai_features=True,
        )
        set_default_config(self.config)

        from bce.ai.models import reset_model_manager

        reset_model_manager()

    def teardown_method(self):
        """Clean up after tests."""
        reset_default_config()

        from bce.ai.models import reset_model_manager

        reset_model_manager()

        for key in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"]:
            os.environ.pop(key, None)

        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_embedding_model_import_error_message(self):
        """Test embedding model import error has helpful message."""
        from bce.ai.models import ModelManager

        manager = ModelManager()

        with patch.dict("sys.modules", {"sentence_transformers": None}):
            with pytest.raises(ImportError) as exc_info:
                manager.get_embedding_model()

            assert "sentence-transformers" in str(exc_info.value)
            assert "pip install" in str(exc_info.value)

    def test_openai_import_error_message(self):
        """Test OpenAI import error has helpful message."""
        from bce.ai.models import ModelManager

        manager = ModelManager()

        with patch.dict("sys.modules", {"openai": None}):
            with pytest.raises(ImportError) as exc_info:
                manager._get_openai_client()

            assert "openai" in str(exc_info.value)
            assert "pip install" in str(exc_info.value)

    def test_anthropic_import_error_message(self):
        """Test Anthropic import error has helpful message."""
        from bce.ai.models import ModelManager

        manager = ModelManager()

        with patch.dict("sys.modules", {"anthropic": None}):
            with pytest.raises(ImportError) as exc_info:
                manager._get_anthropic_client()

            assert "anthropic" in str(exc_info.value)
            assert "pip install" in str(exc_info.value)

    def test_local_llm_not_implemented_message(self):
        """Test local LLM not implemented has helpful message."""
        from bce.ai.models import ModelManager

        manager = ModelManager()

        with pytest.raises(NotImplementedError) as exc_info:
            manager._get_local_llm_client()

        assert "Local LLM support is not yet implemented" in str(exc_info.value)
        assert "openai" in str(exc_info.value).lower()
        assert "anthropic" in str(exc_info.value).lower()

    def test_ai_disabled_error_message(self):
        """Test AI disabled error has helpful message."""
        from bce.ai.models import ModelManager

        config = BceConfig(enable_ai_features=False)
        set_default_config(config)

        manager = ModelManager()

        with pytest.raises(ConfigurationError) as exc_info:
            manager.get_embedding_model()

        assert "AI features are disabled" in str(exc_info.value)
        assert "enable_ai_features" in str(exc_info.value)

    def test_missing_openai_key_error_message(self):
        """Test missing OpenAI key error has helpful message."""
        from bce.ai.models import ModelManager
        import sys

        os.environ.pop("OPENAI_API_KEY", None)

        manager = ModelManager()

        # Create mock openai module
        mock_openai_module = MagicMock()
        mock_openai_module.OpenAI = MagicMock()

        with patch.dict(sys.modules, {"openai": mock_openai_module}):
            with pytest.raises(ConfigurationError) as exc_info:
                manager._get_openai_client()

            assert "OPENAI_API_KEY" in str(exc_info.value)

    def test_missing_anthropic_key_error_message(self):
        """Test missing Anthropic key error has helpful message."""
        from bce.ai.models import ModelManager
        import sys

        os.environ.pop("ANTHROPIC_API_KEY", None)

        manager = ModelManager()

        # Create mock anthropic module
        mock_anthropic_module = MagicMock()
        mock_anthropic_module.Anthropic = MagicMock()

        with patch.dict(sys.modules, {"anthropic": mock_anthropic_module}):
            with pytest.raises(ConfigurationError) as exc_info:
                manager._get_anthropic_client()

            assert "ANTHROPIC_API_KEY" in str(exc_info.value)


class TestModelManagerCaching:
    """Tests for model caching behavior."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = BceConfig(
            data_root=Path(self.temp_dir),
            enable_ai_features=True,
        )
        set_default_config(self.config)

        from bce.ai.models import reset_model_manager

        reset_model_manager()

    def teardown_method(self):
        """Clean up after tests."""
        reset_default_config()

        from bce.ai.models import reset_model_manager

        reset_model_manager()

        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_embedding_model_loaded_once(self):
        """Test embedding model is only loaded once."""
        from bce.ai.models import ModelManager

        mock_model = MagicMock()
        mock_transformer = MagicMock(return_value=mock_model)

        manager = ModelManager()

        with patch("bce.ai.models.SentenceTransformer", mock_transformer):
            # Call multiple times
            model1 = manager.get_embedding_model()
            model2 = manager.get_embedding_model()
            model3 = manager.get_embedding_model()

            # Should all be same instance
            assert model1 is model2 is model3

            # Constructor called only once
            assert mock_transformer.call_count == 1

    def test_reset_clears_cache_for_reloading(self):
        """Test reset allows model to be reloaded."""
        from bce.ai.models import ModelManager

        mock_model1 = MagicMock()
        mock_model2 = MagicMock()
        call_count = 0

        def create_model(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return mock_model1 if call_count == 1 else mock_model2

        manager = ModelManager()

        with patch("bce.ai.models.SentenceTransformer", side_effect=create_model):
            # Load first time
            model1 = manager.get_embedding_model()
            assert model1 is mock_model1

            # Reset
            manager.reset()

            # Load again - should create new instance
            model2 = manager.get_embedding_model()
            assert model2 is mock_model2
            assert model1 is not model2

    def test_global_manager_caches_across_calls(self):
        """Test global manager maintains cache across calls."""
        from bce.ai.models import get_model_manager

        mock_model = MagicMock()
        mock_transformer = MagicMock(return_value=mock_model)

        with patch("bce.ai.models.SentenceTransformer", mock_transformer):
            # Get manager and load model
            manager1 = get_model_manager()
            model1 = manager1.get_embedding_model()

            # Get manager again (should be same instance)
            manager2 = get_model_manager()
            model2 = manager2.get_embedding_model()

            assert manager1 is manager2
            assert model1 is model2
            assert mock_transformer.call_count == 1


class TestModelManagerEdgeCases:
    """Tests for edge cases and unusual scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = BceConfig(
            data_root=Path(self.temp_dir),
            enable_ai_features=True,
        )
        set_default_config(self.config)

        from bce.ai.models import reset_model_manager

        reset_model_manager()

    def teardown_method(self):
        """Clean up after tests."""
        reset_default_config()

        from bce.ai.models import reset_model_manager

        reset_model_manager()

        for key in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"]:
            os.environ.pop(key, None)

        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_backend_case_sensitivity(self):
        """Test backend names are case-sensitive."""
        from bce.ai.models import ModelManager

        manager = ModelManager()

        # Lowercase "openai" should work (once we add the key)
        os.environ["OPENAI_API_KEY"] = "test-key"
        mock_openai = MagicMock()
        mock_openai.OpenAI = MagicMock(return_value=MagicMock())

        with patch("bce.ai.models.openai", mock_openai):
            manager.get_llm_client(backend="openai")  # Should work

        # Uppercase should fail
        with pytest.raises(ConfigurationError, match="Unknown backend: OPENAI"):
            manager.get_llm_client(backend="OPENAI")

    def test_empty_backend_string(self):
        """Test empty backend string raises error."""
        from bce.ai.models import ModelManager

        manager = ModelManager()

        with pytest.raises(ConfigurationError, match="Unknown backend"):
            manager.get_llm_client(backend="")

    def test_none_backend_uses_default(self):
        """Test None backend uses configured default."""
        from bce.ai.models import ModelManager

        config = BceConfig(
            enable_ai_features=True, ai_model_backend="openai"
        )
        set_default_config(config)
        os.environ["OPENAI_API_KEY"] = "test-key"

        manager = ModelManager()
        mock_client = MagicMock()
        mock_openai = MagicMock()
        mock_openai.OpenAI = MagicMock(return_value=mock_client)

        with patch("bce.ai.models.openai", mock_openai):
            result = manager.get_llm_client(backend=None)
            assert result is mock_client

    def test_whitespace_in_api_key(self):
        """Test API keys with whitespace are preserved."""
        from bce.ai.models import ModelManager

        # API key with leading/trailing whitespace
        os.environ["OPENAI_API_KEY"] = "  key-with-spaces  "

        manager = ModelManager()
        mock_client = MagicMock()
        mock_openai = MagicMock()
        mock_openai.OpenAI = MagicMock(return_value=mock_client)

        with patch("bce.ai.models.openai", mock_openai):
            manager._get_openai_client()

            # Should be called with whitespace preserved
            mock_openai.OpenAI.assert_called_once_with(api_key="  key-with-spaces  ")

    def test_model_manager_thread_safety_basic(self):
        """Basic test for model manager in concurrent scenario."""
        from bce.ai.models import get_model_manager

        # This is a basic test - true thread safety would require threading
        managers = [get_model_manager() for _ in range(10)]

        # All should be same instance
        assert all(m is managers[0] for m in managers)
