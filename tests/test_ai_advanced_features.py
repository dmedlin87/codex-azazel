"""
Tests for Phase 7 Advanced AI Features.

Tests the three new feature enhancements:
1. Virtual Source Hypothesis Modeling
2. Narrative Trajectory Mapping
3. External Corpus Ingestion
"""

from __future__ import annotations

import pytest

from bce import api

<<<<<<< HEAD
=======
# Check if numpy is available for embedding tests
try:
    import numpy
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

>>>>>>> ef9fdd51577946e97063a3a4a5223e7c1b7c5f80

# =============================================================================
# Feature 1: Virtual Source Hypothesis Modeling
# =============================================================================

class TestVirtualSourceHypothesis:
    """Tests for virtual source hypothesis modeling."""

    def test_list_source_hypotheses(self):
        """Test listing predefined source hypotheses."""
        hypotheses = api.list_source_hypotheses()

        assert isinstance(hypotheses, list)
        assert len(hypotheses) > 0

        # Check Q source is present
        q_source = next((h for h in hypotheses if h["source_id"] == "q_source"), None)
        assert q_source is not None
        assert q_source["label"] == "Q Source"
        assert "matthew" in q_source["base_sources"]
        assert "luke" in q_source["base_sources"]
        assert "mark" in q_source["exclude_sources"]

        # Check triple tradition is present
        triple = next((h for h in hypotheses if h["source_id"] == "triple_tradition"), None)
        assert triple is not None
        assert triple["operation"] == "intersection"

    def test_query_virtual_source_q(self):
        """Test querying Q source hypothesis."""
        results = api.query_virtual_source("q_source", ["jesus"])

        assert "hypothesis" in results
        assert results["hypothesis"]["source_id"] == "q_source"
        assert "results" in results
        assert "summary" in results

        # Check summary fields
        assert "characters_analyzed" in results["summary"]
        assert results["summary"]["characters_analyzed"] == 1

    def test_query_virtual_source_triple_tradition(self):
        """Test querying triple tradition (all Synoptics)."""
        results = api.query_virtual_source("triple_tradition", ["jesus"])

        assert results["hypothesis"]["operation"] == "intersection"
        assert len(results["results"]) == 1

        # Jesus should have some triple tradition material
        jesus_result = results["results"][0]
        assert jesus_result["character_id"] == "jesus"

    def test_query_virtual_source_all_characters(self):
        """Test querying hypothesis across all characters."""
        results = api.query_virtual_source("q_source")

        assert results["summary"]["characters_analyzed"] > 1
        # Most characters won't have Q material
        assert results["summary"]["characters_with_data"] <= results["summary"]["characters_analyzed"]

    def test_query_unknown_hypothesis_raises(self):
        """Test that unknown hypothesis raises error."""
        with pytest.raises(ValueError, match="Unknown hypothesis"):
            api.query_virtual_source("nonexistent_hypothesis")

    def test_analyze_synoptic_layers(self):
        """Test synoptic layer analysis."""
        layers = api.analyze_synoptic_layers("jesus")

        assert "character_id" in layers
        assert layers["character_id"] == "jesus"
        assert "layers" in layers
        assert "summary" in layers

        # Check expected layers
        assert "triple_tradition" in layers["layers"]
        assert "q_source" in layers["layers"]
        assert "special_matthew" in layers["layers"]
        assert "special_luke" in layers["layers"]

        # Each layer should have label and traits
        for layer_id, layer_data in layers["layers"].items():
            if "error" not in layer_data:
                assert "label" in layer_data
                assert "traits" in layer_data or "trait_count" in layer_data

    def test_compare_hypothesis_to_source(self):
        """Test comparing virtual source to actual source."""
        cmp = api.compare_hypothesis_to_source("q_source", "jesus", "john")

        assert "character_id" in cmp
        assert "hypothesis" in cmp
        assert "compare_source" in cmp

        # Should have comparison results
        if "error" not in cmp:
            assert "shared_traits" in cmp
            assert "only_in_hypothesis" in cmp
            assert "only_in_actual" in cmp
            assert "overlap_ratio" in cmp
            assert 0 <= cmp["overlap_ratio"] <= 1


# =============================================================================
# Feature 2: Narrative Trajectory Mapping
# =============================================================================

class TestNarrativeTrajectory:
    """Tests for narrative trajectory mapping."""

    def test_list_biblical_locations(self):
        """Test listing biblical locations."""
        locs = api.list_biblical_locations()

        assert isinstance(locs, list)
        assert len(locs) > 0

        # Check Jerusalem is present
        jerusalem = next((l for l in locs if l["id"] == "jerusalem"), None)
        assert jerusalem is not None
        assert jerusalem["name"] == "Jerusalem"
        assert "latitude" in jerusalem
        assert "longitude" in jerusalem
        assert jerusalem["region"] == "Judea"

    def test_build_character_trajectory(self):
        """Test building character trajectory."""
        traj = api.build_character_trajectory("jesus", "mark")

        assert "character_id" in traj
        assert traj["character_id"] == "jesus"
        assert "source_id" in traj
        assert traj["source_id"] == "mark"
        assert "waypoints" in traj
        assert "total_distance_km" in traj
        assert "unique_locations" in traj

        # Distance should be non-negative
        assert traj["total_distance_km"] >= 0

        # Waypoints should have proper structure
        for wp in traj["waypoints"]:
            assert "sequence" in wp
            assert "location_id" in wp

    def test_build_trajectory_unknown_source(self):
        """Test building trajectory for source with no profile."""
        traj = api.build_character_trajectory("jesus", "nonexistent_source")

        # Should return empty trajectory, not error
        assert traj["waypoints"] == []
        assert traj["total_distance_km"] == 0

    def test_compare_trajectories(self):
        """Test comparing trajectories across sources."""
        cmp = api.compare_trajectories("jesus", ["mark", "john"])

        assert "character_id" in cmp
        assert "sources" in cmp
        assert cmp["sources"] == ["mark", "john"]
        assert "divergence_points" in cmp
        assert "convergence_points" in cmp
        assert "total_divergence_score" in cmp

        # Score should be 0-1
        assert 0 <= cmp["total_divergence_score"] <= 1

    def test_generate_trajectory_geojson(self):
        """Test GeoJSON generation."""
        geojson = api.generate_trajectory_geojson("jesus", "mark")

        assert geojson["type"] == "FeatureCollection"
        assert "features" in geojson

        # Features should have proper GeoJSON structure
        for feature in geojson["features"]:
            assert "type" in feature
            assert feature["type"] == "Feature"
            assert "geometry" in feature
            assert "properties" in feature

    def test_get_divergent_paths(self):
        """Test getting divergent paths data."""
        paths = api.get_divergent_paths("jesus")

        assert "character_id" in paths
        assert "paths" in paths
        assert "divergence_score" in paths

        # Should have paths for default sources
        for src in ["mark", "matthew", "luke", "john"]:
            assert src in paths["paths"]
            assert isinstance(paths["paths"][src], list)

    def test_analyze_jerusalem_visits(self):
        """Test Jerusalem visits analysis."""
        visits = api.analyze_jerusalem_visits("jesus")

        assert "character_id" in visits
        assert visits["character_id"] == "jesus"
        assert "location" in visits
        assert visits["location"] == "jerusalem"
        assert "visits_per_source" in visits
        assert "divergence_detected" in visits
        assert "analysis" in visits

        # Should have synoptic and johannine patterns
        assert "synoptic_pattern" in visits["analysis"]
        assert "johannine_pattern" in visits["analysis"]


# =============================================================================
# Feature 3: External Corpus Ingestion
# =============================================================================

class TestExternalCorpusIngestion:
    """Tests for external corpus ingestion."""

    def test_list_external_corpora(self):
        """Test listing external corpora."""
        corpora = api.list_external_corpora()

        assert isinstance(corpora, list)
        assert len(corpora) > 0

        # Check 1 Enoch is present (key for Azazel)
        enoch = next((c for c in corpora if c["corpus_id"] == "1_enoch"), None)
        assert enoch is not None
        assert "1 Enoch" in enoch["name"]
        assert enoch["date_range"] is not None
        assert enoch["relevance"] == "high"

        # Check Gospel of Thomas is present
        thomas = next((c for c in corpora if c["corpus_id"] == "gospel_thomas"), None)
        assert thomas is not None

<<<<<<< HEAD
=======
    @pytest.mark.skipif(not HAS_NUMPY, reason="Requires numpy for embeddings")
>>>>>>> ef9fdd51577946e97063a3a4a5223e7c1b7c5f80
    def test_ingest_external_text(self):
        """Test ingesting external text."""
        text = "And Azazel taught men to make swords and knives and shields."
        result = api.ingest_external_text(
            "1_enoch",
            text,
            reference="1 Enoch 8:1"
        )

        assert "corpus_id" in result
        assert result["corpus_id"] == "1_enoch"
        assert "chunks_created" in result
        assert result["chunks_created"] >= 1

    def test_ingest_invalid_corpus_raises(self):
        """Test that unknown corpus raises error."""
        with pytest.raises(ValueError, match="Unknown corpus"):
            api.ingest_external_text(
                "nonexistent_corpus",
                "Some text"
            )

<<<<<<< HEAD
=======
    @pytest.mark.skipif(not HAS_NUMPY, reason="Requires numpy for embeddings")
>>>>>>> ef9fdd51577946e97063a3a4a5223e7c1b7c5f80
    def test_search_external_corpus(self):
        """Test searching external corpus."""
        # First ingest some text
        api.ingest_external_text(
            "1_enoch",
            "The fallen angels bound Azazel in chains of darkness until judgment.",
            reference="1 Enoch 10:4"
        )

        # Search for it
        results = api.search_external_corpus(
            "fallen angels chains",
            corpus_ids=["1_enoch"],
            top_k=5
        )

        assert isinstance(results, list)
        # Results should have proper structure
        for r in results:
            assert "corpus_id" in r
            assert "text" in r
            assert "similarity_score" in r

<<<<<<< HEAD
=======
    @pytest.mark.skipif(not HAS_NUMPY, reason="Requires numpy for embeddings")
>>>>>>> ef9fdd51577946e97063a3a4a5223e7c1b7c5f80
    def test_search_empty_corpus_returns_empty(self):
        """Test searching with no matches returns empty list."""
        results = api.search_external_corpus(
            "completely unrelated xyz query",
            corpus_ids=["josephus_wars"],  # Likely empty
            min_score=0.9  # Very high threshold
        )

        assert isinstance(results, list)

<<<<<<< HEAD
=======
    @pytest.mark.skipif(not HAS_NUMPY, reason="Requires numpy for embeddings")
>>>>>>> ef9fdd51577946e97063a3a4a5223e7c1b7c5f80
    def test_compare_character_to_external(self):
        """Test comparing character to external corpus."""
        cmp = api.compare_character_to_external("azazel", ["1_enoch"])

        assert "character_id" in cmp
        assert cmp["character_id"] == "azazel"
        assert "character_name" in cmp
        assert "external_parallels" in cmp
        assert "corpora_searched" in cmp

        # Parallels should have proper structure
        for p in cmp["external_parallels"]:
            assert "corpus" in p
            assert "text" in p
            assert "similarity" in p

<<<<<<< HEAD
=======
    @pytest.mark.skipif(not HAS_NUMPY, reason="Requires numpy for embeddings")
>>>>>>> ef9fdd51577946e97063a3a4a5223e7c1b7c5f80
    def test_find_azazel_traditions(self):
        """Test finding Azazel traditions."""
        traditions = api.find_azazel_traditions()

        assert "character" in traditions
        assert traditions["character"] == "azazel"
        assert "search_scope" in traditions
        assert "results" in traditions
        assert "traditions_found" in traditions
        assert "note" in traditions

        # Should have searched relevant corpora
        assert "Second Temple" in traditions["search_scope"]

    def test_get_corpus_status(self):
        """Test getting corpus ingestion status."""
        status = api.get_corpus_status()

        assert "total_corpora" in status
        assert "ingested_corpora" in status
        assert "corpora" in status

        assert status["total_corpora"] > 0


# =============================================================================
# Integration Tests
# =============================================================================

class TestAdvancedFeaturesIntegration:
    """Integration tests across features."""

    def test_synoptic_analysis_with_trajectory(self):
        """Test combining synoptic analysis with trajectory."""
        # Get Q material for Jesus
        q_results = api.query_virtual_source("q_source", ["jesus"])

        # Get trajectory divergence
        paths = api.get_divergent_paths("jesus", ["mark", "matthew", "luke"])

        # Both should complete without error
        assert q_results["hypothesis"]["source_id"] == "q_source"
        assert len(paths["paths"]) == 3

<<<<<<< HEAD
=======
    @pytest.mark.skipif(not HAS_NUMPY, reason="Requires numpy for embeddings")
>>>>>>> ef9fdd51577946e97063a3a4a5223e7c1b7c5f80
    def test_azazel_full_analysis(self):
        """Test comprehensive Azazel analysis using all features."""
        # 1. Synoptic layers (even though Azazel is OT)
        layers = api.analyze_synoptic_layers("azazel")
        assert "character_id" in layers

        # 2. External corpus traditions
        traditions = api.find_azazel_traditions()
        assert traditions["character"] == "azazel"

        # 3. Compare to external (if corpus has data)
        cmp = api.compare_character_to_external("azazel", ["1_enoch"])
        assert cmp["character_id"] == "azazel"

    def test_multiple_sources_comparison(self):
        """Test comparing multiple source hypotheses."""
        # Compare Q to John for Jesus
        q_vs_john = api.compare_hypothesis_to_source("q_source", "jesus", "john")

        # Compare triple tradition to John
        triple_vs_john = api.compare_hypothesis_to_source(
            "triple_tradition", "jesus", "john"
        )

        # Both should have overlap ratios
        if "error" not in q_vs_john:
            assert "overlap_ratio" in q_vs_john
        if "error" not in triple_vs_john:
            assert "overlap_ratio" in triple_vs_john
