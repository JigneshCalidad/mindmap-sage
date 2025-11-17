"""File system watcher for real-time mindmap updates.

This module monitors repository changes and automatically updates
the mindmap when files are modified, added, or removed. It provides
a reactive layer that keeps the mindmap in sync with the codebase.
"""

import threading
from pathlib import Path
from typing import Any, Callable, Optional, Type

import networkx as nx
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from mindmap.core import MindmapBuilder


class MindmapWatcher:
    """Watches a directory and rebuilds mindmap on changes."""

    def __init__(
        self,
        repo_path: Path,
        builder: MindmapBuilder,
        on_update: Optional[Callable[[nx.DiGraph], None]] = None,
        debounce_seconds: float = 1.0,
    ) -> None:
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
        self.pending_update = False
        self._update_timer: Optional[threading.Timer] = None
        self._lock = threading.Lock()

    def _rebuild(self) -> None:
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

    def _handle_event(self, event) -> None:
        """Handle file system event."""
        if event.is_directory:
            return

        # Check if file is relevant
        file_path = Path(event.src_path)
        if file_path.suffix.lower() not in {".py", ".js", ".md", ".java"}:
            return

        # Debounce rapid changes using a timer
        with self._lock:
            self.pending_update = True
            # Cancel existing timer if any
            if self._update_timer:
                self._update_timer.cancel()
            # Schedule rebuild after debounce period
            self._update_timer = threading.Timer(
                self.debounce_seconds, self._process_pending_update
            )
            self._update_timer.start()

    def _process_pending_update(self) -> None:
        """Process pending update after debounce period."""
        with self._lock:
            if self.pending_update:
                self.pending_update = False
                self._rebuild()
            if self._update_timer:
                self._update_timer = None

    def start(self) -> None:
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

    def stop(self) -> None:
        """Stop watching."""
        with self._lock:
            if self._update_timer:
                self._update_timer.cancel()
                self._update_timer = None
        if self.observer:
            self.observer.stop()
            self.observer.join()
            print("Watcher stopped")

    def __enter__(self) -> "MindmapWatcher":
        """Context manager entry."""
        self.start()
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> None:
        """Context manager exit."""
        self.stop()


class _MindmapEventHandler(FileSystemEventHandler):
    """Internal event handler for watchdog."""

    def __init__(self, callback: Callable[[FileSystemEvent], None]) -> None:
        self.callback = callback

    def on_modified(self, event: FileSystemEvent) -> None:
        self.callback(event)

    def on_created(self, event: FileSystemEvent) -> None:
        self.callback(event)

    def on_deleted(self, event: FileSystemEvent) -> None:
        self.callback(event)

