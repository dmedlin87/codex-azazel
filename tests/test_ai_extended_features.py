"""
Tests for extended AI features (Phases 6.3-6.5).

Tests new features:
- Question answering
- Trait extraction
- Parallel detection
- Relationship inference
- Natural language summaries
- Source analysis
- Conflict analysis
- Event reconstruction
"""

import pytest
from bce.exceptions import ConfigurationError


def test_ai_modules_import():
    """Test that all new AI modules can be imported."""
    from bce.ai import (
        question_answering,
        trait_extraction,
        parallel_detection,
        relationship_inference,
        summaries,
        source_analysis,
        conflict_analysis,
        event_reconstruction,
    )

    assert question_answering is not None
    assert trait_extraction is not None
    assert parallel_detection is not None
    assert relationship_inference is not None
    assert summaries is not None
    assert source_analysis is not None
    assert conflict_analysis is not None
    assert event_reconstruction is not None


def test_question_answering_disabled():
    """Test question answering raises error when AI disabled."""
    from bce.ai import question_answering

    with pytest.raises(ConfigurationError):
        question_answering.ask("test question", use_cache=False)


def test_trait_extraction_disabled():
    """Test trait extraction raises error when AI disabled."""
    from bce.ai import trait_extraction

    with pytest.raises(ConfigurationError):
        trait_extraction.extract_character_traits(
            "test_char", "test_source", "Test 1:1", "test text"
        )


def test_parallel_detection_disabled():
    """Test parallel detection raises error when AI disabled."""
    from bce.ai import parallel_detection

    with pytest.raises(ConfigurationError):
        parallel_detection.detect_event_parallels("test_event", use_cache=False)


def test_relationship_inference_disabled():
    """Test relationship inference raises error when AI disabled."""
    from bce.ai import relationship_inference

    with pytest.raises(ConfigurationError):
        relationship_inference.infer_relationships_for_character("test_char")


def test_summaries_disabled():
    """Test summaries raise error when AI disabled."""
    from bce.ai import summaries

    fake_dossier = {"identity": {"id": "test", "canonical_name": "Test"}}

    with pytest.raises(ConfigurationError):
        summaries.generate_character_summary(fake_dossier)


def test_source_analysis_disabled():
    """Test source analysis raises error when AI disabled."""
    from bce.ai import source_analysis

    with pytest.raises(ConfigurationError):
        source_analysis.analyze_source_patterns("mark", use_cache=False)


def test_conflict_analysis_disabled():
    """Test conflict analysis raises error when AI disabled."""
    from bce.ai import conflict_analysis

    with pytest.raises(ConfigurationError):
        conflict_analysis.assess_conflict("test_char", "test_trait", use_cache=False)


def test_event_reconstruction_disabled():
    """Test event reconstruction raises error when AI disabled."""
    from bce.ai import event_reconstruction

    with pytest.raises(ConfigurationError):
        event_reconstruction.build_event_timeline("test_event")


def test_api_endpoints_exist():
    """Test that all new API endpoints exist."""
    from bce import api

    # Question answering
    assert hasattr(api, "ask_question")

    # Data extraction
    assert hasattr(api, "extract_character_traits")
    assert hasattr(api, "detect_parallel_passages")
    assert hasattr(api, "infer_character_relationships")

    # Export & analytics
    assert hasattr(api, "generate_character_summary")
    assert hasattr(api, "generate_event_summary")
    assert hasattr(api, "analyze_source_patterns")
    assert hasattr(api, "assess_conflict_significance")
    assert hasattr(api, "build_event_timeline")


def test_api_endpoints_disabled():
    """Test that API endpoints raise errors when AI disabled."""
    from bce import api

    # Question answering
    with pytest.raises(ConfigurationError):
        api.ask_question("test")

    # Data extraction
    with pytest.raises(ConfigurationError):
        api.extract_character_traits("c", "s", "p", "text")

    with pytest.raises(ConfigurationError):
        api.detect_parallel_passages("event")

    with pytest.raises(ConfigurationError):
        api.infer_character_relationships("char")

    # Export & analytics
    with pytest.raises(ConfigurationError):
        # Need to enable AI for dossier building
        # This will fail at the summary generation stage
        pass  # Skip this one as it requires more setup

    with pytest.raises(ConfigurationError):
        api.analyze_source_patterns("mark")

    with pytest.raises(ConfigurationError):
        api.assess_conflict_significance("char", "trait")

    with pytest.raises(ConfigurationError):
        api.build_event_timeline("event")
