from __future__ import annotations

from typing import get_args, get_origin, get_type_hints

from bce.dossier_types import (
    CharacterDossier,
    ClaimGraphBlock,
    EventAccountDossier,
    EventDossier,
    DOSSIER_KEY_ACCOUNTS,
    DOSSIER_KEY_ALIASES,
    DOSSIER_KEY_ACCOUNT_CONFLICTS,
    DOSSIER_KEY_ACCOUNT_CONFLICT_SUMMARIES,
    DOSSIER_KEY_CANONICAL_NAME,
    DOSSIER_KEY_DESCRIPTION,
    DOSSIER_KEY_ID,
    DOSSIER_KEY_LABEL,
    DOSSIER_KEY_PARTICIPANTS,
    DOSSIER_KEY_REFERENCES_BY_SOURCE,
    DOSSIER_KEY_RELATIONSHIPS,
    DOSSIER_KEY_RELATIONSHIPS_BY_TYPE,
    DOSSIER_KEY_ROLES,
    DOSSIER_KEY_SOURCE_IDS,
    DOSSIER_KEY_SOURCE_METADATA,
    DOSSIER_KEY_SUMMARY,
    DOSSIER_KEY_TRAIT_COMPARISON,
    DOSSIER_KEY_TRAIT_CONFLICTS,
    DOSSIER_KEY_TRAIT_CONFLICT_SUMMARIES,
    DOSSIER_KEY_TRAITS_BY_SOURCE,
    DOSSIER_KEY_PARALLELS,
    DOSSIER_KEY_CLAIM_GRAPH,
)


def test_character_dossier_typed_dict_keys() -> None:
    # Ensure the CharacterDossier schema exposes the expected keys
    expected_keys = {
        DOSSIER_KEY_ID,
        DOSSIER_KEY_CANONICAL_NAME,
        DOSSIER_KEY_ALIASES,
        DOSSIER_KEY_ROLES,
        DOSSIER_KEY_SOURCE_IDS,
        DOSSIER_KEY_SOURCE_METADATA,
        DOSSIER_KEY_TRAITS_BY_SOURCE,
        DOSSIER_KEY_REFERENCES_BY_SOURCE,
        DOSSIER_KEY_TRAIT_COMPARISON,
        DOSSIER_KEY_TRAIT_CONFLICTS,
        DOSSIER_KEY_TRAIT_CONFLICT_SUMMARIES,
        DOSSIER_KEY_RELATIONSHIPS,
        DOSSIER_KEY_RELATIONSHIPS_BY_TYPE,
        DOSSIER_KEY_PARALLELS,
        DOSSIER_KEY_CLAIM_GRAPH,
    }

    assert set(CharacterDossier.__annotations__.keys()) == expected_keys


def test_event_dossier_typed_dict_keys() -> None:
    # Ensure the EventDossier schema exposes the expected keys
    expected_keys = {
        DOSSIER_KEY_ID,
        DOSSIER_KEY_LABEL,
        DOSSIER_KEY_PARTICIPANTS,
        DOSSIER_KEY_ACCOUNTS,
        DOSSIER_KEY_ACCOUNT_CONFLICTS,
        DOSSIER_KEY_ACCOUNT_CONFLICT_SUMMARIES,
        DOSSIER_KEY_PARALLELS,
        DOSSIER_KEY_CLAIM_GRAPH,
    }

    assert set(EventDossier.__annotations__.keys()) == expected_keys


def test_event_account_dossier_typed_dict_keys() -> None:
    # Ensure the EventAccountDossier schema exposes the expected keys
    expected_keys = {
        "source_id",
        "reference",
        DOSSIER_KEY_SUMMARY,
        "notes",
    }

    assert set(EventAccountDossier.__annotations__.keys()) == expected_keys


def test_dossier_key_constant_values() -> None:
    # These values form the public JSON shape; guard against accidental renames.
    assert DOSSIER_KEY_ID == "id"
    assert DOSSIER_KEY_CANONICAL_NAME == "canonical_name"
    assert DOSSIER_KEY_LABEL == "label"
    assert DOSSIER_KEY_ALIASES == "aliases"
    assert DOSSIER_KEY_ROLES == "roles"
    assert DOSSIER_KEY_SOURCE_IDS == "source_ids"
    assert DOSSIER_KEY_SOURCE_METADATA == "source_metadata"
    assert DOSSIER_KEY_TRAITS_BY_SOURCE == "traits_by_source"
    assert DOSSIER_KEY_REFERENCES_BY_SOURCE == "references_by_source"
    assert DOSSIER_KEY_TRAIT_COMPARISON == "trait_comparison"
    assert DOSSIER_KEY_TRAIT_CONFLICTS == "trait_conflicts"
    assert DOSSIER_KEY_PARTICIPANTS == "participants"
    assert DOSSIER_KEY_ACCOUNTS == "accounts"
    assert DOSSIER_KEY_ACCOUNT_CONFLICTS == "account_conflicts"
    assert DOSSIER_KEY_SUMMARY == "summary"
    assert DOSSIER_KEY_DESCRIPTION == "description"
    assert DOSSIER_KEY_RELATIONSHIPS == "relationships"
    assert DOSSIER_KEY_PARALLELS == "parallels"
    assert DOSSIER_KEY_CLAIM_GRAPH == "claim_graph"


def test_character_dossier_container_types() -> None:
    hints = get_type_hints(CharacterDossier)
    assert get_origin(hints["aliases"]) is list
    assert get_args(hints["aliases"]) == (str,)
    assert get_origin(hints["roles"]) is list
    assert get_args(hints["roles"]) == (str,)
    assert get_origin(hints["source_ids"]) is list
    assert get_args(hints["source_ids"]) == (str,)
    source_metadata = hints["source_metadata"]
    assert get_origin(source_metadata) is dict
    sm_key, sm_value = get_args(source_metadata)
    assert sm_key is str
    assert get_origin(sm_value) is dict
    assert get_args(sm_value) == (str, str)
    traits = hints["traits_by_source"]
    assert get_origin(traits) is dict
    traits_key, traits_value = get_args(traits)
    assert traits_key is str
    assert get_origin(traits_value) is dict
    assert get_args(traits_value) == (str, str)
    references = hints["references_by_source"]
    assert get_origin(references) is dict
    references_key, references_value = get_args(references)
    assert references_key is str
    assert get_origin(references_value) is list
    assert get_args(references_value) == (str,)
    relationships = hints["relationships"]
    assert get_origin(relationships) is list
    rel_args = get_args(relationships)
    assert rel_args == (dict,)
    comparison = hints["trait_comparison"]
    assert get_origin(comparison) is dict
    comparison_key, comparison_value = get_args(comparison)
    assert comparison_key is str
    assert get_origin(comparison_value) is dict
    assert get_args(comparison_value) == (str, str)
    conflicts = hints["trait_conflicts"]
    assert get_origin(conflicts) is dict
    conflicts_key, conflicts_value = get_args(conflicts)
    assert conflicts_key is str
    assert get_origin(conflicts_value) is dict
    assert get_args(conflicts_value) == (str, str)
    parallels = hints["parallels"]
    assert get_origin(parallels) is list
    parallels_args = get_args(parallels)
    assert parallels_args == (dict,)
    assert hints["claim_graph"] is ClaimGraphBlock


def test_event_dossier_accounts_reference_event_account_dossier() -> None:
    hints = get_type_hints(EventDossier)
    accounts = hints["accounts"]
    assert get_origin(accounts) is list
    assert get_args(accounts) == (EventAccountDossier,)
    conflicts = hints["account_conflicts"]
    assert get_origin(conflicts) is dict
    conflicts_key, conflicts_value = get_args(conflicts)
    assert conflicts_key is str
    assert get_origin(conflicts_value) is dict
    assert get_args(conflicts_value) == (str, str)
    assert hints["claim_graph"] is ClaimGraphBlock


def test_event_account_dossier_notes_optional() -> None:
    hints = get_type_hints(EventAccountDossier)
    notes = hints["notes"]
    args = get_args(notes)
    assert set(args) == {str, type(None)}
