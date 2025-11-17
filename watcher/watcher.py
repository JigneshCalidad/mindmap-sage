"""File system watcher for real-time mindmap updates.

This module monitors repository changes and automatically updates
the mindmap when files are modified, added, or removed. It provides
a reactive layer that keeps the mindmap in sync with the codebase.
"""

import time
from pathlib import Path
from typing import Callable, Optional

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from mindmap.core import MindmapBuilder


class MindmapWatcher:
    """Watches a directory and rebuilds mindmap on changes."""

    def __init__(
        self,
        repo_path: Path,
        builder: MindmapBuilder,
        on_update: Optional[Callable] = None,
        debounce_seconds: float = 1.0,
    ):
        """Initialize watcher.

        Args:
            repo_path: Path to watch
            builder: MindmapBuilder instance to use
            on_update: Optional callback when mindmap updates
            debounce_seconds: Seconds to wait before processing changes
        """
        self.repo_path = Path(repo_path).resolve()
        self.builder = builder
        self.on_update = on_update
        self.debounce_seconds = debounce_seconds
        self.observer = None
        self.last_update_time = 0
        self.pending_update = False

    def _should_rebuild(self) -> bool:
        """Check if enough time has passed since last update."""
        current_time = time.time()
        if current_time - self.last_update_time >= self.debounce_seconds:
            self.last_update_time = current_time
            return True
        return False

    def _rebuild(self):
        """Rebuild the mindmap."""
        try:
            self.builder.build_from_directory(self.repo_path)
            graph = self.builder.get_graph()

            if self.on_update:
                self.on_update(graph)

            print(
                f"Mindmap updated: {graph.number_of_nodes()} nodes, "
                f"{graph.number_of_edges()} edges"
            )
        except Exception as e:
            print(f"Error rebuilding mindmap: {e}")

    def _handle_event(self, event):
        """Handle file system event."""
        if event.is_directory:
            return

        # Check if file is relevant
        file_path = Path(event.src_path)
        if file_path.suffix.lower() not in {".py", ".js", ".md", ".java"}:
            return

        # Debounce rapid changes
        if self._should_rebuild():
            self._rebuild()
        else:
            self.pending_update = True

    def start(self):
        """Start watching the directory."""
        if not self.repo_path.exists():
            raise ValueError(f"Path does not exist: {self.repo_path}")

        event_handler = _MindmapEventHandler(self._handle_event)
        self.observer = Observer()
        self.observer.schedule(event_handler, str(self.repo_path), recursive=True)
        self.observer.start()

        # Initial build
        self._rebuild()

        print(f"Watching: {self.repo_path}")

    def stop(self):
        """Stop watching."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            print("Watcher stopped")

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


class _MindmapEventHandler(FileSystemEventHandler):
    """Internal event handler for watchdog."""

    def __init__(self, callback: Callable):
        self.callback = callback

    def on_modified(self, event):
        self.callback(event)

    def on_created(self, event):
        self.callback(event)

    def on_deleted(self, event):
        self.callback(event)

