"""Type definitions for character relationships and event parallels.

This module provides strongly-typed structures for relationship data,
replacing the generic List[dict] pattern that prevented type safety.

The Relationship and Parallel dataclasses support the canonical array format
used throughout the BCE data files.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(slots=True)
class Relationship:
    """Represents a relationship between two characters.

    This structure captures biographical and narrative connections between
    biblical characters, including source attestation and supporting references.

    Attributes:
        character_id: ID of the related character
        type: Nature of the relationship (e.g., "teacher_and_commissioner",
              "brother_and_fishing_partner")
        sources: List of source IDs that attest this relationship
        references: Scripture references supporting this relationship
        notes: Optional explanatory notes about the relationship dynamics

    Examples:
        >>> rel = Relationship(
        ...     character_id="jesus",
        ...     type="teacher",
        ...     sources=["mark", "matthew"],
        ...     references=["Mark 1:16-18", "Matthew 4:18-20"],
        ...     notes="Called to discipleship"
        ... )
    """

    character_id: str
    type: str
    sources: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    notes: Optional[str] = None

    def __post_init__(self):
        """Validate required fields."""
        if not self.character_id:
            raise ValueError("character_id cannot be empty")
        if not self.type:
            raise ValueError("type cannot be empty")


@dataclass(slots=True)
class EventParallel:
    """Represents parallel accounts of the same event across multiple sources.

    This structure tracks how different biblical sources narrate the same event,
    enabling cross-source comparison and contradiction analysis.

    Attributes:
        sources: List of source IDs that contain accounts of this event
        references: Mapping of source_id to scripture reference for each account
        relationship: Type of parallel relationship (e.g., "gospel_parallel",
                     "synoptic_parallel")

    Examples:
        >>> parallel = EventParallel(
        ...     sources=["mark", "matthew", "luke"],
        ...     references={
        ...         "mark": "Mark 15:22-37",
        ...         "matthew": "Matthew 27:33-50",
        ...         "luke": "Luke 23:33-46"
        ...     },
        ...     relationship="gospel_parallel"
        ... )
    """

    sources: List[str]
    references: Dict[str, str]
    relationship: str

    def __post_init__(self):
        """Validate structure."""
        if not self.sources:
            raise ValueError("sources cannot be empty")
        if not self.references:
            raise ValueError("references cannot be empty")
        if not self.relationship:
            raise ValueError("relationship cannot be empty")

        # Validate that all sources have corresponding references
        source_set = set(self.sources)
        ref_set = set(self.references.keys())
        if source_set != ref_set:
            missing_refs = source_set - ref_set
            extra_refs = ref_set - source_set
            errors = []
            if missing_refs:
                errors.append(f"Sources without references: {missing_refs}")
            if extra_refs:
                errors.append(f"References without sources: {extra_refs}")
            raise ValueError("; ".join(errors))


def relationship_from_dict(data: dict) -> Relationship:
    """Convert a dictionary to a Relationship instance.

    Supports both the canonical format (character_id, type) and legacy
    format (name, relationship) for backward compatibility.

    Parameters:
        data: Dictionary with relationship data

    Returns:
        Relationship instance

    Raises:
        ValueError: If required fields are missing or invalid

    Examples:
        >>> # Canonical format
        >>> rel = relationship_from_dict({
        ...     "character_id": "jesus",
        ...     "type": "teacher",
        ...     "sources": ["mark"],
        ...     "references": ["Mark 1:16"]
        ... })

        >>> # Legacy format (auto-converted)
        >>> rel = relationship_from_dict({
        ...     "name": "Jesus",
        ...     "relationship": "teacher",
        ...     "sources": ["mark"],
        ...     "references": ["Mark 1:16"]
        ... })
    """
    # Handle legacy format with "name" and "relationship" keys
    if "name" in data and "character_id" not in data:
        # Legacy format - note that "name" was a display name, not an ID
        # This is a best-effort conversion; manual review may be needed
        data = {**data, "character_id": data["name"].lower().replace(" ", "_")}

    if "relationship" in data and "type" not in data:
        data = {**data, "type": data["relationship"]}

    # Extract fields with defaults
    character_id = data.get("character_id", "")
    rel_type = data.get("type", "")
    sources = data.get("sources", [])
    references = data.get("references", [])
    notes = data.get("notes")

    return Relationship(
        character_id=character_id,
        type=rel_type,
        sources=sources if isinstance(sources, list) else [],
        references=references if isinstance(references, list) else [],
        notes=notes
    )


def parallel_from_dict(data: dict) -> EventParallel:
    """Convert a dictionary to an EventParallel instance.

    Parameters:
        data: Dictionary with parallel data

    Returns:
        EventParallel instance

    Raises:
        ValueError: If required fields are missing or invalid
    """
    sources = data.get("sources", [])
    references = data.get("references", {})
    relationship = data.get("relationship", "")

    return EventParallel(
        sources=sources if isinstance(sources, list) else [],
        references=references if isinstance(references, dict) else {},
        relationship=relationship
    )
