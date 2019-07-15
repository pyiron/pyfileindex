import unittest
import os
from pyfileindex import PyFileIndex


def filter_function(file_name):
    return '.txt' in file_name


def touch(fname, times=None):
    with open(fname, 'a'):
        os.utime(fname, times)


class TestJobFileTable(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fi_with_filter = PyFileIndex(path='.', filter_function=filter_function)
        cls.fi_without_filter = PyFileIndex(path='.')
        cls.fi_debug = PyFileIndex(path='.', filter_function=filter_function, debug=True)

    def test_project_single_empty_dir(self):
        p_name = 'test_project_single_empty_dir'
        fi_with_filter_lst = self.fi_with_filter.dataframe.path.values
        fi_without_filter_lst = self.fi_without_filter.dataframe.path.values
        fi_debug_lst = self.fi_debug.dataframe.path.values
        os.makedirs(p_name, exist_ok=True)
        self.fi_with_filter.update()
        self.fi_without_filter.update()
        self.fi_debug.update()
        fi_with_filter_diff = list(set(self.fi_with_filter.dataframe.path.values) - set(fi_with_filter_lst))
        fi_without_filter_diff = list(set(self.fi_without_filter.dataframe.path.values) - set(fi_without_filter_lst))
        fi_debug_diff = list(set(self.fi_debug.dataframe.path.values) - set(fi_debug_lst))
        self.assertEqual(len(fi_with_filter_diff), 1)
        self.assertEqual(len(fi_without_filter_diff), 1)
        self.assertEqual(len(fi_debug_diff), 1)
        self.assertEqual(os.path.basename(fi_with_filter_diff[0]), p_name)
        self.assertEqual(os.path.basename(fi_without_filter_diff[0]), p_name)
        self.assertEqual(os.path.basename(fi_debug_diff[0]), p_name)
        os.removedirs(p_name)
        self.fi_with_filter.update()
        self.fi_without_filter.update()
        self.fi_debug.update()
        fi_with_filter_diff = list(set(self.fi_with_filter.dataframe.path.values) - set(fi_with_filter_lst))
        fi_without_filter_diff = list(set(self.fi_without_filter.dataframe.path.values) - set(fi_without_filter_lst))
        fi_debug_diff = list(set(self.fi_debug.dataframe.path.values) - set(fi_debug_lst))
        self.assertEqual(len(fi_with_filter_diff), 0)
        self.assertEqual(len(fi_without_filter_diff), 0)
        self.assertEqual(len(fi_debug_diff), 0)

    def test_project_single_dir_with_files(self):
        p_name = 'test_project_single_dir_with_files'
        fi_with_filter_lst = self.fi_with_filter.dataframe.path.values
        fi_without_filter_lst = self.fi_without_filter.dataframe.path.values
        fi_debug_lst = self.fi_debug.dataframe.path.values
        os.makedirs(p_name, exist_ok=True)
        touch(os.path.join(p_name, 'test.txt'))
        touch(os.path.join(p_name, 'test.o'))
        self.fi_with_filter.update()
        self.fi_without_filter.update()
        self.fi_debug.update()
        fi_with_filter_diff = list(set(self.fi_with_filter.dataframe.path.values) - set(fi_with_filter_lst))
        fi_without_filter_diff = list(set(self.fi_without_filter.dataframe.path.values) - set(fi_without_filter_lst))
        fi_debug_diff = list(set(self.fi_debug.dataframe.path.values) - set(fi_debug_lst))
        self.assertEqual(len(fi_with_filter_diff), 2)
        self.assertEqual(len(fi_without_filter_diff), 3)
        self.assertEqual(len(fi_debug_diff), 2)
        self.assertIn(p_name, [os.path.basename(p) for p in self.fi_with_filter.dataframe.path.values])
        self.assertIn(p_name, [os.path.basename(p) for p in self.fi_without_filter.dataframe.path.values])
        self.assertIn(p_name, [os.path.basename(p) for p in self.fi_debug.dataframe.path.values])
        self.assertIn('test.txt', [os.path.basename(p) for p in self.fi_with_filter.dataframe.path.values])
        self.assertIn('test.o', [os.path.basename(p) for p in self.fi_without_filter.dataframe.path.values])
        self.assertIn('test.txt', [os.path.basename(p) for p in self.fi_without_filter.dataframe.path.values])
        self.assertIn('test.txt', [os.path.basename(p) for p in self.fi_debug.dataframe.path.values])
        os.remove(os.path.join(p_name, 'test.txt'))
        os.remove(os.path.join(p_name, 'test.o'))
        os.removedirs(p_name)
        self.fi_with_filter.update()
        self.fi_without_filter.update()
        self.fi_debug.update()
        fi_with_filter_diff = list(set(self.fi_with_filter.dataframe.path.values) - set(fi_with_filter_lst))
        fi_without_filter_diff = list(set(self.fi_without_filter.dataframe.path.values) - set(fi_without_filter_lst))
        fi_debug_diff = list(set(self.fi_debug.dataframe.path.values) - set(fi_debug_lst))
        self.assertEqual(len(fi_with_filter_diff), 0)
        self.assertEqual(len(fi_without_filter_diff), 0)
        self.assertEqual(len(fi_debug_diff), 0)

    def test_project_sub_dir_with_files(self):
        p_name = 'test_project_sub_dir_with_files/sub'
        fi_with_filter_lst = self.fi_with_filter.dataframe.path.values
        fi_without_filter_lst = self.fi_without_filter.dataframe.path.values
        fi_debug_lst = self.fi_debug.dataframe.path.values
        os.makedirs(p_name, exist_ok=True)
        touch(os.path.join(p_name, 'test.txt'))
        touch(os.path.join(p_name, 'test.o'))
        self.fi_with_filter.update()
        self.fi_without_filter.update()
        self.fi_debug.update()
        fi_with_filter_diff = list(set(self.fi_with_filter.dataframe.path.values) - set(fi_with_filter_lst))
        fi_without_filter_diff = list(set(self.fi_without_filter.dataframe.path.values) - set(fi_without_filter_lst))
        fi_debug_diff = list(set(self.fi_debug.dataframe.path.values) - set(fi_debug_lst))
        self.assertEqual(len(fi_with_filter_diff), 3)
        self.assertEqual(len(fi_without_filter_diff), 4)
        self.assertEqual(len(fi_debug_diff), 3)
        self.assertIn(os.path.basename(p_name),
                      [os.path.basename(p) for p in self.fi_with_filter.dataframe.path.values])
        self.assertIn(os.path.basename(p_name),
                      [os.path.basename(p) for p in self.fi_without_filter.dataframe.path.values])
        self.assertIn(os.path.basename(p_name),
                      [os.path.basename(p) for p in self.fi_debug.dataframe.path.values])
        self.assertIn(os.path.dirname(p_name),
                      [os.path.basename(p) for p in self.fi_with_filter.dataframe.path.values])
        self.assertIn(os.path.dirname(p_name),
                      [os.path.basename(p) for p in self.fi_without_filter.dataframe.path.values])
        self.assertIn(os.path.dirname(p_name),
                      [os.path.basename(p) for p in self.fi_debug.dataframe.path.values])
        self.assertIn('test.txt', [os.path.basename(p) for p in self.fi_with_filter.dataframe.path.values])
        self.assertIn('test.o', [os.path.basename(p) for p in self.fi_without_filter.dataframe.path.values])
        self.assertIn('test.txt', [os.path.basename(p) for p in self.fi_without_filter.dataframe.path.values])
        self.assertIn('test.txt', [os.path.basename(p) for p in self.fi_debug.dataframe.path.values])
        os.remove(os.path.join(p_name, 'test.txt'))
        os.remove(os.path.join(p_name, 'test.o'))
        os.removedirs(p_name)
        self.fi_with_filter.update()
        self.fi_without_filter.update()
        self.fi_debug.update()
        fi_with_filter_diff = list(set(self.fi_with_filter.dataframe.path.values) - set(fi_with_filter_lst))
        fi_without_filter_diff = list(set(self.fi_without_filter.dataframe.path.values) - set(fi_without_filter_lst))
        fi_debug_diff = list(set(self.fi_debug.dataframe.path.values) - set(fi_debug_lst))
        self.assertEqual(len(fi_with_filter_diff), 0)
        self.assertEqual(len(fi_without_filter_diff), 0)
        self.assertEqual(len(fi_debug_diff), 0)

    def test_project_single_dir_with_modified_file(self):
        p_name = 'test_project_single_dir_with_modified_file'
        fi_with_filter_lst = self.fi_with_filter.dataframe.path.values
        fi_without_filter_lst = self.fi_without_filter.dataframe.path.values
        fi_debug_lst = self.fi_debug.dataframe.path.values
        os.makedirs(p_name, exist_ok=True)
        touch(os.path.join(p_name, 'test.txt'))
        self.fi_with_filter.update()
        self.fi_without_filter.update()
        self.fi_debug.update()
        fi_with_filter_diff = list(set(self.fi_with_filter.dataframe.path.values) - set(fi_with_filter_lst))
        fi_without_filter_diff = list(set(self.fi_without_filter.dataframe.path.values) - set(fi_without_filter_lst))
        fi_debug_diff = list(set(self.fi_debug.dataframe.path.values) - set(fi_debug_lst))
        self.assertEqual(len(fi_with_filter_diff), 2)
        self.assertEqual(len(fi_without_filter_diff), 2)
        self.assertEqual(len(fi_debug_diff), 2)
        self.assertIn(p_name, [os.path.basename(p) for p in self.fi_with_filter.dataframe.path.values])
        self.assertIn(p_name, [os.path.basename(p) for p in self.fi_without_filter.dataframe.path.values])
        self.assertIn(p_name, [os.path.basename(p) for p in self.fi_debug.dataframe.path.values])
        self.assertIn('test.txt', [os.path.basename(p) for p in self.fi_with_filter.dataframe.path.values])
        self.assertIn('test.txt', [os.path.basename(p) for p in self.fi_without_filter.dataframe.path.values])
        self.assertIn('test.txt', [os.path.basename(p) for p in self.fi_debug.dataframe.path.values])
        touch(os.path.join(p_name, 'test.txt'), (1330712280, 1330712292))
        self.fi_with_filter.update()
        self.fi_without_filter.update()
        self.fi_debug.update()
        fi_debug_select = self.fi_debug.dataframe.path == os.path.abspath(os.path.join(p_name, 'test.txt'))
        self.assertEqual(int(self.fi_debug.dataframe[fi_debug_select].mtime.values[0]), 1330712292)
        fi_without_filter_select = self.fi_without_filter.dataframe.path == \
                                   os.path.abspath(os.path.join(p_name, 'test.txt'))
        self.assertEqual(int(self.fi_without_filter.dataframe[fi_without_filter_select].mtime.values[0]), 1330712292)
        fi_with_filter_select = self.fi_with_filter.dataframe.path == os.path.abspath(os.path.join(p_name, 'test.txt'))
        self.assertEqual(int(self.fi_with_filter.dataframe[fi_with_filter_select].mtime.values[0]), 1330712292)
        os.remove(os.path.join(p_name, 'test.txt'))
        os.removedirs(p_name)
        self.fi_with_filter.update()
        self.fi_without_filter.update()
        self.fi_debug.update()
        fi_with_filter_diff = list(set(self.fi_with_filter.dataframe.path.values) - set(fi_with_filter_lst))
        fi_without_filter_diff = list(set(self.fi_without_filter.dataframe.path.values) - set(fi_without_filter_lst))
        fi_debug_diff = list(set(self.fi_debug.dataframe.path.values) - set(fi_debug_lst))
        self.assertEqual(len(fi_with_filter_diff), 0)
        self.assertEqual(len(fi_without_filter_diff), 0)
        self.assertEqual(len(fi_debug_diff), 0)
