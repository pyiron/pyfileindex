"""Derive PEP 621 dependency bounds from the validated Pixi environments.

The project's compatibility policy is: the lower bound of a direct
dependency is the oldest version tested by the ``lower`` Pixi environment,
and the upper bound is the newest version tested by the ``upper-py*``
environments. This script reads those resolved, locked environments (via
``pixi list --explicit --json``) and writes ``name>=LOWER,<=UPPER`` into
``[project.dependencies]`` / ``[project.optional-dependencies]`` of
pyproject.toml - and into any entry of ``[build-system] requires`` that
names the same dependency, so the build-time pin doesn't drift from the
runtime one.

See docs/dependency_policy.md for the full policy.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

import tomlkit
from packaging.requirements import Requirement
from packaging.version import Version

REPO_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"


class BoundsError(Exception):
    """A direct dependency's bounds could not be derived consistently."""


def dependency_names(requirements):
    """Return the package names of a list of PEP 508 requirement strings."""
    return [Requirement(req).name for req in requirements]


def versions_from_pixi_list_json(json_text):
    """Parse `pixi list --json` output into a {name: version} mapping."""
    packages = json.loads(json_text)
    return {pkg["name"]: pkg["version"] for pkg in packages}


def pixi_list_versions(environment, manifest_path=PYPROJECT_PATH):
    """Return the explicit (direct) dependency versions of a Pixi environment."""
    result = subprocess.run(
        [
            "pixi",
            "list",
            "--environment",
            environment,
            "--explicit",
            "--json",
            "--manifest-path",
            str(manifest_path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return versions_from_pixi_list_json(result.stdout)


def discover_environments(doc, prefix):
    """Return the names of `[tool.pixi.environments]` starting with `prefix`."""
    environments = doc["tool"]["pixi"]["environments"]
    return sorted(name for name in environments if name.startswith(prefix))


def merge_consistent_versions(name, versions_by_environment):
    """Merge per-environment {name: version} dicts, requiring agreement.

    `versions_by_environment` maps environment name -> {package: version}.
    Raises BoundsError if `name` is missing from an environment, or if the
    environments resolved different versions of it (which would mean the
    bound is not actually validated consistently across the test matrix).
    """
    resolved = {}
    for env_name, versions in versions_by_environment.items():
        if name not in versions:
            raise BoundsError(f"{name!r} was not found in the {env_name!r} environment")
        resolved[env_name] = versions[name]

    distinct = set(resolved.values())
    if len(distinct) > 1:
        detail = ", ".join(f"{env}={ver}" for env, ver in sorted(resolved.items()))
        raise BoundsError(
            f"{name!r} resolved to inconsistent versions across environments: {detail}"
        )
    return next(iter(distinct))


def compute_range(name, lower_version, upper_version):
    """Return the `name>=LOWER,<=UPPER` requirement string for one dependency."""
    lower = Version(lower_version)
    upper = Version(upper_version)
    if lower > upper:
        raise BoundsError(
            f"{name!r}: lower bound {lower} is greater than upper bound {upper}"
        )
    return f"{name}>={lower},<={upper}"


def resolved_ranges(names, lower_versions, upper_versions_by_environment):
    """Return {name: 'name>=LOWER,<=UPPER'} for every name in `names`."""
    ranges = {}
    for name in names:
        if name not in lower_versions:
            raise BoundsError(f"{name!r} was not found in the lower environment")
        upper_version = merge_consistent_versions(name, upper_versions_by_environment)
        ranges[name] = compute_range(name, lower_versions[name], upper_version)
    return ranges


def _apply_ranges(requirements, ranges):
    """Replace, in place, every entry of `requirements` whose name is in `ranges`."""
    for i, req in enumerate(requirements):
        name = Requirement(req).name
        if name in ranges:
            requirements[i] = ranges[name]


def update_pyproject(doc, ranges):
    """Rewrite `[project.dependencies]`, `[project.optional-dependencies]`, and
    any matching entries of `[build-system] requires` in place.

    `[build-system] requires` is a separate, hand-authored list (it pins the
    *build-time* backend, not the package's runtime dependencies), but where
    it happens to name one of the project's own direct dependencies (e.g.
    `pandas`, needed by hatch-vcs' version detection at build time), that
    entry is kept in sync with the same validated range so it doesn't drift.
    """
    project = doc["project"]

    dependencies = project.get("dependencies")
    if dependencies is not None:
        _apply_ranges(dependencies, ranges)

    optional_dependencies = project.get("optional-dependencies")
    if optional_dependencies is not None:
        for reqs in optional_dependencies.values():
            _apply_ranges(reqs, ranges)

    build_requires = doc.get("build-system", {}).get("requires")
    if build_requires is not None:
        _apply_ranges(build_requires, ranges)

    return doc


def direct_dependency_names(doc):
    project = doc["project"]
    names = list(dependency_names(project.get("dependencies", [])))
    for reqs in project.get("optional-dependencies", {}).values():
        names.extend(dependency_names(reqs))
    return names


def generate(
    pyproject_path=PYPROJECT_PATH,
    lower_environment="lower",
    upper_environments=None,
    lower_versions=None,
    upper_versions_by_environment=None,
):
    """Generate the updated pyproject.toml document (without writing it).

    `lower_versions` / `upper_versions_by_environment` can be injected
    directly (used by tests); otherwise they are obtained by invoking
    `pixi list` for `lower_environment` and `upper_environments`.
    """
    with open(pyproject_path) as f:
        doc = tomlkit.parse(f.read())

    if upper_environments is None:
        upper_environments = discover_environments(doc, "upper")
    if not upper_environments:
        raise BoundsError("no 'upper*' Pixi environments are defined")

    if lower_versions is None:
        lower_versions = pixi_list_versions(lower_environment, pyproject_path)
    if upper_versions_by_environment is None:
        upper_versions_by_environment = {
            env: pixi_list_versions(env, pyproject_path) for env in upper_environments
        }

    names = direct_dependency_names(doc)
    ranges = resolved_ranges(names, lower_versions, upper_versions_by_environment)
    return update_pyproject(doc, ranges)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pyproject", type=Path, default=PYPROJECT_PATH)
    parser.add_argument("--lower-environment", default="lower")
    parser.add_argument(
        "--upper-environment",
        action="append",
        dest="upper_environments",
        help="may be repeated; defaults to every 'upper*' environment in pyproject.toml",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="don't write pyproject.toml, exit non-zero if it would change",
    )
    args = parser.parse_args(argv)

    before = args.pyproject.read_text()
    try:
        doc = generate(
            pyproject_path=args.pyproject,
            lower_environment=args.lower_environment,
            upper_environments=args.upper_environments,
        )
    except BoundsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    after = tomlkit.dumps(doc)

    if args.check:
        if before != after:
            print(
                "pyproject.toml does not match the validated lower/upper "
                "environments - run `pixi run generate-bounds` and commit "
                "the result",
                file=sys.stderr,
            )
            return 1
        print("pyproject.toml is up to date with the validated environments")
        return 0

    args.pyproject.write_text(after)
    print(after if before == after else "pyproject.toml updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
