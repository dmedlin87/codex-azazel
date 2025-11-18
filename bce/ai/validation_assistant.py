"""
Smart validation suggestions using AI.

This module provides AI-powered suggestions for fixing validation errors.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ..queries import list_all_characters, list_all_events
from ..storage import list_character_ids, list_event_ids
from ..validation import validate_all
from .cache import AIResultCache
from .config import ensure_ai_enabled
from .embeddings import cosine_similarity, embed_texts, EmbeddingCache


def suggest_fixes(
    errors: Optional[List[str]] = None,
    use_cache: bool = True,
) -> List[Dict[str, Any]]:
    """Generate AI-powered suggestions for validation errors.

    Args:
        errors: List of validation error messages (if None, runs validate_all())
        use_cache: Whether to use cached results (default: True)

    Returns:
        List of suggestion dictionaries with:
        - error: The original error message
        - suggestion: Suggested fix
        - confidence: Confidence score (0.0 to 1.0)
        - similar_items: List of similar existing items (if applicable)

    Raises:
        ConfigurationError: If AI features are disabled
    """
    ensure_ai_enabled()

    if errors is None:
        errors = validate_all()

    if not errors:
        return []

    # Check cache first (cache by error set hash)
    cache_key = _hash_error_list(errors)
    if use_cache:
        cache = AIResultCache("validation_suggestions", max_age_seconds=86400)
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return cached_result

    suggestions = []

    for error in errors:
        suggestion = _suggest_fix_for_error(error)
        if suggestion:
            suggestions.append(suggestion)

    # Cache the result
    if use_cache:
        cache.set(cache_key, suggestions, model_name="validation_assistant")

    return suggestions


def _hash_error_list(errors: List[str]) -> str:
    """Create a stable hash for a list of errors."""
    import hashlib
    error_str = "|".join(sorted(errors))
    return hashlib.sha256(error_str.encode()).hexdigest()[:16]


def _suggest_fix_for_error(error: str) -> Optional[Dict[str, Any]]:
    """Generate suggestion for a single validation error.

    Uses pattern matching and semantic similarity to suggest fixes.
    """
    # Pattern 1: Character/Event not found errors
    if "references unknown character" in error.lower():
        return _suggest_missing_character_fix(error)
    elif "references unknown event" in error.lower():
        return _suggest_missing_event_fix(error)

    # Pattern 2: Invalid reference format
    elif "invalid scripture reference" in error.lower():
        return _suggest_reference_fix(error)

    # Pattern 3: Missing required field
    elif "missing required field" in error.lower():
        return _suggest_missing_field_fix(error)

    # Pattern 4: JSON loading errors
    elif "failed to load" in error.lower():
        return _suggest_json_fix(error)

    # Generic suggestion
    else:
        return {
            "error": error,
            "suggestion": "Review the error message and consult the documentation.",
            "confidence": 0.3,
            "similar_items": [],
        }


def _suggest_missing_character_fix(error: str) -> Dict[str, Any]:
    """Suggest fix for missing character reference."""
    # Extract the referenced character ID from error
    # Example: "Event 'foo' references unknown character 'bar'"
    import re

    match = re.search(r"unknown character ['\"](\w+)['\"]", error)
    if not match:
        return {
            "error": error,
            "suggestion": "Check the character ID spelling and ensure it matches an existing character file.",
            "confidence": 0.5,
            "similar_items": [],
        }

    referenced_id = match.group(1)

    # Find similar character IDs
    all_char_ids = list_character_ids()
    similar_ids = _find_similar_ids(referenced_id, all_char_ids)

    if similar_ids:
        suggestion = (
            f"Character '{referenced_id}' not found. "
            f"Did you mean one of these: {', '.join(similar_ids[:3])}? "
            f"Or create a new character file at bce/data/characters/{referenced_id}.json"
        )
        confidence = 0.85
    else:
        suggestion = (
            f"Character '{referenced_id}' not found. "
            f"Create a new character file at bce/data/characters/{referenced_id}.json "
            f"or remove the reference if it's not needed."
        )
        confidence = 0.70

    return {
        "error": error,
        "suggestion": suggestion,
        "confidence": confidence,
        "similar_items": similar_ids[:5],
    }


def _suggest_missing_event_fix(error: str) -> Dict[str, Any]:
    """Suggest fix for missing event reference."""
    import re

    match = re.search(r"unknown event ['\"](\w+)['\"]", error)
    if not match:
        return {
            "error": error,
            "suggestion": "Check the event ID spelling and ensure it matches an existing event file.",
            "confidence": 0.5,
            "similar_items": [],
        }

    referenced_id = match.group(1)

    # Find similar event IDs
    all_event_ids = list_event_ids()
    similar_ids = _find_similar_ids(referenced_id, all_event_ids)

    if similar_ids:
        suggestion = (
            f"Event '{referenced_id}' not found. "
            f"Did you mean one of these: {', '.join(similar_ids[:3])}? "
            f"Or create a new event file at bce/data/events/{referenced_id}.json"
        )
        confidence = 0.85
    else:
        suggestion = (
            f"Event '{referenced_id}' not found. "
            f"Create a new event file at bce/data/events/{referenced_id}.json "
            f"or remove the reference if it's not needed."
        )
        confidence = 0.70

    return {
        "error": error,
        "suggestion": suggestion,
        "confidence": confidence,
        "similar_items": similar_ids[:5],
    }


def _suggest_reference_fix(error: str) -> Dict[str, Any]:
    """Suggest fix for invalid scripture reference."""
    return {
        "error": error,
        "suggestion": (
            "Scripture references should follow the format: 'Book Chapter:Verse' "
            "or 'Book Chapter:StartVerse-EndVerse'. "
            "Examples: 'John 3:16', 'Matthew 5:1-12', 'Romans 8:28-30'"
        ),
        "confidence": 0.90,
        "similar_items": [],
    }


def _suggest_missing_field_fix(error: str) -> Dict[str, Any]:
    """Suggest fix for missing required field."""
    import re

    match = re.search(r"missing required field ['\"](\w+)['\"]", error, re.IGNORECASE)
    if match:
        field_name = match.group(1)
        suggestion = (
            f"Add the required field '{field_name}' to the JSON file. "
            f"Consult docs/DATA_ENTRY_GUIDE.md for the correct schema."
        )
        confidence = 0.85
    else:
        suggestion = (
            "Ensure all required fields are present in the JSON file. "
            "Consult docs/DATA_ENTRY_GUIDE.md for the correct schema."
        )
        confidence = 0.70

    return {
        "error": error,
        "suggestion": suggestion,
        "confidence": confidence,
        "similar_items": [],
    }


def _suggest_json_fix(error: str) -> Dict[str, Any]:
    """Suggest fix for JSON loading errors."""
    if "expecting property name" in error.lower():
        suggestion = (
            "JSON syntax error: Check for missing commas, extra commas, "
            "or incorrectly formatted property names. All property names must be in double quotes."
        )
        confidence = 0.80
    elif "expecting value" in error.lower():
        suggestion = (
            "JSON syntax error: Check for trailing commas or missing values. "
            "Ensure all fields have valid values (strings in quotes, numbers, booleans, arrays, or objects)."
        )
        confidence = 0.80
    else:
        suggestion = (
            "JSON parsing error. Common issues: "
            "1) Trailing commas in arrays/objects, "
            "2) Unescaped quotes in strings, "
            "3) Missing closing brackets/braces. "
            "Use a JSON validator to identify the exact issue."
        )
        confidence = 0.70

    return {
        "error": error,
        "suggestion": suggestion,
        "confidence": confidence,
        "similar_items": [],
    }


def _find_similar_ids(target_id: str, candidate_ids: List[str], top_k: int = 5) -> List[str]:
    """Find IDs similar to target using semantic similarity and string matching.

    Args:
        target_id: The ID to match
        candidate_ids: List of candidate IDs
        top_k: Number of top matches to return

    Returns:
        List of similar IDs, sorted by similarity
    """
    if not candidate_ids:
        return []

    # Use string-based similarity (Levenshtein distance approximation)
    def similarity_score(id1: str, id2: str) -> float:
        """Simple similarity based on shared substrings."""
        id1_lower = id1.lower()
        id2_lower = id2.lower()

        # Exact match
        if id1_lower == id2_lower:
            return 1.0

        # One is substring of other
        if id1_lower in id2_lower or id2_lower in id1_lower:
            return 0.8

        # Shared prefix
        common_prefix_len = 0
        for c1, c2 in zip(id1_lower, id2_lower):
            if c1 == c2:
                common_prefix_len += 1
            else:
                break

        if common_prefix_len > 0:
            return 0.5 + (common_prefix_len / max(len(id1), len(id2))) * 0.3

        # Count common characters
        set1 = set(id1_lower)
        set2 = set(id2_lower)
        common = set1 & set2
        union = set1 | set2

        return len(common) / len(union) if union else 0.0

    # Score all candidates
    scored = [(cand, similarity_score(target_id, cand)) for cand in candidate_ids]

    # Filter out low scores and sort
    filtered = [(cand, score) for cand, score in scored if score > 0.3]
    filtered.sort(key=lambda x: x[1], reverse=True)

    # Return top-k IDs
    return [cand for cand, score in filtered[:top_k]]


__all__ = [
    "suggest_fixes",
]
