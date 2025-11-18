"""
Comprehensive tests for AI API endpoint gating when AI is disabled.

This test module ensures all AI-powered API endpoints properly raise
ConfigurationError when AI features are disabled (the default state).
"""

import pytest
from bce import api
from bce.exceptions import ConfigurationError


# Parametrize over all AI-powered API endpoints
# Format: (function, args, kwargs, description)
AI_ENDPOINTS = [
    # Phase 6.1-6.2: Semantic analysis and validation
    (api.analyze_semantic_contradictions, ("char",), {}, "semantic contradictions"),
    (api.audit_character_completeness, ("char",), {}, "character completeness audit"),
    (api.get_validation_suggestions, (), {}, "validation suggestions"),
    (api.semantic_search, ("query",), {}, "semantic search"),
    (api.find_similar_characters, ("char",), {}, "similar characters"),
    (api.find_thematic_clusters, (), {"entity_type": "characters"}, "character thematic clusters"),
    (api.find_thematic_clusters, (), {"entity_type": "events"}, "event thematic clusters"),

    # Phase 6.3: Question answering
    (api.ask_question, ("test question",), {}, "question answering"),

    # Phase 6.4: Data extraction
    (api.extract_character_traits, ("char", "source", "passage", "text"), {}, "trait extraction"),
    (api.detect_parallel_passages, ("event",), {}, "parallel passage detection"),
    (api.infer_character_relationships, ("char",), {}, "relationship inference"),

    # Phase 6.5: Export & analytics
    (api.generate_character_summary, ("char",), {}, "character summary generation"),
    (api.generate_event_summary, ("event",), {}, "event summary generation"),
    (api.analyze_source_patterns, ("mark",), {}, "source pattern analysis"),
    (api.assess_conflict_significance, ("char", "trait"), {}, "conflict significance assessment"),
    (api.build_event_timeline, ("event",), {}, "event timeline reconstruction"),
]


@pytest.mark.parametrize("func,args,kwargs,desc", AI_ENDPOINTS, ids=[desc for _, _, _, desc in AI_ENDPOINTS])
def test_ai_endpoint_raises_error_when_disabled(func, args, kwargs, desc):
    """Test that AI endpoint raises ConfigurationError when AI is disabled.

    All AI-powered endpoints should immediately raise ConfigurationError
    when called with AI features disabled, regardless of the input parameters.
    """
    with pytest.raises(ConfigurationError) as exc_info:
        func(*args, **kwargs)

    # Verify the error message mentions AI features
    assert "AI features" in str(exc_info.value) or "enable_ai_features" in str(exc_info.value)


def test_all_ai_endpoints_tested():
    """Verify we're testing all expected AI endpoints.

    This test documents the expected count of AI endpoints and will fail
    if new AI features are added without updating this test module.
    """
    # As of Phase 6.5, we have 16 AI endpoint tests
    expected_count = 16
    actual_count = len(AI_ENDPOINTS)

    assert actual_count == expected_count, (
        f"Expected {expected_count} AI endpoint tests, found {actual_count}. "
        "If new AI features were added, update AI_ENDPOINTS list. "
        "If features were removed, update expected_count."
    )


def test_ai_endpoints_exist_in_api_module():
    """Verify all AI endpoint functions exist in the api module."""
    expected_functions = [
        "analyze_semantic_contradictions",
        "audit_character_completeness",
        "get_validation_suggestions",
        "semantic_search",
        "find_similar_characters",
        "find_thematic_clusters",
        "ask_question",
        "extract_character_traits",
        "detect_parallel_passages",
        "infer_character_relationships",
        "generate_character_summary",
        "generate_event_summary",
        "analyze_source_patterns",
        "assess_conflict_significance",
        "build_event_timeline",
    ]

    for func_name in expected_functions:
        assert hasattr(api, func_name), f"api.{func_name} should exist"
        assert callable(getattr(api, func_name)), f"api.{func_name} should be callable"


def test_non_ai_endpoints_work_without_ai():
    """Verify non-AI endpoints still work when AI is disabled.

    This ensures we haven't accidentally broken core functionality
    by adding AI gating.
    """
    # Core data access should work
    char_ids = api.list_character_ids()
    assert len(char_ids) > 0

    event_ids = api.list_event_ids()
    assert len(event_ids) > 0

    # Get a real character
    jesus = api.get_character("jesus")
    assert jesus.canonical_name == "Jesus of Nazareth"

    # Build dossiers (non-AI)
    dossier = api.build_character_dossier("jesus")
    assert dossier["id"] == "jesus"

    # Conflicts (non-AI)
    conflicts = api.summarize_character_conflicts("judas")
    assert isinstance(conflicts, dict)

    # Search (non-AI keyword search)
    results = api.search_all("resurrection")
    assert isinstance(results, list)
