"""
Tests for the contrastive QA pipeline, ensuring plans + plugins behave as expected.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from bce.ai import qa, plugins
from bce.config import BceConfig, reset_default_config, set_default_config
from bce.hooks import HookRegistry
from bce.models import Character, SourceProfile


def _make_dummy_character() -> Character:
    return Character(
        id="jesus",
        canonical_name="Jesus of Nazareth",
        aliases=[],
        roles=[],
        source_profiles=[
            SourceProfile(
                source_id="john",
                traits={"divine_claims": "High"},
                references=["John 1:1"],
            )
        ],
        relationships=[],
        tags=[],
    )


def _make_semantic_results():
    return [
        {
            "type": "character",
            "id": "jesus",
            "match_in": "traits.john.divine_claims",
            "matching_context": "John depicts Jesus as divine",
            "relevance_score": 0.92,
            "explanation": "Strong match",
        },
        {
            "type": "character",
            "id": "peter",
            "match_in": "traits.acts.role",
            "matching_context": "Peter denies Jesus and is restored",
            "relevance_score": 0.68,
            "explanation": "Moderate match",
        },
    ]


def teardown_function():
    """Clean up global state after each test."""
    reset_default_config()
    HookRegistry.clear()
    plugins._PLUGINS_LOADED = False


def test_contrastive_qa_includes_plan_and_plugin_notes(tmp_path: Path):
    config = BceConfig(
        enable_ai_features=True,
        ai_cache_dir=tmp_path,
        enable_hooks=True,
        ai_plugins=["role_sanity"],
    )
    set_default_config(config)
    HookRegistry.clear()
    plugins._PLUGINS_LOADED = False

    dummy_char = _make_dummy_character()
    with patch("bce.ai.qa.semantic_query") as mock_semantic, \
         patch("bce.ai.qa.queries.get_character") as mock_get_character:

        mock_semantic.return_value = _make_semantic_results()
        mock_get_character.return_value = dummy_char

        response = qa.answer("Which character is most divine?", top_k=1, contrast_k=1, min_score=0.1)

        assert response["question"].startswith("Which character")
        assert response["plan"]["mode"] in {"lookup", "contrastive"}
        assert response["answers"]
        assert response["contrast_set"]
        assert response["explanation"]["summary"]
        assert "notes" in response["explanation"]
        assert any("Role sanity check" in note for note in response["explanation"]["notes"])
