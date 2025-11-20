from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from . import storage


NODE_TYPE_CHARACTER = "character"
NODE_TYPE_EVENT = "event"
NODE_TYPE_SOURCE = "source"

EDGE_TYPE_CHARACTER_PARTICIPATED_IN_EVENT = "character_participated_in_event"
EDGE_TYPE_CHARACTER_PROFILE_IN_SOURCE = "character_profile_in_source"
EDGE_TYPE_EVENT_REPORTED_IN_SOURCE = "event_reported_in_source"
EDGE_TYPE_CHARACTER_RELATIONSHIP = "character_relationship"
EDGE_TYPE_EVENT_PARALLEL_SOURCE = "event_parallel_source"


@dataclass(slots=True)
class GraphNode:
    """Lightweight node representation for graph exports."""

    id: str
    label: str
    type: str
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class GraphEdge:
    """Lightweight edge representation for graph exports."""

    id: str
    source: str
    target: str
    type: str
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class GraphSnapshot:
    """In-memory snapshot of the BCE data as a property graph.

    This is intentionally simple and export-agnostic so it can be reused by
    Neo4j, RDF, or other backends without committing to a specific schema.
    """

    nodes: List[GraphNode]
    edges: List[GraphEdge]


def _get_or_create_node(
    nodes_by_id: Dict[str, GraphNode],
    node_id: str,
    label: str,
    node_type: str,
    **props: Any,
) -> GraphNode:
    node = nodes_by_id.get(node_id)
    if node is None:
        node = GraphNode(id=node_id, label=label, type=node_type, properties=dict(props))
        nodes_by_id[node_id] = node
    else:
        node.properties.update(props)
    return node


def build_graph_snapshot() -> GraphSnapshot:
    """Build a simple property-graph view of all BCE characters and events.

    Nodes include:
    - character: one per Character.id
    - event: one per Event.id
    - source: one per source_id seen in character profiles or event accounts

    Edges include:
    - character_participated_in_event: Character -> Event
    - character_profile_in_source: Character -> Source
    - event_reported_in_source: Event -> Source
    - character_relationship: Character -> Character (from relationships field)
    - event_parallel_source: Event -> Source (from event.parallels)
    """

    nodes_by_id: Dict[str, GraphNode] = {}
    edges: List[GraphEdge] = []

    # Character nodes and character->source profile edges.
    for character in storage.iter_characters():
        char_node_id = f"character:{character.id}"
        _get_or_create_node(
            nodes_by_id,
            char_node_id,
            label=character.canonical_name,
            node_type=NODE_TYPE_CHARACTER,
            character_id=character.id,
            aliases=list(character.aliases),
            roles=list(character.roles),
        )

        for profile in character.source_profiles:
            source_node_id = f"source:{profile.source_id}"
            _get_or_create_node(
                nodes_by_id,
                source_node_id,
                label=profile.source_id,
                node_type=NODE_TYPE_SOURCE,
                source_id=profile.source_id,
            )

            edge_id = f"char_profile:{character.id}:{profile.source_id}"
            edges.append(
                GraphEdge(
                    id=edge_id,
                    source=char_node_id,
                    target=source_node_id,
                    type=EDGE_TYPE_CHARACTER_PROFILE_IN_SOURCE,
                    properties={
                        "character_id": character.id,
                        "source_id": profile.source_id,
                        "trait_count": len(profile.traits),
                        "reference_count": len(profile.references),
                    },
                )
            )

    # Event nodes, participant edges, account/source edges, and parallel edges.
    for event in storage.iter_events():
        event_node_id = f"event:{event.id}"
        _get_or_create_node(
            nodes_by_id,
            event_node_id,
            label=event.label,
            node_type=NODE_TYPE_EVENT,
            event_id=event.id,
            participants=list(event.participants),
        )

        # Character participation edges.
        for participant_id in event.participants:
            char_node_id = f"character:{participant_id}"
            _get_or_create_node(
                nodes_by_id,
                char_node_id,
                label=participant_id,
                node_type=NODE_TYPE_CHARACTER,
                character_id=participant_id,
            )
            edge_id = f"char_event:{participant_id}:{event.id}"
            edges.append(
                GraphEdge(
                    id=edge_id,
                    source=char_node_id,
                    target=event_node_id,
                    type=EDGE_TYPE_CHARACTER_PARTICIPATED_IN_EVENT,
                    properties={
                        "character_id": participant_id,
                        "event_id": event.id,
                    },
                )
            )

        # Event accounts -> sources.
        for idx, account in enumerate(event.accounts):
            source_node_id = f"source:{account.source_id}"
            _get_or_create_node(
                nodes_by_id,
                source_node_id,
                label=account.source_id,
                node_type=NODE_TYPE_SOURCE,
                source_id=account.source_id,
            )
            edge_id = f"event_source:{event.id}:{account.source_id}:{idx}"
            edges.append(
                GraphEdge(
                    id=edge_id,
                    source=event_node_id,
                    target=source_node_id,
                    type=EDGE_TYPE_EVENT_REPORTED_IN_SOURCE,
                    properties={
                        "event_id": event.id,
                        "source_id": account.source_id,
                        "reference": account.reference,
                    },
                )
            )

        # Event parallels -> sources.
        for parallel_index, parallel in enumerate(event.parallels):
            sources = parallel.get("sources") or []
            references = parallel.get("references") or {}
            relationship = parallel.get("relationship")

            for source_id in sources:
                source_node_id = f"source:{source_id}"
                _get_or_create_node(
                    nodes_by_id,
                    source_node_id,
                    label=source_id,
                    node_type=NODE_TYPE_SOURCE,
                    source_id=source_id,
                )
                edge_id = f"event_parallel:{event.id}:{parallel_index}:{source_id}"
                props: Dict[str, Any] = {
                    "event_id": event.id,
                    "parallel_index": parallel_index,
                    "source_id": source_id,
                    "relationship": relationship,
                }
                if source_id in references:
                    props["reference"] = references[source_id]
                edges.append(
                    GraphEdge(
                        id=edge_id,
                        source=event_node_id,
                        target=source_node_id,
                        type=EDGE_TYPE_EVENT_PARALLEL_SOURCE,
                        properties=props,
                    )
                )

    # Character relationships (character -> character edges).
    for character in storage.iter_characters():
        char_node_id = f"character:{character.id}"
        _get_or_create_node(
            nodes_by_id,
            char_node_id,
            label=character.canonical_name,
            node_type=NODE_TYPE_CHARACTER,
            character_id=character.id,
        )
        for rel in character.relationships:
            other_id = getattr(rel, "target_id", None)
            if not isinstance(other_id, str) or not other_id:
                continue
            other_node_id = f"character:{other_id}"
            _get_or_create_node(
                nodes_by_id,
                other_node_id,
                label=other_id,
                node_type=NODE_TYPE_CHARACTER,
                character_id=other_id,
            )
            rel_type = getattr(rel, "type", None) or "relationship"
            edge_id = f"char_rel:{character.id}:{other_id}:{rel_type}"
            edges.append(
                GraphEdge(
                    id=edge_id,
                    source=char_node_id,
                    target=other_node_id,
                    type=EDGE_TYPE_CHARACTER_RELATIONSHIP,
                    properties={
                        "relationship_type": rel_type,
                        "sources": [att.source_id for att in getattr(rel, "attestation", [])],
                        "references": [
                            ref for att in getattr(rel, "attestation", []) for ref in getattr(att, "references", [])
                        ],
                        "notes": getattr(rel, "notes", None),
                    },
                )
            )

    return GraphSnapshot(nodes=list(nodes_by_id.values()), edges=edges)
