"""
Model loading and management for AI features.

This module provides utilities for loading and managing AI models
(local or API-based) used by BCE features.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
import sys

from .config import ensure_ai_enabled, get_ai_backend, validate_api_key
from ..exceptions import ConfigurationError
import importlib

# Optional imports for different backends - imported at module level for testability
# Some environments can have partially installed dependencies (e.g., torch/vision
# mismatches) that raise RuntimeError during import. We catch broad exceptions here
# and degrade gracefully so that the rest of the AI features can still operate
# using lightweight fallbacks.
try:  # pragma: no cover - exercised indirectly via tests
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None  # type: ignore

try:
    import openai
except ImportError:
    openai = None  # type: ignore

try:
    import anthropic
except ImportError:
    anthropic = None  # type: ignore


class ModelManager:
    """Manager for AI models across different backends."""

    def __init__(self):
        """Initialize model manager."""
        self._local_model = None
        self._api_client = None

    def get_embedding_model(self):
        """Get the sentence transformer model for embeddings.

        Returns:
            SentenceTransformer model instance

        Raises:
            ConfigurationError: If AI features are disabled
            ImportError: If sentence-transformers is not installed
        """
        ensure_ai_enabled()

        if self._local_model is None:
            if SentenceTransformer is None:
                raise ImportError(
                    "sentence-transformers is required for local AI features. "
                    "Install it with: pip install sentence-transformers"
                )

            from .config import get_ai_cache_dir, get_embedding_model_name

            model_name = get_embedding_model_name()
            cache_dir = get_ai_cache_dir() / "models"
            cache_dir.mkdir(parents=True, exist_ok=True)

            self._local_model = SentenceTransformer(
                model_name, cache_folder=str(cache_dir)
            )

        return self._local_model

    def get_llm_client(self, backend: Optional[str] = None):
        """Get LLM client for text generation tasks.

        Args:
            backend: Optional backend override ("openai", "anthropic", "local")

        Returns:
            LLM client instance

        Raises:
            ConfigurationError: If AI features are disabled or API key missing
            ImportError: If required client library is not installed
        """
        ensure_ai_enabled()

        if backend is None:
            backend = get_ai_backend()

        if backend == "openai":
            return self._get_openai_client()
        elif backend == "anthropic":
            return self._get_anthropic_client()
        elif backend == "local":
            return self._get_local_llm_client()
        else:
            raise ConfigurationError(f"Unknown backend: {backend}")

    def _get_openai_client(self):
        """Get OpenAI client."""
        openai_mod = openai
        if "openai" in sys.modules and sys.modules.get("openai") is None:
            openai_mod = None

        if openai_mod is None:
            try:
                openai_mod = importlib.import_module("openai")
            except ImportError:
                raise ImportError(
                    "openai is required for OpenAI backend. "
                    "Install it with: pip install openai"
                )

        api_key = validate_api_key("openai")
        return openai_mod.OpenAI(api_key=api_key)

    def _get_anthropic_client(self):
        """Get Anthropic client."""
        anthropic_mod = anthropic
        if "anthropic" in sys.modules and sys.modules.get("anthropic") is None:
            anthropic_mod = None

        if anthropic_mod is None:
            try:
                anthropic_mod = importlib.import_module("anthropic")
            except ImportError:
                raise ImportError(
                    "anthropic is required for Anthropic backend. "
                    "Install it with: pip install anthropic"
                )

        api_key = validate_api_key("anthropic")
        return anthropic_mod.Anthropic(api_key=api_key)

    def _get_local_llm_client(self):
        """Get local LLM client (e.g., via Ollama).

        Raises:
            NotImplementedError: Local LLM support is not yet implemented
        """
        # TODO: Implement local LLM support via Ollama or similar
        raise NotImplementedError(
            "Local LLM support is not yet implemented. "
            "Use 'openai' or 'anthropic' backend for now."
        )

    def reset(self) -> None:
        """Reset all loaded models (useful for testing)."""
        self._local_model = None
        self._api_client = None


# Global model manager instance
_manager: Optional[ModelManager] = None


def get_model_manager() -> ModelManager:
    """Get the global model manager instance.

    Returns:
        ModelManager instance
    """
    global _manager
    if _manager is None:
        _manager = ModelManager()
    return _manager


def reset_model_manager() -> None:
    """Reset the global model manager (useful for testing)."""
    global _manager
    if _manager is not None:
        _manager.reset()
    _manager = None


__all__ = [
    "ModelManager",
    "get_model_manager",
    "reset_model_manager",
]
