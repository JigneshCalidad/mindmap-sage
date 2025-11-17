"""Command-line interface for mindmap-sage.

This CLI provides intuitive commands for scanning repositories,
exporting mindmaps, and serving the API. It's the primary interface
for interacting with the bot.
"""

import sys
from pathlib import Path

import click

from mindmap.core import MindmapBuilder
from mindmap.exporter import Exporter


@click.group()
@click.version_option(version="0.1.0")
def main():
    """Mindmap Sage - Transform codebases into living mindmaps."""
    pass


@main.command()
@click.argument("repo_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output file path (default: print to stdout)",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["mermaid", "json"], case_sensitive=False),
    default="mermaid",
    help="Output format",
)
def scan(repo_path: Path, output: Path, format: str):
    """Scan a repository and generate a mindmap.

    REPO_PATH: Path to the repository to scan
    """
    click.echo(f"Scanning repository: {repo_path}", err=True)

    try:
        builder = MindmapBuilder()
        builder.build_from_directory(repo_path)
        graph = builder.get_graph()

        click.echo(
            f"Found {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges",
            err=True,
        )

        exporter = Exporter(graph)

        if format.lower() == "mermaid":
            result = exporter.to_mermaid()
        else:
            import json

            result = json.dumps(exporter.to_json(), indent=2)

        if output:
            output.write_text(result, encoding="utf-8")
            click.echo(f"Exported to: {output}", err=True)
        else:
            click.echo(result)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option(
    "--host",
    default="127.0.0.1",
    help="Host to bind the server to",
)
@click.option(
    "--port",
    default=8000,
    type=int,
    help="Port to bind the server to",
)
@click.option(
    "--repo-path",
    type=click.Path(exists=True, path_type=Path),
    help="Initial repository path to scan",
)
def serve(host: str, port: int, repo_path: Path):
    """Start the FastAPI server."""
    import uvicorn
    from app.main import builder

    if repo_path:
        click.echo(f"Scanning initial repository: {repo_path}", err=True)
        try:
            builder.build_from_directory(repo_path)
            # Update the global current_repo_path in app.main
            import app.main as app_module
            app_module.current_repo_path = repo_path
            graph = builder.get_graph()
            click.echo(
                f"Scanned: {graph.number_of_nodes()} nodes, "
                f"{graph.number_of_edges()} edges",
                err=True,
            )
        except Exception as e:
            click.echo(f"Warning: Failed to scan repository: {e}", err=True)

    click.echo(f"Starting server at http://{host}:{port}", err=True)
    uvicorn.run("app.main:app", host=host, port=port, reload=False)


@main.command()
@click.argument("repo_path", type=click.Path(exists=True, path_type=Path), required=False)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["mermaid", "json"], case_sensitive=False),
    default="mermaid",
    help="Output format",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output file path (default: print to stdout)",
)
@click.option(
    "--direction",
    "-d",
    type=click.Choice(["TD", "LR", "RL", "BT"], case_sensitive=False),
    default="TD",
    help="Mermaid graph direction (only for mermaid format)",
)
def export(repo_path: Path, format: str, output: Path, direction: str):
    """Export a mindmap from a repository.

    REPO_PATH: Path to the repository to scan and export (optional if graph already built)
    """
    import json

    try:
        builder = MindmapBuilder()

        if repo_path:
            click.echo(f"Scanning repository: {repo_path}", err=True)
            builder.build_from_directory(repo_path)
        else:
            click.echo(
                "No repository path provided. Use 'mindmap scan <repo_path>' first or provide REPO_PATH.",
                err=True,
            )
            sys.exit(1)

        graph = builder.get_graph()

        if graph.number_of_nodes() == 0:
            click.echo("Warning: No nodes found in the graph.", err=True)

        exporter = Exporter(graph)

        if format.lower() == "mermaid":
            result = exporter.to_mermaid(direction=direction)
        else:
            result = json.dumps(exporter.to_json(), indent=2)

        if output:
            output.write_text(result, encoding="utf-8")
            click.echo(f"Exported to: {output}", err=True)
        else:
            click.echo(result)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

