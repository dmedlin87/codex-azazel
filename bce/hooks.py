"""
Hooks and Events System for BCE

This module provides a comprehensive extensibility system that allows users
to hook into BCE's data lifecycle without modifying core code.

Example usage:
    >>> from bce.hooks import hook, HookPoint
    >>>
    >>> @hook(HookPoint.BEFORE_CHARACTER_SAVE)
    >>> def auto_tag_apostles(ctx):
    ...     char = ctx.data
    ...     if "apostle" in char.roles and "apostle" not in char.tags:
    ...         char.tags.append("apostle")
    ...     ctx.data = char
    ...     return ctx
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class HookPoint(Enum):
    """Enumeration of all available hook points in BCE"""

    # Data lifecycle hooks
    BEFORE_CHARACTER_LOAD = "before_character_load"
    AFTER_CHARACTER_LOAD = "after_character_load"
    BEFORE_CHARACTER_SAVE = "before_character_save"
    AFTER_CHARACTER_SAVE = "after_character_save"
    BEFORE_EVENT_LOAD = "before_event_load"
    AFTER_EVENT_LOAD = "after_event_load"
    BEFORE_EVENT_SAVE = "before_event_save"
    AFTER_EVENT_SAVE = "after_event_save"

    # Validation hooks
    BEFORE_VALIDATION = "before_validation"
    AFTER_VALIDATION = "after_validation"
    VALIDATION_ERROR = "validation_error"

    # Query hooks
    BEFORE_QUERY = "before_query"
    AFTER_QUERY = "after_query"
    CACHE_MISS = "cache_miss"
    CACHE_HIT = "cache_hit"

    # Export hooks
    BEFORE_EXPORT = "before_export"
    AFTER_EXPORT = "after_export"
    EXPORT_FORMAT_RESOLVE = "export_format_resolve"

    # Dossier hooks
    BEFORE_DOSSIER_BUILD = "before_dossier_build"
    AFTER_DOSSIER_BUILD = "after_dossier_build"
    DOSSIER_ENRICH = "dossier_enrich"

    # Search hooks
    BEFORE_SEARCH = "before_search"
    AFTER_SEARCH = "after_search"
    SEARCH_RESULT_FILTER = "search_result_filter"
    SEARCH_RESULT_RANK = "search_result_rank"

    # Conflict detection hooks
    BEFORE_CONFLICT_DETECTION = "before_conflict_detection"
    AFTER_CONFLICT_DETECTION = "after_conflict_detection"
    CONFLICT_SEVERITY_SCORE = "conflict_severity_score"

    # System hooks
    STARTUP = "startup"
    SHUTDOWN = "shutdown"
    CONFIG_CHANGE = "config_change"


@dataclass
class HookContext:
    """
    Context object passed to hook handlers

    Attributes:
        hook_point: The hook point that triggered this context
        data: The primary data being processed (can be modified by handlers)
        metadata: Additional context metadata (read-only recommended)
        abort: Set to True to abort the current operation
    """

    hook_point: HookPoint
    data: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    abort: bool = False

    def __repr__(self) -> str:
        return (
            f"HookContext(hook_point={self.hook_point}, "
            f"data_type={type(self.data).__name__}, "
            f"abort={self.abort})"
        )


class HookRegistry:
    """
    Global registry for hook handlers

    This class manages registration and triggering of hooks throughout BCE.
    Handlers are executed in priority order (lower priority numbers execute first).
    """

    _handlers: Dict[HookPoint, List[tuple[int, Callable]]] = {}
    _enabled: bool = True

    @classmethod
    def register(
        cls, hook_point: HookPoint, handler: Callable, priority: int = 100
    ) -> None:
        """
        Register a hook handler

        Args:
            hook_point: The hook point to register for
            handler: Callable that takes HookContext and returns modified context
            priority: Lower numbers run first (0-999, default 100)

        Example:
            >>> def my_handler(ctx: HookContext) -> HookContext:
            ...     print(f"Hook triggered: {ctx.hook_point}")
            ...     return ctx
            >>> HookRegistry.register(HookPoint.BEFORE_CHARACTER_LOAD, my_handler)
        """
        if hook_point not in cls._handlers:
            cls._handlers[hook_point] = []

        cls._handlers[hook_point].append((priority, handler))
        cls._handlers[hook_point].sort(key=lambda x: x[0])

        logger.debug(
            f"Registered handler for {hook_point.value} with priority {priority}"
        )

    @classmethod
    def unregister(cls, hook_point: HookPoint, handler: Callable) -> None:
        """
        Unregister a hook handler

        Args:
            hook_point: The hook point to unregister from
            handler: The handler to remove

        Example:
            >>> HookRegistry.unregister(HookPoint.BEFORE_CHARACTER_LOAD, my_handler)
        """
        if hook_point in cls._handlers:
            original_count = len(cls._handlers[hook_point])
            cls._handlers[hook_point] = [
                (p, h) for p, h in cls._handlers[hook_point] if h != handler
            ]
            removed = original_count - len(cls._handlers[hook_point])
            if removed > 0:
                logger.debug(f"Unregistered handler from {hook_point.value}")

    @classmethod
    def trigger(
        cls, hook_point: HookPoint, data: Any = None, **metadata
    ) -> HookContext:
        """
        Trigger all handlers for a hook point

        Handlers are executed in priority order. If any handler sets context.abort
        to True, execution stops and the context is returned immediately.

        Args:
            hook_point: The hook to trigger
            data: Data to pass to handlers (will be in context.data)
            **metadata: Additional context metadata (will be in context.metadata)

        Returns:
            HookContext with potentially modified data

        Example:
            >>> ctx = HookRegistry.trigger(
            ...     HookPoint.BEFORE_CHARACTER_SAVE,
            ...     data=character,
            ...     char_id="jesus"
            ... )
            >>> if ctx.abort:
            ...     print("Operation aborted by hook")
            >>> else:
            ...     # Use ctx.data (potentially modified character)
            ...     save_to_disk(ctx.data)
        """
        if not cls._enabled:
            return HookContext(hook_point, data, metadata)

        context = HookContext(hook_point, data, metadata)

        handlers = cls._handlers.get(hook_point, [])
        if handlers:
            logger.debug(
                f"Triggering {len(handlers)} handlers for {hook_point.value}"
            )

        for priority, handler in handlers:
            try:
                context = handler(context)
                if context.abort:
                    logger.info(
                        f"Hook {hook_point.value} aborted operation "
                        f"(handler priority {priority})"
                    )
                    break
            except Exception as e:
                # Log but don't crash - hooks shouldn't break core functionality
                logger.error(
                    f"Hook {hook_point.value} handler (priority {priority}) "
                    f"failed: {e}",
                    exc_info=True,
                )

        return context

    @classmethod
    def clear_all(cls) -> None:
        """
        Clear all registered hooks

        This is primarily useful for testing to ensure a clean state.
        """
        cls._handlers = {}
        logger.debug("Cleared all registered hooks")

    @classmethod
    def enable(cls) -> None:
        """Enable the hook system"""
        cls._enabled = True
        logger.debug("Hook system enabled")

    @classmethod
    def disable(cls) -> None:
        """
        Disable the hook system

        When disabled, HookRegistry.trigger() will return immediately without
        executing any handlers. This can be useful for performance-critical
        sections or testing.
        """
        cls._enabled = False
        logger.debug("Hook system disabled")

    @classmethod
    def is_enabled(cls) -> bool:
        """Check if hook system is enabled"""
        return cls._enabled

    @classmethod
    def list_handlers(cls, hook_point: Optional[HookPoint] = None) -> Dict:
        """
        List registered handlers

        Args:
            hook_point: Optional hook point to filter by

        Returns:
            Dict mapping hook points to handler counts

        Example:
            >>> handlers = HookRegistry.list_handlers()
            >>> print(f"Total hooks: {sum(handlers.values())}")
        """
        if hook_point:
            count = len(cls._handlers.get(hook_point, []))
            return {hook_point.value: count}

        return {
            hp.value: len(handlers) for hp, handlers in cls._handlers.items()
        }


def hook(hook_point: HookPoint, priority: int = 100):
    """
    Decorator to register a function as a hook handler

    This provides a convenient way to register hooks without explicitly
    calling HookRegistry.register().

    Args:
        hook_point: The hook point to register for
        priority: Handler priority (lower runs first, default 100)

    Returns:
        Decorator function

    Example:
        >>> @hook(HookPoint.BEFORE_CHARACTER_SAVE, priority=50)
        >>> def validate_character(ctx):
        ...     if not ctx.data.canonical_name:
        ...         ctx.abort = True
        ...     return ctx
    """

    def decorator(func: Callable) -> Callable:
        HookRegistry.register(hook_point, func, priority)
        return func

    return decorator


# Convenience functions for common patterns


def create_abort_hook(hook_point: HookPoint, condition: Callable) -> Callable:
    """
    Create a hook that aborts operation if condition returns True

    Args:
        hook_point: Hook point to register for
        condition: Function that takes context.data and returns bool

    Returns:
        Hook handler function

    Example:
        >>> # Prevent saving characters without names
        >>> abort_hook = create_abort_hook(
        ...     HookPoint.BEFORE_CHARACTER_SAVE,
        ...     lambda char: not char.canonical_name
        ... )
    """

    def handler(ctx: HookContext) -> HookContext:
        if condition(ctx.data):
            ctx.abort = True
            logger.info(f"Operation aborted by condition at {hook_point.value}")
        return ctx

    HookRegistry.register(hook_point, handler)
    return handler


def create_transform_hook(
    hook_point: HookPoint, transform: Callable, priority: int = 100
) -> Callable:
    """
    Create a hook that transforms data

    Args:
        hook_point: Hook point to register for
        transform: Function that takes and returns data
        priority: Handler priority

    Returns:
        Hook handler function

    Example:
        >>> # Auto-uppercase all character names
        >>> transform_hook = create_transform_hook(
        ...     HookPoint.AFTER_CHARACTER_LOAD,
        ...     lambda char: char._replace(
        ...         canonical_name=char.canonical_name.upper()
        ...     )
        ... )
    """

    def handler(ctx: HookContext) -> HookContext:
        try:
            ctx.data = transform(ctx.data)
        except Exception as e:
            logger.error(f"Transform hook failed: {e}")
        return ctx

    HookRegistry.register(hook_point, handler, priority)
    return handler
