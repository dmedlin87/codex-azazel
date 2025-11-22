from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from .config import get_default_config

logger = logging.getLogger(__name__)

class HookPoint(Enum):
    """Enumeration of all available hook points"""
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
    
    # Legacy/AI hooks (kept for compatibility if needed)
    AFTER_QA = "after_qa"

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
    """Context object passed to hook handlers."""
    hook_point: HookPoint
    data: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    abort: bool = False
    
    # Helper fields for reporting/enrichment
    notes: List[str] = field(default_factory=list)
    artifacts: Dict[str, Any] = field(default_factory=dict)

    def record(self, note: str) -> None:
        self.notes.append(note)

    def add_artifact(self, key: str, value: Any) -> None:
        self.artifacts[key] = value


class HookRegistry:
    """Global registry for hook handlers."""

    _handlers: Dict[HookPoint, List[Tuple[int, Callable[[HookContext], HookContext]]]] = {}
    _enabled: bool = True

    @classmethod
    def _hooks_enabled_in_config(cls) -> bool:
        # Check both global switch and config
        if not cls._enabled:
            return False
        try:
            config = get_default_config()
            # Default to True if not specified, or respect config
            return getattr(config, "enable_hooks", True)
        except Exception:
            return cls._enabled

    @classmethod
    def register(cls, hook_point: HookPoint, handler: Callable[[HookContext], HookContext], priority: int = 100) -> None:
        """
        Register a hook handler.
        
        Args:
            hook_point: The hook point to register for
            handler: Callable that takes HookContext and returns modified context
            priority: Lower numbers run first (0-999, default 100)
        """
        if hook_point not in cls._handlers:
            cls._handlers[hook_point] = []
        cls._handlers[hook_point].append((priority, handler))
        cls._handlers[hook_point].sort(key=lambda x: x[0])

    @classmethod
    def unregister(cls, hook_point: HookPoint, handler: Callable[[HookContext], HookContext]) -> None:
        """Unregister a hook handler."""
        if hook_point in cls._handlers:
            cls._handlers[hook_point] = [
                (p, h) for p, h in cls._handlers[hook_point] if h != handler
            ]

    @classmethod
    def trigger(cls, hook_point: HookPoint, data: Any = None, **metadata: Any) -> HookContext:
        """
        Trigger all handlers for a hook point.
        
        Args:
            hook_point: The hook to trigger
            data: Data to pass to handlers
            **metadata: Additional context metadata
            
        Returns:
            HookContext with potentially modified data
        """
        context = HookContext(hook_point=hook_point, data=data, metadata=metadata)

        if not cls._hooks_enabled_in_config():
            return context

        handlers = cls._handlers.get(hook_point, [])
        if not handlers:
            return context

        for priority, handler in handlers:
            try:
                # Support handlers that return context AND handlers that return data (legacy compat)
                result = handler(context)
                
                if isinstance(result, HookContext):
                    context = result
                elif result is not None:
                    # Assume legacy handler returning data
                    context.data = result
                
                if context.abort:
                    break
            except Exception as e:
                logger.error(f"Hook {hook_point} handler failed: {e}", exc_info=True)

        return context

    @classmethod
    def clear(cls) -> None:
        """Clear all registered hooks."""
        cls._handlers = {}
    
    @classmethod
    def clear_all(cls) -> None:
        """Alias for clear()"""
        cls.clear()

    @classmethod
    def enable(cls) -> None:
        """Enable hook system."""
        cls._enabled = True

    @classmethod
    def disable(cls) -> None:
        """Disable hook system."""
        cls._enabled = False


def hook(hook_point: HookPoint, priority: int = 100) -> Callable[[Callable], Callable]:
    """Decorator to register a function as a hook handler."""
    def decorator(func: Callable) -> Callable:
        HookRegistry.register(hook_point, func, priority)
        return func
    return decorator

__all__ = ["HookPoint", "HookContext", "HookRegistry", "hook"]
