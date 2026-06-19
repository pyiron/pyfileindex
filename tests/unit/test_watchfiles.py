import shutil
import time
import unittest
import os

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
        thread = self.fi._watch_thread
        self.assertTrue(thread.is_alive())
        self.fi.close()
        self.assertFalse(thread.is_alive())
        self.assertIsNone(self.fi._watch_thread)
        # closing twice should be a no-op, not raise
        self.fi.close()

    def test_watch_context_manager(self):
        with PyFileIndex(path=self.path, watch=True) as fi:
            thread = fi._watch_thread
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
                self.assertIsNotNone(fi_sub._watch_thread)
            finally:
                fi_sub.close()
        finally:
            os.rmdir(sub_dir)
