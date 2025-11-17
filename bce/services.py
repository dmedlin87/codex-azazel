from __future__ import annotations

from typing import List, Optional

from .models import Character, SourceProfile


def get_source_profile(char: Character, source_id: str) -> Optional[SourceProfile]:
    """Get a character's source profile by source ID.

    This is a service function that operates on Character instances,
    extracting business logic from the data model itself.

    Parameters:
        char: Character instance
        source_id: Source identifier (e.g., "mark", "matthew")

    Returns:
        SourceProfile if found, None otherwise

    Examples:
        >>> char = queries.get_character("jesus")
        >>> profile = get_source_profile(char, "mark")
        >>> if profile:
        ...     print(profile.traits)
    """
    for profile in char.source_profiles:
        if profile.source_id == source_id:
            return profile
    return None


def list_character_sources(char: Character) -> List[str]:
    """List all source IDs that have profiles for this character.

    Removes duplicates and maintains order of first appearance.

    Parameters:
        char: Character instance

    Returns:
        List of unique source IDs

    Examples:
        >>> char = queries.get_character("jesus")
        >>> sources = list_character_sources(char)
        >>> print(sources)
        ['mark', 'matthew', 'luke', 'john']
    """
    seen = set()
    result: List[str] = []
    for profile in char.source_profiles:
        if profile.source_id not in seen:
            seen.add(profile.source_id)
            result.append(profile.source_id)
    return result


def has_trait(
    char: Character,
    trait: str,
    source: Optional[str] = None
) -> bool:
    """Check if character has a specific trait.

    Parameters:
        char: Character instance
        trait: Trait name to check
        source: Optional source ID to check within (default: check all sources)

    Returns:
        True if trait exists, False otherwise

    Examples:
        >>> char = queries.get_character("jesus")
        >>> has_trait(char, "messianic_identity")
        True
        >>> has_trait(char, "messianic_identity", source="mark")
        True
    """
    if source is not None:
        profile = get_source_profile(char, source)
        if profile is None:
            return False
        return trait in profile.traits

    for profile in char.source_profiles:
        if trait in profile.traits:
            return True
    return False


def get_trait_value(
    char: Character,
    trait: str,
    source: str,
    default: Optional[str] = None
) -> Optional[str]:
    """Get a trait value for a specific source.

    Parameters:
        char: Character instance
        trait: Trait name
        source: Source ID
        default: Default value if trait not found

    Returns:
        Trait value if found, otherwise default

    Examples:
        >>> char = queries.get_character("jesus")
        >>> value = get_trait_value(char, "title", "mark", default="unknown")
        >>> print(value)
    """
    profile = get_source_profile(char, source)
    if profile is None:
        return default
    return profile.traits.get(trait, default)
