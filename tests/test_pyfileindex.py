import unittest
import os
import importlib
import sys
from time import sleep

import pandas
from unittest.mock import patch, MagicMock

from pyfileindex import PyFileIndex


def filter_function(file_name):
    return ".txt" in file_name


def touch(fname, times=None):
    with open(fname, "a"):
        os.utime(fname, times)


class TestJobFileTable(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = os.path.dirname(os.path.abspath(__file__))
        cls.fi_with_filter = PyFileIndex(path=cls.path, filter_function=filter_function)
        cls.fi_without_filter = PyFileIndex(path=cls.path)
        cls.fi_debug = PyFileIndex(
            path=cls.path, filter_function=filter_function, debug=True
        )
        cls.sleep_period = 5

    def test_project_single_empty_dir(self):
        p_name = os.path.join(self.path, "test_project_single_empty_dir")
        fi_with_filter_lst = self.fi_with_filter.dataframe.path.values
        fi_without_filter_lst = self.fi_without_filter.dataframe.path.values
        fi_debug_lst = self.fi_debug.dataframe.path.values
        os.makedirs(p_name)
        if os.name == "nt":
            sleep(self.sleep_period)
        self.fi_with_filter.update()
        self.fi_without_filter.update()
        self.fi_debug.update()
        fi_with_filter_diff = list(
            set(self.fi_with_filter.dataframe.path.values) - set(fi_with_filter_lst)
        )
        fi_without_filter_diff = list(
            set(self.fi_without_filter.dataframe.path.values)
            - set(fi_without_filter_lst)
        )
        fi_debug_diff = list(
            set(self.fi_debug.dataframe.path.values) - set(fi_debug_lst)
        )
        self.assertEqual(len(fi_with_filter_diff), 1)
        self.assertEqual(len(fi_without_filter_diff), 1)
        self.assertEqual(len(fi_debug_diff), 1)
        self.assertEqual(fi_with_filter_diff[0], p_name)
        self.assertEqual(fi_without_filter_diff[0], p_name)
        self.assertEqual(fi_debug_diff[0], p_name)
        if os.name != "nt":
            fi_with_filter_sub = self.fi_with_filter.open(p_name)
            fi_without_filter_sub = self.fi_without_filter.open(p_name)
            fi_debug_sub = self.fi_debug.open(p_name)
            self.assertNotEqual(fi_with_filter_sub, self.fi_with_filter)
            self.assertNotEqual(fi_without_filter_sub, self.fi_without_filter)
            self.assertNotEqual(fi_debug_sub, self.fi_debug)
            fi_with_filter_diff_sub = list(
                set(fi_with_filter_sub.dataframe.path.values) - set(fi_with_filter_lst)
            )
            fi_without_filter_diff_sub = list(
                set(fi_without_filter_sub.dataframe.path.values)
                - set(fi_without_filter_lst)
            )
            fi_debug_diff_sub = list(
                set(fi_debug_sub.dataframe.path.values) - set(fi_debug_lst)
            )
            self.assertEqual(len(fi_with_filter_diff_sub), 1)
            self.assertEqual(len(fi_without_filter_diff_sub), 1)
            self.assertEqual(len(fi_debug_diff_sub), 1)
            self.assertEqual(fi_with_filter_diff_sub[0], p_name)
            self.assertEqual(fi_without_filter_diff_sub[0], p_name)
            self.assertEqual(fi_debug_diff_sub[0], p_name)
        if os.name == "nt":
            sleep(self.sleep_period)
        os.removedirs(p_name)
        self.fi_with_filter.update()
        self.fi_without_filter.update()
        self.fi_debug.update()
        fi_with_filter_diff = list(
            set(self.fi_with_filter.dataframe.path.values) - set(fi_with_filter_lst)
        )
        fi_without_filter_diff = list(
            set(self.fi_without_filter.dataframe.path.values)
            - set(fi_without_filter_lst)
        )
        fi_debug_diff = list(
            set(self.fi_debug.dataframe.path.values) - set(fi_debug_lst)
        )
        self.assertEqual(len(fi_with_filter_diff), 0)
        self.assertEqual(len(fi_without_filter_diff), 0)
        self.assertEqual(len(fi_debug_diff), 0)

    def test_project_single_dir_with_files(self):
        p_name = os.path.join(self.path, "test_project_single_dir_with_files")
        fi_with_filter_lst = self.fi_with_filter.dataframe.path.values
        fi_without_filter_lst = self.fi_without_filter.dataframe.path.values
        fi_debug_lst = self.fi_debug.dataframe.path.values
        os.makedirs(p_name)
        touch(os.path.join(p_name, "test.txt"))
        touch(os.path.join(p_name, "test.o"))
        if os.name == "nt":
            sleep(self.sleep_period)
        self.fi_with_filter.update()
        self.fi_without_filter.update()
        self.fi_debug.update()
        fi_with_filter_diff = list(
            set(self.fi_with_filter.dataframe.path.values) - set(fi_with_filter_lst)
        )
        fi_without_filter_diff = list(
            set(self.fi_without_filter.dataframe.path.values)
            - set(fi_without_filter_lst)
        )
        fi_debug_diff = list(
            set(self.fi_debug.dataframe.path.values) - set(fi_debug_lst)
        )
        self.assertEqual(len(fi_with_filter_diff), 2)
        self.assertEqual(len(fi_without_filter_diff), 3)
        self.assertEqual(len(fi_debug_diff), 2)
        self.assertIn(
            p_name,
            [p for p in self.fi_with_filter.dataframe.path.values],
        )
        self.assertIn(
            p_name,
            [p for p in self.fi_without_filter.dataframe.path.values],
        )
        self.assertIn(p_name, [p for p in self.fi_debug.dataframe.path.values])
        self.assertIn(
            "test.txt",
            [os.path.basename(p) for p in self.fi_with_filter.dataframe.path.values],
        )
        self.assertIn(
            "test.o",
            [os.path.basename(p) for p in self.fi_without_filter.dataframe.path.values],
        )
        self.assertIn(
            "test.txt",
            [os.path.basename(p) for p in self.fi_without_filter.dataframe.path.values],
        )
        self.assertIn(
            "test.txt",
            [os.path.basename(p) for p in self.fi_debug.dataframe.path.values],
        )
        os.remove(os.path.join(p_name, "test.txt"))
        os.remove(os.path.join(p_name, "test.o"))
        os.removedirs(p_name)
        if os.name == "nt":
            sleep(self.sleep_period)
        self.fi_with_filter.update()
        self.fi_without_filter.update()
        self.fi_debug.update()
        fi_with_filter_diff = list(
            set(self.fi_with_filter.dataframe.path.values) - set(fi_with_filter_lst)
        )
        fi_without_filter_diff = list(
            set(self.fi_without_filter.dataframe.path.values)
            - set(fi_without_filter_lst)
        )
        fi_debug_diff = list(
            set(self.fi_debug.dataframe.path.values) - set(fi_debug_lst)
        )
        self.assertEqual(len(fi_with_filter_diff), 0)
        self.assertEqual(len(fi_without_filter_diff), 0)
        self.assertEqual(len(fi_debug_diff), 0)

    def test_project_sub_dir_with_files(self):
        if os.name != "nt":
            p_name = os.path.join(self.path, "test_project_sub_dir_with_files", "sub")
            fi_with_filter_lst = self.fi_with_filter.dataframe.path.values
            fi_without_filter_lst = self.fi_without_filter.dataframe.path.values
            fi_debug_lst = self.fi_debug.dataframe.path.values
            os.makedirs(p_name)
            touch(os.path.join(p_name, "test.txt"))
            touch(os.path.join(p_name, "test.o"))
            self.fi_with_filter.update()
            self.fi_without_filter.update()
            self.fi_debug.update()
            fi_with_filter_diff = list(
                set(self.fi_with_filter.dataframe.path.values) - set(fi_with_filter_lst)
            )
            fi_without_filter_diff = list(
                set(self.fi_without_filter.dataframe.path.values)
                - set(fi_without_filter_lst)
            )
            fi_debug_diff = list(
                set(self.fi_debug.dataframe.path.values) - set(fi_debug_lst)
            )
            self.assertEqual(len(fi_with_filter_diff), 3)
            self.assertEqual(len(fi_without_filter_diff), 4)
            self.assertEqual(len(fi_debug_diff), 3)
            self.assertIn(
                os.path.basename(p_name),
                [
                    os.path.basename(p)
                    for p in self.fi_with_filter.dataframe.path.values
                ],
            )
            self.assertIn(
                os.path.basename(p_name),
                [
                    os.path.basename(p)
                    for p in self.fi_without_filter.dataframe.path.values
                ],
            )
            self.assertIn(
                os.path.basename(p_name),
                [os.path.basename(p) for p in self.fi_debug.dataframe.path.values],
            )
            self.assertIn(
                os.path.dirname(p_name),
                [p for p in self.fi_with_filter.dataframe.path.values],
            )
            self.assertIn(
                os.path.dirname(p_name),
                [p for p in self.fi_without_filter.dataframe.path.values],
            )
            self.assertIn(
                os.path.dirname(p_name),
                [p for p in self.fi_debug.dataframe.path.values],
            )
            self.assertIn(
                "test.txt",
                [
                    os.path.basename(p)
                    for p in self.fi_with_filter.dataframe.path.values
                ],
            )
            self.assertIn(
                "test.o",
                [
                    os.path.basename(p)
                    for p in self.fi_without_filter.dataframe.path.values
                ],
            )
            self.assertIn(
                "test.txt",
                [
                    os.path.basename(p)
                    for p in self.fi_without_filter.dataframe.path.values
                ],
            )
            self.assertIn(
                "test.txt",
                [os.path.basename(p) for p in self.fi_debug.dataframe.path.values],
            )
            os.remove(os.path.join(p_name, "test.txt"))
            os.remove(os.path.join(p_name, "test.o"))
            os.removedirs(p_name)
            self.fi_with_filter.update()
            self.fi_without_filter.update()
            self.fi_debug.update()
            fi_with_filter_diff = list(
                set(self.fi_with_filter.dataframe.path.values) - set(fi_with_filter_lst)
            )
            fi_without_filter_diff = list(
                set(self.fi_without_filter.dataframe.path.values)
                - set(fi_without_filter_lst)
            )
            fi_debug_diff = list(
                set(self.fi_debug.dataframe.path.values) - set(fi_debug_lst)
            )
            self.assertEqual(len(fi_with_filter_diff), 0)
            self.assertEqual(len(fi_without_filter_diff), 0)
            self.assertEqual(len(fi_debug_diff), 0)

    def test_project_single_dir_with_modified_file(self):
        p_name = os.path.join(self.path, "test_project_single_dir_with_modified_file")
        fi_with_filter_lst = self.fi_with_filter.dataframe.path.values
        fi_without_filter_lst = self.fi_without_filter.dataframe.path.values
        fi_debug_lst = self.fi_debug.dataframe.path.values
        os.makedirs(p_name)
        touch(os.path.join(p_name, "test.txt"))
        if os.name == "nt":
            sleep(self.sleep_period)
        self.fi_with_filter.update()
        self.fi_without_filter.update()
        self.fi_debug.update()
        fi_with_filter_diff = list(
            set(self.fi_with_filter.dataframe.path.values) - set(fi_with_filter_lst)
        )
        fi_without_filter_diff = list(
            set(self.fi_without_filter.dataframe.path.values)
            - set(fi_without_filter_lst)
        )
        fi_debug_diff = list(
            set(self.fi_debug.dataframe.path.values) - set(fi_debug_lst)
        )
        self.assertEqual(len(fi_with_filter_diff), 2)
        self.assertEqual(len(fi_without_filter_diff), 2)
        self.assertEqual(len(fi_debug_diff), 2)
        self.assertIn(
            p_name,
            [p for p in self.fi_with_filter.dataframe.path.values],
        )
        self.assertIn(
            p_name,
            [p for p in self.fi_without_filter.dataframe.path.values],
        )
        self.assertIn(p_name, [p for p in self.fi_debug.dataframe.path.values])
        self.assertIn(
            "test.txt",
            [os.path.basename(p) for p in self.fi_with_filter.dataframe.path.values],
        )
        self.assertIn(
            "test.txt",
            [os.path.basename(p) for p in self.fi_without_filter.dataframe.path.values],
        )
        self.assertIn(
            "test.txt",
            [os.path.basename(p) for p in self.fi_debug.dataframe.path.values],
        )
        touch(os.path.join(p_name, "test.txt"), (1330712280, 1330712292))
        if os.name == "nt":
            sleep(self.sleep_period)
        self.fi_with_filter.update()
        self.fi_without_filter.update()
        self.fi_debug.update()
        fi_debug_select = self.fi_debug.dataframe.path == os.path.abspath(
            os.path.join(p_name, "test.txt")
        )
        self.assertEqual(
            int(self.fi_debug.dataframe[fi_debug_select].mtime.values[0]), 1330712292
        )
        fi_without_filter_select = (
            self.fi_without_filter.dataframe.path
            == os.path.abspath(os.path.join(p_name, "test.txt"))
        )
        self.assertEqual(
            int(
                self.fi_without_filter.dataframe[fi_without_filter_select].mtime.values[
                    0
                ]
            ),
            1330712292,
        )
        fi_with_filter_select = self.fi_with_filter.dataframe.path == os.path.abspath(
            os.path.join(p_name, "test.txt")
        )
        self.assertEqual(
            int(self.fi_with_filter.dataframe[fi_with_filter_select].mtime.values[0]),
            1330712292,
        )
        os.remove(os.path.join(p_name, "test.txt"))
        os.removedirs(p_name)
        if os.name == "nt":
            sleep(self.sleep_period)
        self.fi_with_filter.update()
        self.fi_without_filter.update()
        self.fi_debug.update()
        fi_with_filter_diff = list(
            set(self.fi_with_filter.dataframe.path.values) - set(fi_with_filter_lst)
        )
        fi_without_filter_diff = list(
            set(self.fi_without_filter.dataframe.path.values)
            - set(fi_without_filter_lst)
        )
        fi_debug_diff = list(
            set(self.fi_debug.dataframe.path.values) - set(fi_debug_lst)
        )
        self.assertEqual(len(fi_with_filter_diff), 0)
        self.assertEqual(len(fi_without_filter_diff), 0)
        self.assertEqual(len(fi_debug_diff), 0)

    def test_len(self):
        self.assertEqual(0, len(self.fi_with_filter))
        self.assertEqual(2, len(self.fi_without_filter))
        self.assertEqual(0, len(self.fi_debug))

    def test_open(self):
        self.assertEqual(self.fi_with_filter.open(self.path), self.fi_with_filter)
        self.assertEqual(self.fi_without_filter.open(self.path), self.fi_without_filter)
        self.assertEqual(self.fi_debug.open(self.path), self.fi_debug)

    def test_create_outside_directory(self):
        p_name = os.path.join(self.path, "..", "test_different_dir")
        os.makedirs(p_name)
        self.assertNotEqual(self.fi_with_filter.open(p_name), self.fi_with_filter)
        self.assertNotEqual(self.fi_without_filter.open(p_name), self.fi_without_filter)
        self.assertNotEqual(self.fi_debug.open(p_name), self.fi_debug)
        os.removedirs(p_name)

    def test_repr_html(self):
        html_str = self.fi_with_filter._repr_html_()
        self.assertEqual(html_str.count("div"), 2)
        self.assertEqual(html_str.count("table"), 2)
        self.assertEqual(html_str.count("tr"), 8)
        self.assertEqual(html_str.count("td"), 24)

    def test_init_df_lst(self):
        self.assertEqual(
            type(
                self.fi_with_filter._init_df_lst(path_lst=[self.fi_with_filter._path])
            ),
            pandas.DataFrame,
        )

    def test_get_changes_quick(self):
        _, files_changed_lst, path_deleted_lst = (
            self.fi_with_filter._get_changes_quick()
        )
        self.assertEqual(files_changed_lst, [])
        self.assertEqual(path_deleted_lst, [])
        with self.assertRaises(FileNotFoundError):
            _, files_changed_lst, path_deleted_lst = self.fi_with_filter.open(
                "no_such_folder"
            )._get_changes_quick()

    def test_folder_does_not_exist(self):
        with self.assertRaises(FileNotFoundError):
            PyFileIndex(path="no_such_folder")


class TestJobFileTableCoverage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = os.path.dirname(os.path.abspath(__file__))
        cls.fi = PyFileIndex(path=cls.path)

    def test_scandir_import_error(self):
        with patch.dict(sys.modules, {'os.scandir': None}):
            import pyfileindex.pyfileindex
            importlib.reload(pyfileindex.pyfileindex)
            fi = pyfileindex.pyfileindex.PyFileIndex(path=self.path)
            self.assertIsInstance(fi, pyfileindex.pyfileindex.PyFileIndex)
        import pyfileindex.pyfileindex
        importlib.reload(pyfileindex.pyfileindex)

    def test_open_windows(self):
        with patch('os.name', 'nt'):
            p_name = os.path.join(self.path, "test_open_windows")
            os.makedirs(p_name, exist_ok=True)
            # To cover the second nt path, we need to create a new PyFileIndex inside the patch
            fi = PyFileIndex(path=self.path)
            fi_new = fi.open(p_name)
            self.assertNotEqual(fi_new, fi)
            self.assertEqual(len(fi_new.df), 1)
            self.assertEqual(fi_new.df.iloc[0].path, os.path.abspath(p_name))
            os.removedirs(p_name)

    def test_get_lst_entry_from_path_with_filter(self):
        def my_filter(file_name):
            return ".pdb" in file_name
        
        p_name = os.path.join(self.path, "filtered_file.txt")
        touch(p_name)
        fi = PyFileIndex(path=self.path, filter_function=my_filter)
        self.assertEqual(len(fi.df[fi.df.basename == "filtered_file.txt"]), 0)
        os.remove(p_name)

    def test_scandir_file_not_found(self):
        result = list(self.fi._scandir(path="non_existent_path"))
        self.assertEqual(result, [])

    def test_get_lst_entry_from_path_file_not_found(self):
        result = self.fi._get_lst_entry_from_path(entry="non_existent_path")
        self.assertEqual(result, [])

    def test_get_lst_entry_file_not_found(self):
        mock_entry = MagicMock()
        mock_entry.name = "test_file"
        mock_entry.path = "/path/to/test_file"
        mock_entry.is_dir.return_value = False
        mock_entry.stat.side_effect = FileNotFoundError
        result = self.fi._get_lst_entry(entry=mock_entry)
        self.assertEqual(result, [])
