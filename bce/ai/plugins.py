"""
Hook-driven AI plugins.

The plugins here are intentionally lightweight: they reuse existing semantic
search outputs and dossier data rather than introducing new model dependencies.
Activation is controlled through BceConfig (enable_hooks + ai_plugins list).
"""

from __future__ import annotations

from typing import Any, Dict, List

from ..config import get_default_config
from ..hooks import HookPoint, HookRegistry
from ..queries import get_character

_PLUGINS_LOADED = False


def ensure_ai_plugins_loaded() -> None:
    """Register plugins based on configuration."""
    global _PLUGINS_LOADED
    if _PLUGINS_LOADED:
        return

    config = get_default_config()
    if not getattr(config, "enable_hooks", False):
        return

    desired = set(getattr(config, "ai_plugins", []) or [])
    if not desired:
        return

    if "search_ranking" in desired:
        HookRegistry.register(HookPoint.SEARCH_RESULT_RANK, _search_ranking_plugin, priority=50)
    if "tag_suggestions" in desired:
        HookRegistry.register(HookPoint.AFTER_SEARCH, _tag_suggestion_plugin, priority=90)
    if "role_sanity" in desired:
        HookRegistry.register(HookPoint.AFTER_QA, _role_sanity_plugin, priority=90)

    _PLUGINS_LOADED = True


def _search_ranking_plugin(ctx):
    """Re-rank results by target type alignment and field weighting."""
    results: List[Dict[str, Any]] = ctx.data or []
    plan = ctx.metadata.get("plan") or {}
    target_type = plan.get("target_type")
    if not target_type:
        return results

    def _score(item: Dict[str, Any]) -> float:
        base = item.get("relevance_score", 0.0)
        if item.get("type") == target_type:
            base += 0.05
        return base

    sorted_results = sorted(results, key=_score, reverse=True)
    ctx.record("search_ranking: boosted matches for target type")
    return sorted_results


def _tag_suggestion_plugin(ctx):
    """Attach suggested tags derived from matching context snippets."""
    results: List[Dict[str, Any]] = ctx.data or []
    enriched: List[Dict[str, Any]] = []

    for item in results:
        snippet = (item.get("matching_context") or "").lower()
        suggestions = []
        for keyword in ("disciple", "apostle", "miracle", "teaching", "conflict"):
            if keyword in snippet:
                suggestions.append(keyword)
        if suggestions:
            item = dict(item)
            item["suggested_tags"] = suggestions
        enriched.append(item)

    if enriched:
        ctx.record("tag_suggestions: derived tags from snippets")
    return enriched


def _role_sanity_plugin(ctx):
    """Flag QA answers where a character is missing expected roles."""
    payload = ctx.data or {}
    answers = payload.get("answers") or []
    flagged = []
    for ans in answers:
        if ans.get("type") != "character":
            continue
        char_id = ans.get("id")
        roles = ans.get("identity", {}).get("roles")
        if roles is None:
            try:
                character = get_character(char_id)
            except Exception:
                continue
            roles = character.roles
        if not roles:
            flagged.append(char_id)

    if flagged:
        payload = dict(payload)
        payload.setdefault("explanation", {})
        notes = payload["explanation"].get("notes", [])
        notes = list(notes) if isinstance(notes, list) else []
        notes.append(f"Role sanity check: {', '.join(flagged)} missing roles")
        payload["explanation"]["notes"] = notes
        ctx.record("role_sanity: flagged missing roles")
    return payload


__all__ = ["ensure_ai_plugins_loaded"]
