"""
Virtual Source Hypothesis Modeling for Codex Azazel.

Enables modeling of hypothetical sources (Q, proto-Mark, oral traditions)
through set operations on existing sources. Users can define "virtual sources"
via query logic rather than manual JSON entry.

Example:
<<<<<<< HEAD
    Q_source = (Matthew ??? Luke) - Mark
=======
    Q_source = (Matthew ∩ Luke) - Mark
>>>>>>> ef9fdd51577946e97063a3a4a5223e7c1b7c5f80
    proto_mark = Mark - later_additions
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from .. import queries, storage
from ..models import Character, SourceProfile


@dataclass
class VirtualSourceDefinition:
    """Definition of a hypothetical source based on set operations.

    A virtual source is defined by set operations on existing sources:
    - INTERSECTION: traits/references appearing in all specified sources
    - UNION: traits/references appearing in any specified source
    - DIFFERENCE: traits in first source but not in others
    """

    source_id: str  # e.g., "q_source", "proto_mark"
    label: str  # Human-readable name
    description: str
    operation: str  # "intersection", "union", "difference"
    base_sources: List[str]  # Sources to combine
    exclude_sources: List[str] = field(default_factory=list)  # Sources to subtract
    date_range: Optional[str] = None  # e.g., "40-50 CE"
    scholarly_basis: Optional[str] = None  # Citation/explanation
    confidence: str = "speculative"  # "high", "medium", "low", "speculative"


@dataclass
class VirtualSourceResult:
    """Result of applying a virtual source definition to a character."""

    source_id: str
    character_id: str
    traits: Dict[str, str]  # Computed traits
    references: List[str]  # Computed references
    contributing_sources: List[str]  # Which sources contributed
    operation_applied: str
    confidence: str


# Pre-defined scholarly hypotheses
PREDEFINED_HYPOTHESES: Dict[str, VirtualSourceDefinition] = {
    "q_source": VirtualSourceDefinition(
        source_id="q_source",
        label="Q Source",
        description="Hypothetical sayings source shared by Matthew and Luke but absent in Mark",
        operation="difference",
        base_sources=["matthew", "luke"],  # Intersection of these
        exclude_sources=["mark"],  # Then subtract Mark
        date_range="40-60 CE",
        scholarly_basis="Two-Source Hypothesis (B.H. Streeter, 1924)",
        confidence="medium",
    ),
    "triple_tradition": VirtualSourceDefinition(
        source_id="triple_tradition",
        label="Triple Tradition",
        description="Material appearing in all three Synoptic Gospels",
        operation="intersection",
        base_sources=["mark", "matthew", "luke"],
        exclude_sources=[],
        date_range="pre-70 CE",
        scholarly_basis="Synoptic Problem analysis",
        confidence="high",
    ),
    "markan_priority": VirtualSourceDefinition(
        source_id="markan_priority",
        label="Markan Material",
        description="Material unique to Mark or shared with other Synoptics",
        operation="union",
        base_sources=["mark"],
        exclude_sources=[],
        date_range="65-70 CE",
        scholarly_basis="Markan priority hypothesis",
        confidence="high",
    ),
    "double_tradition": VirtualSourceDefinition(
        source_id="double_tradition",
        label="Double Tradition (Matthew-Luke)",
        description="Material shared by Matthew and Luke but not Mark (potential Q material)",
        operation="difference",
        base_sources=["matthew", "luke"],
        exclude_sources=["mark"],
        date_range="50-60 CE",
        scholarly_basis="Two-Source Hypothesis",
        confidence="medium",
    ),
    "special_matthew": VirtualSourceDefinition(
        source_id="special_matthew",
        label="M Source (Special Matthew)",
        description="Material unique to Matthew",
        operation="difference",
        base_sources=["matthew"],
        exclude_sources=["mark", "luke"],
        date_range="70-90 CE",
        scholarly_basis="Four-Source Hypothesis",
        confidence="low",
    ),
    "special_luke": VirtualSourceDefinition(
        source_id="special_luke",
        label="L Source (Special Luke)",
        description="Material unique to Luke",
        operation="difference",
        base_sources=["luke"],
        exclude_sources=["mark", "matthew"],
        date_range="70-90 CE",
        scholarly_basis="Four-Source Hypothesis",
        confidence="low",
    ),
    "johannine_independent": VirtualSourceDefinition(
        source_id="johannine_independent",
        label="Johannine Independent Tradition",
        description="Material unique to John, not dependent on Synoptics",
        operation="difference",
        base_sources=["john"],
        exclude_sources=["mark", "matthew", "luke"],
        date_range="90-100 CE",
        scholarly_basis="Johannine independence hypothesis",
        confidence="medium",
    ),
}


def list_predefined_hypotheses() -> List[Dict[str, Any]]:
    """List all predefined source hypotheses.

    Returns
    -------
    list of dict
        Each dict contains: source_id, label, description, confidence
    """
    return [
        {
            "source_id": h.source_id,
            "label": h.label,
            "description": h.description,
            "operation": h.operation,
            "base_sources": h.base_sources,
            "exclude_sources": h.exclude_sources,
            "date_range": h.date_range,
            "confidence": h.confidence,
        }
        for h in PREDEFINED_HYPOTHESES.values()
    ]


def get_hypothesis_definition(hypothesis_id: str) -> Optional[VirtualSourceDefinition]:
    """Get a predefined hypothesis definition by ID."""
    return PREDEFINED_HYPOTHESES.get(hypothesis_id)


def create_custom_hypothesis(
    source_id: str,
    label: str,
    description: str,
    operation: str,
    base_sources: List[str],
    exclude_sources: Optional[List[str]] = None,
    date_range: Optional[str] = None,
    scholarly_basis: Optional[str] = None,
    confidence: str = "speculative",
) -> VirtualSourceDefinition:
    """Create a custom virtual source hypothesis.

    Parameters
    ----------
    source_id : str
        Unique identifier for this hypothesis
    label : str
        Human-readable name
    description : str
        What this hypothesis represents
    operation : str
        Set operation: "intersection", "union", or "difference"
    base_sources : list of str
        Source IDs to include in the operation
    exclude_sources : list of str, optional
        Source IDs to subtract (for difference operation)
    date_range : str, optional
        Estimated date range of the hypothetical source
    scholarly_basis : str, optional
        Academic citation or basis
    confidence : str
        Confidence level: "high", "medium", "low", "speculative"

    Returns
    -------
    VirtualSourceDefinition
        The created hypothesis definition
    """
    if operation not in ("intersection", "union", "difference"):
        raise ValueError(f"Invalid operation: {operation}. Must be 'intersection', 'union', or 'difference'")

    return VirtualSourceDefinition(
        source_id=source_id,
        label=label,
        description=description,
        operation=operation,
        base_sources=base_sources,
        exclude_sources=exclude_sources or [],
        date_range=date_range,
        scholarly_basis=scholarly_basis,
        confidence=confidence,
    )


def _get_trait_keys_for_source(char: Character, source_id: str) -> Set[str]:
    """Get trait keys present in a character's source profile."""
    profile = char.get_source_profile(source_id)
    if profile is None:
        return set()
    return set(profile.traits.keys())


def _get_references_for_source(char: Character, source_id: str) -> Set[str]:
    """Get references present in a character's source profile."""
    profile = char.get_source_profile(source_id)
    if profile is None:
        return set()
    return set(profile.references)


def apply_hypothesis_to_character(
    hypothesis: VirtualSourceDefinition,
    char_id: str,
) -> VirtualSourceResult:
    """Apply a virtual source hypothesis to a specific character.

    Computes which traits and references would belong to the hypothetical
    source based on the set operations defined.

    Parameters
    ----------
    hypothesis : VirtualSourceDefinition
        The hypothesis to apply
    char_id : str
        Character ID to analyze

    Returns
    -------
    VirtualSourceResult
        Computed traits and references for this character in the virtual source
    """
    char = queries.get_character(char_id)

    # Get trait keys for each base source
    base_trait_sets = [
        _get_trait_keys_for_source(char, src)
        for src in hypothesis.base_sources
    ]

    # Get reference sets for each base source
    base_ref_sets = [
        _get_references_for_source(char, src)
        for src in hypothesis.base_sources
    ]

    # Apply operation to traits
    if hypothesis.operation == "intersection":
        if base_trait_sets:
            result_trait_keys = base_trait_sets[0].copy()
            for s in base_trait_sets[1:]:
                result_trait_keys &= s
        else:
            result_trait_keys = set()

        if base_ref_sets:
            result_refs = base_ref_sets[0].copy()
            for s in base_ref_sets[1:]:
                result_refs &= s
        else:
            result_refs = set()

    elif hypothesis.operation == "union":
        result_trait_keys = set()
        for s in base_trait_sets:
            result_trait_keys |= s

        result_refs = set()
        for s in base_ref_sets:
            result_refs |= s

    elif hypothesis.operation == "difference":
        # For difference: intersection of base sources, then subtract exclusions
        if base_trait_sets:
            result_trait_keys = base_trait_sets[0].copy()
            for s in base_trait_sets[1:]:
                result_trait_keys &= s
        else:
            result_trait_keys = set()

        if base_ref_sets:
            result_refs = base_ref_sets[0].copy()
            for s in base_ref_sets[1:]:
                result_refs &= s
        else:
            result_refs = set()
    else:
        raise ValueError(f"Unknown operation: {hypothesis.operation}")

    # Subtract excluded sources
    for exclude_src in hypothesis.exclude_sources:
        exclude_traits = _get_trait_keys_for_source(char, exclude_src)
        exclude_refs = _get_references_for_source(char, exclude_src)
        result_trait_keys -= exclude_traits
        result_refs -= exclude_refs

    # Build result traits dict with values from first available source
    result_traits: Dict[str, str] = {}
    contributing_sources: List[str] = []

    for trait_key in result_trait_keys:
        # Get value from first base source that has it
        for src in hypothesis.base_sources:
            profile = char.get_source_profile(src)
            if profile and trait_key in profile.traits:
                result_traits[trait_key] = profile.traits[trait_key]
                if src not in contributing_sources:
                    contributing_sources.append(src)
                break

    return VirtualSourceResult(
        source_id=hypothesis.source_id,
        character_id=char_id,
        traits=result_traits,
        references=sorted(result_refs),
        contributing_sources=contributing_sources,
        operation_applied=hypothesis.operation,
        confidence=hypothesis.confidence,
    )


def query_virtual_source(
    hypothesis_id: str,
    char_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Query a virtual source across multiple characters.

    Parameters
    ----------
    hypothesis_id : str
        ID of predefined hypothesis or custom hypothesis source_id
    char_ids : list of str, optional
        Character IDs to analyze. If None, analyzes all characters.

    Returns
    -------
    dict
        Query results with:
        - hypothesis: The hypothesis definition
        - results: List of VirtualSourceResult for each character
        - summary: Aggregate statistics
    """
    hypothesis = PREDEFINED_HYPOTHESES.get(hypothesis_id)
    if hypothesis is None:
        raise ValueError(f"Unknown hypothesis: {hypothesis_id}")

    if char_ids is None:
        char_ids = queries.list_character_ids()

    results = []
    total_traits = 0
    total_refs = 0
    chars_with_data = 0

    for char_id in char_ids:
        try:
            result = apply_hypothesis_to_character(hypothesis, char_id)
            if result.traits or result.references:
                chars_with_data += 1
                total_traits += len(result.traits)
                total_refs += len(result.references)
            results.append({
                "character_id": result.character_id,
                "traits": result.traits,
                "references": result.references,
                "contributing_sources": result.contributing_sources,
            })
        except Exception as e:
            results.append({
                "character_id": char_id,
                "error": str(e),
            })

    return {
        "hypothesis": {
            "source_id": hypothesis.source_id,
            "label": hypothesis.label,
            "description": hypothesis.description,
            "operation": hypothesis.operation,
            "base_sources": hypothesis.base_sources,
            "exclude_sources": hypothesis.exclude_sources,
            "date_range": hypothesis.date_range,
            "confidence": hypothesis.confidence,
        },
        "results": results,
        "summary": {
            "characters_analyzed": len(char_ids),
            "characters_with_data": chars_with_data,
            "total_traits": total_traits,
            "total_references": total_refs,
        },
    }


def compare_hypothetical_to_actual(
    hypothesis_id: str,
    char_id: str,
    compare_source: str,
) -> Dict[str, Any]:
    """Compare a virtual source's portrayal to an actual source.

    This helps test hypotheses by showing how the reconstructed source
    differs from actual attested sources.

    Parameters
    ----------
    hypothesis_id : str
        Virtual source hypothesis ID
    char_id : str
        Character to analyze
    compare_source : str
        Actual source to compare against (e.g., "john")

    Returns
    -------
    dict
        Comparison with shared traits, unique to each, and analysis
    """
    hypothesis = PREDEFINED_HYPOTHESES.get(hypothesis_id)
    if hypothesis is None:
        raise ValueError(f"Unknown hypothesis: {hypothesis_id}")

    virtual_result = apply_hypothesis_to_character(hypothesis, char_id)
    char = queries.get_character(char_id)

    actual_profile = char.get_source_profile(compare_source)
    if actual_profile is None:
        return {
            "error": f"Character {char_id} has no profile for source {compare_source}",
        }

    virtual_traits = set(virtual_result.traits.keys())
    actual_traits = set(actual_profile.traits.keys())

    shared = virtual_traits & actual_traits
    only_virtual = virtual_traits - actual_traits
    only_actual = actual_traits - virtual_traits

    return {
        "character_id": char_id,
        "hypothesis": hypothesis.label,
        "compare_source": compare_source,
        "shared_traits": list(shared),
        "only_in_hypothesis": list(only_virtual),
        "only_in_actual": list(only_actual),
        "overlap_ratio": len(shared) / len(virtual_traits | actual_traits) if (virtual_traits | actual_traits) else 0,
        "analysis": {
            "hypothesis_preserves": f"{len(shared)}/{len(virtual_traits)} traits from hypothesis found in {compare_source}",
            "actual_additions": f"{compare_source} adds {len(only_actual)} traits not in hypothesis",
        },
    }


def find_q_material_for_character(char_id: str) -> Dict[str, Any]:
    """Convenience function to find Q source material for a character.

    This is a common scholarly operation: finding material shared by
    Matthew and Luke but absent from Mark.

    Parameters
    ----------
    char_id : str
        Character ID

    Returns
    -------
    dict
        Q material analysis for this character
    """
    return query_virtual_source("q_source", [char_id])


def analyze_synoptic_layers(char_id: str) -> Dict[str, Any]:
    """Analyze how a character appears across Synoptic source layers.

    Applies multiple hypotheses to show:
    - Triple tradition (all three Synoptics)
    - Q material (Matthew + Luke - Mark)
    - Special Matthew (M)
    - Special Luke (L)

    Parameters
    ----------
    char_id : str
        Character to analyze

    Returns
    -------
    dict
        Layered analysis across hypothetical sources
    """
    layers = {}

    for hyp_id in ["triple_tradition", "q_source", "special_matthew", "special_luke"]:
        try:
            result = apply_hypothesis_to_character(
                PREDEFINED_HYPOTHESES[hyp_id],
                char_id
            )
            layers[hyp_id] = {
                "label": PREDEFINED_HYPOTHESES[hyp_id].label,
                "traits": result.traits,
                "references": result.references,
                "trait_count": len(result.traits),
            }
        except Exception as e:
            layers[hyp_id] = {"error": str(e)}

    return {
        "character_id": char_id,
        "layers": layers,
        "summary": {
            "earliest_layer": "triple_tradition",
            "q_material_count": layers.get("q_source", {}).get("trait_count", 0),
            "special_material": {
                "matthew": layers.get("special_matthew", {}).get("trait_count", 0),
                "luke": layers.get("special_luke", {}).get("trait_count", 0),
            },
        },
    }
