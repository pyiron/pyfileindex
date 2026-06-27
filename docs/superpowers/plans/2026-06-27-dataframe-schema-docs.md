# DataFrame Schema & Watch-Mode Caveat Docs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Document the columns of `pfi.dataframe` and the network-filesystem caveat for `watch=True`, surfaced in the docstrings (so they appear on the Sphinx API page), the README, and the getting-started notebook.

**Architecture:** Pure documentation change — docstrings in `src/pyfileindex/pyfileindex.py`, a markdown table in `README.md`, and two markdown cells in `notebooks/getting_started.ipynb`. No code logic changes; no new files.

**Tech Stack:** Python (docstrings consumed by Sphinx `autosummary`), Markdown (README), Jupyter notebook (`.ipynb`, edited via the NotebookEdit tool).

## Global Constraints

- This is a documentation-only change — do not alter any runtime behavior of `PyFileIndex`.
- Column names/types documented must exactly match what `_create_df_from_lst` in `src/pyfileindex/pyfileindex.py` actually produces: `basename` (str), `path` (str), `dirname` (str), `is_directory` (bool), `mtime` (float), `nlink` (int).
- Baseline test suite state before any change (recorded by running `PYTHONPATH=src .pixi/envs/default/bin/python -m unittest discover -s tests/unit`): `Ran 20 tests ... FAILED (failures=1, skipped=2)` — one pre-existing failure (`test_len`) and two skips, unrelated to this work. After each task, rerun the same command and confirm the result is unchanged (still exactly 1 failure, 2 skipped, 20 total) — do not attempt to fix the pre-existing failure, it's out of scope.

---

### Task 1: Docstrings in `src/pyfileindex/pyfileindex.py`

**Files:**
- Modify: `src/pyfileindex/pyfileindex.py:20-22` (the `watch` parameter description in the class docstring)
- Modify: `src/pyfileindex/pyfileindex.py:56-62` (the `df` and `dataframe` properties)

**Interfaces:**
- Consumes: nothing new.
- Produces: nothing consumed by later tasks — README (Task 2) and notebook (Task 3) restate this content independently rather than importing it, since they're separate documents.

- [ ] **Step 1: Update the `watch` parameter docstring**

In `src/pyfileindex/pyfileindex.py`, the class docstring currently reads (lines 20-22):

```python
        watch (bool): keep the file index in sync using a background file system
            watcher instead of rescanning the file system on every update() call
            (optional)
```

Replace it with:

```python
        watch (bool): keep the file index in sync using a background file system
            watcher instead of rescanning the file system on every update() call.
            Relies on OS-level file change notifications (via the optional
            watchfiles dependency), which are not always delivered reliably on
            network filesystems such as NFS, Lustre, or GPFS when the change is
            made by a different node -- a common setup when monitoring HPC
            simulation output from a separate process or login node. Prefer the
            default polling mode (watch=False) in that case (optional)
```

- [ ] **Step 2: Add column documentation to the `df` and `dataframe` properties**

The properties currently read (lines 56-62):

```python
    @property
    def df(self) -> pandas.DataFrame:
        return self._df

    @property
    def dataframe(self) -> pandas.DataFrame:
        return self.df
```

Replace with:

```python
    @property
    def df(self) -> pandas.DataFrame:
        """
        The file index as a pandas DataFrame, with one row per file or
        directory below the indexed path. Columns:

        - ``basename`` (str): file or directory name, e.g. ``"output.txt"``.
        - ``path`` (str): absolute path.
        - ``dirname`` (str): absolute path of the parent directory.
        - ``is_directory`` (bool): ``True`` for directories, ``False`` for files.
        - ``mtime`` (float): last modification time as a POSIX timestamp (the
          same value ``os.stat().st_mtime`` returns). Useful for finding which
          simulation directories have written output most recently.
        - ``nlink`` (int): hard link count (``os.stat().st_nlink``). Used
          internally to detect changes that don't update ``mtime``; rarely
          needed directly.

        Returns:
            pandas.DataFrame: the file index
        """
        return self._df

    @property
    def dataframe(self) -> pandas.DataFrame:
        """Alias for :attr:`df`."""
        return self.df
```

- [ ] **Step 3: Verify the docstrings load correctly and the column list matches reality**

Run:
```bash
PYTHONPATH=src .pixi/envs/default/bin/python -c "
from pyfileindex import PyFileIndex
assert 'mtime' in PyFileIndex.df.__doc__
assert 'NFS' in PyFileIndex.__init__.__doc__
print('docstrings ok')
"
```
Expected output: `docstrings ok`

- [ ] **Step 4: Run the baseline test suite to confirm no regression**

Run: `PYTHONPATH=src .pixi/envs/default/bin/python -m unittest discover -s tests/unit`
Expected: same result as the Global Constraints baseline — `Ran 20 tests ... FAILED (failures=1, skipped=2)`, no new failures.

- [ ] **Step 5: Commit**

```bash
git add src/pyfileindex/pyfileindex.py
git commit -m "Document DataFrame columns and watch-mode network-filesystem caveat"
```

---

### Task 2: README.md column reference table

**Files:**
- Modify: `README.md` (the "List files in the file system index" step of the Usage section, currently around lines 35-38)

**Interfaces:**
- Consumes: nothing.
- Produces: nothing consumed by other tasks.

- [ ] **Step 1: Insert the column table**

In `README.md`, find:

```markdown
List files in the file system index: 
```python
pfi.dataframe 
```
```

Replace with (adding the table immediately after the code block, before the next `Update file system index:` paragraph):

```markdown
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
```

- [ ] **Step 2: Verify the table renders as valid markdown**

Run:
```bash
grep -c '^|' README.md
```
Expected: `7` (the header row, separator row, and 6 data rows for the 6 columns).

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "Add DataFrame column reference table to README"
```

---

### Task 3: Notebook markdown cells in `notebooks/getting_started.ipynb`

**Files:**
- Modify: `notebooks/getting_started.ipynb` (insert one markdown cell, edit one existing markdown cell, via the NotebookEdit tool)

**Interfaces:**
- Consumes: nothing.
- Produces: nothing consumed by other tasks.

**Note:** This task requires the NotebookEdit tool. You must `Read` the notebook file first in the same session before calling NotebookEdit, or the tool will fail. Cell IDs below are taken from the notebook as of this plan's writing — re-read the notebook first to confirm they still match; if a cell was since renumbered, locate it by its visible content instead.

- [ ] **Step 1: Read the notebook**

Use the Read tool on `notebooks/getting_started.ipynb` to load current cell IDs.

- [ ] **Step 2: Insert a column-reference signpost after the first `pfi` display**

The code cell with id `46e3a8b5` contains:
```python
pfi = PyFileIndex(path=".", filter_function=filter_function, debug=True)
pfi
```

Using NotebookEdit with `notebook_path="notebooks/getting_started.ipynb"`, `cell_id="46e3a8b5"`, `edit_mode="insert"`, `cell_type="markdown"`, insert a new cell with this `new_source`:

```markdown
`pfi.dataframe` is a pandas DataFrame with one row per file or directory. See the [README](https://github.com/pyiron/pyfileindex#readme) for the full column reference (`basename`, `path`, `dirname`, `is_directory`, `mtime`, `nlink`).
```

- [ ] **Step 3: Add the network-filesystem caveat to the watch-mode intro cell**

The markdown cell with id `ee3aa41c` currently contains:

```markdown
# 2. Watch mode (`watch=True`)

With `watch=True`, `PyFileIndex` starts a background thread (using [watchfiles](https://watchfiles.helpmanual.io)) that listens for file system events as they happen, instead of rescanning the tree on every `update()` call. This trades a small amount of background resource usage for much cheaper `update()` calls on large trees, since `update()` now just drains whatever change events have already been collected.

Two practical consequences:
- A change made *immediately before* calling `update()` may not have reached the background watcher yet. `update()` accepts a `timeout` argument (default 0.1s) to wait briefly for such pending changes before giving up and returning whatever is available.
- The background thread needs to be stopped explicitly with `close()`, or by using `PyFileIndex` as a context manager, once you're done with it. Forgetting to do so leaks a thread for as long as the process runs.
```

Using NotebookEdit with `notebook_path="notebooks/getting_started.ipynb"`, `cell_id="ee3aa41c"`, `edit_mode="replace"`, `cell_type="markdown"`, replace its `new_source` with:

```markdown
# 2. Watch mode (`watch=True`)

With `watch=True`, `PyFileIndex` starts a background thread (using [watchfiles](https://watchfiles.helpmanual.io)) that listens for file system events as they happen, instead of rescanning the tree on every `update()` call. This trades a small amount of background resource usage for much cheaper `update()` calls on large trees, since `update()` now just drains whatever change events have already been collected.

Three practical consequences:
- A change made *immediately before* calling `update()` may not have reached the background watcher yet. `update()` accepts a `timeout` argument (default 0.1s) to wait briefly for such pending changes before giving up and returning whatever is available.
- The background thread needs to be stopped explicitly with `close()`, or by using `PyFileIndex` as a context manager, once you're done with it. Forgetting to do so leaks a thread for as long as the process runs.
- On network filesystems such as NFS, Lustre, or GPFS -- common on HPC clusters -- changes made by a different node are often not delivered through these OS-level notifications at all. If you are monitoring simulation output written by jobs running on other compute nodes, prefer the default polling mode (`watch=False`) instead.
```

- [ ] **Step 4: Verify the notebook is still valid JSON and both edits landed**

Run:
```bash
.pixi/envs/default/bin/python -c "
import json
nb = json.load(open('notebooks/getting_started.ipynb'))
text = json.dumps(nb)
assert 'full column reference' in text
assert 'GPFS' in text
print('notebook ok, cells:', len(nb['cells']))
"
```
Expected output: `notebook ok, cells: 77` (76 cells currently in the notebook, plus the 1 new markdown cell inserted in Step 2 — Step 3 replaces a cell in place and does not change the count).

- [ ] **Step 5: Commit**

```bash
git add notebooks/getting_started.ipynb
git commit -m "Add column reference and network-filesystem caveat notes to getting-started notebook"
```

---

### Task 4: Final verification

**Files:** none (verification only)

- [ ] **Step 1: Re-run the full baseline test suite**

Run: `PYTHONPATH=src .pixi/envs/default/bin/python -m unittest discover -s tests/unit`
Expected: identical to the Global Constraints baseline (1 pre-existing failure, 2 skipped, 20 total) — confirms the docs-only changes introduced no regressions.

- [ ] **Step 2: Review the full diff**

Run: `git diff main --stat` and `git diff main`
Expected: only `src/pyfileindex/pyfileindex.py`, `README.md`, and `notebooks/getting_started.ipynb` are touched (plus the spec file already committed on this branch).
