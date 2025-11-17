# mindmap-sage

A friendly bot that turns a codebase into a living, evolving mindmap. It watches a repository, understands its conceptual structure, and produces a clear visual map that updates whenever the repo changes. The goal is to help newcomers and experienced developers orient themselves quickly.

## Purpose

mindmap-sage reads the repo like a story: files, modules, docs, imports, and headings become nodes and relationships in a graph. The bot exports the structure as Mermaid so you can view it anywhere. Think of it as a soft mentor mapping the forest before you walk inside it.

## Learning Path: Concept → Pattern → Details → Practice → Reflect

### Concept

A codebase is a conceptual landscape. Seeing its shape reduces uncertainty and boosts intuition. A mindmap offers context: what depends on what, where ideas live, and how parts fit together.

### Pattern

The bot scans files, extracts concepts, builds a directed graph, and exports that graph. It also reacts to file changes through a watcher.

### Details

- **Scanning**: walk directories, parse `.py`, `.js`, `.md`, `.java` for top-level names.
- **Graph**: use NetworkX to model nodes (concepts) and edges (relationships).
- **Export**: produce Mermaid diagrams for easy visualization.
- **API**: FastAPI endpoints expose the current mindmap.
- **CLI**: trigger scans and exports.
- **Watcher**: monitors repository changes and updates the mindmap.

### Practice

Three structured labs help you experience the bot step by step.

### Reflect

After each lab, pause and notice what surprised you, what felt intuitive, and what patterns emerged.

## Features

- Automatic repo scanning
- Mindmap generation (Mermaid)
- Simple API with FastAPI
- CLI tools for scanning and exporting
- File watcher for real-time updates
- Example repo included
- CI pipeline for linting and tests

## Project Structure

```
mindmap-sage/
├─ app/
│  └─ main.py
├─ cli/
│  └─ mindmap_cli.py
├─ mindmap/
│  ├─ core.py
│  ├─ exporter.py
│  └─ parser.py
├─ watcher/
│  └─ watcher.py
├─ docs/
│  └─ architecture.md
├─ examples/sample_repo/
│  ├─ README.md
│  ├─ service.py
│  ├─ models.py
│  └─ docs.md
├─ tests/
│  └─ test_core.py
├─ pyproject.toml
├─ README.md
├─ LICENSE
└─ .github/workflows/ci.yml
```

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

**Scan:**

```bash
mindmap scan examples/sample_repo
```

**Serve API:**

```bash
mindmap serve
```

**Export Mermaid:**

```bash
mindmap scan examples/sample_repo --format mermaid
```

## Hands-on Labs

### Lab A: Generate Your First Mindmap

1. Run a scan on the sample repo:
   ```bash
   mindmap scan examples/sample_repo --format mermaid
   ```

2. View the Mermaid output.

3. Notice how modules and docs become nodes.

### Lab B: Change the Repo and Watch It Update

1. Modify or add a file in `examples/sample_repo/`.

2. Trigger scan again:
   ```bash
   mindmap scan examples/sample_repo
   ```

3. Compare the new map to the old one.

### Lab C: Extend the Parser

1. Add extraction of TODO comments as nodes (already implemented!).

2. Re-run scan.

3. Observe how new concepts appear.

## Reflection Prompts

- What relationships surprised you when you saw the visual map?
- Which parts of the repo felt clearer once mapped?
- How would you like the bot to evolve to match how your mind organizes information?

## License

MIT License

