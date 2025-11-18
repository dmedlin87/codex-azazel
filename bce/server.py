"""
FastAPI server for the Biblical Character Engine (BCE) web interface.

This module provides a REST API exposing BCE functionality to a web frontend.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

from . import api, exceptions

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"


# Create FastAPI app
app = FastAPI(
    title="Biblical Character Engine API",
    description="REST API for exploring New Testament characters and events",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# API Routes

@app.get("/api/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "bce-api"}


@app.get("/api/stats")
async def get_stats() -> Dict[str, Any]:
    """Get dashboard statistics."""
    try:
        char_ids = api.list_character_ids()
        event_ids = api.list_event_ids()

        # Count total conflicts
        total_conflicts = 0
        for char_id in char_ids:
            conflicts = api.summarize_character_conflicts(char_id)
            total_conflicts += len(conflicts)

        for event_id in event_ids:
            conflicts = api.summarize_event_conflicts(event_id)
            total_conflicts += len(conflicts)

        # Get all tags
        all_tags = set()
        for char_id in char_ids:
            char = api.get_character(char_id)
            all_tags.update(char.tags)
        for event_id in event_ids:
            event = api.get_event(event_id)
            all_tags.update(event.tags)

        return {
            "total_characters": len(char_ids),
            "total_events": len(event_ids),
            "total_conflicts": total_conflicts,
            "total_tags": len(all_tags),
            "tags": sorted(list(all_tags)),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/characters")
async def list_characters() -> List[str]:
    """List all character IDs."""
    try:
        return api.list_character_ids()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/characters/{char_id}")
async def get_character(char_id: str) -> Dict[str, Any]:
    """Get character dossier by ID."""
    try:
        return api.build_character_dossier(char_id)
    except exceptions.DataNotFoundError:
        raise HTTPException(status_code=404, detail=f"Character '{char_id}' not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/events")
async def list_events() -> List[str]:
    """List all event IDs."""
    try:
        return api.list_event_ids()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/events/{event_id}")
async def get_event(event_id: str) -> Dict[str, Any]:
    """Get event dossier by ID."""
    try:
        return api.build_event_dossier(event_id)
    except exceptions.DataNotFoundError:
        raise HTTPException(status_code=404, detail=f"Event '{event_id}' not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/search")
async def search(
    q: str = Query(..., description="Search query"),
    scope: Optional[str] = Query(None, description="Comma-separated search scopes")
) -> List[Dict[str, Any]]:
    """Full-text search across characters and events."""
    try:
        scope_list = scope.split(",") if scope else None
        return api.search_all(q, scope=scope_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tags/characters/{tag}")
async def get_characters_by_tag(tag: str) -> List[str]:
    """Get character IDs with a specific tag."""
    try:
        return api.list_characters_with_tag(tag)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tags/events/{tag}")
async def get_events_by_tag(tag: str) -> List[str]:
    """Get event IDs with a specific tag."""
    try:
        return api.list_events_with_tag(tag)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/graph")
async def get_graph() -> Dict[str, Any]:
    """Get graph snapshot for network visualization."""
    try:
        graph = api.build_graph_snapshot()
        return {
            "nodes": [
                {
                    "id": node.id,
                    "label": node.label,
                    "type": node.type,
                    "properties": node.properties,
                }
                for node in graph.nodes
            ],
            "edges": [
                {
                    "source": edge.source,
                    "target": edge.target,
                    "type": edge.type,
                    "properties": edge.properties,
                }
                for edge in graph.edges
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/characters/{char_id}/conflicts")
async def get_character_conflicts(char_id: str) -> Dict[str, Dict[str, Any]]:
    """Get conflict summary for a character."""
    try:
        return api.summarize_character_conflicts(char_id)
    except exceptions.DataNotFoundError:
        raise HTTPException(status_code=404, detail=f"Character '{char_id}' not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/events/{event_id}/conflicts")
async def get_event_conflicts(event_id: str) -> Dict[str, Dict[str, Any]]:
    """Get conflict summary for an event."""
    try:
        return api.summarize_event_conflicts(event_id)
    except exceptions.DataNotFoundError:
        raise HTTPException(status_code=404, detail=f"Event '{event_id}' not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Mount static files (CSS, JS)
if FRONTEND_DIR.exists():
    app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
    app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")


# Root route - serve index.html
@app.get("/")
async def root():
    """Serve the frontend index page."""
    if FRONTEND_DIR.exists():
        return FileResponse(str(FRONTEND_DIR / "index.html"))
    return {"message": "Frontend not found. Please ensure the frontend directory exists."}


# Serve individual HTML pages
@app.get("/{page}.html")
async def serve_page(page: str):
    """Serve HTML pages from the frontend directory."""
    page_path = FRONTEND_DIR / f"{page}.html"
    if page_path.exists():
        return FileResponse(str(page_path))
    raise HTTPException(status_code=404, detail="Page not found")


def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Run the FastAPI server."""
    print(f"Starting BCE Web Server on http://{host}:{port}")
    print(f"Frontend directory: {FRONTEND_DIR}")
    print(f"API documentation: http://{host}:{port}/docs")
    uvicorn.run("bce.server:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    run_server(reload=True)
