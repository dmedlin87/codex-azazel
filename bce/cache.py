from __future__ import annotations

from typing import Callable, List

from .exceptions import CacheError


class CacheRegistry:
    """Registry for cache invalidation callbacks.

    This pattern decouples storage operations from query caching by allowing
    cache invalidators to register themselves. When data changes, the registry
    can invalidate all registered caches without direct module dependencies.

    This replaces the fragile sys.modules inspection pattern previously used
    in storage.py.

    Examples:
        >>> # Register a cache invalidator
        >>> CacheRegistry.register(my_cache.clear)
        >>>
        >>> # Later, when data changes:
        >>> CacheRegistry.invalidate_all()
    """

    _invalidators: List[Callable[[], None]] = []

    @classmethod
    def register(cls, invalidator: Callable[[], None]) -> None:
        """Register a cache invalidation callback.

        Parameters:
            invalidator: A callable that takes no arguments and clears a cache

        Raises:
            CacheError: If invalidator is not callable
        """
        if not callable(invalidator):
            raise CacheError(f"Invalidator must be callable, got {type(invalidator)}")

        if invalidator not in cls._invalidators:
            cls._invalidators.append(invalidator)

    @classmethod
    def unregister(cls, invalidator: Callable[[], None]) -> None:
        """Unregister a cache invalidation callback.

        Parameters:
            invalidator: The callback to remove

        Raises:
            CacheError: If invalidator was not registered
        """
        try:
            cls._invalidators.remove(invalidator)
        except ValueError:
            raise CacheError(f"Invalidator {invalidator} was not registered")

    @classmethod
    def invalidate_all(cls) -> None:
        """Invalidate all registered caches.

        Calls each registered invalidator in registration order.
        If an invalidator fails, the error is propagated and remaining
        invalidators are not called.
        """
        for invalidator in cls._invalidators:
            invalidator()

    @classmethod
    def clear_registry(cls) -> None:
        """Clear all registered invalidators.

        This is primarily useful for testing to reset state between tests.
        """
        cls._invalidators.clear()

    @classmethod
    def count(cls) -> int:
        """Return the number of registered invalidators.

        Returns:
            Number of registered cache invalidators
        """
        return len(cls._invalidators)
