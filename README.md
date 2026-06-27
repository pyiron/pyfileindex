# pyfileindex
PyFileIndex - pythonic file system index 

[![Pipeline](https://github.com/pyiron/pyfileindex/actions/workflows/pipeline.yml/badge.svg)](https://github.com/pyiron/pyfileindex/actions/workflows/pipeline.yml)
[![codecov](https://codecov.io/gh/pyiron/pyfileindex/graph/badge.svg?token=J9EWZBBKPH)](https://codecov.io/gh/pyiron/pyfileindex)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/pyiron/pyfileindex/main?filepath=notebooks%2Fgetting_started.ipynb)

The pyfileindex helps to keep track of files in a specific directory, to monitor added files, modified files and deleted files. The module is compatible with Python 3.7 or later but restricted to Unix-like system - Windows is not supported. 

![Preview](https://raw.githubusercontent.com/pyiron/pyfileindex/main/pyfileindex.gif)

## Installation
The pyfileindex can either be installed via pip using:
```shell
pip install pyfileindex
```
Or via anaconda from the conda-forge channel
```shell
conda install -c conda-forge pyfileindex
```

## Usage 
Import pyfileindex:
```python
from pyfileindex import PyFileIndex 
pfi = PyFileIndex(path='.')
```  
Or you can filter for a specifc file extension: 
```python
def filter_function(file_name):
    return '.txt' in file_name
    
pfi = PyFileIndex(path='.', filter_function=filter_function)
```
List files in the file system index: 
```python
pfi.dataframe 
```
Each row is a file or directory below the indexed path:

| Column | Type | Description |
| --- | --- | --- |
| `basename` | str | File or directory name, e.g. `output.txt` |
| `path` | str | Absolute path |
| `dirname` | str | Absolute path of the parent directory |
| `is_directory` | bool | `True` for directories, `False` for files |
| `mtime` | float | Last modification time (POSIX timestamp, same as `os.stat().st_mtime`) |
| `nlink` | int | Hard link count (`os.stat().st_nlink`), used internally to detect changes |
Update file system index: 
```python
pfi.update()
```
And open a subdirectory using: 
```python
pfi.open(path='subdirectory')
```
For more details, take a look at the example notebook: https://github.com/pyiron/pyfileindex/blob/main/notebooks/getting_started.ipynb


## License
The pyfileindex is released under the BSD license https://github.com/pyiron/pyfileindex/blob/main/LICENSE . It is a spin-off of the pyiron project https://github.com/pyiron/pyiron therefore if you use the pyfileindex for your publication, please cite: 
```
@article{pyiron-paper,
  title = {pyiron: An integrated development environment for computational materials science},
  journal = {Computational Materials Science},
  volume = {163},
  pages = {24 - 36},
  year = {2019},
  issn = {0927-0256},
  doi = {https://doi.org/10.1016/j.commatsci.2018.07.043},
  url = {http://www.sciencedirect.com/science/article/pii/S0927025618304786},
  author = {Jan Janssen and Sudarsan Surendralal and Yury Lysogorskiy and Mira Todorova and Tilmann Hickel and Ralf Drautz and Jörg Neugebauer},
  keywords = {Modelling workflow, Integrated development environment, Complex simulation protocols},
}
```

## Documentation

* [pyfileindex](https://pyfileindex.readthedocs.io/en/latest/README.html)
  * [Installation](https://pyfileindex.readthedocs.io/en/latest/README.html#installation)
  * [Usage](https://pyfileindex.readthedocs.io/en/latest/README.html#usage)
  * [License](https://pyfileindex.readthedocs.io/en/readthedocs/README.html#license)
* [Getting started with pyfileindex](https://pyfileindex.readthedocs.io/en/latest/getting_started.html)
  * [Setup](https://pyfileindex.readthedocs.io/en/latest/getting_started.html#setup)
  * [Polling mode](https://pyfileindex.readthedocs.io/en/latest/getting_started.html#polling-mode-watch-false-the-default)
  * [Watch mode](https://pyfileindex.readthedocs.io/en/latest/getting_started.html#watch-mode-watch-true)
  * [Using pyfileindex in your own project](https://pyfileindex.readthedocs.io/en/latest/getting_started.html#using-pyfileindex-in-your-own-project)
* [Interface](https://pyfileindex.readthedocs.io/en/latest/api.html)