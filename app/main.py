"""FastAPI application serving mindmap data.

This API exposes the current mindmap state, allowing clients to query
the graph structure, export formats, and trigger scans. Think of it
as a window into the living mindmap.
"""

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse

from mindmap.core import MindmapBuilder
from mindmap.exporter import Exporter

app = FastAPI(
    title="Mindmap Sage API",
    description="API for querying and exporting codebase mindmaps",
    version="0.1.0",
)

# Global state
builder = MindmapBuilder()
current_repo_path: Optional[Path] = None


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
    global current_repo_path

    if repo_path:
        # Resolve path to prevent path traversal attacks
        try:
            path = Path(repo_path).resolve()
        except (ValueError, OSError) as e:
            raise HTTPException(
                status_code=400, detail=f"Invalid path: {str(e)}"
            )

        # Security: Ensure path is absolute and exists
        if not path.is_absolute():
            raise HTTPException(
                status_code=400, detail="Path must be absolute"
            )

        # Additional security: Check if path exists and is a directory
        if not path.exists():
            raise HTTPException(
                status_code=404, detail=f"Path not found: {path}"
            )

        if not path.is_dir():
            raise HTTPException(
                status_code=400, detail=f"Path must be a directory: {path}"
            )
    elif current_repo_path:
        path = current_repo_path
    else:
        path = Path.cwd()

    try:
        builder.build_from_directory(path)
        current_repo_path = path
        graph = builder.get_graph()

        return {
            "status": "success",
            "path": str(path),
            "nodes": graph.number_of_nodes(),
            "edges": graph.number_of_edges(),
        }
    except PermissionError as e:
        raise HTTPException(
            status_code=403, detail=f"Permission denied: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")


@app.get("/graph")
async def get_graph():
    """Get the current graph as JSON."""
    graph = builder.get_graph()

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
    graph = builder.get_graph()

    if graph.number_of_nodes() == 0:
        raise HTTPException(
            status_code=404, detail="No graph available. Run /scan first."
        )

    exporter = Exporter(graph)
    return exporter.to_mermaid(direction=direction)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "has_graph": builder.get_graph().number_of_nodes() > 0,
        "current_repo": str(current_repo_path) if current_repo_path else None,
    }

