"""Question answering over BCE data using semantic search and structured retrieval.

This module provides natural language question answering capabilities that
retrieve and analyze BCE data to answer questions about characters, events,
sources, and their relationships.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import re

from .. import queries, contradictions
from ..exceptions import ConfigurationError
from .config import ensure_ai_enabled
from .embeddings import embed_text, cosine_similarity
from .cache import cached_analysis


def ask(question: str, use_cache: bool = True) -> Dict[str, Any]:
    """Answer a natural language question about BCE data.

    Uses semantic search to find relevant data, then structures a response
    with evidence citations and confidence scores.

    Parameters
    ----------
    question : str
        Natural language question
    use_cache : bool, optional
        Whether to use cached results (default: True)

    Returns
    -------
    dict
        Answer with keys: answer, confidence, evidence, comparison

    Raises
    ------
    ConfigurationError
        If AI features are disabled

    Examples
    --------
    >>> from bce.ai import question_answering
    >>> result = question_answering.ask("Which gospels portray Jesus as most divine?")
    >>> print(result["answer"])
    >>> print(result["evidence"])
    """
    ensure_ai_enabled()

    if use_cache:
        return _cached_ask(question)
    else:
        return _ask_impl(question)


@cached_analysis(ttl_hours=24, namespace="qa")
def _cached_ask(question: str) -> Dict[str, Any]:
    """Cached wrapper for ask."""
    return _ask_impl(question)


def _ask_impl(question: str) -> Dict[str, Any]:
    """Internal implementation of question answering."""
    # Determine question type
    q_type = _classify_question(question)

    if q_type == "character_comparison":
        return _answer_character_comparison(question)
    elif q_type == "source_analysis":
        return _answer_source_analysis(question)
    elif q_type == "trait_query":
        return _answer_trait_query(question)
    elif q_type == "relationship_query":
        return _answer_relationship_query(question)
    elif q_type == "event_query":
        return _answer_event_query(question)
    else:
        return _answer_general(question)


def _classify_question(question: str) -> str:
    """Classify question type to route to appropriate handler."""
    q_lower = question.lower()

    # Character comparison patterns
    if any(word in q_lower for word in ["which gospel", "which source", "most", "least"]):
        if any(word in q_lower for word in ["divine", "human", "messianic", "authoritative"]):
            return "character_comparison"

    # Source analysis patterns
    if any(word in q_lower for word in ["gospel of", "acts", "paul", "epistles"]) and \
       any(word in q_lower for word in ["portray", "depict", "present", "emphasize"]):
        return "source_analysis"

    # Trait queries
    if any(word in q_lower for word in ["who", "which character"]) and \
       any(word in q_lower for word in ["trait", "characteristic", "quality"]):
        return "trait_query"

    # Relationship queries
    if any(word in q_lower for word in ["relationship", "related to", "connected to"]):
        return "relationship_query"

    # Event queries
    if any(word in q_lower for word in ["event", "happened", "when", "where"]):
        return "event_query"

    return "general"


def _answer_character_comparison(question: str) -> Dict[str, Any]:
    """Answer character comparison questions."""
    from .semantic_search import query as semantic_search

    # Search for relevant characters and traits
    results = semantic_search(question, top_k=10, scope=["traits"])

    # Extract character IDs
    char_ids = list(set(r["id"] for r in results if r["type"] == "character"))

    # Build evidence
    evidence = []
    for char_id in char_ids[:5]:  # Limit to top 5 characters
        char = queries.get_character(char_id)
        for profile in char.source_profiles:
            for trait_key, trait_val in profile.traits.items():
                evidence.append({
                    "character": char_id,
                    "source": profile.source_id,
                    "trait": trait_key,
                    "value": trait_val,
                    "reference": ", ".join(profile.references) if profile.references else None
                })

    # Build comparison if multiple sources
    comparison = {}
    if evidence:
        sources = list(set(e["source"] for e in evidence))
        for source in sources:
            source_evidence = [e for e in evidence if e["source"] == source]
            if source_evidence:
                comparison[source] = {
                    "character_count": len(set(e["character"] for e in source_evidence)),
                    "trait_count": len(source_evidence),
                }

    # Generate answer using evidence
    answer = _synthesize_answer(question, evidence, comparison)

    return {
        "answer": answer,
        "confidence": _calculate_confidence(evidence),
        "evidence": evidence[:10],  # Limit to top 10 pieces of evidence
        "comparison": comparison
    }


def _answer_source_analysis(question: str) -> Dict[str, Any]:
    """Answer questions about how sources portray characters/events."""
    # Extract source name from question
    source_patterns = ["gospel of (\\w+)", "(mark|matthew|luke|john)", "acts", "paul"]
    source_id = None
    for pattern in source_patterns:
        match = re.search(pattern, question.lower())
        if match:
            source_id = match.group(1) if match.group(1) else match.group(0)
            break

    if not source_id:
        return _answer_general(question)

    # Normalize source ID
    source_id = source_id.lower()
    if source_id in ["mark", "matthew", "luke", "john"]:
        pass  # Already normalized
    elif source_id == "paul":
        source_id = "paul_undisputed"

    # Find all characters with this source profile
    evidence = []
    for char in queries.list_all_characters():
        profile = char.get_source_profile(source_id)
        if profile:
            for trait_key, trait_val in profile.traits.items():
                evidence.append({
                    "character": char.id,
                    "source": source_id,
                    "trait": trait_key,
                    "value": trait_val,
                    "reference": ", ".join(profile.references) if profile.references else None
                })

    answer = f"The source '{source_id}' provides {len(evidence)} trait descriptions across {len(set(e['character'] for e in evidence))} characters."
    if evidence:
        # Find most common themes
        trait_keys = [e["trait"] for e in evidence]
        from collections import Counter
        common_traits = Counter(trait_keys).most_common(5)
        answer += f" Common themes include: {', '.join(t[0] for t in common_traits)}."

    return {
        "answer": answer,
        "confidence": 0.85 if evidence else 0.3,
        "evidence": evidence[:15],
        "comparison": {source_id: {"character_count": len(set(e["character"] for e in evidence))}}
    }


def _answer_trait_query(question: str) -> Dict[str, Any]:
    """Answer questions about character traits."""
    from .semantic_search import query as semantic_search

    results = semantic_search(question, top_k=8, scope=["traits"])

    evidence = []
    for result in results:
        if result["type"] == "character":
            char = queries.get_character(result["id"])
            # Extract source and trait from match_in (e.g., "traits.john.divine_claims")
            match_parts = result["match_in"].split(".")
            if len(match_parts) >= 3 and match_parts[0] == "traits":
                source_id = match_parts[1]
                trait_key = ".".join(match_parts[2:])

                profile = char.get_source_profile(source_id)
                if profile and trait_key in profile.traits:
                    evidence.append({
                        "character": char.id,
                        "source": source_id,
                        "trait": trait_key,
                        "value": profile.traits[trait_key],
                        "reference": ", ".join(profile.references) if profile.references else None
                    })

    # Generate answer
    if evidence:
        chars = list(set(e["character"] for e in evidence))
        answer = f"Found {len(chars)} character(s) matching the query: {', '.join(chars)}."
    else:
        answer = "No characters found matching the specified traits."

    return {
        "answer": answer,
        "confidence": _calculate_confidence(evidence),
        "evidence": evidence,
        "comparison": {}
    }


def _answer_relationship_query(question: str) -> Dict[str, Any]:
    """Answer questions about character relationships."""
    from .semantic_search import query as semantic_search

    results = semantic_search(question, top_k=5, scope=["relationships"])

    evidence = []
    for result in results:
        if result["type"] == "character":
            char = queries.get_character(result["id"])
            for rel in char.relationships:
                evidence.append({
                    "character": char.id,
                    "relationship_type": rel.get("type", "unknown"),
                    "to": rel.get("to", "unknown"),
                    "description": rel.get("description", ""),
                })

    if evidence:
        answer = f"Found {len(evidence)} relationship(s) matching the query."
    else:
        answer = "No relationships found matching the query."

    return {
        "answer": answer,
        "confidence": _calculate_confidence(evidence),
        "evidence": evidence,
        "comparison": {}
    }


def _answer_event_query(question: str) -> Dict[str, Any]:
    """Answer questions about events."""
    from .semantic_search import query as semantic_search

    results = semantic_search(question, top_k=5, scope=["accounts"])

    evidence = []
    for result in results:
        if result["type"] == "event":
            event = queries.get_event(result["id"])
            for account in event.accounts:
                evidence.append({
                    "event": event.id,
                    "source": account.source_id,
                    "reference": account.reference,
                    "summary": account.summary,
                    "notes": account.notes
                })

    if evidence:
        events = list(set(e["event"] for e in evidence))
        answer = f"Found {len(events)} event(s) with {len(evidence)} account(s) matching the query."
    else:
        answer = "No events found matching the query."

    return {
        "answer": answer,
        "confidence": _calculate_confidence(evidence),
        "evidence": evidence,
        "comparison": {}
    }


def _answer_general(question: str) -> Dict[str, Any]:
    """Answer general questions using semantic search across all data."""
    from .semantic_search import query as semantic_search

    results = semantic_search(question, top_k=10)

    evidence = []
    for result in results:
        evidence.append({
            "type": result["type"],
            "id": result["id"],
            "match_in": result["match_in"],
            "context": result["matching_context"][:200],
            "relevance": result["relevance_score"]
        })

    if evidence:
        answer = f"Found {len(evidence)} relevant items in the dataset."
    else:
        answer = "No relevant data found for the query."

    return {
        "answer": answer,
        "confidence": _calculate_confidence(evidence),
        "evidence": evidence,
        "comparison": {}
    }


def _synthesize_answer(question: str, evidence: List[Dict], comparison: Dict) -> str:
    """Synthesize a natural language answer from evidence."""
    if not evidence:
        return "Insufficient data to answer the question."

    # Extract key information
    chars = list(set(e["character"] for e in evidence if "character" in e))
    sources = list(set(e["source"] for e in evidence if "source" in e))

    # Build answer
    if len(chars) == 1:
        answer = f"Regarding {chars[0]}, "
    elif len(chars) > 1:
        answer = f"Regarding {len(chars)} characters ({', '.join(chars[:3])}{'...' if len(chars) > 3 else ''}), "
    else:
        answer = "Based on the available data, "

    if sources:
        answer += f"sources {', '.join(sources)} provide relevant information."

    return answer


def _calculate_confidence(evidence: List[Dict]) -> float:
    """Calculate confidence score based on evidence quantity and quality."""
    if not evidence:
        return 0.0

    # Base confidence on amount of evidence
    base_confidence = min(0.5 + (len(evidence) * 0.05), 0.95)

    # Adjust for evidence quality (presence of references)
    has_refs = sum(1 for e in evidence if e.get("reference"))
    if has_refs > 0:
        base_confidence += 0.05

    return round(base_confidence, 2)
