"""
Contrastive, schema-aware QA built on top of semantic search.

This module keeps heavy lifting inside existing embeddings and indexes while
adding:
- A question compiler that maps natural-language questions onto BCE scopes
  (traits, relationships, accounts) and intent (lookup vs. contrastive).
- A contrastive answer builder that surfaces top answers alongside nearest
  alternatives, plus explanation metadata suitable for UI widgets.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .. import queries
from ..hooks import HookRegistry, HookPoint
from .config import ensure_ai_enabled
from .semantic_search import (
    compile_semantic_query,
    query as semantic_query,
    CompiledQuery,
)
from .plugins import ensure_ai_plugins_loaded


@dataclass
class QAPlan:
    """Structured plan for answering a natural-language question."""

    question: str
    mode: str
    scope: List[str]
    target_type: Optional[str] = None
    focus: List[str] = field(default_factory=list)
    contrast_focus: List[str] = field(default_factory=list)
    min_score: float = 0.25

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "mode": self.mode,
            "scope": self.scope,
            "target_type": self.target_type,
            "focus": self.focus,
            "contrast_focus": self.contrast_focus,
            "min_score": self.min_score,
        }


def compile_question(question: str) -> QAPlan:
    """Compile a question into a QAPlan aligned with BCE schemas."""
    normalized = question.strip().lower()
    scope = ["traits", "relationships", "accounts"]
    focus: List[str] = []
    contrast_focus: List[str] = []
    mode = "lookup"
    target_type: Optional[str] = None

    if any(word in normalized for word in ["compare", "versus", "vs", "most", "least"]):
        mode = "contrastive"
        contrast_focus.append("ranking")

    if "relationship" in normalized or "related" in normalized:
        focus.append("relationships")
        target_type = target_type or "character"
    if "role" in normalized or "office" in normalized:
        focus.append("roles")
        target_type = target_type or "character"
    if "tag" in normalized or "#" in normalized:
        focus.append("tags")
    if "event" in normalized or "timeline" in normalized or "account" in normalized:
        focus.append("accounts")
        target_type = target_type or "event"
    if "who" in normalized and target_type is None:
        target_type = "character"

    return QAPlan(
        question=question,
        mode=mode,
        scope=scope,
        target_type=target_type,
        focus=focus,
        contrast_focus=list(set(contrast_focus)),
    )


def answer(
    question: str,
    top_k: int = 3,
    contrast_k: int = 2,
    min_score: float = 0.25,
    use_cache: bool = True,
) -> Dict[str, Any]:
    """Provide a structured, explainable answer with contrastive context."""
    ensure_ai_enabled()
    ensure_ai_plugins_loaded()

    plan = compile_question(question)
    plan.min_score = max(plan.min_score, min_score)

    compiled_query: CompiledQuery = compile_semantic_query(
        question, scope=plan.scope
    )
    compiled_query.min_score = plan.min_score

    raw_results = semantic_query(
        question,
        top_k=top_k + contrast_k,
        scope=compiled_query.scope,
        min_score=compiled_query.min_score,
        use_cache=use_cache,
    )

    primary = raw_results[:top_k]
    contrast = raw_results[top_k : top_k + contrast_k]

    enriched_primary = [_enrich_result(r, plan) for r in primary]
    enriched_contrast = [_enrich_result(r, plan) for r in contrast]

    explanation = _build_explanation(plan, enriched_primary, enriched_contrast)

    response = {
        "question": question,
        "plan": plan.to_dict(),
        "compiled_query": compiled_query.to_dict(),
        "answers": enriched_primary,
        "contrast_set": enriched_contrast,
        "explanation": explanation,
    }

    final_ctx = HookRegistry.trigger(
        HookPoint.AFTER_QA,
        response,
        plan=plan.to_dict(),
    )

    return final_ctx.data or response


def _enrich_result(result: Dict[str, Any], plan: QAPlan) -> Dict[str, Any]:
    """Attach lightweight evidence to a semantic search result."""
    enriched = dict(result)
    entity_type = result.get("type")
    entity_id = result.get("id")

    if entity_type == "character":
        character = queries.get_character(entity_id)
        enriched["evidence"] = _collect_character_evidence(character, plan.focus)
        enriched["identity"] = {
            "id": character.id,
            "canonical_name": character.canonical_name,
            "roles": character.roles,
            "tags": character.tags,
        }
    elif entity_type == "event":
        event = queries.get_event(entity_id)
        enriched["evidence"] = _collect_event_evidence(event, plan.focus)
        enriched["identity"] = {
            "id": event.id,
            "label": event.label,
            "tags": event.tags,
        }
    else:
        enriched["evidence"] = []

    return enriched


def _collect_character_evidence(character, focus: List[str]) -> List[Dict[str, Any]]:
    evidence: List[Dict[str, Any]] = []
    focus_set = set(focus) if focus else {"traits", "roles", "relationships", "tags"}

    if "traits" in focus_set:
        for profile in character.source_profiles[:2]:
            for trait_key, trait_val in list(profile.traits.items())[:2]:
                evidence.append(
                    {
                        "type": "trait",
                        "source": profile.source_id,
                        "trait": trait_key,
                        "value": trait_val,
                        "reference": ", ".join(profile.references)
                        if profile.references
                        else None,
                    }
                )

    if "roles" in focus_set and character.roles:
        evidence.append(
            {
                "type": "roles",
                "roles": character.roles[:5],
            }
        )

    if "relationships" in focus_set and character.relationships:
        for rel in character.relationships[:2]:
            evidence.append(
                {
                    "type": "relationship",
                    "relationship_type": getattr(rel, "type", None)
                    or getattr(rel, "relationship_type", None),
                    "to": getattr(rel, "target_id", None)
                    or getattr(rel, "character_id", None)
                    or getattr(rel, "to", None),
                    "description": getattr(rel, "description", None)
                    or getattr(rel, "notes", None),
                }
            )

    if "tags" in focus_set and character.tags:
        evidence.append({"type": "tags", "tags": character.tags[:8]})

    return evidence


def _collect_event_evidence(event, focus: List[str]) -> List[Dict[str, Any]]:
    evidence: List[Dict[str, Any]] = []
    focus_set = set(focus) if focus else {"accounts", "tags"}

    if "accounts" in focus_set:
        for account in event.accounts[:3]:
            evidence.append(
                {
                    "type": "account",
                    "source": account.source_id,
                    "reference": account.reference,
                    "summary": account.summary,
                    "notes": account.notes,
                }
            )

    if "tags" in focus_set and event.tags:
        evidence.append({"type": "tags", "tags": event.tags[:8]})

    return evidence


def _build_explanation(
    plan: QAPlan,
    answers: List[Dict[str, Any]],
    contrast: List[Dict[str, Any]],
) -> Dict[str, Any]:
    if not answers:
        return {
            "summary": "No confident answer found.",
            "reasoning": "All candidates scored below the minimum threshold.",
            "what_if": [],
        }

    top = answers[0]
    summary_parts = [
        f"Top answer: {top.get('id')} ({top.get('type')}) with score {top.get('relevance_score')}",
    ]

    secondary: List[str] = []
    if plan.mode == "contrastive" and contrast:
        secondary.append(f"Contrast set includes {len(contrast)} close alternative(s).")

    if top.get("evidence"):
        primary_evidence = top["evidence"][0]
        if primary_evidence.get("type") == "trait":
            summary_parts.append(
                f"Anchored on trait '{primary_evidence.get('trait')}' from {primary_evidence.get('source')}."
            )
        elif primary_evidence.get("type") == "account":
            summary_parts.append(
                f"Anchored on account {primary_evidence.get('reference')} ({primary_evidence.get('source')})."
            )

    what_if = []
    if plan.focus:
        what_if.append(
            {
                "toggle": "broaden_scope",
                "description": "Broaden scope to all fields to surface peripheral matches.",
            }
        )
    else:
        what_if.append(
            {
                "toggle": "tighten_scope",
                "description": "Focus on relationships or tags to get more precise contrast.",
            }
        )

    return {
        "summary": " ".join(summary_parts + secondary),
        "reasoning": {
            "mode": plan.mode,
            "focus": plan.focus,
            "contrast_focus": plan.contrast_focus,
        },
        "what_if": what_if,
    }


__all__ = ["QAPlan", "compile_question", "answer"]
