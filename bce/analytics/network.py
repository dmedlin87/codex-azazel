from __future__ import annotations

from typing import Dict, List, Optional, Set

import networkx as nx

from bce.export_graph import GraphSnapshot, build_graph_snapshot


def build_networkx_graph(snapshot: Optional[GraphSnapshot] = None) -> nx.MultiDiGraph:
    """Construct a NetworkX ``MultiDiGraph`` from a ``GraphSnapshot``.

    The resulting graph preserves node metadata (``label``, ``type``, and all
    properties) and attaches edge metadata (``type`` plus properties) to each
    multi-edge keyed by the edge ID.
    """

    snapshot = snapshot or build_graph_snapshot()

    graph = nx.MultiDiGraph()

    for node in snapshot.nodes:
        graph.add_node(node.id, label=node.label, type=node.type, **node.properties)

    for edge in snapshot.edges:
        graph.add_edge(edge.source, edge.target, key=edge.id, type=edge.type, **edge.properties)

    return graph


def _as_simple_digraph(graph: nx.MultiDiGraph) -> nx.DiGraph:
    simple = nx.DiGraph()
    simple.add_nodes_from(graph.nodes(data=True))
    simple.add_edges_from((u, v, attrs) for u, v, attrs in graph.edges(data=True))
    return simple


def _as_simple_graph(graph: nx.MultiDiGraph) -> nx.Graph:
    simple = nx.Graph()
    simple.add_nodes_from(graph.nodes(data=True))
    simple.add_edges_from((u, v, attrs) for u, v, attrs in graph.edges(data=True))
    return simple


def compute_degree_centrality(graph: Optional[nx.MultiDiGraph] = None) -> Dict[str, float]:
    """Return degree centrality for all nodes."""

    graph = graph or build_networkx_graph()
    return nx.degree_centrality(_as_simple_digraph(graph))


def compute_betweenness_centrality(graph: Optional[nx.MultiDiGraph] = None) -> Dict[str, float]:
    """Return betweenness centrality for all nodes."""

    graph = graph or build_networkx_graph()
    return nx.betweenness_centrality(_as_simple_digraph(graph))


def compute_eigenvector_centrality(graph: Optional[nx.MultiDiGraph] = None) -> Dict[str, float]:
    """Return eigenvector centrality for all nodes using an undirected view."""

    graph = graph or build_networkx_graph()
    undirected = _as_simple_graph(graph)
    if undirected.number_of_nodes() == 0:
        return {}
    return nx.eigenvector_centrality(undirected, max_iter=1000)


def detect_communities(graph: Optional[nx.MultiDiGraph] = None) -> List[Set[str]]:
    """Detect communities using greedy modularity clustering on an undirected view."""

    graph = graph or build_networkx_graph()
    undirected = _as_simple_graph(graph)
    if undirected.number_of_nodes() == 0:
        return []

    communities = nx.algorithms.community.greedy_modularity_communities(undirected)
    return [set(comm) for comm in communities]


def shortest_path(
    source: str,
    target: str,
    graph: Optional[nx.MultiDiGraph] = None,
    weight: Optional[str] = None,
) -> List[str]:
    """Find a shortest path between two node IDs.

    Parameters
    ----------
    source : str
        Source node identifier (e.g., ``"character:jesus"``).
    target : str
        Target node identifier (e.g., ``"event:crucifixion"``).
    graph : nx.MultiDiGraph, optional
        Existing graph to search. If omitted, a new graph is built from
        ``build_graph_snapshot``.
    weight : str, optional
        Optional edge attribute to use as edge weight when computing the path.
    """

    graph = graph or build_networkx_graph()
    simple = _as_simple_digraph(graph)
    return nx.shortest_path(simple, source=source, target=target, weight=weight)
