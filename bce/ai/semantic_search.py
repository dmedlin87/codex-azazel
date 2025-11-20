"""
Semantic search using sentence embeddings.

This module enhances the basic keyword search with semantic understanding,
enabling conceptual queries that match meaning rather than just keywords.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..queries import get_character, get_event, list_all_characters, list_all_events
from .cache import AIResultCache
from .config import ensure_ai_enabled
from .embeddings import cosine_similarity, EmbeddingCache


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

    if scope is None:
        scope = ["traits", "relationships", "accounts"]

    # Build or retrieve search index
    index = _build_search_index(scope, use_cache=use_cache)

    # Embed the query
    embedding_cache = EmbeddingCache("semantic_search_queries")
    query_embedding = embedding_cache.get_or_compute(search_query)

    # Compute similarities
    results = []
    for item in index:
        similarity = cosine_similarity(query_embedding, item["embedding"])

        if similarity >= min_score:
            results.append({
                "type": item["type"],
                "id": item["id"],
                "relevance_score": round(similarity, 3),
                "matching_context": item["text"][:200],  # Truncate for display
                "match_in": item["field"],
                "explanation": _explain_match(
                    search_query, item["text"], similarity, item["type"], item["id"]
                ),
            })

    # Sort by relevance and return top-k
    results.sort(key=lambda x: x["relevance_score"], reverse=True)
    return results[:top_k]


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
                    text = f"{rel.get('type', 'relationship')} with {rel.get('to', 'unknown')}: {rel.get('description', '')}"
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
            desc = rel.get("description", "")
            if desc:
                texts.append(desc)
            else:
                # Fall back to combining type/target when description is missing
                rel_type = rel.get("type") or rel.get("relationship_type")
                target = rel.get("to") or rel.get("character_id")
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
]
