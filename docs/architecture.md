# Architecture

## Overview

Mindmap Sage transforms codebases into visual mindmaps by understanding their conceptual structure. The system follows a clear pipeline: **Parse → Build → Export → Serve**.

## Components

### Parser (`mindmap/parser.py`)

The parser reads source files and extracts concepts:
- **Classes**: Object-oriented structures
- **Functions/Methods**: Executable units
- **Imports**: Dependencies and relationships
- **Headings**: Documentation structure (Markdown)
- **TODOs**: Future work items

The parser supports multiple languages:
- Python (via AST)
- JavaScript (via regex)
- Java (via regex)
- Markdown (via regex)

### Core Builder (`mindmap/core.py`)

The builder constructs a directed graph using NetworkX:
- **Nodes**: Represent files and concepts
- **Edges**: Represent relationships (imports, containment, dependencies)

The graph structure captures:
- Which concepts belong to which files
- How files depend on each other
- The hierarchical structure of the codebase

### Exporter (`mindmap/exporter.py`)

The exporter transforms the graph into visual formats:
- **Mermaid**: Diagram format for visualization
- **JSON**: Structured data format

The exporter understands node types and formats them appropriately for visualization.

### API (`app/main.py`)

FastAPI application providing:
- `/scan`: Trigger repository scanning
- `/graph`: Get graph as JSON
- `/mermaid`: Get graph as Mermaid diagram
- `/health`: Health check

### CLI (`cli/mindmap_cli.py`)

Command-line interface with three main commands:
- `scan`: Scan a repository and export mindmap
- `serve`: Start the API server
- `export`: Export current mindmap (requires prior scan)

### Watcher (`watcher/watcher.py`)

File system watcher that:
- Monitors repository for changes
- Automatically rebuilds mindmap on file modifications
- Debounces rapid changes to avoid excessive rebuilds

## Data Flow

```
Repository Files
    ↓
Parser (extracts concepts)
    ↓
Core Builder (constructs graph)
    ↓
Exporter (formats output)
    ↓
Mermaid/JSON/API
```

## Design Principles

1. **Non-intrusive**: Reads code without executing it
2. **Language-agnostic**: Supports multiple languages
3. **Reactive**: Updates automatically when code changes
4. **Visual-first**: Outputs are designed for human understanding
5. **Modular**: Each component has a clear responsibility

## Extension Points

- **New Languages**: Add parsers in `parser.py`
- **New Formats**: Add exporters in `exporter.py`
- **New Relationships**: Extend graph building in `core.py`
- **New Features**: Add API endpoints in `app/main.py`

