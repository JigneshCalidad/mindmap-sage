"""Core graph building logic.

This module constructs a directed graph from parsed file data.
Nodes represent concepts (files, classes, functions), and edges
represent relationships (imports, dependencies, containment).
"""

import networkx as nx
from pathlib import Path
from typing import Dict, List, Optional

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

        for file_data in parsed_files:
            file_path = Path(file_data["file"])
            relative_path = file_path.relative_to(root_path)
            file_node = str(relative_path)

            for import_name in file_data.get("imports", []):
                imported_file = self._resolve_import_target(module_to_file, import_name)
                if imported_file and imported_file != file_node:
                    self.graph.add_edge(file_node, imported_file, relation="imports")

    def _build_module_index(
        self, parsed_files: List[Dict], root_path: Path
    ) -> Dict[str, str]:
        """Map possible module identifiers to file nodes."""
        module_to_file: Dict[str, str] = {}

        for file_data in parsed_files:
            file_path = Path(file_data["file"])
            relative_path = file_path.relative_to(root_path)
            file_node = str(relative_path)

            for alias in self._module_aliases(relative_path):
                module_to_file.setdefault(alias, file_node)

        return module_to_file

    def _module_aliases(self, relative_path: Path) -> List[str]:
        """Generate identifiers that may be used to import a file."""
        aliases = set()
        relative_posix = relative_path.as_posix()
        aliases.add(relative_posix)

        without_suffix = relative_path.with_suffix("")
        without_suffix_posix = without_suffix.as_posix()
        aliases.add(without_suffix_posix)

        dotted = ".".join(without_suffix.parts)
        if dotted:
            aliases.add(dotted)

        aliases.add(relative_path.stem)

        if relative_path.name == "__init__.py":
            package_path = relative_path.parent
            if package_path and package_path != Path("."):
                aliases.add(package_path.as_posix())
                dotted_package = ".".join(package_path.parts)
                if dotted_package:
                    aliases.add(dotted_package)
                aliases.add(package_path.name)

        return [alias for alias in aliases if alias]

    def _resolve_import_target(
        self, module_to_file: Dict[str, str], import_name: str
    ) -> Optional[str]:
        """Resolve an import string to a graph node."""
        if not import_name:
            return None

        normalized = import_name.replace("\\", "/").strip()
        if not normalized:
            return None

        dotted = normalized.replace("/", ".")
        parts = [part for part in dotted.split(".") if part]

        candidates = []
        for i in range(len(parts), 0, -1):
            candidates.append(".".join(parts[:i]))

        path_style = "/".join(parts)
        if path_style:
            candidates.append(path_style)
            candidates.append(f"{path_style}.py")

        candidates.append(normalized)

        for candidate in candidates:
            target = module_to_file.get(candidate)
            if target:
                return target

        return None

    def get_graph(self) -> nx.DiGraph:
        """Get the current graph."""
        return self.graph

    def clear(self):
        """Clear the graph."""
        self.graph.clear()

