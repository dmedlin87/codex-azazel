from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(slots=True)
class SourceProfile:
    source_id: str
    traits: Dict[str, str] = field(default_factory=dict)
    references: List[str] = field(default_factory=list)

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
class Character:
    id: str
    canonical_name: str
    aliases: List[str] = field(default_factory=list)
    roles: List[str] = field(default_factory=list)
    source_profiles: List[SourceProfile] = field(default_factory=list)
    relationships: List[dict] = field(default_factory=list)

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
        if source is not None:
            profile = self.get_source_profile(source)
            if profile is None:
                return False
            return profile.has_trait(trait)
        for profile in self.source_profiles:
            if profile.has_trait(trait):
                return True
        return False


@dataclass(slots=True)
class EventAccount:
    source_id: str
    reference: str
    summary: str
    notes: Optional[str] = None


@dataclass(slots=True)
class Event:
    id: str
    label: str
    participants: List[str] = field(default_factory=list)
    accounts: List[EventAccount] = field(default_factory=list)
    parallels: List[dict] = field(default_factory=list)
