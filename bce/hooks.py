"""
Lightweight hook registry for pluggable extensions.

The registry is intentionally small: it provides a handful of hook points used
by the semantic search and QA layers so AI plugins can adjust ranking, suggest
tags, or sanity-check roles without touching core claim/curation logic.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from .config import get_default_config


class HookPoint(str, Enum):
    BEFORE_SEARCH = "before_search"
    SEARCH_RESULT_RANK = "search_result_rank"
    AFTER_SEARCH = "after_search"
    AFTER_QA = "after_qa"


@dataclass
class HookContext:
    """Context object passed to hook handlers."""

    hook_point: HookPoint
    data: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)
    artifacts: Dict[str, Any] = field(default_factory=dict)

    def record(self, note: str) -> None:
        self.notes.append(note)

    def add_artifact(self, key: str, value: Any) -> None:
        self.artifacts[key] = value


class HookRegistry:
    """Global registry for hook handlers."""

    _handlers: Dict[HookPoint, List[Tuple[int, Callable[[HookContext], Any]]]] = {}

    @classmethod
    def _hooks_enabled(cls) -> bool:
        config = get_default_config()
        return getattr(config, "enable_hooks", False)

    @classmethod
    def register(cls, hook_point: HookPoint, handler: Callable[[HookContext], Any], priority: int = 100) -> None:
        """Register a hook handler."""
        cls._handlers.setdefault(hook_point, []).append((priority, handler))
        cls._handlers[hook_point].sort(key=lambda x: x[0])

    @classmethod
    def unregister(cls, hook_point: HookPoint, handler: Callable[[HookContext], Any]) -> None:
        """Unregister a hook handler."""
        if hook_point in cls._handlers:
            cls._handlers[hook_point] = [
                (p, h) for p, h in cls._handlers[hook_point] if h != handler
            ]

    @classmethod
    def trigger(cls, hook_point: HookPoint, data: Any = None, **metadata: Any) -> HookContext:
        """Trigger all handlers for a hook point."""
        context = HookContext(hook_point, data, metadata)
        if not cls._hooks_enabled():
            return context

        for priority, handler in cls._handlers.get(hook_point, []):
            try:
                result = handler(context)
                if result is not None:
                    context.data = result
            except Exception as exc:  # pragma: no cover - defensive logging
                logging.error("Hook %s handler failed: %s", hook_point, exc)
        return context

    @classmethod
    def clear(cls) -> None:
        """Clear all registered hooks."""
        cls._handlers.clear()


def hook(hook_point: HookPoint, priority: int = 100):
    """Decorator to register a function as a hook handler."""

    def decorator(func):
        HookRegistry.register(hook_point, func, priority)
        return func

    return decorator


__all__ = ["HookPoint", "HookContext", "HookRegistry", "hook"]

