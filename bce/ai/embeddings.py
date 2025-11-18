"""
Sentence embedding utilities for AI-powered features.

This module provides local embedding generation using sentence-transformers
for semantic search, similarity comparison, and clustering.
"""

from __future__ import annotations

import hashlib
import json
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .config import ensure_ai_enabled, get_ai_cache_dir, get_embedding_model_name

if TYPE_CHECKING:
    import numpy as np

# Lazy imports for optional dependencies
_model = None
_np = None


def _get_numpy():
    """Lazy-load numpy."""
    global _np
    if _np is None:
        try:
            import numpy
            _np = numpy
        except ImportError:
            raise ImportError(
                "numpy is required for AI features. "
                "Install it with: pip install 'codex-azazel[ai]'"
            )
    return _np


def _get_model():
    """Lazy-load the sentence transformer model."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "sentence-transformers is required for AI features. "
                "Install it with: pip install sentence-transformers"
            )

        model_name = get_embedding_model_name()
        cache_dir = get_ai_cache_dir() / "models"
        cache_dir.mkdir(parents=True, exist_ok=True)

        _model = SentenceTransformer(model_name, cache_folder=str(cache_dir))

    return _model


def embed_text(text: str):
    """Generate embedding for a single text string.

    Args:
        text: The text to embed

    Returns:
        Numpy array containing the embedding vector

    Raises:
        ConfigurationError: If AI features are disabled
        ImportError: If sentence-transformers is not installed
    """
    ensure_ai_enabled()
    model = _get_model()
    return model.encode(text, convert_to_numpy=True)


def embed_texts(texts: List[str]):
    """Generate embeddings for multiple text strings.

    Args:
        texts: List of texts to embed

    Returns:
        Numpy array of shape (len(texts), embedding_dim) containing embeddings

    Raises:
        ConfigurationError: If AI features are disabled
        ImportError: If sentence-transformers is not installed
    """
    ensure_ai_enabled()
    model = _get_model()
    return model.encode(texts, convert_to_numpy=True)


def cosine_similarity(embedding1, embedding2) -> float:
    """Compute cosine similarity between two embeddings.

    Args:
        embedding1: First embedding vector
        embedding2: Second embedding vector

    Returns:
        Cosine similarity score between 0 and 1
    """
    np = _get_numpy()
    # Normalize vectors
    norm1 = np.linalg.norm(embedding1)
    norm2 = np.linalg.norm(embedding2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return float(np.dot(embedding1, embedding2) / (norm1 * norm2))


def compute_similarity_matrix(embeddings):
    """Compute pairwise cosine similarity matrix for a set of embeddings.

    Args:
        embeddings: Array of shape (n, embedding_dim)

    Returns:
        Similarity matrix of shape (n, n)
    """
    np = _get_numpy()
    # Normalize embeddings
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1  # Avoid division by zero
    normalized = embeddings / norms

    # Compute similarity matrix
    similarity = np.dot(normalized, normalized.T)

    return similarity


class EmbeddingCache:
    """Cache for storing and retrieving pre-computed embeddings."""

    def __init__(self, cache_name: str):
        """Initialize embedding cache.

        Args:
            cache_name: Name for this cache (e.g., "character_traits", "event_accounts")
        """
        self.cache_name = cache_name
        self.cache_dir = get_ai_cache_dir() / "embeddings"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / f"{cache_name}.pkl"
        self._cache: Dict[str, Any] = {}
        self._load_cache()

    def _load_cache(self) -> None:
        """Load cache from disk if it exists."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "rb") as f:
                    self._cache = pickle.load(f)
            except Exception:
                # If cache is corrupted, start fresh
                self._cache = {}

    def _save_cache(self) -> None:
        """Save cache to disk."""
        with open(self.cache_file, "wb") as f:
            pickle.dump(self._cache, f)

    def _hash_text(self, text: str) -> str:
        """Create hash key for text."""
        return hashlib.sha256(text.encode()).hexdigest()

    def get(self, text: str):
        """Get cached embedding for text.

        Args:
            text: The text to look up

        Returns:
            Cached embedding if available, None otherwise
        """
        key = self._hash_text(text)
        return self._cache.get(key)

    def set(self, text: str, embedding) -> None:
        """Cache embedding for text.

        Args:
            text: The text
            embedding: The embedding to cache
        """
        key = self._hash_text(text)
        self._cache[key] = embedding
        self._save_cache()

    def get_or_compute(self, text: str):
        """Get cached embedding or compute and cache it.

        Args:
            text: The text to embed

        Returns:
            The embedding vector
        """
        cached = self.get(text)
        if cached is not None:
            return cached

        embedding = embed_text(text)
        self.set(text, embedding)
        return embedding

    def get_or_compute_batch(self, texts: List[str]):
        """Get cached embeddings or compute and cache missing ones.

        Args:
            texts: List of texts to embed

        Returns:
            Array of embeddings
        """
        np = _get_numpy()
        embeddings = []
        missing_indices = []
        missing_texts = []

        # Check cache for each text
        for i, text in enumerate(texts):
            cached = self.get(text)
            if cached is not None:
                embeddings.append(cached)
            else:
                embeddings.append(None)
                missing_indices.append(i)
                missing_texts.append(text)

        # Compute missing embeddings in batch
        if missing_texts:
            new_embeddings = embed_texts(missing_texts)
            for i, idx in enumerate(missing_indices):
                embeddings[idx] = new_embeddings[i]
                self.set(missing_texts[i], new_embeddings[i])

        return np.array(embeddings)

    def clear(self) -> None:
        """Clear all cached embeddings."""
        self._cache = {}
        if self.cache_file.exists():
            self.cache_file.unlink()

    def size(self) -> int:
        """Get number of cached embeddings."""
        return len(self._cache)


__all__ = [
    "embed_text",
    "embed_texts",
    "cosine_similarity",
    "compute_similarity_matrix",
    "EmbeddingCache",
]
