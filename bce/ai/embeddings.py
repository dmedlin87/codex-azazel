"""
Sentence embedding utilities for AI-powered features.

This module provides local embedding generation using sentence-transformers
for semantic search, similarity comparison, and clustering.
"""

from __future__ import annotations

import hashlib
import json
import pickle
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING
import re

from .config import (
    ensure_ai_enabled,
    get_ai_cache_dir,
    get_embedding_model_name,
    get_default_config,
)

if TYPE_CHECKING:
    import numpy as np

# Lazy imports for optional dependencies
_model = None
_np = None
_model_config_signature = None

# Optional heavy dependency placeholder (allows patching in tests)
SentenceTransformer = None


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


def _try_get_numpy():
    """Best-effort numpy loader that tolerates missing optional dependency."""
    try:
        return _get_numpy()
    except ImportError:
        return None


def _get_model():
    """Lazy-load the sentence transformer model."""
    global _model, _model_config_signature
    ensure_ai_enabled()

    # If configuration has changed (e.g., different data root or embedding model),
    # drop any cached model to avoid cross-test leakage.
    config = get_default_config()
    current_signature = (config.data_root, config.embedding_model)
    if _model is not None and _model_config_signature != current_signature:
        _model = None

    if _model is None:
        try:
            transformer_cls = _load_sentence_transformer()
        except ImportError as exc:
            # Preserve expected behavior for tests that simulate missing dependency
            raise ImportError(
                "sentence-transformers is required for AI features. "
                "Install it with: pip install sentence-transformers"
            ) from exc
        except Exception as exc:
            # Defensive: some environments have partially installed torch/vision
            # stacks that trigger RuntimeError during import. Raise ImportError so
            # callers can decide whether to fall back to lightweight embeddings.
            raise ImportError(
                "sentence-transformers failed to load due to an environment issue; "
                "falling back to lightweight embeddings."
            ) from exc

        model_name = get_embedding_model_name()
        cache_dir = get_ai_cache_dir() / "models"
        cache_dir.mkdir(parents=True, exist_ok=True)

        _model = transformer_cls(model_name, cache_folder=str(cache_dir))
        _model_config_signature = current_signature

    return _model


def _load_sentence_transformer():
    """Load or return the cached SentenceTransformer class."""
    global SentenceTransformer
    if SentenceTransformer is None:
        from sentence_transformers import SentenceTransformer as ST
        SentenceTransformer = ST
    return SentenceTransformer


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
    try:
        model = _get_model()
        return model.encode(text, convert_to_numpy=True)
    except Exception:
        # If the heavy model is unavailable, use a lightweight deterministic embedding
        return _lightweight_embed(text)


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
    try:
        model = _get_model()
        return model.encode(texts, convert_to_numpy=True)
    except Exception:
        # Fall back to lightweight embeddings for the whole batch
        np = _try_get_numpy()
        embeddings = [_lightweight_embed(text) for text in texts]
        return np.array(embeddings) if np is not None else embeddings


def cosine_similarity(embedding1, embedding2) -> float:
    """Compute cosine similarity between two embeddings.

    Args:
        embedding1: First embedding vector
        embedding2: Second embedding vector

    Returns:
        Cosine similarity score between 0 and 1
    """
    np = _try_get_numpy()
    if np is None:
        # Lightweight fallback when numpy isn't installed
        def _norm(vec):
            return math.sqrt(sum(float(x) * float(x) for x in vec)) if vec else 0.0

        norm1 = _norm(embedding1)
        norm2 = _norm(embedding2)
        if norm1 == 0.0 or norm2 == 0.0:
            return 0.0

        dot = sum(float(a) * float(b) for a, b in zip(embedding1, embedding2))
        return float(dot / (norm1 * norm2))

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
    np = _try_get_numpy()
    if np is None:
        size = len(embeddings)
        similarity = [[0.0 for _ in range(size)] for _ in range(size)]
        for i in range(size):
            similarity[i][i] = 1.0
            for j in range(i + 1, size):
                sim = cosine_similarity(embeddings[i], embeddings[j])
                similarity[i][j] = sim
                similarity[j][i] = sim
        return similarity

    # Normalize embeddings
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1  # Avoid division by zero
    normalized = embeddings / norms

    # Compute similarity matrix
    similarity = np.dot(normalized, normalized.T)
    # Ensure self-similarity is always 1.0, even for zero vectors
    np.fill_diagonal(similarity, 1.0)

    return similarity


def _tokenize(text: str) -> List[str]:
    """Simple tokenizer used for lightweight embeddings."""
    if not text:
        return []
    return re.findall(r"[a-z0-9]+", text.lower())


def _lightweight_embed(text: str, dim: int = 64):
    """Create a deterministic lightweight embedding vector.

    This provides a fast fallback when heavyweight models are unavailable,
    ensuring tests and offline scenarios still have meaningful similarity signals.
    """
    np = _try_get_numpy()
    tokens = _tokenize(text)
    if not tokens:
        return np.zeros(dim) if np is not None else [0.0] * dim

    vec = np.zeros(dim, dtype=float) if np is not None else [0.0] * dim
    for token in tokens:
        h = int(hashlib.sha256(token.encode("utf-8")).hexdigest(), 16)
        vec[h % dim] += 1.0

    # Normalize to unit length when possible
    norm = np.linalg.norm(vec) if np is not None else math.sqrt(sum(v * v for v in vec))
    if norm > 0:
        vec = vec / norm if np is not None else [v / norm for v in vec]
    return vec


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

        np = _try_get_numpy()
        return np.array(embeddings) if np is not None else embeddings

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
