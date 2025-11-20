from __future__ import annotations

from typing import Dict, List, TypedDict


class CharacterDossier(TypedDict):
    id: str
    canonical_name: str
    aliases: List[str]
    roles: List[str]
    source_ids: List[str]
    source_metadata: Dict[str, Dict[str, str]]
    traits_by_source: Dict[str, Dict[str, str]]
    references_by_source: Dict[str, List[str]]
    trait_comparison: Dict[str, Dict[str, str]]
    trait_conflicts: Dict[str, Dict[str, str]]
    trait_conflict_summaries: Dict[str, Dict[str, object]]
    relationships: List[dict]
    parallels: List[dict]


class EventAccountDossier(TypedDict):
    source_id: str
    reference: str
    summary: str
    notes: str | None


class EventDossier(TypedDict):
    id: str
    label: str
    participants: List[str]
    accounts: List[EventAccountDossier]
    account_conflicts: Dict[str, Dict[str, str]]
    account_conflict_summaries: Dict[str, Dict[str, object]]
    parallels: List[dict]


DOSSIER_KEY_ID = "id"
DOSSIER_KEY_CANONICAL_NAME = "canonical_name"
DOSSIER_KEY_LABEL = "label"
DOSSIER_KEY_ALIASES = "aliases"
DOSSIER_KEY_ROLES = "roles"
DOSSIER_KEY_SOURCE_IDS = "source_ids"
DOSSIER_KEY_SOURCE_METADATA = "source_metadata"
DOSSIER_KEY_TRAITS_BY_SOURCE = "traits_by_source"
DOSSIER_KEY_REFERENCES_BY_SOURCE = "references_by_source"
DOSSIER_KEY_VARIANTS_BY_SOURCE = "variants_by_source"
DOSSIER_KEY_CITATIONS_BY_SOURCE = "citations_by_source"
DOSSIER_KEY_TRAIT_COMPARISON = "trait_comparison"
DOSSIER_KEY_TRAIT_CONFLICTS = "trait_conflicts"
DOSSIER_KEY_TRAIT_CONFLICT_SUMMARIES = "trait_conflict_summaries"
DOSSIER_KEY_PARTICIPANTS = "participants"
DOSSIER_KEY_ACCOUNTS = "accounts"
DOSSIER_KEY_ACCOUNT_CONFLICTS = "account_conflicts"
DOSSIER_KEY_ACCOUNT_CONFLICT_SUMMARIES = "account_conflict_summaries"
DOSSIER_KEY_SUMMARY = "summary"
DOSSIER_KEY_DESCRIPTION = "description"
DOSSIER_KEY_RELATIONSHIPS = "relationships"
DOSSIER_KEY_PARALLELS = "parallels"
DOSSIER_KEY_CITATIONS = "citations"
DOSSIER_KEY_TEXTUAL_VARIANTS = "textual_variants"
