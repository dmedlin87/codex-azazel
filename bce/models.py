from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

# =============================================================================
# STANDARD TRAIT KEYS - Controlled Vocabulary
# =============================================================================
# This vocabulary helps maintain consistency across source profiles.
# Validators will warn when trait keys fall outside this set, but won't fail.

STANDARD_TRAIT_KEYS: Set[str] = {
    # Core theological categories
    "christology",
    "eschatology",
    "soteriology",
    "pneumatology",
    "ecclesiology",

    # Mission and ministry
    "mission_focus",
    "teaching_emphasis",
    "ministry_location",
    "ministry_duration",
    "ministry_recipients",

    # Miracles and signs
    "miracles",
    "signs",
    "healings",
    "exorcisms",
    "nature_miracles",

    # Conflict and opposition
    "conflicts",
    "opponents",
    "trial_details",
    "accusations",

    # Death and resurrection
    "death_resurrection",
    "passion_narrative",
    "crucifixion_details",
    "resurrection_details",
    "post_resurrection_appearances",

    # Torah and law
    "torah_stance",
    "halakha_interpretation",
    "purity_laws",
    "sabbath_observance",
    "temple_attitude",

    # Identity and titles
    "messianic_claims",
    "divine_sonship",
    "prophetic_identity",
    "authority_claims",

    # Relationship dynamics
    "discipleship_model",
    "family_relations",
    "gender_inclusivity",
    "social_justice",

    # Literary and rhetorical features
    "parables",
    "apocalyptic_discourse",
    "wisdom_sayings",
    "pronouncement_stories",
    "controversy_stories",

    # Contextual positioning
    "jewish_context",
    "greco_roman_context",
    "political_stance",
    "economic_teaching",

    # Character traits
    "portrayal",
    "character_development",
    "emotions",
    "virtues",
    "vices",

    # Eschatological themes
    "kingdom_of_god",
    "future_hope",
    "judgment_themes",
    "imminent_expectation",
    "realized_eschatology",

    # Spirit and supernatural
    "spirit_activity",
    "angelic_encounters",
    "demonic_opposition",
    "visions",
    "revelations",

    # Community and ethics
    "ethical_teaching",
    "community_formation",
    "ritual_practices",
    "prayer_life",
    "table_fellowship",
}


# =============================================================================
# TEXTUAL VARIANT MODEL
# =============================================================================

@dataclass(slots=True)
class TextualVariant:
    """Represents a textual variant reading from different manuscript families.

    This model captures differences between manuscript traditions (MT, LXX, DSS, etc.)
    that are significant for understanding character portrayals or event details.

    Examples:
        - Goliath's height: MT "six cubits" vs LXX "four cubits"
        - Deuteronomy 32:8: MT "sons of Israel" vs LXX/DSS "sons of God"
        - P46 variant readings in Pauline epistles
    """

    manuscript_family: str  # e.g., "MT", "LXX", "4QSamuel-a", "P46", "Codex Sinaiticus"
    reading: str  # The specific text or value in this tradition
    significance: str  # Why this variant matters for interpretation

    def __post_init__(self) -> None:
        """Validate required fields are non-empty."""
        if not self.manuscript_family:
            raise ValueError("manuscript_family cannot be empty")
        if not self.reading:
            raise ValueError("reading cannot be empty")
        if not self.significance:
            raise ValueError("significance cannot be empty")


# =============================================================================
# SOURCE PROFILE MODEL
# =============================================================================

@dataclass(slots=True)
class SourceProfile:
    """Per-source character profile with traits, references, and optional variants/citations.

    This is the core model for source-critical analysis, allowing each source
    (Mark, Q, Paul, etc.) to present its own distinct portrayal of a character.
    """

    source_id: str
    traits: Dict[str, str] = field(default_factory=dict)
    structured_traits: Dict[str, Any] = field(default_factory=dict)
    trait_notes: Dict[str, str] = field(default_factory=dict)
    references: List[str] = field(default_factory=list)
    variants: List[TextualVariant] = field(default_factory=list)  # NEW: Textual variants
    citations: List[str] = field(default_factory=list)  # NEW: Bibliography keys

    def __post_init__(self) -> None:
        """Keep legacy and new trait fields in sync."""
        # If callers provide only traits, reflect them into trait_notes for prose.
        if self.traits and not self.trait_notes:
            self.trait_notes = dict(self.traits)
        # If callers provide only trait_notes, keep traits for backward compatibility.
        if self.trait_notes and not self.traits:
            self.traits = dict(self.trait_notes)

    def has_trait(self, trait: str) -> bool:
        return trait in self.traits

    def get_trait(self, trait: str, default: Optional[str] = None) -> Optional[str]:
        return self.traits.get(trait, default)


@dataclass(slots=True)
class SourceMetadata:
    source_id: str
    date_range: Optional[str] = None
    provenance: Optional[str] = None
    audience: Optional[str] = None
    depends_on: List[str] = field(default_factory=list)


@dataclass(slots=True)
class RelationshipAttestation:
    """Attestation for a relationship from a specific source."""

    source_id: str
    references: List[str] = field(default_factory=list)


@dataclass(slots=True)
class Relationship:
    """First-class relationship between two characters."""

    source_id: str  # owner/subject of the relationship
    target_id: str  # other character
    type: str
    attestation: List[RelationshipAttestation] = field(default_factory=list)
    strength: Optional[float] = None
    notes: Optional[str] = None
    description: Optional[str] = None

    @classmethod
    def from_raw(cls, raw: dict, owner_id: str) -> "Relationship":
        """Build from legacy or new-form dict data."""
        if not isinstance(raw, dict):
            raise ValueError("Relationship raw value must be a dict")

        # Legacy format: character_id + sources/references/notes
        target = raw.get("target_id") or raw.get("character_id") or raw.get("to")
        rel_type = raw.get("type") or raw.get("relationship_type") or "relationship"
        notes = raw.get("notes") or raw.get("description")
        strength = raw.get("strength")

        attestation: List[RelationshipAttestation] = []

        if "attestation" in raw and isinstance(raw.get("attestation"), list):
            for att in raw["attestation"]:
                if not isinstance(att, dict):
                    continue
                src = att.get("source_id")
                if not isinstance(src, str) or not src:
                    continue
                refs = att.get("references") if isinstance(att.get("references"), list) else []
                attestation.append(RelationshipAttestation(src, list(refs)))
        else:
            sources = raw.get("sources") if isinstance(raw.get("sources"), list) else []
            references = raw.get("references") if isinstance(raw.get("references"), list) else []
            for src in sources:
                if isinstance(src, str) and src:
                    attestation.append(RelationshipAttestation(src, list(references)))

        return cls(
            source_id=owner_id,
            target_id=str(target) if target is not None else "",
            type=str(rel_type) if rel_type is not None else "",
            attestation=attestation,
            strength=strength if isinstance(strength, (int, float)) else None,
            notes=notes if isinstance(notes, str) else None,
            description=notes if isinstance(notes, str) else raw.get("description"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable representation."""
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "type": self.type,
            "attestation": [
                {"source_id": att.source_id, "references": list(att.references)}
                for att in self.attestation
            ],
            "strength": self.strength,
            "notes": self.notes,
            "description": self.description,
        }


@dataclass(slots=True)
class Character:
    id: str
    canonical_name: str
    aliases: List[str] = field(default_factory=list)
    roles: List[str] = field(default_factory=list)
    source_profiles: List[SourceProfile] = field(default_factory=list)
    relationships: List[Relationship] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    citations: List[str] = field(default_factory=list)  # NEW: Bibliography keys

    def get_source_profile(self, source_id: str) -> Optional[SourceProfile]:
        for profile in self.source_profiles:
            if profile.source_id == source_id:
                return profile
        return None

    def list_sources(self) -> List[str]:
        seen = set()
        result: List[str] = []
        for profile in self.source_profiles:
            if profile.source_id not in seen:
                seen.add(profile.source_id)
                result.append(profile.source_id)
        return result

    def has_trait(self, trait: str, source: Optional[str] = None) -> bool:
        """Return True when a trait or tag matches the requested name."""

        needle = trait.lower()

        if source is not None:
            profile = self.get_source_profile(source)
            if profile and any(k.lower() == needle for k in profile.traits.keys()):
                return True
            # Fallback to tag lookup so callers that previously relied on
            # global character tags continue to work when a specific source is
            # requested.
            return any(isinstance(tag, str) and tag.lower() == needle for tag in self.tags)

        for profile in self.source_profiles:
            if any(k.lower() == needle for k in profile.traits.keys()):
                return True
        return any(isinstance(tag, str) and tag.lower() == needle for tag in self.tags)


@dataclass(slots=True)
class EventAccount:
    """Per-source event account with summary, references, and optional variants.

    Each source may report the same event differently, with textual variants
    capturing manuscript-level differences in how the event is described.
    """

    source_id: str
    reference: str
    summary: str
    notes: Optional[str] = None
    variants: List[TextualVariant] = field(default_factory=list)  # NEW: Textual variants


@dataclass(slots=True)
class Event:
    """Biblical event with multiple source accounts and optional citations.

    Events capture key moments in biblical narrative (crucifixion, resurrection,
    Damascus road, etc.) with source-specific accounts and scholarly citations.
    """

    id: str
    label: str
    participants: List[str] = field(default_factory=list)
    accounts: List[EventAccount] = field(default_factory=list)
    parallels: List[dict] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    citations: List[str] = field(default_factory=list)  # NEW: Bibliography keys
    textual_variants: List[dict] = field(default_factory=list)  # NEW: Major textual variants
