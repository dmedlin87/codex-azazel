"""Advanced conflict analysis with severity assessment and scholarly context.

This module enhances basic contradiction detection with theological, historical,
and narrative significance analysis.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .. import queries, contradictions
from ..exceptions import ConfigurationError
from .config import ensure_ai_enabled
from .embeddings import embed_text, cosine_similarity
from .cache import cached_analysis


def assess_conflict(
    character_id: str,
    trait: str,
    use_cache: bool = True,
) -> Dict[str, Any]:
    """Assess a specific character trait conflict with enhanced analysis.

    Provides detailed assessment of theological, historical, and narrative
    significance beyond basic string comparison.

    Parameters
    ----------
    character_id : str
        Character identifier
    trait : str
        Trait key with conflict
    use_cache : bool, optional
        Whether to use cached results (default: True)

    Returns
    -------
    dict
        Enhanced conflict assessment

    Raises
    ------
    ConfigurationError
        If AI features are disabled

    Examples
    --------
    >>> from bce.ai import conflict_analysis
    >>> assessment = conflict_analysis.assess_conflict("jesus", "resurrection_appearances_timeline")
    >>> print(assessment["ai_assessment"]["theological_significance"])
    """
    ensure_ai_enabled()

    if use_cache:
        return _cached_assess_conflict(character_id, trait)
    else:
        return _assess_conflict_impl(character_id, trait)


@cached_analysis(ttl_hours=48, namespace="conflict_assessment")
def _cached_assess_conflict(character_id: str, trait: str) -> Dict[str, Any]:
    """Cached wrapper for conflict assessment."""
    return _assess_conflict_impl(character_id, trait)


def _assess_conflict_impl(character_id: str, trait: str) -> Dict[str, Any]:
    """Internal implementation of conflict assessment."""
    # Get basic conflict data
    char = queries.get_character(character_id)
    conflicts = contradictions.find_trait_conflicts(character_id)

    if trait not in conflicts:
        return {
            "character_id": character_id,
            "trait": trait,
            "has_conflict": False,
            "message": f"No conflict detected for trait '{trait}'"
        }

    conflict_data = conflicts[trait]

    # Get basic severity from existing logic
    basic_severity = _estimate_basic_severity(trait, conflict_data)

    # Perform enhanced AI assessment
    ai_assessment = _perform_ai_assessment(character_id, trait, conflict_data)

    return {
        "character_id": character_id,
        "trait": trait,
        "sources": conflict_data,
        "basic_severity": basic_severity,
        "ai_assessment": ai_assessment,
    }


def assess_all_conflicts(
    character_id: str,
) -> Dict[str, Any]:
    """Assess all conflicts for a character.

    Parameters
    ----------
    character_id : str
        Character identifier

    Returns
    -------
    dict
        All conflict assessments
    """
    ensure_ai_enabled()

    conflicts = contradictions.find_trait_conflicts(character_id)

    assessments = {}
    for trait in conflicts.keys():
        assessment = _assess_conflict_impl(character_id, trait)
        assessments[trait] = assessment

    # Generate summary
    if assessments:
        severities = [a["ai_assessment"]["theological_significance"] for a in assessments.values()]
        summary = {
            "total_conflicts": len(assessments),
            "high_significance": sum(1 for s in severities if s == "high"),
            "medium_significance": sum(1 for s in severities if s == "medium"),
            "low_significance": sum(1 for s in severities if s == "low"),
        }
    else:
        summary = {"total_conflicts": 0}

    return {
        "character_id": character_id,
        "assessments": assessments,
        "summary": summary,
    }


def _estimate_basic_severity(trait: str, conflict_data: Dict[str, str]) -> str:
    """Estimate basic severity using existing heuristics."""
    # High severity traits
    high_severity_keys = [
        "death_method", "resurrection_appearances", "divine_claims",
        "messianic_self_understanding", "conversion_experience",
    ]

    if any(key in trait.lower() for key in high_severity_keys):
        return "high"

    # Medium severity traits
    medium_severity_keys = [
        "authority", "relationship", "timeline", "location",
    ]

    if any(key in trait.lower() for key in medium_severity_keys):
        return "medium"

    return "low"


def _perform_ai_assessment(
    character_id: str,
    trait: str,
    conflict_data: Dict[str, str],
) -> Dict[str, Any]:
    """Perform AI-enhanced assessment of conflict significance."""
    # Assess theological significance
    theological_sig = _assess_theological_significance(trait, conflict_data)

    # Assess historical significance
    historical_sig = _assess_historical_significance(trait, conflict_data)

    # Assess narrative coherence impact
    narrative_impact = _assess_narrative_impact(trait, conflict_data)

    # Generate explanation
    explanation = _generate_conflict_explanation(trait, conflict_data, theological_sig)

    # Assess scholarly consensus
    scholarly_consensus = _assess_scholarly_consensus(trait)

    # Identify implications
    implications = _identify_implications(trait, conflict_data)

    return {
        "theological_significance": theological_sig,
        "historical_significance": historical_sig,
        "narrative_coherence_impact": narrative_impact,
        "explanation": explanation,
        "scholarly_consensus": scholarly_consensus,
        "implications": implications,
    }


def _assess_theological_significance(trait: str, conflict_data: Dict[str, str]) -> str:
    """Assess theological significance of the conflict."""
    # High theological significance keywords
    high_theological = [
        "divine", "divinity", "god", "messianic", "resurrection",
        "salvation", "atonement", "incarnation", "trinity",
    ]

    trait_lower = trait.lower()
    values_lower = " ".join(conflict_data.values()).lower()

    if any(keyword in trait_lower or keyword in values_lower for keyword in high_theological):
        return "high"

    # Medium theological significance
    medium_theological = [
        "authority", "mission", "teaching", "law", "torah",
        "gentile", "covenant", "prophecy",
    ]

    if any(keyword in trait_lower or keyword in values_lower for keyword in medium_theological):
        return "medium"

    return "low"


def _assess_historical_significance(trait: str, conflict_data: Dict[str, str]) -> str:
    """Assess historical significance of the conflict."""
    # High historical significance keywords
    high_historical = [
        "death", "crucifixion", "trial", "birth", "baptism",
        "timeline", "date", "location", "jerusalem", "rome",
    ]

    trait_lower = trait.lower()

    if any(keyword in trait_lower for keyword in high_historical):
        return "high"

    # Medium historical significance
    medium_historical = [
        "journey", "travel", "visit", "encounter", "meeting",
    ]

    if any(keyword in trait_lower for keyword in medium_historical):
        return "medium"

    return "low"


def _assess_narrative_impact(trait: str, conflict_data: Dict[str, str]) -> str:
    """Assess impact on narrative coherence."""
    # Calculate semantic similarity between conflicting values
    values = list(conflict_data.values())

    if len(values) < 2:
        return "low"

    # Embed the values
    embeddings = [embed_text(val) for val in values]

    # Calculate pairwise similarities
    similarities = []
    for i in range(len(embeddings)):
        for j in range(i + 1, len(embeddings)):
            sim = cosine_similarity(embeddings[i], embeddings[j])
            similarities.append(sim)

    avg_similarity = sum(similarities) / len(similarities) if similarities else 0.0

    # High similarity = low narrative impact (just different emphasis)
    # Low similarity = high narrative impact (genuinely different stories)
    if avg_similarity > 0.7:
        return "low"
    elif avg_similarity > 0.4:
        return "medium"
    else:
        return "high"


def _generate_conflict_explanation(
    trait: str,
    conflict_data: Dict[str, str],
    theological_sig: str,
) -> str:
    """Generate natural language explanation of the conflict."""
    sources = list(conflict_data.keys())

    if len(sources) == 2:
        explanation = f"Discrepancy in {trait.replace('_', ' ')} reflects different theological priorities "
        explanation += f"between {sources[0]} and {sources[1]}. "
    else:
        explanation = f"Multiple sources disagree on {trait.replace('_', ' ')}. "

    # Add context based on theological significance
    if theological_sig == "high":
        explanation += "This represents a significant theological divergence with implications for understanding the character's nature and mission."
    elif theological_sig == "medium":
        explanation += "This reflects differing emphases rather than irreconcilable contradictions."
    else:
        explanation += "This represents minor variation in narrative detail."

    return explanation


def _assess_scholarly_consensus(trait: str) -> str:
    """Assess level of scholarly consensus on the conflict."""
    # Well-known conflicts with strong scholarly consensus
    well_known_conflicts = [
        "death_method", "resurrection_appearances", "conversion_timeline",
        "divine_claims", "messianic_secret", "temple_cleansing_timing",
    ]

    if any(known in trait.lower() for known in well_known_conflicts):
        return "Widely acknowledged as source-specific emphasis"

    # Less discussed conflicts
    return "Recognized by scholars but less prominently discussed"


def _identify_implications(trait: str, conflict_data: Dict[str, str]) -> List[str]:
    """Identify scholarly implications of the conflict."""
    implications = []

    # Check for independent tradition indication
    if len(conflict_data) >= 2:
        implications.append("Reflects independent traditions")

    # Check for oral transmission variants
    if "timeline" in trait.lower() or "sequence" in trait.lower():
        implications.append("May indicate oral transmission variants")

    # Check for theological redaction
    if "divine" in trait.lower() or "messianic" in trait.lower():
        implications.append("Suggests theological redaction or development")

    # Check for witness priority
    if "appearance" in trait.lower() or "witness" in trait.lower():
        implications.append("Each gospel prioritizes different witnesses")

    # Check for chronological vs theological arrangement
    if "timeline" in trait.lower() or "order" in trait.lower():
        implications.append("May reflect theological rather than chronological arrangement")

    return implications if implications else ["Indicates source diversity"]


def compare_conflict_severity(
    character_id1: str,
    character_id2: str,
) -> Dict[str, Any]:
    """Compare conflict severity between two characters.

    Parameters
    ----------
    character_id1 : str
        First character ID
    character_id2 : str
        Second character ID

    Returns
    -------
    dict
        Comparative analysis
    """
    ensure_ai_enabled()

    analysis1 = assess_all_conflicts(character_id1)
    analysis2 = assess_all_conflicts(character_id2)

    return {
        "characters": [character_id1, character_id2],
        "comparison": {
            character_id1: analysis1["summary"],
            character_id2: analysis2["summary"],
        },
        "interpretation": _generate_comparison_interpretation(
            character_id1, analysis1,
            character_id2, analysis2
        ),
    }


def _generate_comparison_interpretation(
    char1: str, analysis1: Dict,
    char2: str, analysis2: Dict,
) -> str:
    """Generate interpretation of conflict comparison."""
    total1 = analysis1["summary"].get("total_conflicts", 0)
    total2 = analysis2["summary"].get("total_conflicts", 0)

    if total1 > total2:
        return f"{char1} has more conflicts ({total1}) than {char2} ({total2}), suggesting more diverse source traditions."
    elif total2 > total1:
        return f"{char2} has more conflicts ({total2}) than {char1} ({total1}), suggesting more diverse source traditions."
    else:
        return f"Both characters have similar conflict levels ({total1}), indicating comparable source diversity."
