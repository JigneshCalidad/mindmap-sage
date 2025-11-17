"""File system watcher for real-time mindmap updates.

This module monitors repository changes and automatically updates
the mindmap when files are modified, added, or removed. It provides
a reactive layer that keeps the mindmap in sync with the codebase.
"""

import threading
from pathlib import Path
from typing import Any, Callable, Optional

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
        self._rebuild_timer: Optional[threading.Timer] = None
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

    def _schedule_rebuild(self) -> None:
        """Schedule a rebuild with debouncing."""
        with self._lock:
            # Cancel any pending rebuild
            if self._rebuild_timer is not None:
                self._rebuild_timer.cancel()

            # Schedule a new rebuild after debounce delay
            self._rebuild_timer = threading.Timer(
                self.debounce_seconds, self._rebuild
            )
            self._rebuild_timer.start()

    def _handle_event(self, event: Any) -> None:
        """Handle file system event."""
        if event.is_directory:
            return

        # Check if file is relevant
        file_path = Path(event.src_path)
        if file_path.suffix.lower() not in {".py", ".js", ".md", ".java"}:
            return

        # Schedule rebuild with debouncing
        self._schedule_rebuild()

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
            if self._rebuild_timer is not None:
                self._rebuild_timer.cancel()
                self._rebuild_timer = None

        if self.observer:
            self.observer.stop()
            self.observer.join()
            print("Watcher stopped")

    def __enter__(self) -> "MindmapWatcher":
        """Context manager entry."""
        self.start()
        return self

    def __exit__(
        self, exc_type: Optional[type], exc_val: Optional[BaseException], exc_tb: Optional[Any]
    ) -> None:
        """Context manager exit."""
        self.stop()


class _MindmapEventHandler(FileSystemEventHandler):
    """Internal event handler for watchdog."""

    def __init__(self, callback: Callable[[Any], None]) -> None:
        self.callback = callback

    def on_modified(self, event: Any) -> None:
        self.callback(event)

    def on_created(self, event: Any) -> None:
        self.callback(event)

    def on_deleted(self, event: Any) -> None:
        self.callback(event)

