"""Parse files and extract conceptual structure.

This module reads source files and extracts top-level concepts:
classes, functions, modules, and their relationships. Think of it
as a gentle reader that understands code structure without executing it.
"""

import ast
import re
from pathlib import Path
from typing import Any, Dict, List


class Parser:
    """Extracts concepts from source files."""

    def __init__(self):
        self.supported_extensions = {".py", ".js", ".md", ".java"}
        self.ignore_patterns = {
            "__pycache__",
            ".git",
            ".venv",
            "venv",
            "node_modules",
            ".pytest_cache",
        }

    def should_ignore(self, path: Path) -> bool:
        """Check if a path should be ignored."""
        parts = path.parts
        return any(ignore in parts for ignore in self.ignore_patterns)

    def parse_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse a single file and extract its concepts."""
        if not file_path.exists():
            return {}

        suffix = file_path.suffix.lower()
        if suffix == ".py":
            return self._parse_python(file_path)
        elif suffix == ".js":
            return self._parse_javascript(file_path)
        elif suffix == ".md":
            return self._parse_markdown(file_path)
        elif suffix == ".java":
            return self._parse_java(file_path)
        return {}

    def _parse_python(self, file_path: Path) -> Dict[str, Any]:
        """Parse Python file using AST."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                tree = ast.parse(content, filename=str(file_path))
        except (SyntaxError, UnicodeDecodeError):
            return {"file": str(file_path), "concepts": []}

        concepts = []
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module.split(".")[0])
                for alias in node.names:
                    concepts.append(
                        {
                            "name": alias.name,
                            "type": "import",
                            "module": node.module or "",
                        }
                    )

        # Use a visitor to track class context with proper nesting
        class FunctionVisitor(ast.NodeVisitor):
            def __init__(self) -> None:
                self.class_stack: List[ast.ClassDef] = []

            def visit_ClassDef(self, node: ast.ClassDef) -> None:
                self.class_stack.append(node)
                concepts.append(
                    {
                        "name": node.name,
                        "type": "class",
                        "line": node.lineno,
                    }
                )
                self.generic_visit(node)
                self.class_stack.pop()

            def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
                # Check if we're inside a class by checking the stack
                if not self.class_stack:
                    # Top-level function
                    concepts.append(
                        {
                            "name": node.name,
                            "type": "function",
                            "line": node.lineno,
                        }
                    )
                self.generic_visit(node)

        visitor = FunctionVisitor()
        visitor.visit(tree)

        # Add TODO comments as concepts
        for i, line in enumerate(content.split("\n"), 1):
            todo_match = re.search(r"#\s*TODO[:\s]*(.+)", line, re.IGNORECASE)
            if todo_match:
                concepts.append(
                    {
                        "name": f"TODO: {todo_match.group(1).strip()}",
                        "type": "todo",
                        "line": i,
                    }
                )

        return {
            "file": str(file_path),
            "concepts": concepts,
            "imports": list(set(imports)),
        }

    def _parse_javascript(self, file_path: Path) -> Dict[str, Any]:
        """Parse JavaScript file using regex patterns."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            return {"file": str(file_path), "concepts": []}

        concepts = []
        imports = []

        # Extract imports
        import_pattern = r"import\s+(?:(?:\{[^}]+\}|\*\s+as\s+\w+|\w+)\s+from\s+)?['\"]([^'\"]+)['\"]"
        for match in re.finditer(import_pattern, content):
            imports.append(match.group(1).split("/")[0])

        # Extract classes
        class_pattern = r"class\s+(\w+)(?:\s+extends\s+\w+)?\s*\{"
        for match in re.finditer(class_pattern, content):
            concepts.append(
                {
                    "name": match.group(1),
                    "type": "class",
                }
            )

        # Extract functions
        function_pattern = r"(?:export\s+)?(?:async\s+)?function\s+(\w+)|(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>"
        for match in re.finditer(function_pattern, content):
            name = match.group(1) or match.group(2)
            if name:
                concepts.append(
                    {
                        "name": name,
                        "type": "function",
                    }
                )

        # Extract TODO comments
        todo_pattern = r"//\s*TODO[:\s]*(.+)"
        for i, line in enumerate(content.split("\n"), 1):
            todo_match = re.search(todo_pattern, line, re.IGNORECASE)
            if todo_match:
                concepts.append(
                    {
                        "name": f"TODO: {todo_match.group(1).strip()}",
                        "type": "todo",
                        "line": i,
                    }
                )

        return {
            "file": str(file_path),
            "concepts": concepts,
            "imports": list(set(imports)),
        }

    def _parse_markdown(self, file_path: Path) -> Dict[str, Any]:
        """Parse Markdown file for headings and structure."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            return {"file": str(file_path), "concepts": []}

        concepts = []
        heading_pattern = r"^(#{1,6})\s+(.+)$"

        for i, line in enumerate(content.split("\n"), 1):
            match = re.match(heading_pattern, line)
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()
                concepts.append(
                    {
                        "name": title,
                        "type": f"heading-{level}",
                        "line": i,
                    }
                )

        return {
            "file": str(file_path),
            "concepts": concepts,
            "imports": [],
        }

    def _parse_java(self, file_path: Path) -> Dict[str, Any]:
        """Parse Java file using regex patterns."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            return {"file": str(file_path), "concepts": []}

        concepts = []
        imports = []

        # Extract imports
        import_pattern = r"import\s+(?:static\s+)?([\w.]+)\s*;"
        for match in re.finditer(import_pattern, content):
            imports.append(match.group(1).split(".")[0])

        # Extract classes and interfaces
        class_pattern = r"(?:public\s+)?(?:abstract\s+)?(?:class|interface|enum)\s+(\w+)"
        for match in re.finditer(class_pattern, content):
            concepts.append(
                {
                    "name": match.group(1),
                    "type": "class",
                }
            )

        # Extract methods (public methods)
        method_pattern = r"(?:public|private|protected)\s+(?:\w+\s+)*(\w+)\s*\([^)]*\)\s*\{"
        for match in re.finditer(method_pattern, content):
            method_name = match.group(1)
            if method_name not in ["if", "for", "while", "switch"]:
                concepts.append(
                    {
                        "name": method_name,
                        "type": "method",
                    }
                )

        # Extract TODO comments
        todo_pattern = r"//\s*TODO[:\s]*(.+)"
        for i, line in enumerate(content.split("\n"), 1):
            todo_match = re.search(todo_pattern, line, re.IGNORECASE)
            if todo_match:
                concepts.append(
                    {
                        "name": f"TODO: {todo_match.group(1).strip()}",
                        "type": "todo",
                        "line": i,
                    }
                )

        return {
            "file": str(file_path),
            "concepts": concepts,
            "imports": list(set(imports)),
        }

    def scan_directory(self, root_path: Path) -> List[Dict[str, Any]]:
        """Scan a directory recursively and parse all supported files."""
        results = []
        root_path = Path(root_path).resolve()

        if not root_path.exists():
            return results

        for file_path in root_path.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in self.supported_extensions:
                if not self.should_ignore(file_path):
                    parsed = self.parse_file(file_path)
                    if parsed:
                        results.append(parsed)

        return results

