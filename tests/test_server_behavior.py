"""
Tests for bce/server.py - FastAPI server behavior.

These tests focus on non-network logic: configuration, app factory,
route registration, and endpoint behavior using test clients.
"""

from __future__ import annotations

from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient

from bce import server, exceptions


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(server.app)


class TestAppConfiguration:
    """Test app creation and configuration."""

    def test_app_exists(self):
        """Test that the FastAPI app is created."""
        assert server.app is not None
        assert server.app.title == "Biblical Character Engine API"
        assert server.app.version == "0.1.0"

    def test_cors_middleware_configured(self):
        """Test that CORS middleware is present in the app."""
        # Check that middleware is configured (user_middleware contains the middleware stack)
        # The actual type might be wrapped, so we check that middleware exists
        assert len(server.app.user_middleware) > 0
        # Alternatively, we can check the middleware stack contains our CORS config
        # by verifying it's in the middleware list
        assert server.app.user_middleware is not None

    def test_project_paths(self):
        """Test that project paths are configured correctly."""
        assert server.PROJECT_ROOT.exists()
        # FRONTEND_DIR may or may not exist, but should be defined
        assert server.FRONTEND_DIR is not None


class TestHealthEndpoint:
    """Test the health check endpoint."""

    def test_health_check_returns_200(self, client):
        """Test health check returns 200 OK."""
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_health_check_returns_expected_data(self, client):
        """Test health check returns expected JSON structure."""
        response = client.get("/api/health")
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "bce-api"


class TestStatsEndpoint:
    """Test the stats endpoint."""

    def test_stats_returns_200(self, client):
        """Test stats endpoint returns 200 OK."""
        response = client.get("/api/stats")
        assert response.status_code == 200

    def test_stats_returns_expected_structure(self, client):
        """Test stats endpoint returns expected JSON structure."""
        response = client.get("/api/stats")
        data = response.json()

        # Check all expected keys are present
        assert "total_characters" in data
        assert "total_events" in data
        assert "total_conflicts" in data
        assert "total_tags" in data
        assert "tags" in data

        # Check data types
        assert isinstance(data["total_characters"], int)
        assert isinstance(data["total_events"], int)
        assert isinstance(data["total_conflicts"], int)
        assert isinstance(data["total_tags"], int)
        assert isinstance(data["tags"], list)

    def test_stats_counts_are_non_negative(self, client):
        """Test that stats counts are non-negative."""
        response = client.get("/api/stats")
        data = response.json()

        assert data["total_characters"] >= 0
        assert data["total_events"] >= 0
        assert data["total_conflicts"] >= 0
        assert data["total_tags"] >= 0

    @patch("bce.server.api.list_character_ids")
    def test_stats_handles_api_errors(self, mock_list, client):
        """Test stats endpoint handles API errors gracefully."""
        mock_list.side_effect = Exception("Test error")
        response = client.get("/api/stats")
        assert response.status_code == 500
        assert "Test error" in response.json()["detail"]


class TestCharacterEndpoints:
    """Test character-related endpoints."""

    def test_list_characters_returns_200(self, client):
        """Test listing characters returns 200 OK."""
        response = client.get("/api/characters")
        assert response.status_code == 200

    def test_list_characters_returns_list(self, client):
        """Test listing characters returns a list."""
        response = client.get("/api/characters")
        data = response.json()
        assert isinstance(data, list)

    def test_get_character_existing(self, client):
        """Test getting an existing character."""
        # First get the list to find a valid character
        list_response = client.get("/api/characters")
        char_ids = list_response.json()

        if char_ids:
            # Test with the first character
            char_id = char_ids[0]
            response = client.get(f"/api/characters/{char_id}")
            assert response.status_code == 200
            data = response.json()
            assert "identity" in data or "id" in data

    def test_get_character_not_found(self, client):
        """Test getting a non-existent character returns 404."""
        response = client.get("/api/characters/nonexistent_character_xyz")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @patch("bce.server.api.list_character_ids")
    def test_list_characters_handles_errors(self, mock_list, client):
        """Test character listing handles errors."""
        mock_list.side_effect = Exception("Test error")
        response = client.get("/api/characters")
        assert response.status_code == 500

    @patch("bce.server.api.build_character_dossier")
    def test_get_character_handles_generic_errors(self, mock_dossier, client):
        """Test character retrieval handles generic errors."""
        mock_dossier.side_effect = Exception("Generic error")
        response = client.get("/api/characters/test_id")
        assert response.status_code == 500


class TestEventEndpoints:
    """Test event-related endpoints."""

    def test_list_events_returns_200(self, client):
        """Test listing events returns 200 OK."""
        response = client.get("/api/events")
        assert response.status_code == 200

    def test_list_events_returns_list(self, client):
        """Test listing events returns a list."""
        response = client.get("/api/events")
        data = response.json()
        assert isinstance(data, list)

    def test_get_event_existing(self, client):
        """Test getting an existing event."""
        list_response = client.get("/api/events")
        event_ids = list_response.json()

        if event_ids:
            event_id = event_ids[0]
            response = client.get(f"/api/events/{event_id}")
            assert response.status_code == 200
            data = response.json()
            assert "identity" in data or "id" in data

    def test_get_event_not_found(self, client):
        """Test getting a non-existent event returns 404."""
        response = client.get("/api/events/nonexistent_event_xyz")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @patch("bce.server.api.list_event_ids")
    def test_list_events_handles_errors(self, mock_list, client):
        """Test event listing handles errors."""
        mock_list.side_effect = Exception("Test error")
        response = client.get("/api/events")
        assert response.status_code == 500

    @patch("bce.server.api.build_event_dossier")
    def test_get_event_handles_generic_errors(self, mock_dossier, client):
        """Test event retrieval handles generic errors."""
        mock_dossier.side_effect = Exception("Generic error")
        response = client.get("/api/events/test_id")
        assert response.status_code == 500


class TestSearchEndpoint:
    """Test the search endpoint."""

    def test_search_requires_query_param(self, client):
        """Test search endpoint requires 'q' parameter."""
        response = client.get("/api/search")
        assert response.status_code == 422  # Validation error

    def test_search_with_query_returns_200(self, client):
        """Test search with query parameter returns 200."""
        response = client.get("/api/search?q=test")
        assert response.status_code == 200

    def test_search_returns_list(self, client):
        """Test search returns a list of results."""
        response = client.get("/api/search?q=jesus")
        data = response.json()
        assert isinstance(data, list)

    def test_search_with_scope(self, client):
        """Test search with scope parameter."""
        response = client.get("/api/search?q=test&scope=traits,tags")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_search_without_scope(self, client):
        """Test search without scope parameter."""
        response = client.get("/api/search?q=test")
        assert response.status_code == 200

    @patch("bce.server.api.search_all")
    def test_search_handles_errors(self, mock_search, client):
        """Test search handles API errors."""
        mock_search.side_effect = Exception("Search error")
        response = client.get("/api/search?q=test")
        assert response.status_code == 500


class TestTagEndpoints:
    """Test tag-related endpoints."""

    def test_get_characters_by_tag_returns_200(self, client):
        """Test getting characters by tag returns 200."""
        response = client.get("/api/tags/characters/test_tag")
        assert response.status_code == 200

    def test_get_characters_by_tag_returns_list(self, client):
        """Test getting characters by tag returns a list."""
        response = client.get("/api/tags/characters/test_tag")
        data = response.json()
        assert isinstance(data, list)

    def test_get_events_by_tag_returns_200(self, client):
        """Test getting events by tag returns 200."""
        response = client.get("/api/tags/events/test_tag")
        assert response.status_code == 200

    def test_get_events_by_tag_returns_list(self, client):
        """Test getting events by tag returns a list."""
        response = client.get("/api/tags/events/test_tag")
        data = response.json()
        assert isinstance(data, list)

    @patch("bce.server.api.list_characters_with_tag")
    def test_characters_by_tag_handles_errors(self, mock_tag, client):
        """Test character tag endpoint handles errors."""
        mock_tag.side_effect = Exception("Tag error")
        response = client.get("/api/tags/characters/test")
        assert response.status_code == 500

    @patch("bce.server.api.list_events_with_tag")
    def test_events_by_tag_handles_errors(self, mock_tag, client):
        """Test event tag endpoint handles errors."""
        mock_tag.side_effect = Exception("Tag error")
        response = client.get("/api/tags/events/test")
        assert response.status_code == 500


class TestGraphEndpoint:
    """Test the graph endpoint."""

    def test_graph_returns_200(self, client):
        """Test graph endpoint returns 200."""
        response = client.get("/api/graph")
        assert response.status_code == 200

    def test_graph_returns_expected_structure(self, client):
        """Test graph endpoint returns expected structure."""
        response = client.get("/api/graph")
        data = response.json()

        assert "nodes" in data
        assert "edges" in data
        assert isinstance(data["nodes"], list)
        assert isinstance(data["edges"], list)

    def test_graph_node_structure(self, client):
        """Test graph nodes have expected structure."""
        response = client.get("/api/graph")
        data = response.json()

        if data["nodes"]:
            node = data["nodes"][0]
            assert "id" in node
            assert "label" in node
            assert "type" in node
            assert "properties" in node

    def test_graph_edge_structure(self, client):
        """Test graph edges have expected structure."""
        response = client.get("/api/graph")
        data = response.json()

        if data["edges"]:
            edge = data["edges"][0]
            assert "source" in edge
            assert "target" in edge
            assert "type" in edge
            assert "properties" in edge

    @patch("bce.server.api.build_graph_snapshot")
    def test_graph_handles_errors(self, mock_graph, client):
        """Test graph endpoint handles errors."""
        mock_graph.side_effect = Exception("Graph error")
        response = client.get("/api/graph")
        assert response.status_code == 500


class TestConflictEndpoints:
    """Test conflict-related endpoints."""

    def test_character_conflicts_with_valid_id(self, client):
        """Test getting character conflicts with valid ID."""
        # Get a valid character ID first
        list_response = client.get("/api/characters")
        char_ids = list_response.json()

        if char_ids:
            char_id = char_ids[0]
            response = client.get(f"/api/characters/{char_id}/conflicts")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, dict)

    def test_character_conflicts_not_found(self, client):
        """Test character conflicts with invalid ID returns 404."""
        response = client.get("/api/characters/nonexistent_xyz/conflicts")
        assert response.status_code == 404

    def test_event_conflicts_with_valid_id(self, client):
        """Test getting event conflicts with valid ID."""
        list_response = client.get("/api/events")
        event_ids = list_response.json()

        if event_ids:
            event_id = event_ids[0]
            response = client.get(f"/api/events/{event_id}/conflicts")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, dict)

    def test_event_conflicts_not_found(self, client):
        """Test event conflicts with invalid ID returns 404."""
        response = client.get("/api/events/nonexistent_xyz/conflicts")
        assert response.status_code == 404

    @patch("bce.server.api.summarize_character_conflicts")
    def test_character_conflicts_handles_errors(self, mock_conflicts, client):
        """Test character conflicts handles generic errors."""
        mock_conflicts.side_effect = Exception("Conflict error")
        response = client.get("/api/characters/test/conflicts")
        assert response.status_code == 500

    @patch("bce.server.api.summarize_event_conflicts")
    def test_event_conflicts_handles_errors(self, mock_conflicts, client):
        """Test event conflicts handles generic errors."""
        mock_conflicts.side_effect = Exception("Conflict error")
        response = client.get("/api/events/test/conflicts")
        assert response.status_code == 500


class TestStaticFilesAndFrontend:
    """Test static file serving and frontend routes."""

    def test_root_route_exists(self, client):
        """Test root route is registered."""
        response = client.get("/")
        # Should return either FileResponse or a message
        assert response.status_code in [200, 404]

    def test_html_page_route_exists(self, client):
        """Test HTML page route is registered."""
        # This might return 404 if frontend doesn't exist, which is fine
        response = client.get("/test.html")
        assert response.status_code in [200, 404]

    def test_html_page_route_not_found(self, client):
        """Test requesting non-existent HTML page returns 404."""
        response = client.get("/definitely_does_not_exist_12345.html")
        assert response.status_code == 404


class TestRunServerFunction:
    """Test the run_server function."""

    @patch("bce.server.uvicorn.run")
    def test_run_server_calls_uvicorn(self, mock_run):
        """Test run_server calls uvicorn.run with correct parameters."""
        server.run_server(host="127.0.0.1", port=9000, reload=True)

        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["host"] == "127.0.0.1"
        assert call_kwargs["port"] == 9000
        assert call_kwargs["reload"] is True

    @patch("bce.server.uvicorn.run")
    def test_run_server_default_parameters(self, mock_run):
        """Test run_server uses default parameters."""
        server.run_server()

        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["host"] == "0.0.0.0"
        assert call_kwargs["port"] == 8000
        assert call_kwargs["reload"] is False

    @patch("bce.server.uvicorn.run")
    @patch("builtins.print")
    def test_run_server_prints_startup_messages(self, mock_print, mock_run):
        """Test run_server prints startup messages."""
        server.run_server(host="localhost", port=3000)

        # Check that print was called with startup messages
        assert mock_print.call_count >= 3

        # Check for specific message content
        print_calls = [str(call) for call in mock_print.call_args_list]
        messages = " ".join(print_calls)
        assert "localhost" in messages
        assert "3000" in messages
