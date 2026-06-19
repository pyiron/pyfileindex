import threading
import time
import unittest
from unittest.mock import MagicMock, patch

try:
    import watchfiles  # noqa: F401
except ImportError:
    raise unittest.SkipTest("watchfiles is required for these tests")

from pyfileindex.watcher import FileSystemWatcher


class TestFileSystemWatcher(unittest.TestCase):
    """
    Unit tests for FileSystemWatcher in isolation, without going through
    PyFileIndex.
    """

    def test_worker_none_generator(self):
        watcher = FileSystemWatcher(path=".")
        watcher._generator = None
        watcher._worker()
        self.assertEqual(watcher._pending_changes, set())

    def test_worker_file_not_found(self):
        def raise_file_not_found():
            raise FileNotFoundError
            yield set()

        watcher = FileSystemWatcher(path=".")
        watcher._generator = raise_file_not_found()
        watcher._worker()
        self.assertEqual(watcher._pending_changes, set())

    def test_worker_collects_changes(self):
        change = (watchfiles.Change.added, "/some/path")

        def generate_changes():
            yield {change}

        watcher = FileSystemWatcher(path=".")
        watcher._generator = generate_changes()
        watcher._worker()
        self.assertEqual(watcher._pending_changes, {change})

    def test_drain_pending_changes(self):
        watcher = FileSystemWatcher(path=".")
        change = (watchfiles.Change.added, "/some/path")
        watcher._pending_changes = {change}
        watcher._changes_available.set()
        drained = watcher.drain_pending_changes()
        self.assertEqual(drained, {change})
        self.assertEqual(watcher._pending_changes, set())
        self.assertFalse(watcher._changes_available.is_set())

    def test_drain_pending_changes_without_timeout_does_not_wait(self):
        watcher = FileSystemWatcher(path=".")
        start = time.monotonic()
        drained = watcher.drain_pending_changes(timeout=0)
        self.assertEqual(drained, set())
        self.assertLess(time.monotonic() - start, 1)

    def test_drain_pending_changes_waits_for_late_arriving_change(self):
        watcher = FileSystemWatcher(path=".")
        change = (watchfiles.Change.added, "/some/path")

        def add_change_after_delay():
            time.sleep(0.05)
            with watcher._lock:
                watcher._pending_changes.add(change)
                watcher._changes_available.set()

        threading.Thread(target=add_change_after_delay).start()
        drained = watcher.drain_pending_changes(timeout=1)
        self.assertEqual(drained, {change})

    def test_start_advances_generator_and_starts_thread(self):
        release = threading.Event()

        def generate_changes():
            yield {(watchfiles.Change.added, "/some/path")}
            release.wait()

        with patch("watchfiles.watch", return_value=generate_changes()):
            watcher = FileSystemWatcher(path=".")
            watcher.start()
            try:
                self.assertIsInstance(watcher.thread, threading.Thread)
                self.assertTrue(watcher.thread.is_alive())
            finally:
                release.set()
                watcher.stop()
        self.assertIsNone(watcher.thread)

    def test_stop_without_start_is_noop(self):
        watcher = FileSystemWatcher(path=".")
        watcher.stop()
        self.assertIsNone(watcher.thread)

    def test_stop_sets_stop_event_and_joins_thread(self):
        watcher = FileSystemWatcher(path=".")
        watcher._stop_event = MagicMock()
        thread = MagicMock()
        watcher._thread = thread
        watcher.stop()
        watcher._stop_event.set.assert_called_once()
        thread.join.assert_called_once_with(timeout=5)
        self.assertIsNone(watcher.thread)
