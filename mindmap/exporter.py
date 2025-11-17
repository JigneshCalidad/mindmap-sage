"""Export mindmap graphs to various formats.

This module transforms the NetworkX graph into visual representations,
primarily Mermaid diagrams. The exporter understands the graph structure
and formats it for human-readable visualization.
"""

import networkx as nx
from pathlib import Path


class Exporter:
    """Exports graphs to different formats."""

    def __init__(self, graph: nx.DiGraph):
        self.graph = graph

    def to_mermaid(self, direction: str = "TD") -> str:
        """Export graph to Mermaid diagram format.

        Args:
            direction: Graph direction (TD=top-down, LR=left-right, etc.)

        Returns:
            Mermaid diagram as string
        """
        if not self.graph.nodes():
            return "graph TD\n    Empty[No nodes found]"

        lines = [f"graph {direction}"]
        node_ids = {}
        node_counter = 0

        # Assign IDs to nodes
        for node in self.graph.nodes():
            node_data = self.graph.nodes[node]
            node_type = node_data.get("type", "unknown")

            # Create a safe ID for Mermaid
            node_id = f"node{node_counter}"
            node_ids[node] = node_id
            node_counter += 1

            # Format node label
            label = self._format_label(node, node_data)
            shape = self._get_shape(node_type)

            lines.append(f'    {node_id}{shape}["{label}"]')

        # Add edges
        for source, target, data in self.graph.edges(data=True):
            source_id = node_ids.get(source)
            target_id = node_ids.get(target)

            if source_id and target_id:
                relation = data.get("relation", "")
                edge_style = self._get_edge_style(relation)
                lines.append(f"    {source_id} {edge_style} {target_id}")

        return "\n".join(lines)

    def _format_label(self, node: str, node_data: dict) -> str:
        """Format node label for display."""
        node_type = node_data.get("type", "unknown")
        name = node_data.get("name", node)

        if node_type == "file":
            # Show just the filename
            return Path(node).name if "/" in node else node
        elif node_type in ["class", "function", "method"]:
            return f"{node_type}: {name}"
        elif node_type.startswith("heading"):
            return f"📄 {name}"
        elif node_type == "todo":
            return f"✓ {name}"
        else:
            return name

    def _get_shape(self, node_type: str) -> str:
        """Get Mermaid shape based on node type."""
        shapes = {
            "file": "",
            "class": "((()))",
            "function": "()",
            "method": "()",
            "todo": "{{}}",
            "heading-1": "[()]",
            "heading-2": "[()]",
            "heading-3": "[()]",
        }
        return shapes.get(node_type, "")

    def _get_edge_style(self, relation: str) -> str:
        """Get edge style based on relation type."""
        if relation == "imports":
            return "-->"
        elif relation == "defined_in":
            return "-.->"
        else:
            return "-->"

    def to_json(self) -> dict:
        """Export graph to JSON format."""
        nodes = []
        edges = []

        for node, data in self.graph.nodes(data=True):
            nodes.append(
                {
                    "id": node,
                    "type": data.get("type", "unknown"),
                    "name": data.get("name", node),
                    "file": data.get("file"),
                    "line": data.get("line"),
                }
            )

        for source, target, data in self.graph.edges(data=True):
            edges.append(
                {
                    "source": source,
                    "target": target,
                    "relation": data.get("relation", ""),
                }
            )

        return {"nodes": nodes, "edges": edges}

