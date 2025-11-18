"""Automated trait extraction from scripture passages.

This module helps accelerate data entry by extracting character traits and
event details from Bible text. All extractions require human review before
being added to the dataset.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import re

from ..exceptions import ConfigurationError
from .config import ensure_ai_enabled
from .embeddings import embed_text


def extract_character_traits(
    character_id: str,
    source: str,
    passage: str,
    bible_text: str,
) -> Dict[str, Any]:
    """Extract suggested character traits from a scripture passage.

    Uses text analysis and pattern matching to identify potential traits.
    All suggestions require human review before being added to character JSON.

    Parameters
    ----------
    character_id : str
        Character identifier
    source : str
        Source ID (e.g., "mark", "john")
    passage : str
        Scripture reference (e.g., "John 3:1-21")
    bible_text : str
        Full text of the passage

    Returns
    -------
    dict
        Extraction results with keys: character_id, source, reference,
        suggested_traits, needs_review

    Raises
    ------
    ConfigurationError
        If AI features are disabled

    Examples
    --------
    >>> from bce.ai import trait_extraction
    >>> traits = trait_extraction.extract_character_traits(
    ...     "nicodemus",
    ...     "john",
    ...     "John 3:1-21",
    ...     "<full text here>"
    ... )
    >>> for trait in traits["suggested_traits"]:
    ...     print(f"{trait['trait_key']}: {trait['trait_value']}")
    """
    ensure_ai_enabled()

    # Parse the passage text
    suggested_traits = _extract_traits_from_text(character_id, bible_text)

    # Add confidence scores
    for trait in suggested_traits:
        trait["confidence"] = _calculate_trait_confidence(trait, bible_text)

    return {
        "character_id": character_id,
        "source": source,
        "reference": passage,
        "suggested_traits": suggested_traits,
        "needs_review": True,
    }


def extract_event_details(
    event_id: str,
    source: str,
    passage: str,
    bible_text: str,
) -> Dict[str, Any]:
    """Extract event account details from a scripture passage.

    Parameters
    ----------
    event_id : str
        Event identifier
    source : str
        Source ID
    passage : str
        Scripture reference
    bible_text : str
        Full passage text

    Returns
    -------
    dict
        Extracted event details
    """
    ensure_ai_enabled()

    # Extract key details
    participants = _extract_participants(bible_text)
    location = _extract_location(bible_text)
    time_markers = _extract_time_markers(bible_text)

    # Generate summary
    summary = _generate_summary(bible_text)

    return {
        "event_id": event_id,
        "source": source,
        "reference": passage,
        "suggested_participants": participants,
        "suggested_location": location,
        "time_markers": time_markers,
        "suggested_summary": summary,
        "needs_review": True,
    }


def _extract_traits_from_text(character_id: str, text: str) -> List[Dict[str, Any]]:
    """Extract traits using pattern matching and text analysis."""
    traits = []

    # Social status patterns
    status_patterns = [
        (r"(Pharisee|Sadducee|priest|scribe|elder|ruler|council|Sanhedrin)", "social_status"),
        (r"(tax collector|publican|sinner)", "social_status"),
        (r"(fisherman|carpenter|tentmaker)", "occupation"),
        (r"(teacher|rabbi|master)", "role"),
    ]

    for pattern, trait_key in status_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            context = _extract_context(text, match.start(), match.end())
            traits.append({
                "trait_key": trait_key,
                "trait_value": context,
                "evidence": f"Text mentions: {match.group(0)}",
            })

    # Action patterns (verbs that reveal character)
    action_patterns = [
        (r"(came|went|approached) (to|at) night", "secretive_seeking"),
        (r"(asked|questioned|inquired)", "inquisitive_nature"),
        (r"(believed|trusted|had faith)", "faith_response"),
        (r"(doubted|questioned|did not believe)", "skepticism"),
        (r"(followed|went with|accompanied)", "discipleship_action"),
        (r"(denied|rejected|refused)", "rejection_action"),
    ]

    for pattern, trait_key in action_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            # Extract sentence containing the pattern
            sentences = text.split(".")
            for sent in sentences:
                if re.search(pattern, sent, re.IGNORECASE):
                    traits.append({
                        "trait_key": trait_key,
                        "trait_value": sent.strip(),
                        "evidence": f"Action described: {sent.strip()[:100]}",
                    })
                    break

    # Dialogue analysis
    if '"' in text or '"' in text or '"' in text:
        # Character speaks - extract what they say
        speech_pattern = r'["""]([^"""]+)["""]'
        speeches = re.findall(speech_pattern, text)
        if speeches:
            # Analyze tone and content of speech
            for speech in speeches[:3]:  # Limit to first 3 speeches
                if len(speech) > 20:  # Meaningful dialogue
                    traits.append({
                        "trait_key": "dialogue_content",
                        "trait_value": speech[:200],
                        "evidence": f"Character speaks: {speech[:100]}...",
                    })

    # Emotional/attitudinal markers
    emotion_patterns = [
        (r"(afraid|fearful|terrified)", "emotional_state"),
        (r"(joyful|rejoiced|glad)", "emotional_state"),
        (r"(angry|wrathful|indignant)", "emotional_state"),
        (r"(compassionate|merciful|kind)", "character_quality"),
        (r"(humble|meek)", "character_quality"),
        (r"(proud|arrogant)", "character_quality"),
    ]

    for pattern, trait_key in emotion_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            context = re.search(f".{{0,50}}{pattern}.{{0,50}}", text, re.IGNORECASE)
            if context:
                traits.append({
                    "trait_key": trait_key,
                    "trait_value": context.group(0).strip(),
                    "evidence": context.group(0).strip(),
                })

    # Deduplicate similar traits
    return _deduplicate_traits(traits)


def _extract_participants(text: str) -> List[str]:
    """Extract character names from text."""
    # Common NT character names
    name_patterns = [
        r"\bJesus\b", r"\bPeter\b", r"\bJohn\b", r"\bJames\b", r"\bAndrew\b",
        r"\bPhilip\b", r"\bThomas\b", r"\bMatthew\b", r"\bBartholomew\b",
        r"\bSimon\b", r"\bJudas\b", r"\bMary\b", r"\bMartha\b", r"\bLazarus\b",
        r"\bNicodemus\b", r"\bPilate\b", r"\bPaul\b", r"\bSaul\b", r"\bBarabbas\b",
    ]

    participants = []
    for pattern in name_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            # Extract the name
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                participants.append(match.group(0).lower())

    return list(set(participants))  # Deduplicate


def _extract_location(text: str) -> Optional[str]:
    """Extract location markers from text."""
    location_patterns = [
        r"in (Jerusalem|Galilee|Bethany|Capernaum|Nazareth|Bethlehem|Jericho|Samaria)",
        r"at (the temple|the synagogue|the well|the sea|the mount|Golgotha)",
        r"near (the Jordan|the pool|the garden)",
    ]

    for pattern in location_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)

    return None


def _extract_time_markers(text: str) -> List[str]:
    """Extract temporal markers from text."""
    time_patterns = [
        r"(at night|during the day|at dawn|at dusk|in the evening|in the morning)",
        r"(on the sabbath|on the first day|on the third day|after \w+ days)",
        r"(during (Passover|Pentecost|Tabernacles|the feast))",
    ]

    markers = []
    for pattern in time_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            markers.append(match.group(0))

    return markers


def _generate_summary(text: str, max_length: int = 200) -> str:
    """Generate a summary of the passage.

    For now, uses simple heuristics. Could be enhanced with LLM in future.
    """
    # Split into sentences
    sentences = re.split(r'[.!?]', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

    if not sentences:
        return text[:max_length]

    # Take first 2-3 sentences as summary
    summary = ". ".join(sentences[:3]) + "."

    if len(summary) > max_length:
        summary = summary[:max_length] + "..."

    return summary


def _extract_context(text: str, start: int, end: int, window: int = 50) -> str:
    """Extract context around a match."""
    context_start = max(0, start - window)
    context_end = min(len(text), end + window)
    context = text[context_start:context_end].strip()

    # Clean up partial words at boundaries
    if context_start > 0:
        context = "..." + context[context.find(" ") + 1:]
    if context_end < len(text):
        context = context[:context.rfind(" ")] + "..."

    return context


def _calculate_trait_confidence(trait: Dict[str, Any], full_text: str) -> float:
    """Calculate confidence score for extracted trait."""
    confidence = 0.5  # Base confidence

    # Increase confidence if trait is explicitly stated
    if trait["trait_value"] in full_text:
        confidence += 0.2

    # Increase confidence if evidence is substantial
    if len(trait.get("evidence", "")) > 50:
        confidence += 0.1

    # Increase confidence for specific trait keys
    high_confidence_keys = ["social_status", "occupation", "role"]
    if trait["trait_key"] in high_confidence_keys:
        confidence += 0.15

    return min(confidence, 0.95)


def _deduplicate_traits(traits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate or highly similar traits."""
    if len(traits) <= 1:
        return traits

    # Group by trait_key
    by_key = {}
    for trait in traits:
        key = trait["trait_key"]
        if key not in by_key:
            by_key[key] = []
        by_key[key].append(trait)

    # For each key, keep only unique values
    deduped = []
    for key, trait_list in by_key.items():
        seen_values = set()
        for trait in trait_list:
            # Normalize value for comparison
            norm_value = trait["trait_value"].lower().strip()
            if norm_value not in seen_values:
                seen_values.add(norm_value)
                deduped.append(trait)

    return deduped
