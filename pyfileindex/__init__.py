from . import _version

try:
    from pyfileindex.pyfileindex import PyFileIndex
except ImportError:
    pass

__version__ = _version.get_versions()["version"]
