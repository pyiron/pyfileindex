# pyfileindex
PyFileIndex - pythonic file system index 

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/61d50c2f9f5f404f879a02650ff3da35)](https://www.codacy.com/app/jan-janssen/pyfileindex?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=pyfileindex/pyfileindex&amp;utm_campaign=Badge_Grade)
[![Python package](https://github.com/pyiron/pyfileindex/workflows/Python%20package/badge.svg)](https://github.com/pyiron/pyfileindex/actions)
[![Coverage Status](https://coveralls.io/repos/github/pyiron/pyfileindex/badge.svg?branch=master)](https://coveralls.io/github/pyiron/pyfileindex?branch=master)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/pyiron/pyfileindex/master?filepath=notebooks%2Fdemo.ipynb)

The pyfileindex helps to keep track of files in a specific directory, to monitor added files, modified files and deleted files. The module is compatible with Python 3.7 or later but restricted to Unix-like system - Windows is not supported. 

![Preview](pyfileindex.gif)

# Installation
The pyfileindex can either be installed via pip using:

    pip install pyfileindex

Or via anaconda from the conda-forge channel

    conda install -c conda-forge pyfileindex


# Usage 
Import pyfileindex:

    from pyfileindex import PyFileIndex 
    pfi = PyFileIndex(path='.')
    
Or you can filter for a specifc file extension: 

    def filter_function(file_name):
        return '.txt' in file_name
        
    pfi = PyFileIndex(path='.', filter_function=filter_function)

List files in the file system index: 

    pfi.dataframe 

Update file system index: 

    pfi.update()

For more details, take a look at the example notebook: https://github.com/pyiron/pyfileindex/blob/master/notebooks/demo.ipynb


# License
The pyfileindex is released under the BSD license https://github.com/pyiron/pyfileindex/blob/master/LICENSE . It is a spin-off of the pyiron project https://github.com/pyiron/pyiron therefore if you use the pyfileindex for your publication, please cite: 

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
