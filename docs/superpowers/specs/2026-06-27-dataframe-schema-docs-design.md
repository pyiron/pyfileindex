# Design: Document DataFrame schema and watch-mode network-filesystem caveat

## Context

pyfileindex's docs (README, getting_started notebook, Sphinx autosummary API page)
explain how to call `update()`, `open()`, and `filter_function`, but never describe
the columns of `pfi.dataframe` itself. The target audience — scientists monitoring
many simulation output directories, often on a shared HPC filesystem — needs to know
which columns exist and what they mean to build monitoring logic (e.g. filter to
files only, sort by `mtime` to find the most recently written output).

Separately, `watch=True` uses `watchfiles` (inotify/FSEvents-based). On network
filesystems commonly used on HPC clusters (NFS, Lustre, GPFS), changes made by other
nodes are frequently not reported through these OS-level file-change notifications.
This is currently undocumented and would silently break the most natural use case for
this audience (one process watching a directory while compute jobs on other nodes
write into it).

## Changes

1. **`src/pyfileindex/pyfileindex.py`**
   - Extend the `df`/`dataframe` property docstring with a description of each
     column: `basename` (str), `path` (str, absolute), `dirname` (str), `is_directory`
     (bool), `mtime` (float, POSIX timestamp), `nlink` (int, hard-link count). This
     docstring is picked up by Sphinx autosummary, so it appears on the existing
     `docs/api.html` page with no structural doc changes needed.
   - Extend the `watch` parameter docstring in `__init__` with a one- to
     two-sentence caveat: on network filesystems (NFS, Lustre, GPFS) commonly used
     on HPC clusters, changes made by other nodes may not be reported reliably;
     polling mode (`watch=False`, the default) is the safer choice in that setting.

2. **`README.md`**
   - Under the existing "List files in the file system index" usage step, add a
     small table listing the six columns and their meaning, so a reader gets the
     schema without following a link into the API reference.

3. **`notebooks/getting_started.ipynb`**
   - Near the first display of `pfi` (in "1. Polling mode" → "Initialise
     PyFileIndex"), add a one-line markdown note pointing at the column meanings
     (signpost only, not a duplicate table — link to README).
   - In the "2. Watch mode" intro markdown cell, add the network-filesystem caveat
     (same content as the docstring, phrased for the notebook).

## Out of scope

- No changes to `docs/_toc.yml` or `docs/api.rst` structure — autosummary already
  surfaces the extended docstrings without any reorganization.
- No new example notebook for multi-directory HPC monitoring (descoped per user
  decision — schema docs are the priority for this change).

## Testing

Documentation-only change. Verify by:
- Building the notebook to confirm it still executes top-to-bottom (`jupyter
  nbconvert --execute` or running existing notebook test/lint if present).
- Visual check of rendered README table.
