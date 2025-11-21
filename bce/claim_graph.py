"""Claim graph helpers and conflict classification.

This module normalizes character traits and event account fields into
structured ``Claim`` records, infers their topical type (chronology,
theology, geography, etc.), and detects conflicts with lightweight
harmonization suggestions.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Iterable, List, Optional, Tuple

from .models import Character, Event


class ClaimType(str, Enum):
    """Controlled taxonomy for claim types."""

    CHRONOLOGY = "chronology"
    THEOLOGY = "theology"
    GEOGRAPHY = "geography"
    NARRATIVE = "narrative"
    IDENTITY = "identity"
    TEXTUAL = "textual"
    OTHER = "other"


@dataclass(slots=True)
class Claim:
    """A single assertion made by a source about a subject."""

    subject_id: str
    predicate: str
    value: str
    source_id: str
    claim_type: ClaimType
    aspect: str
    references: List[str] = field(default_factory=list)
    note: Optional[str] = None

    def to_dict(self) -> Dict[str, object]:
        return {
            "subject_id": self.subject_id,
            "predicate": self.predicate,
            "value": self.value,
            "source_id": self.source_id,
            "claim_type": self.claim_type.value,
            "aspect": self.aspect,
            "references": list(self.references),
            "note": self.note,
        }


@dataclass(slots=True)
class ClaimConflict:
    """Conflict between multiple claims for the same predicate."""

    subject_id: str
    predicate: str
    claim_type: ClaimType
    conflict_type: str
    aspect: str
    severity: str
    values_by_source: Dict[str, str]
    distinct_values: List[str]
    harmonization_moves: List[Dict[str, str]] = field(default_factory=list)
    dominant_value: Optional[str] = None
    rationale: Optional[str] = None

    def to_dict(self) -> Dict[str, object]:
        return {
            "subject_id": self.subject_id,
            "predicate": self.predicate,
            "claim_type": self.claim_type.value,
            "conflict_type": self.conflict_type,
            "aspect": self.aspect,
            "severity": self.severity,
            "values_by_source": dict(self.values_by_source),
            "distinct_values": list(self.distinct_values),
            "harmonization_moves": list(self.harmonization_moves),
            "dominant_value": self.dominant_value,
            "rationale": self.rationale,
        }


def _classify_claim_type(name: str, value: Optional[str] = None) -> Tuple[ClaimType, str]:
    """Infer a claim type and aspect from a predicate/value pair."""

    lowered = name.lower()
    aspect = "other"
    value_lower = value.lower() if isinstance(value, str) else ""

    def _match(tokens: Iterable[str]) -> bool:
        return any(token in lowered for token in tokens)

    if _match(("chronolog", "date", "timeline", "order", "sequence", "reference", "passover")):
        aspect = "sequence" if "order" in lowered or "sequence" in lowered else "dating"
        return ClaimType.CHRONOLOGY, aspect

    if _match(("christolog", "theolog", "divine", "messianic", "resurrect", "aton", "salvation", "spirit", "lord", "kingdom")):
        aspect = "christology" if "christolog" in lowered or "messianic" in lowered else "theological_emphasis"
        return ClaimType.THEOLOGY, aspect

    if _match(("location", "place", "region", "city", "village", "mount", "sea", "road", "galilee", "jerusalem")):
        aspect = "locale"
        return ClaimType.GEOGRAPHY, aspect

    if _match(("summary", "story", "narrative", "account", "notes", "plot")):
        aspect = "narrative_emphasis"
        return ClaimType.NARRATIVE, aspect

    if _match(("name", "title", "alias", "role", "identity", "call", "commission")):
        aspect = "identity"
        return ClaimType.IDENTITY, aspect

    if _match(("variant", "manuscript", "reading", "textual")) or "codex" in value_lower:
        aspect = "textual_variant"
        return ClaimType.TEXTUAL, aspect

    return ClaimType.OTHER, aspect


def _classify_conflict_type(predicate: str, claim_type: ClaimType, aspect: str) -> str:
    """Map a claim type/aspect into a more specific conflict label."""

    lowered = predicate.lower()
    if claim_type is ClaimType.CHRONOLOGY:
        return "chronology_sequence" if "order" in lowered or "sequence" in lowered else "chronology_dating"
    if claim_type is ClaimType.GEOGRAPHY:
        return "geography_location"
    if claim_type is ClaimType.THEOLOGY:
        if "resurrect" in lowered:
            return "theological_resurrection"
        if "messianic" in lowered or "christolog" in lowered:
            return "theological_christology"
        return "theological_emphasis"
    if claim_type is ClaimType.IDENTITY:
        return "identity_title"
    if claim_type is ClaimType.TEXTUAL:
        return "textual_variant"
    if aspect.startswith("narrative"):
        return "narrative_emphasis"
    return "other"


def _estimate_severity(num_sources: int, num_distinct: int) -> str:
    """Estimate conflict severity from how many sources and values disagree."""

    if num_distinct >= 3 or num_sources >= 4:
        return "high"
    if num_distinct == 2 and num_sources >= 3:
        return "medium"
    return "low"


def _pick_dominant_value(values_by_source: Dict[str, str]) -> Optional[str]:
    """Pick the most-attested value, falling back deterministically."""

    if not values_by_source:
        return None
    counter = Counter(values_by_source.values())
    most_common = counter.most_common()
    if not most_common:
        return None
    top_count = most_common[0][1]
    top_values = sorted([val for val, count in most_common if count == top_count])
    return top_values[0] if top_values else None


def _suggest_harmonization_moves(
    conflict_type: str,
    claim_type: ClaimType,
    distinct_values: List[str],
    dominant_value: Optional[str],
) -> List[Dict[str, str]]:
    """Return lightweight harmonization ideas tailored to the conflict."""

    moves: List[Dict[str, str]] = []
    magnitude = len(distinct_values)

    if claim_type is ClaimType.CHRONOLOGY:
        moves.append(
            {
                "move": "anchor_by_range",
                "description": "Use a date/sequence range broad enough to contain every attested ordering.",
                "impact": "low",
            }
        )
        if dominant_value:
            moves.append(
                {
                    "move": "prefer_majority_sequence",
                    "description": f"Present {dominant_value!r} as the dominant ordering while annotating minority views.",
                    "impact": "medium",
                }
            )
    elif claim_type is ClaimType.THEOLOGY:
        moves.append(
            {
                "move": "surface_multivoice",
                "description": "Keep all theological emphases visible and note the audience or source context for each.",
                "impact": "low",
            }
        )
    elif claim_type is ClaimType.GEOGRAPHY:
        moves.append(
            {
                "move": "broaden_location",
                "description": "Express the location at a higher level (region/route) to accommodate each specific locale.",
                "impact": "low",
            }
        )
    elif claim_type is ClaimType.IDENTITY:
        moves.append(
            {
                "move": "capture_as_alias",
                "description": "Retain all titles/epithets as aliases with source attributions instead of forcing a single one.",
                "impact": "low",
            }
        )
    elif claim_type is ClaimType.TEXTUAL:
        moves.append(
            {
                "move": "note_variant_stack",
                "description": "List each manuscript reading with manuscript family instead of collapsing to one.",
                "impact": "low",
            }
        )
    else:
        moves.append(
            {
                "move": "annotate_divergence",
                "description": "Preserve each version and annotate the divergence inline.",
                "impact": "low",
            }
        )

    if magnitude >= 3:
        moves.append(
            {
                "move": "flag_high_disagreement",
                "description": "Mark this as high disagreement to alert downstream consumers.",
                "impact": "low",
            }
        )

    return moves


def _rationale(values_by_source: Dict[str, str], conflict_type: str) -> str:
    distinct = sorted(set(values_by_source.values()))
    return f"{len(distinct)} distinct value(s) across {len(values_by_source)} source(s); type={conflict_type}"


def _group_claims(claims: Iterable[Claim]) -> Dict[Tuple[str, str], List[Claim]]:
    groups: Dict[Tuple[str, str], List[Claim]] = defaultdict(list)
    for claim in claims:
        groups[(claim.subject_id, claim.predicate)].append(claim)
    return groups


def detect_conflicts_from_claims(claims: List[Claim]) -> List[ClaimConflict]:
    """Detect conflicts within a set of claims, grouped by predicate."""

    conflicts: List[ClaimConflict] = []
    for (subject_id, predicate), grouped in _group_claims(claims).items():
        values_by_source: Dict[str, str] = {}
        for claim in grouped:
            if claim.value:
                values_by_source[claim.source_id] = claim.value

        distinct_values = sorted(set(values_by_source.values()))
        if len(distinct_values) <= 1:
            continue

        claim_type, aspect = _resolve_claim_type_for_group(grouped)
        conflict_type = _classify_conflict_type(predicate, claim_type, aspect)
        severity = _estimate_severity(len(values_by_source), len(distinct_values))
        dominant_value = _pick_dominant_value(values_by_source)
        harmonization_moves = _suggest_harmonization_moves(
            conflict_type, claim_type, distinct_values, dominant_value
        )

        conflicts.append(
            ClaimConflict(
                subject_id=subject_id,
                predicate=predicate,
                claim_type=claim_type,
                conflict_type=conflict_type,
                aspect=aspect,
                severity=severity,
                values_by_source=values_by_source,
                distinct_values=distinct_values,
                harmonization_moves=harmonization_moves,
                dominant_value=dominant_value,
                rationale=_rationale(values_by_source, conflict_type),
            )
        )

    return conflicts


def _resolve_claim_type_for_group(grouped: List[Claim]) -> Tuple[ClaimType, str]:
    """Pick the dominant claim type/aspect for a set of claims."""

    if not grouped:
        return ClaimType.OTHER, "other"

    counter = Counter([claim.claim_type for claim in grouped])
    claim_type = counter.most_common(1)[0][0]

    aspect_counter = Counter([claim.aspect for claim in grouped if claim.aspect])
    aspect = aspect_counter.most_common(1)[0][0] if aspect_counter else "other"

    return claim_type, aspect


def build_claims_for_character(character: Character) -> List[Claim]:
    """Flatten a character's source profiles into Claim objects."""

    claims: List[Claim] = []
    for profile in character.source_profiles:
        for trait, value in profile.traits.items():
            if not isinstance(value, str) or not value.strip():
                continue
            claim_type, aspect = _classify_claim_type(trait, value)
            note = profile.trait_notes.get(trait) if hasattr(profile, "trait_notes") else None
            claims.append(
                Claim(
                    subject_id=character.id,
                    predicate=trait,
                    value=value,
                    source_id=profile.source_id,
                    claim_type=claim_type,
                    aspect=aspect,
                    references=list(profile.references),
                    note=note,
                )
            )
    return claims


def build_claims_for_event(event: Event) -> List[Claim]:
    """Flatten an event's accounts into Claim objects."""

    claims: List[Claim] = []
    for account in event.accounts:
        for predicate in ("summary", "notes", "reference"):
            value = getattr(account, predicate, None)
            if not isinstance(value, str) or not value.strip():
                continue
            claim_type, aspect = _classify_claim_type(predicate, value)
            claims.append(
                Claim(
                    subject_id=event.id,
                    predicate=predicate,
                    value=value,
                    source_id=account.source_id,
                    claim_type=claim_type,
                    aspect=aspect,
                    references=[account.reference] if predicate != "reference" else [value],
                    note=None,
                )
            )
    return claims


def build_claim_graph_for_character(character: Character) -> Dict[str, List[Dict[str, object]]]:
    """Return serialized claims and conflicts for a character."""

    claims = build_claims_for_character(character)
    conflicts = detect_conflicts_from_claims(claims)
    return {
        "claims": [claim.to_dict() for claim in claims],
        "conflicts": [conflict.to_dict() for conflict in conflicts],
    }


def build_claim_graph_for_event(event: Event) -> Dict[str, List[Dict[str, object]]]:
    """Return serialized claims and conflicts for an event."""

    claims = build_claims_for_event(event)
    conflicts = detect_conflicts_from_claims(claims)
    return {
        "claims": [claim.to_dict() for claim in claims],
        "conflicts": [conflict.to_dict() for conflict in conflicts],
    }
