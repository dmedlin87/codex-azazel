from __future__ import annotations

from typing import Dict

from bce.config import BceConfig, reset_default_config, set_default_config
from bce.models import Character, SourceProfile
from bce.ai import completeness


class TestReviewQueue:
    def setup_method(self):
        reset_default_config()
        set_default_config(BceConfig(enable_ai_features=True))

    def teardown_method(self):
        reset_default_config()

    def test_review_queue_ranks_by_priority(self, monkeypatch):
        """Queue should sort items by blended priority score."""
        fake_chars = [
            Character(id="alpha", canonical_name="Alpha"),
            Character(id="beta", canonical_name="Beta"),
        ]

        audits: Dict[str, Dict[str, object]] = {
            "alpha": {
                "completeness_score": 0.3,
                "gap_count": 3,
            },
            "beta": {
                "completeness_score": 0.85,
                "gap_count": 0,
            },
        }

        conflicts = {
            "alpha": {"tension": {"mark": "x", "john": "y", "severity": "high"}},
            "beta": {},
        }

        monkeypatch.setattr(completeness, "list_all_characters", lambda: fake_chars)
        monkeypatch.setattr(completeness, "get_character", lambda cid: next(c for c in fake_chars if c.id == cid))
        monkeypatch.setattr(
            completeness,
            "audit_character",
            lambda cid, use_cache=True: audits[cid],
        )
        monkeypatch.setattr(
            completeness.contradictions,
            "summarize_character_conflicts",
            lambda cid: conflicts[cid],
        )
        monkeypatch.setattr(
            completeness.semantic_contradictions,
            "analyze_character_traits",
            lambda cid, use_cache=True: {
                "summary": {
                    "different_emphases": 1 if cid == "alpha" else 0,
                    "complementary_details": 0,
                    "genuine_conflicts": 0,
                }
            },
        )

        queue = completeness.build_curation_review_queue(limit=2, use_cache=False)
        assert queue["entity_type"] == "character"
        assert len(queue["items"]) == 2

        # Alpha should rank ahead of Beta due to low completeness and conflicts
        assert queue["items"][0]["id"] == "alpha"
        assert queue["items"][0]["priority_score"] >= queue["items"][1]["priority_score"]


class TestClusterGuardian:
    def setup_method(self):
        reset_default_config()
        set_default_config(BceConfig(enable_ai_features=True))

    def teardown_method(self):
        reset_default_config()

    def test_guardian_flags_missing_role_tags(self, monkeypatch):
        """Cluster guardian should surface missing role-aligned tags."""
        cluster = {
            "cluster_id": "cluster_0",
            "label": "Leaders",
            "members": ["alpha", "beta"],
            "size": 2,
        }

        alpha = Character(
            id="alpha",
            canonical_name="Alpha",
            tags=["leader"],
            roles=["leader"],
            source_profiles=[SourceProfile(source_id="mark", traits={"title": "Leader"})],
        )
        beta = Character(
            id="beta",
            canonical_name="Beta",
            tags=[],
            roles=["leader"],
            source_profiles=[SourceProfile(source_id="mark", traits={"title": "Follower"})],
        )

        monkeypatch.setattr(
            completeness.clustering,
            "find_character_clusters",
            lambda num_clusters=6, use_cache=True, basis=None: [cluster],
        )
        monkeypatch.setattr(completeness, "get_character", lambda cid: alpha if cid == "alpha" else beta)

        result = completeness.run_cluster_guardian(
            num_clusters=1,
            support_threshold=0.5,
            use_cache=False,
        )

        assert result["clusters_checked"] == 1
        members = result["clusters"][0]["members"]
        beta_report = next(m for m in members if m["character_id"] == "beta")
        assert "leader" in beta_report["missing_role_tags"]
        assert beta_report["alignment_score"] < 1.0


class TestSemanticDiffReporter:
    def setup_method(self):
        reset_default_config()
        set_default_config(BceConfig(enable_ai_features=True))

    def teardown_method(self):
        reset_default_config()

    def test_diff_report_tracks_metric_delta(self):
        """Diff report should capture completeness and conflict changes."""
        before = {
            "id": "sample",
            "source_profiles": [],
            "tags": [],
            "relationships": [],
        }
        after = {
            "id": "sample",
            "source_profiles": [
                {
                    "source_id": "mark",
                    "traits": {"focus": "teaching"},
                    "references": ["Mark 1:1"],
                }
            ],
            "tags": ["teacher"],
            "relationships": [{"character_id": "peter"}],
        }

        diff = completeness.describe_json_edit_impact(
            before=before,
            after=after,
            entity_type="character",
            use_cache=False,
        )

        assert diff["deltas"]["completeness_delta"] > 0
        assert diff["deltas"]["gap_delta"] < 0
        assert any("Completeness improved" in line for line in diff["summary"])
