"""
Semantic search using sentence embeddings.

This module enhances the basic keyword search with semantic understanding,
enabling conceptual queries that match meaning rather than just keywords.

The module now includes a lightweight, schema-aware query compiler that maps
natural language to BCE search scopes (traits, relationships, accounts). It
produces a small plan object that can be used for guided UI experiences and
for hook-based ranking extensions without changing the legacy query shape.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Dict, List, Optional

from ..queries import get_character, get_event, list_all_characters, list_all_events
from ..hooks import HookPoint, HookRegistry
from .cache import AIResultCache
from .config import ensure_ai_enabled
from .embeddings import cosine_similarity, EmbeddingCache
from .plugins import ensure_ai_plugins_loaded

FIELD_ROOTS = {"traits", "relationships", "accounts"}


@dataclass
class QueryClause:
    """Single clause within a compiled semantic query."""

    field: str
    keywords: List[str] = field(default_factory=list)
    weight: float = 1.0
    reason: str = ""

    def applies_to(self, field_name: str) -> bool:
        root = field_name.split(".")[0]
        return self.field == root

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field": self.field,
            "keywords": self.keywords,
            "weight": self.weight,
            "reason": self.reason,
        }


@dataclass
class CompiledQuery:
    """Structured representation of a semantic search request."""

    raw: str
    normalized: str
    scope: List[str]
    target_type: Optional[str] = None
    clauses: List[QueryClause] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    hints: List[str] = field(default_factory=list)
    min_score: float = 0.3

    def get_field_weight(self, field_name: str) -> float:
        for clause in self.clauses:
            if clause.applies_to(field_name):
                return clause.weight
        return 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw": self.raw,
            "normalized": self.normalized,
            "scope": self.scope,
            "target_type": self.target_type,
            "clauses": [c.to_dict() for c in self.clauses],
            "tags": self.tags,
            "hints": self.hints,
            "min_score": self.min_score,
        }


def compile_semantic_query(search_query: str, scope: Optional[List[str]] = None) -> CompiledQuery:
    """Compile a natural language query into a structured search plan.

    The compiler inspects the query for schema-aligned hints such as
    "relationship", "trait", or "event timeline" and boosts the corresponding
    scopes while leaving the default behavior intact for legacy callers.
    """
    normalized = search_query.strip()
    lowered = normalized.lower()

    inferred_scope = scope or ["traits", "relationships", "accounts"]
    clauses: List[QueryClause] = []
    hints: List[str] = []
    tags = re.findall(r"#([a-z0-9_\-]+)", lowered)
    target_type: Optional[str] = None

    # Detect intent for specific fields
    if re.search(r"relationship|connected|related", lowered):
        clauses.append(QueryClause(field="relationships", weight=1.2, reason="relationship intent"))
        if "relationships" not in inferred_scope:
            inferred_scope.append("relationships")
        target_type = target_type or "character"
    if re.search(r"trait|characteristic|quality", lowered):
        clauses.append(QueryClause(field="traits", weight=1.15, reason="trait intent"))
    if re.search(r"event|account|timeline|when|where", lowered):
        clauses.append(QueryClause(field="accounts", weight=1.1, reason="event intent"))

    # Default clauses to keep weights predictable when no hints exist
    if not clauses:
        for field in inferred_scope:
            if field in FIELD_ROOTS:
                clauses.append(QueryClause(field=field, weight=1.0, reason="default scope weight"))

    # Target type inference
    if "character" in lowered or "who" in lowered:
        target_type = "character"
    if "event" in lowered or "where" in lowered or "when" in lowered:
        target_type = target_type or "event"

    # Extract lightweight keywords for later highlighting
    keyword_tokens = [t for t in re.findall(r"[a-z0-9_]+", lowered) if len(t) > 3]
    if keyword_tokens:
        clauses[0].keywords.extend(keyword_tokens[:5])
        hints.append("keyword_seeded")

    return CompiledQuery(
        raw=search_query,
        normalized=lowered,
        scope=inferred_scope,
        target_type=target_type,
        clauses=clauses,
        tags=tags,
        hints=hints,
    )


def query(
    search_query: str,
    top_k: int = 10,
    scope: Optional[List[str]] = None,
    min_score: float = 0.3,
    use_cache: bool = True,
) -> List[Dict[str, Any]]:
    """Perform semantic search across characters and events.

    Unlike keyword search which matches exact strings, semantic search
    understands conceptual similarity. For example, searching for
    "doubting disciples" will match Thomas even if the word "doubt"
    doesn't appear verbatim.

    Args:
        search_query: Natural language query
        top_k: Maximum number of results to return (default: 10)
        scope: List of fields to search in (default: ["traits", "relationships", "accounts"])
        min_score: Minimum similarity score (0.0-1.0, default: 0.3)
        use_cache: Whether to use cached search index (default: True)

    Returns:
        List of results, each containing:
        - type: "character" or "event"
        - id: The item ID
        - relevance_score: Similarity score (0.0-1.0)
        - matching_context: The text that matched
        - match_in: Which field matched
        - explanation: Why this result matched

    Raises:
        ConfigurationError: If AI features are disabled
        ImportError: If required AI dependencies are missing

    Example:
        >>> results = semantic_search.query("characters who experience transformation")
        >>> for result in results[:3]:
        ...     print(f"{result['id']}: {result['relevance_score']:.2f}")
        paul: 0.89
        peter: 0.76
        mary_magdalene: 0.68
    """
    ensure_ai_enabled()
    ensure_ai_plugins_loaded()

    if scope is None:
        scope = ["traits", "relationships", "accounts"]

    # Compile a schema-aware plan. The plan keeps default weights at 1.0 so
    # existing behavior is preserved unless the query contains explicit hints.
    compiled = compile_semantic_query(search_query, scope=scope)
    compiled.min_score = max(min_score, compiled.min_score)

    # Allow plugins to adjust plan or injected metadata
    HookRegistry.trigger(
        HookPoint.BEFORE_SEARCH,
        {"query": search_query},
        plan=compiled.to_dict(),
    )

    # Build or retrieve search index
    index = _build_search_index(compiled.scope, use_cache=use_cache)

    # Embed the query
    embedding_cache = EmbeddingCache("semantic_search_queries")
    query_embedding = embedding_cache.get_or_compute(search_query)

    # Compute similarities
    results = []
    for item in index:
        similarity = cosine_similarity(query_embedding, item["embedding"])
        field_root = item["field"].split(".")[0]
        field_weight = compiled.get_field_weight(field_root)
        weighted_score = similarity * field_weight

        if weighted_score >= compiled.min_score:
            results.append({
                "type": item["type"],
                "id": item["id"],
                "relevance_score": round(weighted_score, 3),
                "matching_context": item["text"][:200],  # Truncate for display
                "match_in": item["field"],
                "explanation": _explain_match(
                    search_query, item["text"], similarity, item["type"], item["id"]
                ),
                "score_details": {
                    "similarity": round(float(similarity), 4),
                    "field_weight": field_weight,
                },
                "plan": compiled.to_dict(),
            })

    # Sort by relevance
    results.sort(key=lambda x: x["relevance_score"], reverse=True)

    # Hook for custom ranking
    rank_ctx = HookRegistry.trigger(
        HookPoint.SEARCH_RESULT_RANK,
        results,
        plan=compiled.to_dict(),
        query=search_query,
    )
    ranked_results = rank_ctx.data or results

    final_ctx = HookRegistry.trigger(
        HookPoint.AFTER_SEARCH,
        ranked_results,
        plan=compiled.to_dict(),
        query=search_query,
    )

    return (final_ctx.data or ranked_results)[:top_k]


def _build_search_index(
    scope: List[str],
    use_cache: bool = True,
) -> List[Dict[str, Any]]:
    """Build searchable index of all characters and events.

    Args:
        scope: Fields to include in index
        use_cache: Whether to use cached index

    Returns:
        List of index entries with embeddings
    """
    # Check cache first
    cache_key = f"index_{'_'.join(sorted(scope))}"
    if use_cache:
        cache = AIResultCache("semantic_search_index", max_age_seconds=3600)
        cached_index = cache.get(cache_key)
        if cached_index is not None:
            return cached_index

    index = []
    embedding_cache = EmbeddingCache("semantic_search_index")

    # Index characters
    if "traits" in scope or "relationships" in scope:
        for char in list_all_characters():
            # Index traits
            if "traits" in scope:
                for profile in char.source_profiles:
                    for trait_key, trait_value in profile.traits.items():
                        text = f"{trait_key}: {trait_value}"
                        embedding = embedding_cache.get_or_compute(text)
                        index.append({
                            "type": "character",
                            "id": char.id,
                            "field": f"traits.{profile.source_id}.{trait_key}",
                            "text": text,
                            "embedding": embedding,
                        })

            # Index relationships
            if "relationships" in scope and char.relationships:
                for rel in char.relationships:
                    rel_type = getattr(rel, "type", None) or "relationship"
                    target = getattr(rel, "target_id", None) or getattr(rel, "character_id", None) or "unknown"
                    desc = getattr(rel, "description", None) or getattr(rel, "notes", "") or ""
                    text = f"{rel_type} with {target}: {desc}"
                    embedding = embedding_cache.get_or_compute(text)
                    index.append({
                        "type": "character",
                        "id": char.id,
                        "field": "relationships",
                        "text": text,
                        "embedding": embedding,
                    })

    # Index events
    if "accounts" in scope:
        for event in list_all_events():
            for account in event.accounts:
                text = f"{event.label}: {account.summary}"
                if account.notes:
                    text += f" ({account.notes})"
                embedding = embedding_cache.get_or_compute(text)
                index.append({
                    "type": "event",
                    "id": event.id,
                    "field": f"accounts.{account.source_id}",
                    "text": text,
                    "embedding": embedding,
                })

    # Cache the index
    if use_cache:
        cache = AIResultCache("semantic_search_index", max_age_seconds=3600)
        cache.set(cache_key, index, model_name="semantic_search")

    return index


def _explain_match(
    query: str,
    matched_text: str,
    score: float,
    item_type: str,
    item_id: str,
) -> str:
    """Generate human-readable explanation for why result matched.

    Args:
        query: The search query
        matched_text: The text that matched
        score: Similarity score
        item_type: "character" or "event"
        item_id: The item ID

    Returns:
        Explanation string
    """
    if score >= 0.8:
        strength = "Strong"
    elif score >= 0.6:
        strength = "Moderate"
    else:
        strength = "Weak"

    return (
        f"{strength} semantic match: Query '{query}' is conceptually similar to "
        f"content in {item_type} '{item_id}'"
    )


def find_similar_characters(
    char_id: str,
    top_k: int = 5,
    basis: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Find characters similar to a given character.

    Uses semantic embeddings of character traits to find conceptually
    similar characters.

    Args:
        char_id: The reference character ID
        top_k: Number of similar characters to return (default: 5)
        basis: Which fields to use for similarity (default: ["traits"])

    Returns:
        List of similar characters with similarity scores

    Raises:
        ConfigurationError: If AI features are disabled
    """
    ensure_ai_enabled()

    if basis is None:
        basis = ["traits"]

    character = get_character(char_id)
    all_characters = list_all_characters()

    # Collect text for reference character
    ref_texts = _collect_character_texts(character, basis)
    ref_text = " ".join(ref_texts)

    # Embed reference character
    embedding_cache = EmbeddingCache("character_similarity")
    ref_embedding = embedding_cache.get_or_compute(ref_text)

    # Compare with all other characters
    similarities = []
    for other_char in all_characters:
        if other_char.id == char_id:
            continue

        other_texts = _collect_character_texts(other_char, basis)
        other_text = " ".join(other_texts)
        other_embedding = embedding_cache.get_or_compute(other_text)

        similarity = cosine_similarity(ref_embedding, other_embedding)

        similarities.append({
            "character_id": other_char.id,
            "canonical_name": other_char.canonical_name,
            "similarity_score": round(similarity, 3),
        })

    # Sort and return top-k
    similarities.sort(key=lambda x: x["similarity_score"], reverse=True)
    return similarities[:top_k]


def _collect_character_texts(character, basis: List[str]) -> List[str]:
    """Collect text from character based on specified fields.

    Args:
        character: Character object
        basis: Fields to collect from

    Returns:
        List of text strings
    """
    texts = []

    if "traits" in basis:
        for profile in character.source_profiles:
            for trait_key, trait_value in profile.traits.items():
                texts.append(f"{trait_key}: {trait_value}")

    if "roles" in basis and character.roles:
        texts.append(" ".join(character.roles))

    if "relationships" in basis and character.relationships:
        for rel in character.relationships:
            desc = getattr(rel, "description", None) or getattr(rel, "notes", "")
            if desc:
                texts.append(desc)
            else:
                rel_type = getattr(rel, "type", None)
                target = getattr(rel, "target_id", None)
                parts = [str(v) for v in (rel_type, target) if v]
                if parts:
                    texts.append(" ".join(parts))

    if "tags" in basis and character.tags:
        texts.append(" ".join(character.tags))

    return texts


def find_similar_events(
    event_id: str,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """Find events similar to a given event.

    Uses semantic embeddings of event accounts to find conceptually
    similar events.

    Args:
        event_id: The reference event ID
        top_k: Number of similar events to return (default: 5)

    Returns:
        List of similar events with similarity scores

    Raises:
        ConfigurationError: If AI features are disabled
    """
    ensure_ai_enabled()

    event = get_event(event_id)
    all_events = list_all_events()

    # Collect text for reference event
    ref_text = " ".join([
        f"{acc.summary} {acc.notes or ''}" for acc in event.accounts
    ])

    # Embed reference event
    embedding_cache = EmbeddingCache("event_similarity")
    ref_embedding = embedding_cache.get_or_compute(ref_text)

    # Compare with all other events
    similarities = []
    for other_event in all_events:
        if other_event.id == event_id:
            continue

        other_text = " ".join([
            f"{acc.summary} {acc.notes or ''}" for acc in other_event.accounts
        ])
        other_embedding = embedding_cache.get_or_compute(other_text)

        similarity = cosine_similarity(ref_embedding, other_embedding)

        similarities.append({
            "event_id": other_event.id,
            "label": other_event.label,
            "similarity_score": round(similarity, 3),
        })

    # Sort and return top-k
    similarities.sort(key=lambda x: x["similarity_score"], reverse=True)
    return similarities[:top_k]


__all__ = [
    "query",
    "find_similar_characters",
    "find_similar_events",
    "compile_semantic_query",
    "CompiledQuery",
    "QueryClause",
]
