import threading
from collections.abc import Generator
from typing import Optional


class FileSystemWatcher:
    """
    Runs watchfiles in a background thread to collect file system change
    events for a path, so callers can drain already-collected changes
    instead of repeatedly rescanning the file system.

    watchfiles is an optional dependency of pyfileindex: importing this
    module never requires it, only start() does.

    Args:
        path (str): file system path to watch
    """

    def __init__(self, path: str) -> None:
        self._path = path
        self._lock = threading.Lock()
        self._pending_changes: set = set()
        self._stop_event: Optional[threading.Event] = None
        self._thread: Optional[threading.Thread] = None
        self._generator: Optional[Generator[set[tuple], None, None]] = None

    @property
    def thread(self) -> Optional[threading.Thread]:
        return self._thread

    def start(self) -> None:
        """
        Start the background file system watcher.

        watchfiles.watch() only registers the underlying OS-level watch the
        first time the generator is advanced, which otherwise happens lazily
        inside the background thread. To avoid missing changes made right
        after construction, the generator is advanced once synchronously here
        before the background thread takes over.
        """
        import watchfiles

        self._stop_event = threading.Event()
        self._generator = watchfiles.watch(
            self._path,
            watch_filter=None,
            stop_event=self._stop_event,
            rust_timeout=50,
            yield_on_timeout=True,
        )
        if self._generator is not None:
            next(self._generator)
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """
        Stop the background file system watcher. Safe to call even if no
        watcher is running.
        """
        if self._stop_event is not None:
            self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None

    def drain_pending_changes(self) -> set:
        """
        Atomically take the file system changes collected since the last
        call.

        Returns:
            set: set of (watchfiles.Change, path) tuples
        """
        with self._lock:
            changes = self._pending_changes
            self._pending_changes = set()
        return changes

    def _worker(self) -> None:
        """
        Internal function run in a background thread to collect file system
        changes reported by watchfiles into self._pending_changes
        """
        if self._generator is None:
            return
        try:
            for changes in self._generator:
                if len(changes) != 0:
                    with self._lock:
                        self._pending_changes.update(changes)
        except FileNotFoundError:
            pass
