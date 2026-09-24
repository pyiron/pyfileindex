"""Print the package names pinned as open-ended lower bounds in the Pixi
manifest - the direct dependencies eligible for the weekly upper-bound
update (see .github/workflows/weekly_update.yml).

These live in `[tool.pixi.dependencies]` (shared by every environment) and
`[tool.pixi.feature.wf.dependencies]` (the optional `watchfiles` extra).
"""

from pathlib import Path

import tomlkit

REPO_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"


def pinned_dependency_names(doc):
    pixi = doc["tool"]["pixi"]
    names = list(pixi.get("dependencies", {}).keys())
    names += list(pixi["feature"]["wf"].get("dependencies", {}).keys())
    return sorted(set(names))


if __name__ == "__main__":
    with open(PYPROJECT_PATH) as f:
        doc = tomlkit.parse(f.read())
    print(" ".join(pinned_dependency_names(doc)))
