import shutil
import time
import unittest
import os

from unittest.mock import patch

from pyfileindex import PyFileIndex

try:
    import watchfiles
except ImportError:
    raise unittest.SkipTest("watchfiles is required for these tests")


def filter_function(file_name):
    return ".txt" in file_name


def touch(fname, times=None):
    with open(fname, "a"):
        os.utime(fname, times)


def update_until(fi, condition, timeout=10, interval=0.05):
    """
    Repeatedly call fi.update() until condition() is True or timeout (in
    seconds) is reached. Used to wait for the background watchfiles watcher
    to report changes, since that happens asynchronously.
    """
    deadline = time.monotonic() + timeout
    fi.update()
    while not condition() and time.monotonic() < deadline:
        time.sleep(interval)
        fi.update()
    return condition()


class TestPyFileIndexWatch(unittest.TestCase):
    """
    Tests for the watch=True mode, which keeps the file index in sync using a
    background watchfiles watcher instead of rescanning the file system on
    every update() call.
    """

    def setUp(self):
        self.path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "test_watch_dir"
        )
        os.makedirs(self.path, exist_ok=True)
        self.fi = PyFileIndex(path=self.path, watch=True)

    def tearDown(self):
        self.fi.close()
        shutil.rmtree(self.path)

    def test_watch_add_modify_delete_file(self):
        f_name = os.path.join(self.path, "watched.txt")
        touch(f_name)
        self.assertTrue(update_until(self.fi, lambda: f_name in self.fi.df.path.values))

        touch(f_name, (1330712280, 1330712292))
        self.assertTrue(
            update_until(
                self.fi,
                lambda: int(self.fi.df[self.fi.df.path == f_name].mtime.values[0])
                == 1330712292,
            )
        )

        os.remove(f_name)
        self.assertTrue(
            update_until(self.fi, lambda: f_name not in self.fi.df.path.values)
        )

    def test_watch_update_default_timeout_catches_immediate_change(self):
        """
        A filesystem change made right before update() may not have reached
        the background watcher yet (e.g. when a notebook runs "Run All" and
        cells execute back-to-back with no delay between them). update()'s
        default timeout should wait long enough for it to arrive without the
        caller needing to add a manual sleep, though OS scheduling jitter
        means a single call isn't always guaranteed to land within the
        timeout, so a couple of immediate retries are allowed.
        """
        sub_dir = os.path.join(self.path, "immediate")
        os.makedirs(sub_dir)
        found = False
        for _ in range(3):
            self.fi.update()
            if sub_dir in self.fi.df.path.values:
                found = True
                break
        self.assertTrue(found)

    def test_watch_add_remove_directory(self):
        sub_dir = os.path.join(self.path, "sub")
        nested_file = os.path.join(sub_dir, "nested.txt")
        os.makedirs(sub_dir)
        touch(nested_file)
        self.assertTrue(
            update_until(self.fi, lambda: nested_file in self.fi.df.path.values)
        )
        self.assertIn(sub_dir, self.fi.df.path.values)

        os.remove(nested_file)
        os.rmdir(sub_dir)
        self.assertTrue(
            update_until(self.fi, lambda: sub_dir not in self.fi.df.path.values)
        )
        self.assertNotIn(nested_file, self.fi.df.path.values)

    def test_watch_with_filter_function(self):
        fi = PyFileIndex(path=self.path, filter_function=filter_function, watch=True)
        try:
            txt_file = os.path.join(self.path, "watched.txt")
            o_file = os.path.join(self.path, "watched.o")
            touch(txt_file)
            touch(o_file)
            self.assertTrue(update_until(fi, lambda: txt_file in fi.df.path.values))
            self.assertNotIn(o_file, fi.df.path.values)
        finally:
            fi.close()

    def test_watch_close_stops_background_thread(self):
        thread = self.fi._watcher.thread
        self.assertTrue(thread.is_alive())
        self.fi.close()
        self.assertFalse(thread.is_alive())
        self.assertIsNone(self.fi._watcher.thread)
        # closing twice should be a no-op, not raise
        self.fi.close()

    def test_watch_context_manager(self):
        with PyFileIndex(path=self.path, watch=True) as fi:
            thread = fi._watcher.thread
            self.assertTrue(thread.is_alive())
        self.assertFalse(thread.is_alive())

    def test_open_propagates_watch_flag(self):
        sub_dir = os.path.join(self.path, "sub_propagate")
        os.makedirs(sub_dir)
        try:
            self.assertTrue(
                update_until(self.fi, lambda: sub_dir in self.fi.df.path.values)
            )
            fi_sub = self.fi.open(sub_dir)
            try:
                self.assertTrue(fi_sub._watch_enabled)
                self.assertIsNotNone(fi_sub._watcher.thread)
            finally:
                fi_sub.close()
        finally:
            os.rmdir(sub_dir)

    def test_open_backfills_files_missed_by_stale_parent_snapshot(self):
        """
        Regression test for a permanent-loss race: open() hands the child a
        snapshot filtered from the parent's dataframe, which can be stale if
        the parent's background watcher has not drained a recent change yet.
        A freshly started child watcher only reports changes from the moment
        it starts, so if the child trusted that stale snapshot instead of
        scanning the directory itself, a file that already existed before
        the child started watching would be permanently invisible to it --
        no amount of retrying update() afterwards would ever recover it.
        """
        sub_dir = os.path.join(self.path, "sub_stale")
        os.makedirs(sub_dir)
        nested_file = os.path.join(sub_dir, "nested.txt")
        touch(nested_file)

        # Simulate the parent's watcher not having drained the change yet by
        # making its update() a no-op for the duration of open(), so the
        # parent's df does not contain `nested_file` (or even `sub_dir`)
        # when it gets filtered for the child.
        with patch.object(self.fi, "update", lambda timeout=0.1: None):
            self.assertNotIn(sub_dir, self.fi.df.path.values)
            fi_sub = self.fi.open(sub_dir)
        try:
            self.assertIn(
                nested_file,
                fi_sub.df.path.values,
                msg="open() must not rely solely on a (possibly stale) "
                "snapshot filtered from the parent's dataframe -- a freshly "
                "started child watcher can never backfill a file that "
                "already existed before it started watching.",
            )
        finally:
            fi_sub.close()


class TestApplyWatchChanges(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = os.path.dirname(os.path.abspath(__file__))

    def test_apply_watch_changes_debug_print(self):
        fi = PyFileIndex(path=self.path, debug=True)
        try:
            with patch("builtins.print") as mock_print:
                fi._apply_watch_changes(
                    {(watchfiles.Change.deleted, os.path.join(self.path, "missing"))}
                )
                mock_print.assert_called()
        finally:
            fi.close()
