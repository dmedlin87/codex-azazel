"""Tests for bce.export_graph module.

These tests validate the graph snapshot schema (nodes/edges) used for
potential graph database exports.
"""

from __future__ import annotations

from typing import Dict

from bce import storage
from bce.analytics import network as graph_network
from bce.export_graph import (
    EDGE_TYPE_CHARACTER_PARTICIPATED_IN_EVENT,
    EDGE_TYPE_CHARACTER_PROFILE_IN_SOURCE,
    EDGE_TYPE_CHARACTER_RELATIONSHIP,
    EDGE_TYPE_EVENT_PARALLEL_SOURCE,
    EDGE_TYPE_EVENT_REPORTED_IN_SOURCE,
    NODE_TYPE_CHARACTER,
    NODE_TYPE_EVENT,
    NODE_TYPE_SOURCE,
    GraphEdge,
    GraphNode,
    GraphSnapshot,
    build_graph_snapshot,
)


def _index_nodes(snapshot: GraphSnapshot) -> Dict[str, GraphNode]:
    return {node.id: node for node in snapshot.nodes}


def _filter_edges(snapshot: GraphSnapshot, edge_type: str) -> list[GraphEdge]:
    return [e for e in snapshot.edges if e.type == edge_type]


class TestGraphSnapshotBasics:
    """Basic shape and core node/edge presence tests."""

    def test_build_graph_snapshot_basic_shape(self) -> None:
        """Snapshot should contain lists of GraphNode and GraphEdge instances."""
        snapshot = build_graph_snapshot()

        assert isinstance(snapshot, GraphSnapshot)
        assert isinstance(snapshot.nodes, list)
        assert isinstance(snapshot.edges, list)

        assert any(isinstance(n, GraphNode) for n in snapshot.nodes)
        assert any(isinstance(e, GraphEdge) for e in snapshot.edges)

        # Should have at least one node of each core type.
        node_types = {n.type for n in snapshot.nodes}
        assert NODE_TYPE_CHARACTER in node_types
        assert NODE_TYPE_EVENT in node_types
        assert NODE_TYPE_SOURCE in node_types

        # Core edge types should appear in a non-empty dataset.
        edge_types = {e.type for e in snapshot.edges}
        assert EDGE_TYPE_CHARACTER_PARTICIPATED_IN_EVENT in edge_types
        assert EDGE_TYPE_CHARACTER_PROFILE_IN_SOURCE in edge_types
        assert EDGE_TYPE_EVENT_REPORTED_IN_SOURCE in edge_types

    def test_includes_core_character_and_event_nodes(self) -> None:
        """Snapshot should include nodes for Jesus and the crucifixion event."""
        snapshot = build_graph_snapshot()
        nodes_by_id = _index_nodes(snapshot)

        # Node IDs are namespaced with type prefixes.
        assert "character:jesus" in nodes_by_id
        assert nodes_by_id["character:jesus"].type == NODE_TYPE_CHARACTER

        assert "event:crucifixion" in nodes_by_id
        assert nodes_by_id["event:crucifixion"].type == NODE_TYPE_EVENT


class TestParticipationAndSources:
    """Tests for participation and source-related edges."""

    def test_participation_edges_for_crucifixion(self) -> None:
        """Crucifixion should have participation edges from its participants."""
        snapshot = build_graph_snapshot()

        crucifixion_participation = [
            e
            for e in _filter_edges(snapshot, EDGE_TYPE_CHARACTER_PARTICIPATED_IN_EVENT)
            if e.properties.get("event_id") == "crucifixion"
        ]

        assert crucifixion_participation, "expected participation edges for crucifixion"

        # At least one edge from Jesus -> crucifixion.
        assert any(
            e.properties.get("character_id") == "jesus" for e in crucifixion_participation
        )

    def test_character_profile_edges_match_source_profiles(self) -> None:
        """For each character/source profile, there should be a profile edge."""
        snapshot = build_graph_snapshot()
        profile_edges = _filter_edges(snapshot, EDGE_TYPE_CHARACTER_PROFILE_IN_SOURCE)

        # Build a quick index of edges by (char_id, source_id).
        seen_pairs = {
            (e.properties.get("character_id"), e.properties.get("source_id"))
            for e in profile_edges
        }

        for char in storage.iter_characters():
            for profile in char.source_profiles:
                pair = (char.id, profile.source_id)
                assert pair in seen_pairs

    def test_event_reported_in_source_edges_match_accounts(self) -> None:
        """For each event account, there should be an event->source edge."""
        snapshot = build_graph_snapshot()
        account_edges = _filter_edges(snapshot, EDGE_TYPE_EVENT_REPORTED_IN_SOURCE)

        seen_pairs = {
            (e.properties.get("event_id"), e.properties.get("source_id"))
            for e in account_edges
        }

        for event in storage.iter_events():
            for account in event.accounts:
                pair = (event.id, account.source_id)
                assert pair in seen_pairs


class TestParallelsAndRelationships:
    """Tests for parallels and character relationship edges."""

    def test_event_parallel_edges_for_crucifixion(self) -> None:
        """Crucifixion parallels should be represented as event_parallel_source edges."""
        snapshot = build_graph_snapshot()
        parallel_edges = [
            e
            for e in _filter_edges(snapshot, EDGE_TYPE_EVENT_PARALLEL_SOURCE)
            if e.properties.get("event_id") == "crucifixion"
        ]

        # If parallels are defined in the data, expect edges for their sources.
        crucifixion = storage.load_event("crucifixion")
        if crucifixion.parallels:
            assert parallel_edges, "expected parallel edges for crucifixion"
            sources_from_edges = {e.properties.get("source_id") for e in parallel_edges}
            defined_sources = set()
            for para in crucifixion.parallels:
                for sid in para.get("sources") or []:
                    defined_sources.add(sid)
            assert defined_sources.issubset(sources_from_edges)

    def test_character_relationship_edges_for_characters_with_relationships(self) -> None:
        """Characters that declare relationships should produce relationship edges."""
        snapshot = build_graph_snapshot()
        rel_edges = _filter_edges(snapshot, EDGE_TYPE_CHARACTER_RELATIONSHIP)

        # Index edges by their source character node.
        edges_by_source_node: Dict[str, list[GraphEdge]] = {}
        for edge in rel_edges:
            edges_by_source_node.setdefault(edge.source, []).append(edge)

        for char in storage.iter_characters():
            if not char.relationships:
                continue
            node_id = f"character:{char.id}"
            assert node_id in edges_by_source_node, (
                f"Expected relationship edges originating from {node_id} "
                "for character with relationships"
            )


class TestGraphAnalytics:
    """Ensure analytics utilities can operate on the graph snapshot."""

    def test_build_networkx_graph_matches_snapshot_counts(self) -> None:
        snapshot = build_graph_snapshot()
        nx_graph = graph_network.build_networkx_graph(snapshot)

        assert nx_graph.number_of_nodes() == len(snapshot.nodes)
        assert nx_graph.number_of_edges() == len(snapshot.edges)

    def test_centrality_includes_core_character(self) -> None:
        degree_scores = graph_network.compute_degree_centrality()

        assert "character:jesus" in degree_scores
        assert degree_scores["character:jesus"] >= 0

    def test_communities_include_core_character(self) -> None:
        communities = graph_network.detect_communities()

        assert communities, "expected at least one community"
        assert any("character:jesus" in community for community in communities)

    def test_shortest_path_between_character_and_event(self) -> None:
        path = graph_network.shortest_path("character:jesus", "event:crucifixion")

        assert path[0] == "character:jesus"
        assert path[-1] == "event:crucifixion"
        assert len(path) >= 2
