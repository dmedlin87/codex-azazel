"""
Thematic clustering for discovering character and event groupings.

This module uses unsupervised learning to automatically discover
thematic groupings across characters and events.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..queries import list_all_characters, list_all_events
from .cache import AIResultCache
from .config import ensure_ai_enabled
from .embeddings import EmbeddingCache


def find_character_clusters(
    num_clusters: int = 8,
    basis: Optional[List[str]] = None,
    use_cache: bool = True,
) -> List[Dict[str, Any]]:
    """Discover thematic clusters among characters.

    Uses K-means clustering on character embeddings to automatically
    identify thematic groupings. Useful for discovering patterns and
    suggesting tags.

    Args:
        num_clusters: Target number of clusters (default: 8)
        basis: Which fields to use for clustering (default: ["traits", "tags", "roles"])
        use_cache: Whether to use cached results (default: True)

    Returns:
        List of cluster dictionaries, each containing:
        - cluster_id: Cluster identifier
        - label: Interpretable cluster label
        - members: List of character IDs in cluster
        - representative_traits: Common traits/themes
        - confidence: Cluster coherence score (0.0-1.0)

    Raises:
        ConfigurationError: If AI features are disabled
        ImportError: If scikit-learn is not installed

    Example:
        >>> clusters = find_character_clusters(num_clusters=5)
        >>> for cluster in clusters:
        ...     print(f"{cluster['label']}: {cluster['members']}")
        Apostolic Leaders: ['peter', 'john', 'james_son_of_zebedee']
        Pauline Circle: ['paul', 'timothy', 'barnabas']
        ...
    """
    ensure_ai_enabled()

    if basis is None:
        basis = ["traits", "tags", "roles"]

    # Check cache first
    cache_key = f"char_clusters_{num_clusters}_{'_'.join(sorted(basis))}"
    if use_cache:
        cache = AIResultCache("clustering", max_age_seconds=7200)
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return cached_result

    # Import scikit-learn (lazy import)
    try:
        from sklearn.cluster import KMeans
    except ImportError:
        raise ImportError(
            "scikit-learn is required for clustering. "
            "Install it with: pip install 'codex-azazel[ai]'"
        )

    # Get all characters and build embeddings
    characters = list_all_characters()

    # Build character embeddings
    char_data = []
    embedding_cache = EmbeddingCache("character_clustering")

    for char in characters:
        texts = []

        if "traits" in basis:
            for profile in char.source_profiles:
                for trait_key, trait_value in profile.traits.items():
                    texts.append(f"{trait_key}: {trait_value}")

        if "tags" in basis and char.tags:
            texts.append(" ".join(char.tags))

        if "roles" in basis and char.roles:
            texts.append(" ".join(char.roles))

        combined_text = " ".join(texts)
        if combined_text.strip():
            embedding = embedding_cache.get_or_compute(combined_text)
            char_data.append({
                "id": char.id,
                "canonical_name": char.canonical_name,
                "text": combined_text,
                "embedding": embedding,
                "tags": char.tags,
                "roles": char.roles,
            })

    if len(char_data) < num_clusters:
        num_clusters = max(2, len(char_data) // 3)

    # Prepare embeddings matrix
    import numpy as np
    embeddings_matrix = np.array([item["embedding"] for item in char_data])

    # Perform clustering
    kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(embeddings_matrix)

    # Build cluster results
    clusters = []
    for cluster_idx in range(num_clusters):
        # Get members
        member_indices = [i for i, label in enumerate(cluster_labels) if label == cluster_idx]
        members = [char_data[i]["id"] for i in member_indices]
        member_names = [char_data[i]["canonical_name"] for i in member_indices]

        # Extract representative traits/tags
        all_tags = []
        all_roles = []
        for i in member_indices:
            all_tags.extend(char_data[i]["tags"])
            all_roles.extend(char_data[i]["roles"])

        # Count frequency
        from collections import Counter
        tag_counts = Counter(all_tags)
        role_counts = Counter(all_roles)

        # Get most common
        representative_traits = []
        if tag_counts:
            representative_traits.extend([tag for tag, count in tag_counts.most_common(3)])
        if role_counts:
            representative_traits.extend([role for role, count in role_counts.most_common(2)])

        # Generate cluster label
        label = _generate_cluster_label(
            member_names, representative_traits, cluster_idx
        )

        # Calculate cluster coherence (average within-cluster similarity)
        coherence = _calculate_cluster_coherence(
            embeddings_matrix, member_indices, kmeans.cluster_centers_[cluster_idx]
        )

        clusters.append({
            "cluster_id": f"cluster_{cluster_idx}",
            "label": label,
            "members": members,
            "member_names": member_names,
            "representative_traits": representative_traits,
            "confidence": round(coherence, 3),
            "size": len(members),
        })

    # Sort by size (descending)
    clusters.sort(key=lambda x: x["size"], reverse=True)

    # Cache the result
    if use_cache:
        cache.set(cache_key, clusters, model_name="kmeans_clustering")

    return clusters


def find_event_clusters(
    num_clusters: int = 5,
    use_cache: bool = True,
) -> List[Dict[str, Any]]:
    """Discover thematic clusters among events.

    Similar to character clustering but for events.

    Args:
        num_clusters: Target number of clusters (default: 5)
        use_cache: Whether to use cached results (default: True)

    Returns:
        List of cluster dictionaries

    Raises:
        ConfigurationError: If AI features are disabled
        ImportError: If scikit-learn is not installed
    """
    ensure_ai_enabled()

    # Check cache first
    cache_key = f"event_clusters_{num_clusters}"
    if use_cache:
        cache = AIResultCache("clustering", max_age_seconds=7200)
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return cached_result

    # Import scikit-learn
    try:
        from sklearn.cluster import KMeans
    except ImportError:
        raise ImportError(
            "scikit-learn is required for clustering. "
            "Install it with: pip install 'codex-azazel[ai]'"
        )

    # Get all events and build embeddings
    events = list_all_events()

    event_data = []
    embedding_cache = EmbeddingCache("event_clustering")

    for event in events:
        # Combine all account summaries
        texts = [f"{acc.summary} {acc.notes or ''}" for acc in event.accounts]

        # Add tags if present
        if event.tags:
            texts.append(" ".join(event.tags))

        combined_text = " ".join(texts)
        if combined_text.strip():
            embedding = embedding_cache.get_or_compute(combined_text)
            event_data.append({
                "id": event.id,
                "label": event.label,
                "text": combined_text,
                "embedding": embedding,
                "tags": event.tags,
            })

    if len(event_data) < num_clusters:
        num_clusters = max(2, len(event_data) // 2)

    # Prepare embeddings matrix
    import numpy as np
    embeddings_matrix = np.array([item["embedding"] for item in event_data])

    # Perform clustering
    kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(embeddings_matrix)

    # Build cluster results
    clusters = []
    for cluster_idx in range(num_clusters):
        member_indices = [i for i, label in enumerate(cluster_labels) if label == cluster_idx]
        members = [event_data[i]["id"] for i in member_indices]
        member_labels = [event_data[i]["label"] for i in member_indices]

        # Extract representative tags
        all_tags = []
        for i in member_indices:
            all_tags.extend(event_data[i]["tags"])

        from collections import Counter
        tag_counts = Counter(all_tags)
        representative_traits = [tag for tag, count in tag_counts.most_common(3)]

        # Generate cluster label
        label = _generate_cluster_label(
            member_labels, representative_traits, cluster_idx
        )

        # Calculate coherence
        coherence = _calculate_cluster_coherence(
            embeddings_matrix, member_indices, kmeans.cluster_centers_[cluster_idx]
        )

        clusters.append({
            "cluster_id": f"event_cluster_{cluster_idx}",
            "label": label,
            "members": members,
            "member_labels": member_labels,
            "representative_traits": representative_traits,
            "confidence": round(coherence, 3),
            "size": len(members),
        })

    # Sort by size
    clusters.sort(key=lambda x: x["size"], reverse=True)

    # Cache the result
    if use_cache:
        cache.set(cache_key, clusters, model_name="kmeans_clustering")

    return clusters


def _generate_cluster_label(
    member_names: List[str],
    representative_traits: List[str],
    cluster_idx: int,
) -> str:
    """Generate an interpretable label for a cluster.

    Args:
        member_names: Names of cluster members
        representative_traits: Common traits/tags
        cluster_idx: Cluster index

    Returns:
        Human-readable cluster label
    """
    if representative_traits:
        # Use most common traits
        primary_trait = representative_traits[0].replace("_", " ").title()
        if len(representative_traits) > 1:
            secondary = representative_traits[1].replace("_", " ").title()
            return f"{primary_trait} and {secondary} Figures"
        else:
            return f"{primary_trait} Cluster"
    else:
        # Fallback to generic label
        return f"Cluster {cluster_idx + 1}"


def _calculate_cluster_coherence(
    embeddings_matrix,
    member_indices: List[int],
    centroid,
) -> float:
    """Calculate cluster coherence (tightness).

    Args:
        embeddings_matrix: All embeddings
        member_indices: Indices of cluster members
        centroid: Cluster centroid

    Returns:
        Coherence score (0.0 to 1.0, higher is better)
    """
    if not member_indices:
        return 0.0

    # Calculate average cosine similarity to centroid
    from .embeddings import cosine_similarity

    similarities = []
    for idx in member_indices:
        embedding = embeddings_matrix[idx]
        similarity = cosine_similarity(embedding, centroid)
        similarities.append(similarity)

    return sum(similarities) / len(similarities) if similarities else 0.0


def suggest_tags_from_clusters(
    clusters: List[Dict[str, Any]],
    min_cluster_size: int = 2,
) -> Dict[str, List[str]]:
    """Suggest tags for characters based on cluster membership.

    Args:
        clusters: Output from find_character_clusters()
        min_cluster_size: Minimum cluster size to consider (default: 2)

    Returns:
        Dictionary mapping character_id -> suggested_tags
    """
    suggestions = {}

    for cluster in clusters:
        if cluster["size"] < min_cluster_size:
            continue

        # Suggest cluster's representative traits as tags
        suggested_tags = cluster["representative_traits"]

        for char_id in cluster["members"]:
            if char_id not in suggestions:
                suggestions[char_id] = []
            suggestions[char_id].extend(suggested_tags)

    # Deduplicate
    for char_id in suggestions:
        suggestions[char_id] = list(set(suggestions[char_id]))

    return suggestions


__all__ = [
    "find_character_clusters",
    "find_event_clusters",
    "suggest_tags_from_clusters",
]
