"""Source tendency analysis to identify systematic patterns in how sources portray characters and events.

This module analyzes source-level theological tendencies and narrative priorities.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from collections import Counter, defaultdict

from .. import queries
from ..exceptions import ConfigurationError
from .config import ensure_ai_enabled
from .cache import cached_analysis


def analyze_source_patterns(
    source_id: str,
    use_cache: bool = True,
) -> Dict[str, Any]:
    """Analyze systematic patterns in how a source portrays characters and events.

    Identifies theological tendencies, narrative priorities, and characteristic
    portrayals across all characters in a source.

    Parameters
    ----------
    source_id : str
        Source identifier (e.g., "mark", "matthew", "john")
    use_cache : bool, optional
        Whether to use cached results (default: True)

    Returns
    -------
    dict
        Source analysis with keys: source_id, character_portrayal_patterns,
        narrative_priorities, vocabulary, statistics

    Raises
    ------
    ConfigurationError
        If AI features are disabled

    Examples
    --------
    >>> from bce.ai import source_analysis
    >>> patterns = source_analysis.analyze_source_patterns("mark")
    >>> for pattern in patterns["character_portrayal_patterns"]:
    ...     print(f"{pattern['pattern']}: {pattern['frequency']}")
    """
    ensure_ai_enabled()

    if use_cache:
        return _cached_analyze_source(source_id)
    else:
        return _analyze_source_impl(source_id)


@cached_analysis(ttl_hours=48, namespace="source_analysis")
def _cached_analyze_source(source_id: str) -> Dict[str, Any]:
    """Cached wrapper for source analysis."""
    return _analyze_source_impl(source_id)


def _analyze_source_impl(source_id: str) -> Dict[str, Any]:
    """Internal implementation of source analysis."""
    # Get all characters with this source profile
    all_chars = queries.list_all_characters()
    chars_in_source = [c for c in all_chars if c.get_source_profile(source_id) is not None]

    if not chars_in_source:
        return {
            "source_id": source_id,
            "message": f"No characters found with source profile for '{source_id}'",
            "character_portrayal_patterns": [],
            "narrative_priorities": [],
        }

    # Analyze character portrayals
    portrayal_patterns = _identify_portrayal_patterns(source_id, chars_in_source)

    # Identify narrative priorities
    narrative_priorities = _identify_narrative_priorities(source_id, chars_in_source)

    # Analyze vocabulary and trait keys
    vocabulary = _analyze_vocabulary(source_id, chars_in_source)

    # Generate statistics
    statistics = _generate_source_statistics(source_id, chars_in_source)

    # Identify theological themes
    theological_themes = _identify_theological_themes(source_id, chars_in_source)

    return {
        "source_id": source_id,
        "character_portrayal_patterns": portrayal_patterns,
        "narrative_priorities": narrative_priorities,
        "vocabulary": vocabulary,
        "theological_themes": theological_themes,
        "statistics": statistics,
    }


def compare_source_tendencies(
    source_ids: List[str],
) -> Dict[str, Any]:
    """Compare tendencies across multiple sources.

    Parameters
    ----------
    source_ids : list of str
        Source identifiers to compare

    Returns
    -------
    dict
        Comparative analysis
    """
    ensure_ai_enabled()

    analyses = {}
    for source_id in source_ids:
        analyses[source_id] = _analyze_source_impl(source_id)

    # Compare patterns
    comparison = {
        "sources": source_ids,
        "pattern_comparison": _compare_patterns(analyses),
        "priority_comparison": _compare_priorities(analyses),
        "vocabulary_comparison": _compare_vocabulary(analyses),
    }

    return comparison


def _identify_portrayal_patterns(
    source_id: str,
    characters: List[Any],
) -> List[Dict[str, Any]]:
    """Identify systematic patterns in character portrayals."""
    patterns = []

    # Collect all traits for this source
    all_traits = {}
    for char in characters:
        profile = char.get_source_profile(source_id)
        if profile:
            for trait_key, trait_val in profile.traits.items():
                if trait_key not in all_traits:
                    all_traits[trait_key] = []
                all_traits[trait_key].append({
                    "character": char.id,
                    "value": trait_val,
                })

    # Identify high-frequency patterns
    trait_frequency = Counter(all_traits.keys())

    # Pattern: Messianic secrecy (Mark)
    messianic_keys = ["messianic_secret", "messianic_self_understanding", "hidden_identity"]
    if any(key in trait_frequency for key in messianic_keys):
        affected_chars = []
        for key in messianic_keys:
            if key in all_traits:
                affected_chars.extend([t["character"] for t in all_traits[key]])

        patterns.append({
            "pattern": "messianic_secrecy",
            "frequency": "high" if len(set(affected_chars)) > 1 else "medium",
            "characters_affected": list(set(affected_chars)),
            "evidence": "Traits emphasize hidden or revealed identity",
            "theological_significance": "Theme of gradual revelation and identity disclosure"
        })

    # Pattern: Disciple misunderstanding
    misunderstanding_keys = ["misunderstanding", "failure", "lack_of_understanding"]
    if any(key in trait_frequency for key in misunderstanding_keys):
        affected_chars = []
        for key in misunderstanding_keys:
            if key in all_traits:
                affected_chars.extend([t["character"] for t in all_traits[key]])

        patterns.append({
            "pattern": "disciple_misunderstanding",
            "frequency": "high" if len(set(affected_chars)) > 2 else "medium",
            "characters_affected": list(set(affected_chars)),
            "evidence": "Traits show repeated failure to comprehend mission or teachings",
        })

    # Pattern: Divine Christology (John)
    divine_keys = ["divine_claims", "divinity", "pre_existence", "unity_with_god"]
    if any(key in trait_frequency for key in divine_keys):
        affected_chars = []
        for key in divine_keys:
            if key in all_traits:
                affected_chars.extend([t["character"] for t in all_traits[key]])

        patterns.append({
            "pattern": "divine_christology",
            "frequency": "high" if len(set(affected_chars)) >= 1 else "low",
            "characters_affected": list(set(affected_chars)),
            "evidence": "Traits emphasize divine nature and pre-existence",
            "theological_significance": "High Christology with explicit divine claims"
        })

    # Pattern: Legal/Torah observance
    torah_keys = ["torah_observance", "jewish_law", "temple_observance"]
    if any(key in trait_frequency for key in torah_keys):
        affected_chars = []
        for key in torah_keys:
            if key in all_traits:
                affected_chars.extend([t["character"] for t in all_traits[key]])

        patterns.append({
            "pattern": "torah_observance",
            "frequency": "medium",
            "characters_affected": list(set(affected_chars)),
            "evidence": "Traits show relationship to Jewish law and temple practice"
        })

    # Pattern: Suffering and persecution
    suffering_keys = ["suffering", "persecution", "martyrdom", "trials"]
    if any(key in trait_frequency for key in suffering_keys):
        affected_chars = []
        for key in suffering_keys:
            if key in all_traits:
                affected_chars.extend([t["character"] for t in all_traits[key]])

        patterns.append({
            "pattern": "suffering_emphasis",
            "frequency": "high" if len(set(affected_chars)) > 2 else "medium",
            "characters_affected": list(set(affected_chars)),
            "evidence": "Traits emphasize suffering, persecution, or endurance"
        })

    return patterns


def _identify_narrative_priorities(
    source_id: str,
    characters: List[Any],
) -> List[str]:
    """Identify narrative priorities from trait analysis."""
    priorities = []

    # Collect trait keywords
    all_trait_keys = []
    for char in characters:
        profile = char.get_source_profile(source_id)
        if profile:
            all_trait_keys.extend(profile.traits.keys())

    # Analyze frequency
    trait_counts = Counter(all_trait_keys)

    # Map to narrative priorities
    priority_mappings = {
        "suffering": "suffering_christology",
        "divine": "divine_christology",
        "kingdom": "kingdom_theology",
        "apocalyptic": "apocalyptic_urgency",
        "failure": "discipleship_failure",
        "mission": "mission_emphasis",
        "gentile": "gentile_inclusion",
        "jewish": "jewish_identity",
        "torah": "law_and_covenant",
    }

    for keyword, priority in priority_mappings.items():
        # Check if keyword appears in trait keys
        matching_keys = [k for k in trait_counts if keyword in k.lower()]
        if matching_keys:
            frequency = sum(trait_counts[k] for k in matching_keys)
            if frequency >= 2:  # Appears at least twice
                priorities.append(priority)

    return list(set(priorities))


def _analyze_vocabulary(
    source_id: str,
    characters: List[Any],
) -> Dict[str, Any]:
    """Analyze characteristic vocabulary and phrasing."""
    all_trait_keys = []
    all_trait_values = []

    for char in characters:
        profile = char.get_source_profile(source_id)
        if profile:
            all_trait_keys.extend(profile.traits.keys())
            all_trait_values.extend(profile.traits.values())

    # Most common trait keys
    trait_key_counts = Counter(all_trait_keys)
    common_trait_keys = trait_key_counts.most_common(10)

    # Extract common words from trait values (simplified)
    value_words = []
    for value in all_trait_values:
        words = value.lower().split()
        value_words.extend([w for w in words if len(w) > 4])  # Meaningful words

    common_words = Counter(value_words).most_common(15)

    return {
        "common_trait_keys": [{"key": k, "count": c} for k, c in common_trait_keys],
        "common_vocabulary": [{"word": w, "count": c} for w, c in common_words],
        "total_unique_trait_keys": len(set(all_trait_keys)),
    }


def _identify_theological_themes(
    source_id: str,
    characters: List[Any],
) -> List[str]:
    """Identify major theological themes."""
    themes = []

    # Collect all trait values
    all_values = []
    for char in characters:
        profile = char.get_source_profile(source_id)
        if profile:
            all_values.extend(profile.traits.values())

    combined_text = " ".join(all_values).lower()

    # Theme detection
    theme_keywords = {
        "kingdom_of_god": ["kingdom", "kingdom of god", "kingdom of heaven"],
        "salvation": ["salvation", "saved", "redemption", "forgiveness"],
        "faith": ["faith", "believe", "trust"],
        "discipleship": ["disciple", "follow", "follower"],
        "authority": ["authority", "power", "exousia"],
        "identity": ["identity", "who he is", "messianic"],
        "covenant": ["covenant", "promise", "torah", "law"],
        "spirit": ["spirit", "holy spirit", "pneuma"],
    }

    for theme, keywords in theme_keywords.items():
        if any(keyword in combined_text for keyword in keywords):
            themes.append(theme)

    return themes


def _generate_source_statistics(
    source_id: str,
    characters: List[Any],
) -> Dict[str, Any]:
    """Generate statistical summary of source."""
    total_traits = 0
    total_references = 0

    for char in characters:
        profile = char.get_source_profile(source_id)
        if profile:
            total_traits += len(profile.traits)
            total_references += len(profile.references)

    return {
        "character_count": len(characters),
        "total_traits": total_traits,
        "total_references": total_references,
        "avg_traits_per_character": round(total_traits / len(characters), 1) if characters else 0,
    }


def _compare_patterns(analyses: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Compare portrayal patterns across sources."""
    # Extract patterns from each source
    pattern_by_source = {}
    for source_id, analysis in analyses.items():
        patterns = analysis.get("character_portrayal_patterns", [])
        pattern_by_source[source_id] = {p["pattern"] for p in patterns}

    # Find unique and shared patterns
    all_patterns = set()
    for patterns in pattern_by_source.values():
        all_patterns.update(patterns)

    comparisons = []
    for pattern in all_patterns:
        sources_with_pattern = [s for s, pats in pattern_by_source.items() if pattern in pats]
        comparisons.append({
            "pattern": pattern,
            "present_in": sources_with_pattern,
            "unique_to": sources_with_pattern[0] if len(sources_with_pattern) == 1 else None,
        })

    return comparisons


def _compare_priorities(analyses: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
    """Compare narrative priorities across sources."""
    comparison = {}
    for source_id, analysis in analyses.items():
        comparison[source_id] = analysis.get("narrative_priorities", [])

    return comparison


def _compare_vocabulary(analyses: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Compare vocabulary usage across sources."""
    vocab_comparison = {}

    for source_id, analysis in analyses.items():
        vocab = analysis.get("vocabulary", {})
        common_keys = vocab.get("common_trait_keys", [])
        vocab_comparison[source_id] = {
            "top_trait_keys": [k["key"] for k in common_keys[:5]],
            "unique_trait_count": vocab.get("total_unique_trait_keys", 0),
        }

    return vocab_comparison
