"""Core graph building logic.

This module constructs a directed graph from parsed file data.
Nodes represent concepts (files, classes, functions), and edges
represent relationships (imports, dependencies, containment).
"""

import networkx as nx
from pathlib import Path
from typing import Any, Dict, List, Optional

from .parser import Parser


class MindmapBuilder:
    """Builds a NetworkX graph from repository structure."""

    def __init__(self):
        self.graph = nx.DiGraph()
        self.parser = Parser()

    def build_from_directory(self, root_path: Path) -> nx.DiGraph:
        """Scan directory and build the mindmap graph."""
        self.graph.clear()
        root_path = Path(root_path).resolve()

        # Parse all files
        parsed_files = self.parser.scan_directory(root_path)

        # Add file nodes
        for file_data in parsed_files:
            file_path = file_data["file"]
            relative_path = Path(file_path).relative_to(root_path)
            file_node = str(relative_path)

            self.graph.add_node(
                file_node,
                type="file",
                path=file_path,
            )

            # Add concept nodes and link them to their file
            for concept in file_data.get("concepts", []):
                concept_name = concept["name"]
                concept_type = concept.get("type", "unknown")
                concept_id = f"{file_node}::{concept_name}"

                self.graph.add_node(
                    concept_id,
                    type=concept_type,
                    name=concept_name,
                    file=file_node,
                    line=concept.get("line"),
                )

                # Link concept to its file
                self.graph.add_edge(concept_id, file_node, relation="defined_in")

        # Add cross-file relationships based on imports
        self._add_import_relationships(parsed_files, root_path)

        return self.graph

    def _add_import_relationships(
        self, parsed_files: List[Dict[str, Any]], root_path: Path
    ) -> None:
        """Add edges based on import statements."""
        root_path = Path(root_path).resolve()

        # Build a map of module names to file nodes
        module_to_file: Dict[str, str] = {}
        for file_data in parsed_files:
            file_path = Path(file_data["file"])
            relative_path = file_path.relative_to(root_path)
            file_node = str(relative_path)

            # Map by filename without extension
            module_name = file_path.stem
            module_to_file[module_name] = file_node

            # Also map by full relative path
            module_to_file[str(relative_path)] = file_node

        # Add import edges
        for file_data in parsed_files:
            file_path = Path(file_data["file"])
            relative_path = file_path.relative_to(root_path)
            file_node = str(relative_path)

            for import_name in file_data.get("imports", []):
                # Try to resolve the import
                base_import = import_name.split(".")[0]
                if base_import in module_to_file:
                    imported_file = module_to_file[base_import]
                    if imported_file != file_node:
                        self.graph.add_edge(
                            file_node, imported_file, relation="imports"
                        )

    def get_graph(self) -> nx.DiGraph:
        """Get the current graph."""
        return self.graph

    def clear(self) -> None:
        """Clear the graph."""
        self.graph.clear()

