"""
AI-specific caching infrastructure.

This module provides caching for AI-generated analyses and results.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

from .config import get_ai_cache_dir


@dataclass
class CachedResult:
    """Container for cached AI analysis results."""

    result: Any
    timestamp: float = field(default_factory=time.time)
    model_name: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self, max_age_seconds: float) -> bool:
        """Check if cached result has expired.

        Args:
            max_age_seconds: Maximum age in seconds

        Returns:
            True if expired, False otherwise
        """
        age = time.time() - self.timestamp
        return age > max_age_seconds

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "result": self.result,
            "timestamp": self.timestamp,
            "model_name": self.model_name,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CachedResult:
        """Create from dictionary."""
        return cls(
            result=data["result"],
            timestamp=data["timestamp"],
            model_name=data.get("model_name", ""),
            metadata=data.get("metadata", {}),
        )


class AIResultCache:
    """Cache for AI analysis results (contradictions, completeness audits, etc.)."""

    def __init__(self, cache_name: str, max_age_seconds: float = 86400):
        """Initialize AI result cache.

        Args:
            cache_name: Name for this cache (e.g., "semantic_contradictions")
            max_age_seconds: Maximum age for cached results (default: 24 hours)
        """
        self.cache_name = cache_name
        self.max_age_seconds = max_age_seconds
        self.cache_dir = get_ai_cache_dir() / "results"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / f"{cache_name}.json"
        self._cache: Dict[str, CachedResult] = {}
        self._load_cache()

    def _load_cache(self) -> None:
        """Load cache from disk if it exists."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r") as f:
                    data = json.load(f)
                    self._cache = {
                        key: CachedResult.from_dict(value)
                        for key, value in data.items()
                    }
            except Exception:
                # If cache is corrupted, start fresh
                self._cache = {}

    def _save_cache(self) -> None:
        """Save cache to disk."""
        data = {key: value.to_dict() for key, value in self._cache.items()}
        with open(self.cache_file, "w") as f:
            json.dump(data, f, indent=2)

    def get(self, key: str) -> Optional[Any]:
        """Get cached result if available and not expired.

        Args:
            key: Cache key

        Returns:
            Cached result if available and fresh, None otherwise
        """
        if key not in self._cache:
            return None

        cached = self._cache[key]
        if cached.is_expired(self.max_age_seconds):
            # Remove expired entry
            del self._cache[key]
            self._save_cache()
            return None

        return cached.result

    def set(
        self,
        key: str,
        result: Any,
        model_name: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Cache result.

        Args:
            key: Cache key
            result: The result to cache
            model_name: Name of the model used
            metadata: Additional metadata
        """
        self._cache[key] = CachedResult(
            result=result,
            model_name=model_name,
            metadata=metadata or {},
        )
        self._save_cache()

    def invalidate(self, key: str) -> None:
        """Invalidate specific cached result.

        Args:
            key: Cache key to invalidate
        """
        if key in self._cache:
            del self._cache[key]
            self._save_cache()

    def clear(self) -> None:
        """Clear all cached results."""
        self._cache = {}
        if self.cache_file.exists():
            self.cache_file.unlink()

    def size(self) -> int:
        """Get number of cached results."""
        return len(self._cache)

    def prune_expired(self) -> int:
        """Remove all expired entries.

        Returns:
            Number of entries removed
        """
        expired_keys = [
            key
            for key, cached in self._cache.items()
            if cached.is_expired(self.max_age_seconds)
        ]

        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            self._save_cache()

        return len(expired_keys)


def invalidate_character_caches(char_id: str) -> None:
    """Invalidate all AI caches related to a character.

    This should be called when character data is updated.

    Args:
        char_id: The character ID
    """
    cache_names = [
        "semantic_contradictions",
        "completeness_audit",
        "validation_suggestions",
    ]

    for cache_name in cache_names:
        cache = AIResultCache(cache_name)
        cache.invalidate(char_id)


def invalidate_event_caches(event_id: str) -> None:
    """Invalidate all AI caches related to an event.

    This should be called when event data is updated.

    Args:
        event_id: The event ID
    """
    cache_names = [
        "semantic_contradictions",
        "parallel_detection",
    ]

    for cache_name in cache_names:
        cache = AIResultCache(cache_name)
        cache.invalidate(event_id)


def clear_all_ai_caches() -> None:
    """Clear all AI caches (embeddings and results)."""
    cache_dir = get_ai_cache_dir()
    if cache_dir.exists():
        # Clear all cache files
        for cache_file in cache_dir.rglob("*.pkl"):
            cache_file.unlink()
        for cache_file in cache_dir.rglob("*.json"):
            cache_file.unlink()


def cached_analysis(ttl_hours: float = 24, namespace: str = "default"):
    """Decorator for caching AI analysis results.

    Args:
        ttl_hours: Time-to-live in hours (default: 24)
        namespace: Cache namespace (default: "default")

    Returns:
        Decorated function that caches results
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Create cache key from function name and args
            cache_key = f"{func.__name__}_{str(args)}_{str(kwargs)}"

            # Check cache
            cache = AIResultCache(namespace, max_age_seconds=ttl_hours * 3600)
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Call function
            result = func(*args, **kwargs)

            # Cache result
            cache.set(cache_key, result, model_name=func.__name__)

            return result

        return wrapper
    return decorator


__all__ = [
    "CachedResult",
    "AIResultCache",
    "invalidate_character_caches",
    "invalidate_event_caches",
    "clear_all_ai_caches",
    "cached_analysis",
]
