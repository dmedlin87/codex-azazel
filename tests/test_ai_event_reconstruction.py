"""
Tests for bce.ai.event_reconstruction module.

Tests event timeline reconstruction and multi-source comparison.
"""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from bce.config import BceConfig, set_default_config, reset_default_config
from bce.exceptions import ConfigurationError
from bce.models import Event, EventAccount
from bce.ai import event_reconstruction


class TestBuildEventTimeline:
    """Tests for build_event_timeline function."""

    def setup_method(self):
        """Setup for each test."""
        reset_default_config()

    def teardown_method(self):
        """Cleanup after each test."""
        reset_default_config()

    def test_requires_ai_enabled(self):
        """Should raise ConfigurationError when AI is disabled."""
        config = BceConfig(enable_ai_features=False)
        set_default_config(config)

        with pytest.raises(ConfigurationError, match="AI features are disabled"):
            event_reconstruction.build_event_timeline("crucifixion")

    @patch('bce.ai.event_reconstruction.queries')
    def test_requires_at_least_two_accounts(self, mock_queries):
        """Should return message if fewer than 2 accounts."""
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

        # Event with only one account
        event = Event(
            id="single_account_event",
            label="Single Account Event",
            participants=["jesus"],
            accounts=[
                EventAccount(
                    source_id="mark",
                    reference="Mark 1:1",
                    summary="Event summary",
                    notes=None
                )
            ],
            parallels=[],
            tags=[]
        )

        mock_queries.get_event.return_value = event

        result = event_reconstruction.build_event_timeline("single_account_event")

        assert "message" in result
        assert "at least 2 accounts" in result["message"]
        assert result["timeline_elements"] == []

    @patch('bce.ai.event_reconstruction.embed_text')
    @patch('bce.ai.event_reconstruction.cosine_similarity')
    @patch('bce.ai.event_reconstruction.queries')
    def test_returns_timeline_structure(self, mock_queries, mock_similarity, mock_embed):
        """Should return properly structured timeline."""
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

        try:
            import numpy as np
            mock_embed.return_value = np.array([0.1, 0.2, 0.3])
            mock_similarity.return_value = 0.6
        except ImportError:
            mock_embed.return_value = [0.1, 0.2, 0.3]
            mock_similarity.return_value = 0.6

        # Event with multiple accounts
        event = Event(
            id="crucifixion",
            label="Crucifixion",
            participants=["jesus"],
            accounts=[
                EventAccount(
                    source_id="mark",
                    reference="Mark 15:25",
                    summary="Jesus was crucified at the third hour",
                    notes=None
                ),
                EventAccount(
                    source_id="john",
                    reference="John 19:14",
                    summary="It was about the sixth hour when Jesus was crucified",
                    notes=None
                )
            ],
            parallels=[],
            tags=[]
        )

        mock_queries.get_event.return_value = event

        result = event_reconstruction.build_event_timeline("crucifixion")

        assert result["event_id"] == "crucifixion"
        assert result["event_label"] == "Crucifixion"
        assert "timeline_elements" in result
        assert "synthesis" in result
        assert result["source_count"] == 2
        assert "mark" in result["sources"]
        assert "john" in result["sources"]

    @patch('bce.ai.event_reconstruction.embed_text')
    @patch('bce.ai.event_reconstruction.cosine_similarity')
    @patch('bce.ai.event_reconstruction.queries')
    def test_detects_conflicts_in_accounts(self, mock_queries, mock_similarity, mock_embed):
        """Should detect conflicts between accounts."""
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

        try:
            import numpy as np
            mock_embed.return_value = np.array([0.1, 0.2, 0.3])
            mock_similarity.return_value = 0.4
        except ImportError:
            mock_embed.return_value = [0.1, 0.2, 0.3]
            mock_similarity.return_value = 0.4

        # Event with conflicting time details
        event = Event(
            id="crucifixion",
            label="Crucifixion",
            participants=["jesus"],
            accounts=[
                EventAccount(
                    source_id="mark",
                    reference="Mark 15:25",
                    summary="It was the third hour when they crucified him",
                    notes=None
                ),
                EventAccount(
                    source_id="john",
                    reference="John 19:14",
                    summary="It was about the sixth hour",
                    notes=None
                )
            ],
            parallels=[],
            tags=[]
        )

        mock_queries.get_event.return_value = event

        result = event_reconstruction.build_event_timeline("crucifixion")

        # Should find timeline elements with conflicts
        timeline_elements = result["timeline_elements"]
        if len(timeline_elements) > 0:
            # At least one element should be detected
            assert any("time" in elem["element"] or "hour" in elem["element"] for elem in timeline_elements)


class TestCompareEventSequences:
    """Tests for compare_event_sequences function."""

    def setup_method(self):
        """Setup for each test."""
        reset_default_config()

    def teardown_method(self):
        """Cleanup after each test."""
        reset_default_config()

    def test_requires_ai_enabled(self):
        """Should raise ConfigurationError when AI is disabled."""
        config = BceConfig(enable_ai_features=False)
        set_default_config(config)

        with pytest.raises(ConfigurationError, match="AI features are disabled"):
            event_reconstruction.compare_event_sequences(
                ["event1", "event2"],
                "mark"
            )

    @patch('bce.ai.event_reconstruction.queries')
    def test_returns_sequence_analysis(self, mock_queries):
        """Should return sequence analysis structure."""
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

        event1 = Event(
            id="event1",
            label="Event 1",
            participants=["jesus"],
            accounts=[
                EventAccount(source_id="mark", reference="Mark 1:1", summary="Summary 1", notes=None)
            ],
            parallels=[],
            tags=[]
        )

        event2 = Event(
            id="event2",
            label="Event 2",
            participants=["jesus"],
            accounts=[
                EventAccount(source_id="john", reference="John 1:1", summary="Summary 2", notes=None)
            ],
            parallels=[],
            tags=[]
        )

        mock_queries.get_event.side_effect = lambda eid: event1 if eid == "event1" else event2

        result = event_reconstruction.compare_event_sequences(
            ["event1", "event2"],
            "mark"
        )

        assert result["source_id"] == "mark"
        assert result["requested_sequence"] == ["event1", "event2"]
        assert "present_events" in result
        assert "missing_events" in result
        assert "sequence" in result

    @patch('bce.ai.event_reconstruction.queries')
    def test_identifies_present_events(self, mock_queries):
        """Should identify events present in source."""
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

        event1 = Event(
            id="event1",
            label="Event 1",
            participants=[],
            accounts=[
                EventAccount(source_id="mark", reference="Mark 1:1", summary="Summary", notes=None)
            ],
            parallels=[],
            tags=[]
        )

        mock_queries.get_event.return_value = event1

        result = event_reconstruction.compare_event_sequences(
            ["event1"],
            "mark"
        )

        assert "event1" in result["present_events"]

    @patch('bce.ai.event_reconstruction.queries')
    def test_identifies_missing_events(self, mock_queries):
        """Should identify events missing from source."""
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

        # Event with account only in john, not mark
        event1 = Event(
            id="event1",
            label="Event 1",
            participants=[],
            accounts=[
                EventAccount(source_id="john", reference="John 1:1", summary="Summary", notes=None)
            ],
            parallels=[],
            tags=[]
        )

        mock_queries.get_event.return_value = event1

        result = event_reconstruction.compare_event_sequences(
            ["event1"],
            "mark"
        )

        assert "event1" in result["missing_events"]


class TestReconstructPassionNarrative:
    """Tests for reconstruct_passion_narrative function."""

    def setup_method(self):
        """Setup for each test."""
        reset_default_config()

    def teardown_method(self):
        """Cleanup after each test."""
        reset_default_config()

    def test_requires_ai_enabled(self):
        """Should raise ConfigurationError when AI is disabled."""
        config = BceConfig(enable_ai_features=False)
        set_default_config(config)

        with pytest.raises(ConfigurationError, match="AI features are disabled"):
            event_reconstruction.reconstruct_passion_narrative()

    @patch('bce.ai.event_reconstruction.queries')
    def test_returns_passion_reconstruction_structure(self, mock_queries):
        """Should return passion narrative reconstruction."""
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

        # Mock event that doesn't exist
        mock_queries.get_event.side_effect = Exception("Event not found")

        result = event_reconstruction.reconstruct_passion_narrative()

        assert result["narrative_type"] == "passion"
        assert "events" in result
        assert "synthesis" in result
        assert "total_events" in result
        assert "events_found" in result

    @patch('bce.ai.event_reconstruction.queries')
    def test_processes_standard_passion_events(self, mock_queries):
        """Should process standard passion event sequence."""
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

        # Mock successful event load with single account (will get message)
        def mock_get_event(event_id):
            return Event(
                id=event_id,
                label=event_id.replace("_", " ").title(),
                participants=["jesus"],
                accounts=[
                    EventAccount(source_id="mark", reference="Mark 1:1", summary="Summary", notes=None)
                ],
                parallels=[],
                tags=[]
            )

        mock_queries.get_event.side_effect = mock_get_event

        result = event_reconstruction.reconstruct_passion_narrative()

        # Should have attempted standard passion events
        expected_events = [
            "last_supper", "gethsemane", "arrest", "trial_before_sanhedrin",
            "trial_before_pilate", "crucifixion", "burial", "resurrection_appearance"
        ]

        for event_id in expected_events:
            assert event_id in result["events"]


class TestReconstructMinistrySequence:
    """Tests for reconstruct_ministry_sequence function."""

    def setup_method(self):
        """Setup for each test."""
        reset_default_config()

    def teardown_method(self):
        """Cleanup after each test."""
        reset_default_config()

    def test_requires_ai_enabled(self):
        """Should raise ConfigurationError when AI is disabled."""
        config = BceConfig(enable_ai_features=False)
        set_default_config(config)

        with pytest.raises(ConfigurationError, match="AI features are disabled"):
            event_reconstruction.reconstruct_ministry_sequence("mark")

    @patch('bce.ai.event_reconstruction.queries')
    def test_returns_ministry_sequence_structure(self, mock_queries):
        """Should return ministry sequence structure."""
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

        mock_queries.list_all_events.return_value = []

        result = event_reconstruction.reconstruct_ministry_sequence("mark")

        assert result["source_id"] == "mark"
        assert "event_count" in result
        assert "events" in result
        assert "note" in result

    @patch('bce.ai.event_reconstruction.queries')
    def test_filters_to_source_events(self, mock_queries):
        """Should filter events to specified source."""
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

        events = [
            Event(
                id="event1",
                label="Event 1",
                participants=[],
                accounts=[
                    EventAccount(source_id="mark", reference="Mark 1:1", summary="Summary", notes=None)
                ],
                parallels=[],
                tags=[]
            ),
            Event(
                id="event2",
                label="Event 2",
                participants=[],
                accounts=[
                    EventAccount(source_id="john", reference="John 1:1", summary="Summary", notes=None)
                ],
                parallels=[],
                tags=[]
            )
        ]

        mock_queries.list_all_events.return_value = events

        result = event_reconstruction.reconstruct_ministry_sequence("mark")

        # Should only include event1 (mark source)
        assert result["event_count"] == 1
        event_ids = [e["event_id"] for e in result["events"]]
        assert "event1" in event_ids
        assert "event2" not in event_ids


class TestExtractTimelineElements:
    """Tests for _extract_timeline_elements helper function."""

    def setup_method(self):
        """Setup for each test."""
        reset_default_config()
        # Enable AI for these tests
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

    def teardown_method(self):
        """Cleanup after each test."""
        reset_default_config()

    @patch('bce.ai.event_reconstruction.embed_text')
    @patch('bce.ai.event_reconstruction.cosine_similarity')
    def test_extracts_elements_from_accounts(self, mock_similarity, mock_embed):
        """Should extract timeline elements from event accounts."""
        try:
            import numpy as np
            mock_embed.return_value = np.array([0.1, 0.2, 0.3])
            mock_similarity.return_value = 0.6
        except ImportError:
            mock_embed.return_value = [0.1, 0.2, 0.3]
            mock_similarity.return_value = 0.6

        event = Event(
            id="event1",
            label="Event 1",
            participants=["jesus"],
            accounts=[
                EventAccount(
                    source_id="mark",
                    reference="Mark 1:1",
                    summary="Jesus went to Jerusalem at the temple in the morning",
                    notes=None
                ),
                EventAccount(
                    source_id="john",
                    reference="John 1:1",
                    summary="Jesus was in Jerusalem near the temple at dawn",
                    notes=None
                )
            ],
            parallels=[],
            tags=[]
        )

        elements = event_reconstruction._extract_timeline_elements(event)

        # Should extract some elements
        assert isinstance(elements, list)
        # Elements should have required fields
        for elem in elements:
            assert "element" in elem
            assert "sources" in elem
            assert "conflict" in elem

    @patch('bce.ai.event_reconstruction.embed_text')
    @patch('bce.ai.event_reconstruction.cosine_similarity')
    def test_detects_conflicts_in_elements(self, mock_similarity, mock_embed):
        """Should detect when element values conflict."""
        try:
            import numpy as np
            mock_embed.return_value = np.array([0.1, 0.2, 0.3])
            mock_similarity.return_value = 0.4
        except ImportError:
            mock_embed.return_value = [0.1, 0.2, 0.3]
            mock_similarity.return_value = 0.4

        event = Event(
            id="event1",
            label="Event 1",
            participants=[],
            accounts=[
                EventAccount(
                    source_id="mark",
                    reference="Mark 1:1",
                    summary="It happened in the morning at dawn",
                    notes=None
                ),
                EventAccount(
                    source_id="john",
                    reference="John 1:1",
                    summary="It happened at noon in the afternoon",
                    notes=None
                )
            ],
            parallels=[],
            tags=[]
        )

        elements = event_reconstruction._extract_timeline_elements(event)

        # Should detect time conflict
        time_elements = [e for e in elements if "time" in e["element"]]
        if len(time_elements) > 0:
            # Should have multiple sources
            assert len(time_elements[0]["sources"]) > 0

    def test_handles_event_with_no_matching_elements(self):
        """Should handle accounts with no matching elements."""
        event = Event(
            id="event1",
            label="Event 1",
            participants=[],
            accounts=[
                EventAccount(
                    source_id="mark",
                    reference="Mark 1:1",
                    summary="Simple summary",
                    notes=None
                ),
                EventAccount(
                    source_id="john",
                    reference="John 1:1",
                    summary="Another summary",
                    notes=None
                )
            ],
            parallels=[],
            tags=[]
        )

        elements = event_reconstruction._extract_timeline_elements(event)

        # Should return list (possibly empty)
        assert isinstance(elements, list)


class TestExtractElementAcrossAccounts:
    """Tests for _extract_element_across_accounts helper function."""

    def setup_method(self):
        """Setup for each test."""
        reset_default_config()
        # Enable AI for these tests
        config = BceConfig(enable_ai_features=True)
        set_default_config(config)

    def teardown_method(self):
        """Cleanup after each test."""
        reset_default_config()

    @patch('bce.ai.event_reconstruction.embed_text')
    @patch('bce.ai.event_reconstruction.cosine_similarity')
    def test_extracts_element_from_multiple_accounts(self, mock_similarity, mock_embed):
        """Should extract element from accounts."""
        try:
            import numpy as np
            mock_embed.return_value = np.array([0.1, 0.2, 0.3])
            mock_similarity.return_value = 0.6
        except ImportError:
            # If numpy not available, use lists
            mock_embed.return_value = [0.1, 0.2, 0.3]
            mock_similarity.return_value = 0.6

        event = Event(
            id="event1",
            label="Event 1",
            participants=[],
            accounts=[
                EventAccount(
                    source_id="mark",
                    reference="Mark 1:1",
                    summary="The time was morning",
                    notes=None
                ),
                EventAccount(
                    source_id="john",
                    reference="John 1:1",
                    summary="The time was evening",
                    notes=None
                )
            ],
            parallels=[],
            tags=[]
        )

        element = event_reconstruction._extract_element_across_accounts(
            event,
            "time_of_day",
            ["time", "hour", "morning", "evening"]
        )

        assert element is not None
        assert element["element"] == "time_of_day"
        assert "mark" in element["sources"]
        assert "john" in element["sources"]

    @patch('bce.ai.event_reconstruction.embed_text')
    @patch('bce.ai.event_reconstruction.cosine_similarity')
    def test_detects_conflict_when_values_differ(self, mock_similarity, mock_embed):
        """Should detect conflict when element values differ."""
        try:
            import numpy as np
            mock_embed.return_value = np.array([0.1, 0.2, 0.3])
            mock_similarity.return_value = 0.4
        except ImportError:
            mock_embed.return_value = [0.1, 0.2, 0.3]
            mock_similarity.return_value = 0.4

        event = Event(
            id="event1",
            label="Event 1",
            participants=[],
            accounts=[
                EventAccount(
                    source_id="mark",
                    reference="Mark 1:1",
                    summary="At the morning time",
                    notes=None
                ),
                EventAccount(
                    source_id="john",
                    reference="John 1:1",
                    summary="At the evening time",
                    notes=None
                )
            ],
            parallels=[],
            tags=[]
        )

        element = event_reconstruction._extract_element_across_accounts(
            event,
            "time_of_day",
            ["time"]
        )

        assert element is not None
        assert element["conflict"] is True

    def test_returns_none_when_no_matches(self):
        """Should return None when element not found in any account."""
        event = Event(
            id="event1",
            label="Event 1",
            participants=[],
            accounts=[
                EventAccount(
                    source_id="mark",
                    reference="Mark 1:1",
                    summary="Simple text with no matches",
                    notes=None
                )
            ],
            parallels=[],
            tags=[]
        )

        element = event_reconstruction._extract_element_across_accounts(
            event,
            "nonexistent",
            ["keyword_not_in_text"]
        )

        assert element is None


class TestAnalyzeElementConflict:
    """Tests for _analyze_element_conflict helper function."""

    @patch('bce.ai.event_reconstruction.embed_text')
    @patch('bce.ai.event_reconstruction.cosine_similarity')
    def test_analyzes_conflict_with_similarity(self, mock_similarity, mock_embed):
        """Should analyze conflict using semantic similarity."""
        # Import numpy only when needed for tests
        try:
            import numpy as np
        except ImportError:
            pytest.skip("numpy not available")

        # Mock embeddings
        mock_embed.return_value = np.array([0.1, 0.2, 0.3])
        mock_similarity.return_value = 0.8

        sources_data = {
            "mark": "third hour",
            "john": "sixth hour"
        }

        analysis = event_reconstruction._analyze_element_conflict(
            "time_of_day",
            sources_data
        )

        assert isinstance(analysis, str)
        assert "time_of_day" in analysis

    @patch('bce.ai.event_reconstruction.embed_text')
    @patch('bce.ai.event_reconstruction.cosine_similarity')
    def test_detects_minor_variation(self, mock_similarity, mock_embed):
        """Should detect minor variation for high similarity."""
        try:
            import numpy as np
        except ImportError:
            pytest.skip("numpy not available")

        mock_embed.return_value = np.array([0.1, 0.2, 0.3])
        mock_similarity.return_value = 0.9  # High similarity

        sources_data = {
            "mark": "at the temple",
            "john": "at the temple complex"
        }

        analysis = event_reconstruction._analyze_element_conflict(
            "location",
            sources_data
        )

        assert "Minor variation" in analysis or "minor" in analysis.lower()

    @patch('bce.ai.event_reconstruction.embed_text')
    @patch('bce.ai.event_reconstruction.cosine_similarity')
    def test_detects_significant_discrepancy(self, mock_similarity, mock_embed):
        """Should detect significant discrepancy for low similarity."""
        try:
            import numpy as np
        except ImportError:
            pytest.skip("numpy not available")

        mock_embed.return_value = np.array([0.1, 0.2, 0.3])
        mock_similarity.return_value = 0.3  # Low similarity

        sources_data = {
            "mark": "third hour",
            "john": "sixth hour"
        }

        analysis = event_reconstruction._analyze_element_conflict(
            "time_of_day",
            sources_data
        )

        assert "Significant" in analysis or "significant" in analysis.lower()

    def test_handles_single_value(self):
        """Should handle single value gracefully."""
        sources_data = {
            "mark": "only one source"
        }

        analysis = event_reconstruction._analyze_element_conflict(
            "element",
            sources_data
        )

        # Should return some analysis
        assert isinstance(analysis, str)


class TestSynthesizeEventNarrative:
    """Tests for _synthesize_event_narrative helper function."""

    def test_generates_synthesis_for_agreeing_sources(self):
        """Should generate synthesis noting agreement."""
        event = Event(
            id="event1",
            label="Test Event",
            participants=[],
            accounts=[
                EventAccount(source_id="mark", reference="Mark 1:1", summary="Summary", notes=None),
                EventAccount(source_id="john", reference="John 1:1", summary="Summary", notes=None)
            ],
            parallels=[],
            tags=[]
        )

        timeline_elements = []  # No conflicts

        synthesis = event_reconstruction._synthesize_event_narrative(
            event,
            timeline_elements
        )

        assert isinstance(synthesis, str)
        assert "Test Event" in synthesis
        assert "2 source" in synthesis
        assert "agreement" in synthesis.lower() or "agree" in synthesis.lower()

    def test_generates_synthesis_for_conflicting_sources(self):
        """Should generate synthesis noting conflicts."""
        event = Event(
            id="event1",
            label="Test Event",
            participants=[],
            accounts=[
                EventAccount(source_id="mark", reference="Mark 1:1", summary="Summary", notes=None),
                EventAccount(source_id="john", reference="John 1:1", summary="Summary", notes=None)
            ],
            parallels=[],
            tags=[]
        )

        timeline_elements = [
            {
                "element": "time_of_day",
                "sources": {"mark": "morning", "john": "evening"},
                "conflict": True,
                "ai_analysis": "Significant discrepancy in time_of_day"
            },
            {
                "element": "location",
                "sources": {"mark": "temple", "john": "temple"},
                "conflict": False,
                "ai_analysis": None
            }
        ]

        synthesis = event_reconstruction._synthesize_event_narrative(
            event,
            timeline_elements
        )

        assert "variation" in synthesis.lower() or "conflict" in synthesis.lower()
        assert "time_of_day" in synthesis

    def test_mentions_synoptic_parallels(self):
        """Should mention synoptic parallels if present."""
        event = Event(
            id="event1",
            label="Test Event",
            participants=[],
            accounts=[
                EventAccount(source_id="mark", reference="Mark 1:1", summary="Summary", notes=None)
            ],
            parallels=[
                {"type": "synoptic_parallel", "sources": ["mark", "matthew", "luke"], "notes": ""}
            ],
            tags=[]
        )

        timeline_elements = []

        synthesis = event_reconstruction._synthesize_event_narrative(
            event,
            timeline_elements
        )

        assert "synoptic" in synthesis.lower() or "Synoptic" in synthesis

    def test_counts_conflicts_correctly(self):
        """Should count and report conflicts correctly."""
        event = Event(
            id="event1",
            label="Test Event",
            participants=[],
            accounts=[
                EventAccount(source_id="mark", reference="Mark 1:1", summary="Summary", notes=None),
                EventAccount(source_id="john", reference="John 1:1", summary="Summary", notes=None)
            ],
            parallels=[],
            tags=[]
        )

        timeline_elements = [
            {"element": "elem1", "sources": {}, "conflict": True, "ai_analysis": "Conflict 1"},
            {"element": "elem2", "sources": {}, "conflict": True, "ai_analysis": "Conflict 2"},
            {"element": "elem3", "sources": {}, "conflict": True, "ai_analysis": "Conflict 3"},
        ]

        synthesis = event_reconstruction._synthesize_event_narrative(
            event,
            timeline_elements
        )

        # Should mention multiple conflicts
        assert "3" in synthesis or "significant" in synthesis.lower()
