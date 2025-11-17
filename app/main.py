"""FastAPI application serving mindmap data.

This API exposes the current mindmap state, allowing clients to query
the graph structure, export formats, and trigger scans. Think of it
as a window into the living mindmap.
"""

from pathlib import Path
from threading import Lock
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse

from mindmap.core import MindmapBuilder
from mindmap.exporter import Exporter


class AppState:
    """Thread-safe application state container."""

    def __init__(self):
        self.builder = MindmapBuilder()
        self.current_repo_path: Optional[Path] = None
        self._lock = Lock()

    def build_from_directory(self, path: Path):
        """Thread-safe build operation."""
        with self._lock:
            self.builder.build_from_directory(path)
            self.current_repo_path = path

    def get_graph(self):
        """Thread-safe graph access."""
        with self._lock:
            return self.builder.get_graph()


app = FastAPI(
    title="Mindmap Sage API",
    description="API for querying and exporting codebase mindmaps",
    version="0.1.0",
)

# Application state
state = AppState()


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Mindmap Sage API",
        "version": "0.1.0",
        "endpoints": {
            "/scan": "POST - Scan a repository",
            "/graph": "GET - Get current graph as JSON",
            "/mermaid": "GET - Get current graph as Mermaid diagram",
            "/health": "GET - Health check",
        },
    }


@app.post("/scan")
async def scan_repository(repo_path: Optional[str] = None):
    """Scan a repository and build the mindmap.

    Args:
        repo_path: Path to repository. If not provided, uses current directory.
    """
    if repo_path:
        path = Path(repo_path)
    elif state.current_repo_path:
        path = state.current_repo_path
    else:
        path = Path.cwd()

    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Path not found: {path}")

    try:
        state.build_from_directory(path)
        graph = state.get_graph()

        return {
            "status": "success",
            "path": str(path),
            "nodes": graph.number_of_nodes(),
            "edges": graph.number_of_edges(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")


@app.get("/graph")
async def get_graph():
    """Get the current graph as JSON."""
    graph = state.get_graph()

    if graph.number_of_nodes() == 0:
        raise HTTPException(
            status_code=404, detail="No graph available. Run /scan first."
        )

    exporter = Exporter(graph)
    return exporter.to_json()


@app.get("/mermaid", response_class=PlainTextResponse)
async def get_mermaid(direction: str = "TD"):
    """Get the current graph as a Mermaid diagram.

    Args:
        direction: Graph direction (TD, LR, RL, BT)
    """
    graph = state.get_graph()

    if graph.number_of_nodes() == 0:
        raise HTTPException(
            status_code=404, detail="No graph available. Run /scan first."
        )

    exporter = Exporter(graph)
    return exporter.to_mermaid(direction=direction)


@app.get("/health")
async def health():
    """Health check endpoint."""
    graph = state.get_graph()
    return {
        "status": "healthy",
        "has_graph": graph.number_of_nodes() > 0,
        "current_repo": str(state.current_repo_path) if state.current_repo_path else None,
    }

