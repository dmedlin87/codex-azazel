from __future__ import annotations

from bce.claim_graph import (
    ClaimType,
    build_claim_graph_for_event,
    build_claims_for_character,
    detect_conflicts_from_claims,
)
from bce.models import Character, Event, EventAccount, SourceProfile


def test_claim_type_and_conflict_harmonization_for_character() -> None:
    character = Character(
        id="c1",
        canonical_name="Claim Tester",
        source_profiles=[
            SourceProfile(
                source_id="s1",
                traits={"timeline": "after exile"},
                references=["Ref 1"],
            ),
            SourceProfile(
                source_id="s2",
                traits={"timeline": "before exile"},
                references=["Ref 2"],
            ),
        ],
    )

    claims = build_claims_for_character(character)
    claim_types = {c.predicate: c.claim_type for c in claims}
    assert claim_types["timeline"] is ClaimType.CHRONOLOGY

    conflicts = detect_conflicts_from_claims(claims)
    conflict_index = {conf.predicate: conf for conf in conflicts}

    timeline_conflict = conflict_index["timeline"]
    assert timeline_conflict.conflict_type.startswith("chronology")
    assert timeline_conflict.harmonization_moves
    assert timeline_conflict.severity in {"low", "medium", "high"}


def test_build_claim_graph_for_event_serializes_conflicts() -> None:
    event = Event(
        id="e1",
        label="Test Event",
        accounts=[
            EventAccount(
                source_id="mark",
                reference="Mark 1:1",
                summary="Version one",
                notes="note",
            ),
            EventAccount(
                source_id="john",
                reference="John 1:1",
                summary="Different telling",
                notes=None,
            ),
        ],
    )

    block = build_claim_graph_for_event(event)

    assert "claims" in block
    assert "conflicts" in block
    conflict_map = {conf["predicate"]: conf for conf in block["conflicts"]}

    summary_conflict = conflict_map.get("summary")
    assert summary_conflict
    assert summary_conflict["claim_type"] == ClaimType.NARRATIVE.value
    assert summary_conflict["harmonization_moves"]
