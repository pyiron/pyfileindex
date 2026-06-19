import contextlib
import os
import threading
from collections.abc import Generator
from typing import Callable, Optional

import pandas


class PyFileIndex:
    """
    The PyFileIndex maintains a pandas DataFrame to track changes in the file system.

    Args:
        path (str): file system path
        filter_function (Callable): function to filter for specific files (optional)
        debug (bool): enable debug print statements (optional)
        df (pandas.DataFrame): DataFrame of a previous PyFileIndex object (optional)
        watch (bool): keep the file index in sync using a background file system
            watcher instead of rescanning the file system on every update() call
            (optional)
    """

    def __init__(
        self,
        path: str = ".",
        filter_function: Optional[Callable] = None,
        debug: bool = False,
        df: Optional[pandas.DataFrame] = None,
        watch: bool = False,
    ) -> None:
        abs_path = os.path.abspath(os.path.expanduser(path))
        self._check_if_path_exists(path=abs_path)
        self._debug = debug
        self._filter_function = filter_function
        self._path = abs_path
        self._watch_enabled = watch
        self._watch_lock = threading.Lock()
        self._pending_changes: set = set()
        self._watch_stop_event: Optional[threading.Event] = None
        self._watch_thread: Optional[threading.Thread] = None
        self._watch_generator: Optional[
            Generator[set[tuple], None, None]
        ] = None
        if watch:
            self._start_watch()
        if df is None:
            self._df = self._create_df_from_lst(
                [self._get_lst_entry_from_path(entry=self._path)]
                + list(self._scandir(path=self._path, df=None, recursive=True))
            )
        else:
            self._df = df

    @property
    def df(self) -> pandas.DataFrame:
        return self._df

    @property
    def dataframe(self) -> pandas.DataFrame:
        return self.df

    def open(self, path: str) -> "PyFileIndex":
        """
        Open PyFileIndex in the subdirectory path

        Args:
             path (str): subdirectory to open

        Returns:
            PyFileIndex: PyFileIndex for subdirectory
        """
        abs_path = os.path.abspath(os.path.expanduser(os.path.join(self._path, path)))
        self._check_if_path_exists(path=abs_path)
        self.update()
        if abs_path == self._path:
            return self
        elif (
            os.path.commonpath([abs_path, self._path]) == self._path and os.name != "nt"
        ):
            return PyFileIndex(
                path=abs_path,
                filter_function=self._filter_function,
                debug=self._debug,
                df=self._df[self._df.path.str.contains(abs_path)],
                watch=self._watch_enabled,
            )
        elif (
            os.path.commonpath([abs_path, self._path]) == self._path and os.name != "nt"
        ):
            abs_path_unix = abs_path.replace("\\", "/")
            return PyFileIndex(
                path=abs_path,
                filter_function=self._filter_function,
                debug=self._debug,
                df=self._df[
                    self._df.path.str.replace("\\", "/").str.contains(abs_path_unix)
                ],
                watch=self._watch_enabled,
            )
        else:
            return PyFileIndex(
                path=abs_path,
                filter_function=self._filter_function,
                debug=self._debug,
                watch=self._watch_enabled,
            )

    def update(self) -> None:
        """
        Update file index
        """
        self._check_if_path_exists(path=self._path)
        if self._watch_enabled:
            self._apply_watch_changes(changes=self._drain_pending_changes())
            return
        df_new, files_changed_lst, path_deleted_lst = self._get_changes_quick()
        if self._debug:
            print("Changes: ", df_new.path.values, files_changed_lst, path_deleted_lst)
        if len(path_deleted_lst) != 0:
            self._df = self._df[~self._df.path.isin(path_deleted_lst)]
        if len(files_changed_lst) != 0:
            df_updated = self._create_df_from_lst(
                [self._get_lst_entry_from_path(entry=f) for f in files_changed_lst]
            )
            self._df = self._df[~self._df.path.isin(df_updated.path)]
            self._df = (
                pandas.concat([self._df, df_updated])
                .drop_duplicates()
                .reset_index(drop=True)
            )
        if len(df_new) != 0:
            self._df = (
                pandas.concat([self._df, df_new])
                .drop_duplicates()
                .reset_index(drop=True)
            )

    def close(self) -> None:
        """
        Stop the background file system watcher started with watch=True. Safe to
        call even if no watcher is running.
        """
        if self._watch_stop_event is not None:
            self._watch_stop_event.set()
        if self._watch_thread is not None:
            self._watch_thread.join(timeout=5)
            self._watch_thread = None

    def __enter__(self) -> "PyFileIndex":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def __del__(self) -> None:
        with contextlib.suppress(Exception):
            self.close()

    def _init_df_lst(
        self,
        path_lst: list,
        df: Optional[pandas.DataFrame] = None,
        include_root: bool = True,
    ) -> pandas.DataFrame:
        """
        Internal function to build the pandas file index from a list of directories

        Args:
            path_lst (list): list of directories to scan
            df (pandas.DataFrame/ None): existing file index table
            include_root (bool): include the root directory in file index

        Returns:
            pandas.DataFrame: pandas file index
        """
        total_lst = []
        for p in path_lst:
            if include_root:
                total_lst.append(self._get_lst_entry_from_path(entry=p))
            for entry in list(self._scandir(path=p, df=df, recursive=True)):
                total_lst.append(entry)
        return self._create_df_from_lst(total_lst)

    def _scandir(
        self, path: str, df: Optional[pandas.DataFrame] = None, recursive: bool = True
    ) -> Generator:
        """
        Internal function to recursively scan directories

        Args:
            path (str): file system path
            df (pandas.DataFrame/ None): existing file index table
            recursive (bool): recursively iterate over subdirectories

        Returns:
            list: list of file entries
        """
        try:
            if df is not None and len(df) > 0:
                with os.scandir(path) as it:
                    for entry in it:
                        if entry.path not in df.path.values:
                            if entry.is_dir(follow_symlinks=False) and recursive:
                                yield from self._scandir(
                                    path=entry.path, df=df, recursive=recursive
                                )
                                yield self._get_lst_entry(entry=entry)
                            else:
                                yield self._get_lst_entry(entry=entry)
            else:
                with os.scandir(path) as it:
                    for entry in it:
                        if entry.is_dir(follow_symlinks=False) and recursive:
                            yield from self._scandir(
                                path=entry.path, recursive=recursive
                            )
                            yield self._get_lst_entry(entry=entry)
                        else:
                            yield self._get_lst_entry(entry=entry)
        except FileNotFoundError:
            yield from ()

    def _start_watch(self) -> None:
        """
        Internal function to start the background file system watcher

        watchfiles.watch() only registers the underlying OS-level watch the
        first time the generator is advanced, which otherwise happens lazily
        inside the background thread. To avoid missing changes made right
        after construction, the generator is advanced once synchronously here
        before the background thread takes over.
        """
        import watchfiles

        self._watch_stop_event = threading.Event()
        self._watch_generator = watchfiles.watch(
            self._path,
            watch_filter=None,
            stop_event=self._watch_stop_event,
            rust_timeout=50,
            yield_on_timeout=True,
        )
        if self._watch_generator is not None:
            next(self._watch_generator)
        self._watch_thread = threading.Thread(target=self._watch_worker, daemon=True)
        self._watch_thread.start()

    def _watch_worker(self) -> None:
        """
        Internal function run in a background thread to collect file system
        changes reported by watchfiles into self._pending_changes
        """
        if self._watch_generator is None:
            return
        try:
            for changes in self._watch_generator:
                if len(changes) != 0:
                    with self._watch_lock:
                        self._pending_changes.update(changes)
        except FileNotFoundError:
            pass

    def _drain_pending_changes(self) -> set:
        """
        Internal function to atomically take the file system changes collected
        by the background watcher since the last call

        Returns:
            set: set of (watchfiles.Change, path) tuples
        """
        with self._watch_lock:
            changes = self._pending_changes
            self._pending_changes = set()
        return changes

    def _apply_watch_changes(self, changes: set) -> None:
        """
        Internal function to apply the changes collected by the background
        watcher to the file index

        Args:
            changes (set): set of (watchfiles.Change, path) tuples
        """
        import watchfiles

        if len(changes) == 0:
            return
        deleted_lst = [
            p for change, p in changes if change == watchfiles.Change.deleted
        ]
        changed_lst = [
            p for change, p in changes if change != watchfiles.Change.deleted
        ]
        if self._debug:
            print("Changes: ", changed_lst, deleted_lst)
        if len(deleted_lst) != 0:
            prefix_tuple = tuple(p + os.sep for p in deleted_lst)
            self._df = self._df[
                ~(
                    self._df.path.isin(deleted_lst)
                    | self._df.path.str.startswith(prefix_tuple)
                )
            ]
        if len(changed_lst) != 0:
            entry_lst = []
            for p in changed_lst:
                entry = self._get_lst_entry_from_path(entry=p)
                if len(entry) != 0:
                    entry_lst.append(entry)
                    if entry[3]:
                        entry_lst += list(
                            self._scandir(path=p, df=None, recursive=True)
                        )
            df_updated = self._create_df_from_lst(entry_lst)
            if len(df_updated) != 0:
                self._df = self._df[~self._df.path.isin(df_updated.path)]
                self._df = (
                    pandas.concat([self._df, df_updated])
                    .drop_duplicates()
                    .reset_index(drop=True)
                )

    def _get_changes_quick(self) -> tuple:
        """
        Internal function to list the changes to the file system

        Returns:
            tuple: pandas.DataFrame with new entries, list of changed files, and list of deleted paths
        """
        path_exists_bool_lst = self._df.path.apply(os.path.exists)
        path_deleted_lst = self._df[~path_exists_bool_lst].path.values
        df_exists = self._df[path_exists_bool_lst]
        stat_lst = [os.stat(p) for p in df_exists.path.values]
        st_mtime = pandas.Series([s.st_mtime for s in stat_lst], index=df_exists.index)
        st_nlink = pandas.Series([s.st_nlink for s in stat_lst], index=df_exists.index)
        df_modified = df_exists[
            ((df_exists.mtime - st_mtime).abs() > (1e-15 + 1e-10 * st_mtime.abs()))
            | (df_exists.nlink != st_nlink)
        ]
        if len(df_modified) > 0:
            if sum(df_modified.is_directory.values) > 0:
                dir_changed_lst = df_modified[df_modified.is_directory].path.values
            else:
                dir_changed_lst = []
            files_changed_lst = df_modified.path.values
        else:
            files_changed_lst, dir_changed_lst = [], []
        df_new = self._init_df_lst(
            path_lst=dir_changed_lst, df=df_exists, include_root=False
        )
        return df_new, files_changed_lst, path_deleted_lst

    def _get_lst_entry_from_path(self, entry: str) -> list:
        """
        Internal function to generate file index entry from file system path

        Args:
            entry (str): file system path

        Returns:
            list: file index entry
        """
        try:
            stat = os.stat(entry)
            isdir = os.path.isdir(entry)
            if not isdir and self._filter_function is not None:
                flag = self._filter_function(entry)
            else:
                flag = True
            if flag:
                return [
                    os.path.basename(entry),
                    entry,
                    os.path.dirname(entry),
                    isdir,
                    stat.st_mtime,
                    stat.st_nlink,
                ]
            else:
                return []
        except FileNotFoundError:
            return []

    def _get_lst_entry(self, entry) -> list:
        """
        Internal function to generate file index entry from scandir DirEntry

        Args:
            entry (DirEntry): scandir DirEntry

        Returns:
            list: file index entry
        """
        try:
            stat = entry.stat()
            isdir = entry.is_dir()
            if not isdir and self._filter_function is not None:
                flag = self._filter_function(entry.path)
            else:
                flag = True
            if flag:
                return [
                    entry.name,
                    entry.path,
                    os.path.dirname(entry.path),
                    isdir,
                    stat.st_mtime,
                    stat.st_nlink,
                ]
            else:
                return []
        except FileNotFoundError:
            return []

    def _repr_html_(self) -> str:
        """
        Internal visualization function for iPython notebooks

        Returns:
            str: iPython notebook representation of the pandas.DataFrame
        """
        return self._df._repr_html_()

    @staticmethod
    def _check_if_path_exists(path: str) -> None:
        """
        Internal function to check if the given path exists

        Args:
            path (str): file system path

        Raises:
            FileNotFoundError: if the path does not exist
        """
        if not os.path.exists(path):
            raise FileNotFoundError(
                "The path " + path + " does not exist on your filesystem."
            )

    @staticmethod
    def _create_df_from_lst(lst: list) -> pandas.DataFrame:
        """
        Internal function to generate file index as pandas from a list of entries

        Args:
            lst (list): list of file index entries

        Returns:
            pandas.DataFrame: file index
        """
        lst_clean = [sub_lst for sub_lst in lst if len(sub_lst) != 0]
        if len(lst_clean) != 0:
            name_lst, path_lst, dirname_lst, dir_lst, mtime_lst, nlink_lst = zip(
                *lst_clean
            )
        else:
            name_lst, path_lst, dirname_lst, dir_lst, mtime_lst, nlink_lst = (
                (),
                (),
                (),
                (),
                (),
                (),
            )
        return pandas.DataFrame(
            {
                "basename": name_lst,
                "path": path_lst,
                "dirname": dirname_lst,
                "is_directory": dir_lst,
                "mtime": mtime_lst,
                "nlink": nlink_lst,
            }
        )

    def __len__(self) -> int:
        """
        Returns the number of files in the index.

        Returns:
            int: The number of files in the index.
        """
        return len(self._df[~self._df.is_directory])
