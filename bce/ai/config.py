"""
AI feature configuration and utilities.

This module provides AI-specific configuration helpers and validation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from ..config import get_default_config
from ..exceptions import ConfigurationError


def ensure_ai_enabled() -> None:
    """Raise ConfigurationError if AI features are not enabled.

    This should be called at the entry point of all AI features.

    Raises:
        ConfigurationError: If enable_ai_features is False
    """
    config = get_default_config()
    if not config.enable_ai_features:
        raise ConfigurationError(
            "AI features are disabled. Enable them by setting enable_ai_features=True "
            "in BceConfig or by setting the BCE_ENABLE_AI_FEATURES environment variable."
        )


def get_ai_cache_dir() -> Path:
    """Get the AI cache directory, creating it if necessary.

    Returns:
        Path to the AI cache directory
    """
    config = get_default_config()
    cache_dir = config.ai_cache_dir
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def get_embedding_model_name() -> str:
    """Get the configured embedding model name.

    Returns:
        The embedding model name (e.g., "all-MiniLM-L6-v2")
    """
    config = get_default_config()
    return config.embedding_model


def get_ai_backend() -> str:
    """Get the configured AI backend.

    Returns:
        The AI backend: "local", "openai", or "anthropic"
    """
    config = get_default_config()
    return config.ai_model_backend


def validate_api_key(backend: str) -> Optional[str]:
    """Validate and retrieve API key for external backends.

    Args:
        backend: The backend name ("openai" or "anthropic")

    Returns:
        The API key if available, None otherwise

    Raises:
        ConfigurationError: If backend requires API key but none is found
    """
    import os

    if backend == "openai":
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise ConfigurationError(
                "OpenAI backend requires OPENAI_API_KEY environment variable"
            )
        return key
    elif backend == "anthropic":
        key = os.getenv("ANTHROPIC_API_KEY")
        if not key:
            raise ConfigurationError(
                "Anthropic backend requires ANTHROPIC_API_KEY environment variable"
            )
        return key

    return None


__all__ = [
    "ensure_ai_enabled",
    "get_ai_cache_dir",
    "get_embedding_model_name",
    "get_ai_backend",
    "validate_api_key",
]
