import numpy as np
import pandas
import os

try:
    from os import scandir
except ImportError:
    from scandir import scandir


class PyFileIndex(object):
    """
    The PyFileIndex maintains a pandas Dataframe to track changes in the file system.

    Args:
        path (str): file system path
        filter_function (function): function to filter for specific files
        debug (bool): enable debug print statements
    """

    def __init__(self, path=".", filter_function=None, debug=False):
        self._debug = debug
        self._filter_function = filter_function
        path = os.path.abspath(path)
        self._df = self._create_df_from_lst(
            list([self._get_lst_entry_from_path(entry=path)])
            + list(self._scandir(path=path, df=None, recursive=True))
        )

    @property
    def df(self):
        return self._df

    @property
    def dataframe(self):
        return self.df

    def _init_df_lst(self, path_lst, df=None, include_root=True):
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

    def _scandir(self, path, df=None, recursive=True):
        """
        Internal function to recursivley scan directories

        Args:
            path (str): file system path
            df (pandas.DataFrame/ None): existing file index table
            recursive (bool): recusivley iterate over sub directories

        Returns:
            list: list of file entries
        """
        try:
            if df is not None and len(df) > 0:
                for entry in scandir(path):
                    if entry.path not in df.path.values:
                        if entry.is_dir(follow_symlinks=False) and recursive:
                            yield from self._scandir(
                                path=entry.path, df=df, recursive=recursive
                            )
                            yield self._get_lst_entry(entry=entry)
                        else:
                            yield self._get_lst_entry(entry=entry)
            else:
                for entry in scandir(path):
                    if entry.is_dir(follow_symlinks=False) and recursive:
                        yield from self._scandir(path=entry.path, recursive=recursive)
                        yield self._get_lst_entry(entry=entry)
                    else:
                        yield self._get_lst_entry(entry=entry)
        except FileNotFoundError:
            return []

    def _get_changes_quick(self):
        """
        Internal function to list the changes to the file system

        Returns:
            list: pandas.DataFrame with new entries, list of changed files and list of deleted paths
        """
        path_exists_bool_lst = [os.path.exists(p) for p in self._df.path.values]
        path_deleted_lst = self._df[~np.array(path_exists_bool_lst)].path.values
        df_exists = self._df[path_exists_bool_lst]
        stat_lst = [os.stat(p) for p in df_exists.path.values]
        st_mtime = [s.st_mtime for s in stat_lst]
        st_nlink = [s.st_nlink for s in stat_lst]
        df_modified = df_exists[
            ~np.isclose(df_exists.mtime.values, st_mtime, rtol=1e-10, atol=1e-15)
            | np.not_equal(df_exists.nlink.values, st_nlink)
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

    def update(self):
        """
        Update file index
        """
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

    def _get_lst_entry_from_path(self, entry):
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

    def _get_lst_entry(self, entry):
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

    def _repr_html_(self):
        """
        Internal visualisation function for iPython notebooks

        Returns:
            HTML object: iPython notebook representation of the pandas.DataFrame
        """
        return self._df._repr_html_()

    @staticmethod
    def _create_df_from_lst(lst):
        """
        Internal function to generate file index as pandas from a list of entries

        Args:
            lst (list): list of file index entries

        Returns:
            pandas.DataFrame: file index
        """
        lst_clean = [l for l in lst if len(l) != 0]
        if len(lst_clean) != 0:
            name_lst, path_lst, dirname_lst, dir_lst, mtime_lst, nlink_lst = zip(
                *lst_clean
            )
        else:
            name_lst, path_lst, dirname_lst, dir_lst, mtime_lst, nlink_lst = (
                [],
                [],
                [],
                [],
                [],
                [],
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
