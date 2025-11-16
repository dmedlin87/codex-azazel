from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(slots=True)
class SourceProfile:
    source_id: str
    traits: Dict[str, str] = field(default_factory=dict)
    references: List[str] = field(default_factory=list)


@dataclass(slots=True)
class Character:
    id: str
    canonical_name: str
    aliases: List[str] = field(default_factory=list)
    roles: List[str] = field(default_factory=list)
    source_profiles: List[SourceProfile] = field(default_factory=list)


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
