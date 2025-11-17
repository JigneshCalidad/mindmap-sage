"""Core graph building logic.

This module constructs a directed graph from parsed file data.
Nodes represent concepts (files, classes, functions), and edges
represent relationships (imports, dependencies, containment).
"""

import networkx as nx
from pathlib import Path
from typing import Dict, List

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
        self, parsed_files: List[Dict], root_path: Path
    ):
        """Add edges based on import statements."""
        root_path = Path(root_path).resolve()

        module_to_file = self._build_module_index(parsed_files, root_path)

        # Add import edges
        for file_data in parsed_files:
            file_path = Path(file_data["file"])
            relative_path = file_path.relative_to(root_path)
            file_node = str(relative_path)

            for import_name in file_data.get("imports", []):
                for candidate in self._candidate_import_keys(import_name):
                    imported_file = module_to_file.get(candidate)
                    if imported_file and imported_file != file_node:
                        if not self._has_import_edge(file_node, imported_file):
                            self.graph.add_edge(
                                file_node, imported_file, relation="imports"
                            )
                        break

    def _build_module_index(
        self, parsed_files: List[Dict], root_path: Path
    ) -> Dict[str, str]:
        """Create a lookup map for resolving module names to file nodes."""
        module_to_file: Dict[str, str] = {}
        for file_data in parsed_files:
            file_path = Path(file_data["file"])
            relative_path = file_path.relative_to(root_path)
            file_node = str(relative_path)

            for alias in self._module_aliases(relative_path):
                module_to_file.setdefault(alias, file_node)

        return module_to_file

    def _module_aliases(self, relative_path: Path) -> List[str]:
        """Generate alias keys for a file based on common import styles."""
        without_suffix = relative_path.with_suffix("")

        candidates = [
            relative_path.as_posix(),
            str(relative_path),
            without_suffix.as_posix(),
            str(without_suffix),
            ".".join(without_suffix.parts),
            relative_path.stem,
        ]

        if relative_path.name == "__init__.py":
            parent = relative_path.parent
            if parent != Path("."):
                candidates.extend(
                    [
                        parent.as_posix(),
                        ".".join(parent.parts),
                    ]
                )

        return self._unique_preserve(candidates)

    def _candidate_import_keys(self, import_name: str) -> List[str]:
        """Generate possible lookup keys for an import statement."""
        cleaned = import_name.strip()
        if not cleaned:
            return []

        parts = cleaned.split(".")
        candidates: List[str] = []

        for i in range(len(parts), 0, -1):
            partial = ".".join(parts[:i])
            slash_partial = "/".join(parts[:i])
            candidates.extend(
                [
                    partial,
                    f"{partial}.py",
                    slash_partial,
                    f"{slash_partial}.py",
                ]
            )

        return self._unique_preserve(candidates)

    @staticmethod
    def _unique_preserve(values: List[str]) -> List[str]:
        """Deduplicate a list while preserving order."""
        seen = set()
        result = []
        for value in values:
            normalized = value.strip()
            if normalized and normalized not in seen:
                seen.add(normalized)
                result.append(normalized)
        return result

    def _has_import_edge(self, source: str, target: str) -> bool:
        """Check if an imports edge already exists between two files."""
        edge_data = self.graph.get_edge_data(source, target, default=None)
        if not edge_data:
            return False
        return edge_data.get("relation") == "imports"

    def get_graph(self) -> nx.DiGraph:
        """Get the current graph."""
        return self.graph

    def clear(self):
        """Clear the graph."""
        self.graph.clear()

