# Dependency policy

pyfileindex is scientific software: an upstream dependency release that
silently breaks us can cost users months of confusing failures before
anyone notices. So we don't advertise compatibility with a dependency
version until we've actually tested it in CI. This document explains how
that works and how to do the common day-to-day operations.

## The three states

1. **Lower bound** - the oldest version of a direct dependency we currently
   guarantee compatibility with. Represented by the `lower` Pixi
   environment (`pyproject.toml`, `[tool.pixi.environments].lower`), which
   solves with `solve-strategy = "lowest-direct"`. It only changes when a
   maintainer deliberately edits the floor in `[tool.pixi.dependencies]` /
   `[tool.pixi.feature.wf.dependencies]` - never automatically.

2. **Upper bound** - the newest version of a direct dependency that CI has
   explicitly validated. Represented by the `upper-py311` .. `upper-py314`
   environments, which solve with `solve-strategy = "highest"`. These are
   refreshed automatically, but only after the new version passes the full
   test suite (see "the weekly update" below).

3. **Published dependency range** - what actually ships in
   `[project.dependencies]` / `[project.optional-dependencies]` when we cut
   a release: `dependency>=LOWER,<=UPPER`, generated from states 1 and 2 by
   `.ci_support/pyproject_bounds.py`.

Updating the upper environment (state 2) and publishing a new package
version (state 3) are deliberately separate operations. A green weekly-update
PR only means "this version doesn't break us" - it does not, by itself,
change what a `pip install pyfileindex` gets today. That only happens the
next time someone runs the bounds generator and cuts a release.

## Why the upper bound is strict

`dependency>=LOWER` with no ceiling looks convenient, but it means a user's
independently-resolved environment can silently pick up a dependency
release the day it hits PyPI/conda-forge - before we've even seen it in
CI. We have been bitten by this repeatedly. Capping at the newest
*validated* version instead means: worst case, a user's resolver picks a
combination we have actually run our test suite against.

## How dependency versions are represented

Everything lives in `pyproject.toml` under `[tool.pixi.*]`:

- `[tool.pixi.dependencies]` (and `[tool.pixi.feature.wf.dependencies]` for
  the optional `watchfiles` extra) declare each direct dependency's floor
  as an open-ended requirement, e.g. `pandas = ">=1.5.3"`.
- `[tool.pixi.feature.lower]` sets `solve-strategy = "lowest-direct"`,
  so the `lower` environment resolves that requirement to the *oldest*
  satisfying version.
- `[tool.pixi.feature.upper]` sets `solve-strategy = "highest"` (pixi's
  default), so `upper-py311..upper-py314` resolve it to the *newest*
  available version, independently for each supported Python version.
- A single `pixi.lock`, committed to the repo, pins the exact resolution of
  every environment.

This means there is only one place a dependency's floor is declared - the
ceiling isn't hand-maintained anywhere; it falls out of what conda-forge
currently offers, each time the lock is refreshed.

## How the weekly update works

`.github/workflows/weekly_update.yml` runs every Monday (and on demand via
`workflow_dispatch`). For each direct dependency, independently:

1. `pixi update <package> --environment <env>` for every `upper-py*`
   environment (`pixi.lock` is backed up first).
2. Run `pixi run -e <env> test` for every `upper-py*` environment.
3. If all pass, keep the update. If any fail, restore the previous
   `pixi.lock` for that package and move on to the next one.

This uses pixi's own per-package, per-environment update instead of a
custom resolver, so (for example) a numpy release that breaks us doesn't
block an unrelated, passing h5py update. If anything advanced, the
workflow opens a pull request with the updated `pixi.lock` for review -
`pyproject.toml` is never touched by this workflow.

## How dependency bounds are generated for a release

`.ci_support/pyproject_bounds.py`:

1. Reads the direct dependency names straight out of
   `[project.dependencies]` / `[project.optional-dependencies]`.
2. Resolves each one's version in the `lower` environment, and in every
   `upper-py*` environment (via `pixi list --explicit --json`).
3. Requires all `upper-py*` environments to agree on the same version for a
   given dependency - if they don't, that's treated as inconsistent
   validated data and the run fails rather than guessing.
4. Writes `name>=LOWER,<=UPPER` back into `pyproject.toml` with `tomlkit`,
   preserving everything else in the file.

It fails (non-zero exit) if a direct dependency is missing from the lower
or an upper environment, if the lower bound is greater than the upper
bound, or if the upper environments disagree - so a release can't
accidentally publish an unvalidated or inconsistent range.

`.github/workflows/deploy.yml` runs this generator against the tagged
commit's `pixi.lock` immediately before building the sdist/wheel, so the
published metadata always matches what that commit's lock file actually
validated. It never updates `pixi.lock` itself.

## Common operations

- **Run the tests locally**: `pixi run -e upper-py313 test` (swap the
  environment for `lower`, `mini`, or any `upper-py31{1,2,4}`).
- **See what a `pixi run <env> test` will use**: `pixi list -e <env>`.
- **Update the lower bound** (drop support for an old dependency version):
  edit the version in `[tool.pixi.dependencies]` /
  `[tool.pixi.feature.wf.dependencies]`, run `pixi lock`, then
  `pixi run -e lower test` to confirm it still works.
- **Manually test a newer dependency** before the weekly job gets to it:
  `pixi update <package> --environment upper-py313`, then
  `pixi run -e upper-py313 test`. Revert with `git checkout -- pixi.lock`
  if it fails.
- **See what the weekly update does**: read
  `.github/workflows/weekly_update.yml`, or trigger it manually via
  `workflow_dispatch` from the Actions tab.
- **When a new dependency version breaks the tests**: nothing to do - the
  weekly workflow already reverts that one package's `pixi.lock` entry and
  reports it in the PR body. Investigate and fix compatibility (or wait for
  a further upstream fix) at your own pace; the upper bound simply doesn't
  advance for that package until it passes.
- **Update dependency bounds before a release**:
  `pixi run generate-bounds`, review the `pyproject.toml` diff, commit it.
  `pixi run check-bounds` (also run in CI as the `bounds_check` job) tells
  you whether this is even necessary.
