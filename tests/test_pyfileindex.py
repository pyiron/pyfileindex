import os
import importlib
import sys
import shutil
from time import sleep
import pandas
import pytest

from pyfileindex import PyFileIndex


def filter_function(file_name):
    return ".txt" in file_name


def touch(fname, times=None):
    with open(fname, "a"):
        os.utime(fname, times)


@pytest.fixture(scope="module")
def job_file_table_fixture():
    path = os.path.dirname(os.path.abspath(__file__))
    fi_with_filter = PyFileIndex(path=path, filter_function=filter_function)
    fi_without_filter = PyFileIndex(path=path)
    fi_debug = PyFileIndex(
        path=path, filter_function=filter_function, debug=True
    )
    sleep_period = 5
    yield path, fi_with_filter, fi_without_filter, fi_debug, sleep_period


def test_project_single_empty_dir(job_file_table_fixture):
    path, fi_with_filter, fi_without_filter, fi_debug, sleep_period = job_file_table_fixture
    p_name = os.path.join(path, "test_project_single_empty_dir")
    fi_with_filter_lst = fi_with_filter.dataframe.path.values
    fi_without_filter_lst = fi_without_filter.dataframe.path.values
    fi_debug_lst = fi_debug.dataframe.path.values
    os.makedirs(p_name)
    if os.name == "nt":
        sleep(sleep_period)
    fi_with_filter.update()
    fi_without_filter.update()
    fi_debug.update()
    fi_with_filter_diff = list(
        set(fi_with_filter.dataframe.path.values) - set(fi_with_filter_lst)
    )
    fi_without_filter_diff = list(
        set(fi_without_filter.dataframe.path.values)
        - set(fi_without_filter_lst)
    )
    fi_debug_diff = list(
        set(fi_debug.dataframe.path.values) - set(fi_debug_lst)
    )
    assert len(fi_with_filter_diff) == 1
    assert len(fi_without_filter_diff) == 1
    assert len(fi_debug_diff) == 1
    assert fi_with_filter_diff[0] == p_name
    assert fi_without_filter_diff[0] == p_name
    assert fi_debug_diff[0] == p_name
    if os.name != "nt":
        fi_with_filter_sub = fi_with_filter.open(p_name)
        fi_without_filter_sub = fi_without_filter.open(p_name)
        fi_debug_sub = fi_debug.open(p_name)
        assert fi_with_filter_sub != fi_with_filter
        assert fi_without_filter_sub != fi_without_filter
        assert fi_debug_sub != fi_debug
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
        assert len(fi_with_filter_diff_sub) == 1
        assert len(fi_without_filter_diff_sub) == 1
        assert len(fi_debug_diff_sub) == 1
        assert fi_with_filter_diff_sub[0] == p_name
        assert fi_without_filter_diff_sub[0] == p_name
        assert fi_debug_diff_sub[0] == p_name
    if os.name == "nt":
        sleep(sleep_period)
    os.removedirs(p_name)
    fi_with_filter.update()
    fi_without_filter.update()
    fi_debug.update()
    fi_with_filter_diff = list(
        set(fi_with_filter.dataframe.path.values) - set(fi_with_filter_lst)
    )
    fi_without_filter_diff = list(
        set(fi_without_filter.dataframe.path.values)
        - set(fi_without_filter_lst)
    )
    fi_debug_diff = list(
        set(fi_debug.dataframe.path.values) - set(fi_debug_lst)
    )
    assert len(fi_with_filter_diff) == 0
    assert len(fi_without_filter_diff) == 0
    assert len(fi_debug_diff) == 0


def test_project_single_dir_with_files(job_file_table_fixture):
    path, fi_with_filter, fi_without_filter, fi_debug, sleep_period = job_file_table_fixture
    p_name = os.path.join(path, "test_project_single_dir_with_files")
    fi_with_filter_lst = fi_with_filter.dataframe.path.values
    fi_without_filter_lst = fi_without_filter.dataframe.path.values
    fi_debug_lst = fi_debug.dataframe.path.values
    os.makedirs(p_name)
    touch(os.path.join(p_name, "test.txt"))
    touch(os.path.join(p_name, "test.o"))
    if os.name == "nt":
        sleep(sleep_period)
    fi_with_filter.update()
    fi_without_filter.update()
    fi_debug.update()
    fi_with_filter_diff = list(
        set(fi_with_filter.dataframe.path.values) - set(fi_with_filter_lst)
    )
    fi_without_filter_diff = list(
        set(fi_without_filter.dataframe.path.values)
        - set(fi_without_filter_lst)
    )
    fi_debug_diff = list(
        set(fi_debug.dataframe.path.values) - set(fi_debug_lst)
    )
    assert len(fi_with_filter_diff) == 2
    assert len(fi_without_filter_diff) == 3
    assert len(fi_debug_diff) == 2
    assert p_name in fi_with_filter.dataframe.path.values
    assert p_name in fi_without_filter.dataframe.path.values
    assert p_name in fi_debug.dataframe.path.values
    assert "test.txt" in fi_with_filter.dataframe.basename.values
    assert "test.o" in fi_without_filter.dataframe.basename.values
    assert "test.txt" in fi_without_filter.dataframe.basename.values
    assert "test.txt" in fi_debug.dataframe.basename.values
    os.remove(os.path.join(p_name, "test.txt"))
    os.remove(os.path.join(p_name, "test.o"))
    os.removedirs(p_name)
    if os.name == "nt":
        sleep(sleep_period)
    fi_with_filter.update()
    fi_without_filter.update()
    fi_debug.update()
    fi_with_filter_diff = list(
        set(fi_with_filter.dataframe.path.values) - set(fi_with_filter_lst)
    )
    fi_without_filter_diff = list(
        set(fi_without_filter.dataframe.path.values)
        - set(fi_without_filter_lst)
    )
    fi_debug_diff = list(
        set(fi_debug.dataframe.path.values) - set(fi_debug_lst)
    )
    assert len(fi_with_filter_diff) == 0
    assert len(fi_without_filter_diff) == 0
    assert len(fi_debug_diff) == 0


def test_project_sub_dir_with_files(job_file_table_fixture):
    path, fi_with_filter, fi_without_filter, fi_debug, sleep_period = job_file_table_fixture
    if os.name != "nt":
        p_name = os.path.join(path, "test_project_sub_dir_with_files", "sub")
        fi_with_filter_lst = fi_with_filter.dataframe.path.values
        fi_without_filter_lst = fi_without_filter.dataframe.path.values
        fi_debug_lst = fi_debug.dataframe.path.values
        os.makedirs(p_name)
        touch(os.path.join(p_name, "test.txt"))
        touch(os.path.join(p_name, "test.o"))
        fi_with_filter.update()
        fi_without_filter.update()
        fi_debug.update()
        fi_with_filter_diff = list(
            set(fi_with_filter.dataframe.path.values) - set(fi_with_filter_lst)
        )
        fi_without_filter_diff = list(
            set(fi_without_filter.dataframe.path.values)
            - set(fi_without_filter_lst)
        )
        fi_debug_diff = list(
            set(fi_debug.dataframe.path.values) - set(fi_debug_lst)
        )
        assert len(fi_with_filter_diff) == 3
        assert len(fi_without_filter_diff) == 4
        assert len(fi_debug_diff) == 3
        assert os.path.basename(p_name) in fi_with_filter.dataframe.basename.values
        assert os.path.basename(p_name) in fi_without_filter.dataframe.basename.values
        assert os.path.basename(p_name) in fi_debug.dataframe.basename.values
        assert os.path.dirname(p_name) in fi_with_filter.dataframe.path.values
        assert os.path.dirname(p_name) in fi_without_filter.dataframe.path.values
        assert os.path.dirname(p_name) in fi_debug.dataframe.path.values
        assert "test.txt" in fi_with_filter.dataframe.basename.values
        assert "test.o" in fi_without_filter.dataframe.basename.values
        assert "test.txt" in fi_without_filter.dataframe.basename.values
        assert "test.txt" in fi_debug.dataframe.basename.values
        os.remove(os.path.join(p_name, "test.txt"))
        os.remove(os.path.join(p_name, "test.o"))
        os.removedirs(p_name)
        fi_with_filter.update()
        fi_without_filter.update()
        fi_debug.update()
        fi_with_filter_diff = list(
            set(fi_with_filter.dataframe.path.values) - set(fi_with_filter_lst)
        )
        fi_without_filter_diff = list(
            set(fi_without_filter.dataframe.path.values)
            - set(fi_without_filter_lst)
        )
        fi_debug_diff = list(
            set(fi_debug.dataframe.path.values) - set(fi_debug_lst)
        )
        assert len(fi_with_filter_diff) == 0
        assert len(fi_without_filter_diff) == 0
        assert len(fi_debug_diff) == 0


def test_project_single_dir_with_modified_file(job_file_table_fixture):
    path, fi_with_filter, fi_without_filter, fi_debug, sleep_period = job_file_table_fixture
    p_name = os.path.join(path, "test_project_single_dir_with_modified_file")
    fi_with_filter_lst = fi_with_filter.dataframe.path.values
    fi_without_filter_lst = fi_without_filter.dataframe.path.values
    fi_debug_lst = fi_debug.dataframe.path.values
    os.makedirs(p_name)
    touch(os.path.join(p_name, "test.txt"))
    if os.name == "nt":
        sleep(sleep_period)
    fi_with_filter.update()
    fi_without_filter.update()
    fi_debug.update()
    fi_with_filter_diff = list(
        set(fi_with_filter.dataframe.path.values) - set(fi_with_filter_lst)
    )
    fi_without_filter_diff = list(
        set(fi_without_filter.dataframe.path.values)
        - set(fi_without_filter_lst)
    )
    fi_debug_diff = list(
        set(fi_debug.dataframe.path.values) - set(fi_debug_lst)
    )
    assert len(fi_with_filter_diff) == 2
    assert len(fi_without_filter_diff) == 2
    assert len(fi_debug_diff) == 2
    assert p_name in fi_with_filter.dataframe.path.values
    assert p_name in fi_without_filter.dataframe.path.values
    assert p_name in fi_debug.dataframe.path.values
    assert "test.txt" in fi_with_filter.dataframe.basename.values
    assert "test.txt" in fi_without_filter.dataframe.basename.values
    assert "test.txt" in fi_debug.dataframe.basename.values
    touch(os.path.join(p_name, "test.txt"), (1330712280, 1330712292))
    if os.name == "nt":
        sleep(sleep_period)
    fi_with_filter.update()
    fi_without_filter.update()
    fi_debug.update()
    fi_debug_select = fi_debug.dataframe.path == os.path.abspath(
        os.path.join(p_name, "test.txt")
    )
    assert int(fi_debug.dataframe[fi_debug_select].mtime.values[0]) == 1330712292
    fi_without_filter_select = (
        fi_without_filter.dataframe.path
        == os.path.abspath(os.path.join(p_name, "test.txt"))
    )
    assert int(fi_without_filter.dataframe[fi_without_filter_select].mtime.values[0]) == 1330712292
    fi_with_filter_select = fi_with_filter.dataframe.path == os.path.abspath(
        os.path.join(p_name, "test.txt")
    )
    assert int(fi_with_filter.dataframe[fi_with_filter_select].mtime.values[0]) == 1330712292
    os.remove(os.path.join(p_name, "test.txt"))
    os.removedirs(p_name)
    if os.name == "nt":
        sleep(sleep_period)
    fi_with_filter.update()
    fi_without_filter.update()
    fi_debug.update()
    fi_with_filter_diff = list(
        set(fi_with_filter.dataframe.path.values) - set(fi_with_filter_lst)
    )
    fi_without_filter_diff = list(
        set(fi_without_filter.dataframe.path.values)
        - set(fi_without_filter_lst)
    )
    fi_debug_diff = list(
        set(fi_debug.dataframe.path.values) - set(fi_debug_lst)
    )
    assert len(fi_with_filter_diff) == 0
    assert len(fi_without_filter_diff) == 0
    assert len(fi_debug_diff) == 0


def test_len():
    # Create a temporary directory for the test
    temp_dir = "test_len_temp_dir"
    os.makedirs(temp_dir, exist_ok=True)

    # Create a couple of files in the temporary directory
    touch(os.path.join(temp_dir, "file1.txt"))
    touch(os.path.join(temp_dir, "file2.dat"))

    # Initialize PyFileIndex instances with different configurations
    fi_with_filter = PyFileIndex(path=temp_dir, filter_function=filter_function)
    fi_without_filter = PyFileIndex(path=temp_dir)
    fi_debug = PyFileIndex(path=temp_dir, filter_function=filter_function, debug=True)

    # The length should be the number of files we created, respecting the filters
    assert len(fi_with_filter) == 1
    assert len(fi_without_filter) == 2
    assert len(fi_debug) == 1

    # Clean up the temporary directory
    shutil.rmtree(temp_dir)


def test_open(job_file_table_fixture):
    path, fi_with_filter, fi_without_filter, fi_debug, _ = job_file_table_fixture
    assert fi_with_filter.open(path) == fi_with_filter
    assert fi_without_filter.open(path) == fi_without_filter
    assert fi_debug.open(path) == fi_debug


def test_create_outside_directory(job_file_table_fixture):
    path, fi_with_filter, fi_without_filter, fi_debug, _ = job_file_table_fixture
    p_name = os.path.join(path, "..", "test_different_dir")
    os.makedirs(p_name)
    assert fi_with_filter.open(p_name) != fi_with_filter
    assert fi_without_filter.open(p_name) != fi_without_filter
    assert fi_debug.open(p_name) != fi_debug
    os.removedirs(p_name)


def test_repr_html(job_file_table_fixture):
    _, fi_with_filter, _, _, _ = job_file_table_fixture
    html_str = fi_with_filter._repr_html_()
    assert html_str.count("div") == 2
    assert html_str.count("table") == 2
    assert html_str.count("tr") == 8
    assert html_str.count("td") == 24


def test_init_df_lst(job_file_table_fixture):
    _, fi_with_filter, _, _, _ = job_file_table_fixture
    assert isinstance(fi_with_filter._init_df_lst(path_lst=[fi_with_filter._path]), pandas.DataFrame)


def test_get_changes_quick(job_file_table_fixture):
    _, fi_with_filter, _, _, _ = job_file_table_fixture
    _, files_changed_lst, path_deleted_lst = fi_with_filter._get_changes_quick()
    assert files_changed_lst == []
    assert path_deleted_lst.tolist() == []
    with pytest.raises(FileNotFoundError):
        _, files_changed_lst, path_deleted_lst = fi_with_filter.open("no_such_folder")._get_changes_quick()


def test_folder_does_not_exist():
    with pytest.raises(FileNotFoundError):
        PyFileIndex(path="no_such_folder")


@pytest.fixture(scope="module")
def job_file_table_coverage_fixture():
    path = os.path.dirname(os.path.abspath(__file__))
    fi = PyFileIndex(path=path)
    yield path, fi


def test_scandir_import_error(job_file_table_coverage_fixture, mocker):
    path, _ = job_file_table_coverage_fixture
    mocker.patch.dict(sys.modules, {'os.scandir': None})
    import pyfileindex.pyfileindex
    importlib.reload(pyfileindex.pyfileindex)
    fi = pyfileindex.pyfileindex.PyFileIndex(path=path)
    assert isinstance(fi, pyfileindex.pyfileindex.PyFileIndex)
    import pyfileindex.pyfileindex
    importlib.reload(pyfileindex.pyfileindex)


def test_open_windows(job_file_table_coverage_fixture, mocker):
    path, _ = job_file_table_coverage_fixture
    mocker.patch('os.name', 'nt')
    p_name = os.path.join(path, "test_open_windows")
    os.makedirs(p_name, exist_ok=True)
    # To cover the second nt path, we need to create a new PyFileIndex inside the patch
    fi = PyFileIndex(path=path)
    fi_new = fi.open(p_name)
    assert fi_new != fi
    assert len(fi_new.df) == 1
    assert fi_new.df.iloc[0].path == os.path.abspath(p_name)
    os.removedirs(p_name)


def test_get_lst_entry_from_path_with_filter(job_file_table_coverage_fixture):
    path, _ = job_file_table_coverage_fixture
    def my_filter(file_name):
        return ".pdb" in file_name

    p_name = os.path.join(path, "filtered_file.txt")
    touch(p_name)
    fi = PyFileIndex(path=path, filter_function=my_filter)
    assert len(fi.df[fi.df.basename == "filtered_file.txt"]) == 0
    os.remove(p_name)


def test_scandir_file_not_found(job_file_table_coverage_fixture):
    _, fi = job_file_table_coverage_fixture
    result = list(fi._scandir(path="non_existent_path"))
    assert result == []


def test_get_lst_entry_from_path_file_not_found(job_file_table_coverage_fixture):
    _, fi = job_file_table_coverage_fixture
    result = fi._get_lst_entry_from_path(entry="non_existent_path")
    assert result == []


def test_get_lst_entry_file_not_found(job_file_table_coverage_fixture, mocker):
    _, fi = job_file_table_coverage_fixture
    mock_entry = mocker.MagicMock()
    mock_entry.name = "test_file"
    mock_entry.path = "/path/to/test_file"
    mock_entry.is_dir.return_value = False
    mock_entry.stat.side_effect = FileNotFoundError
    result = fi._get_lst_entry(entry=mock_entry)
    assert result == []
