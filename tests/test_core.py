"""Tests for core mindmap functionality."""

import tempfile
from pathlib import Path

from mindmap.core import MindmapBuilder


def create_sample_python_file(directory: Path, filename: str, content: str):
    """Helper to create a test Python file."""
    file_path = directory / filename
    file_path.write_text(content, encoding="utf-8")
    return file_path


def test_build_from_directory():
    """Test building a mindmap from a directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create sample files
        create_sample_python_file(
            tmp_path,
            "module1.py",
            """
class MyClass:
    def method1(self):
        pass

def my_function():
    pass
""",
        )

        create_sample_python_file(
            tmp_path,
            "module2.py",
            """
import module1

class AnotherClass:
    pass
""",
        )

        builder = MindmapBuilder()
        graph = builder.build_from_directory(tmp_path)

        assert graph.number_of_nodes() > 0
        assert graph.number_of_edges() > 0

        # Check that files are nodes
        file_nodes = [
            n for n, data in graph.nodes(data=True) if data.get("type") == "file"
        ]
        assert len(file_nodes) >= 2


def test_empty_directory():
    """Test building from an empty directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        builder = MindmapBuilder()
        graph = builder.build_from_directory(tmp_path)

        assert graph.number_of_nodes() == 0
        assert graph.number_of_edges() == 0


def test_parser_extracts_concepts():
    """Test that parser extracts classes and functions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        create_sample_python_file(
            tmp_path,
            "test.py",
            """
class TestClass:
    pass

def test_function():
    pass
""",
        )

        builder = MindmapBuilder()
        graph = builder.build_from_directory(tmp_path)

        # Should have file node and concept nodes
        assert graph.number_of_nodes() >= 3  # file + 2 concepts


def test_import_relationships():
    """Test that imports create edges."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        create_sample_python_file(tmp_path, "a.py", "pass")
        create_sample_python_file(tmp_path, "b.py", "import a")

        builder = MindmapBuilder()
        graph = builder.build_from_directory(tmp_path)

        # Check for import edges
        edges = list(graph.edges(data=True))
        import_edges = [
            edge for edge in edges if edge[2].get("relation") == "imports"
        ]
        assert len(import_edges) > 0

