import importlib.util
import sys
import unittest
from pathlib import Path

try:
    import tomlkit
except ImportError:
    raise unittest.SkipTest("tomlkit is required for these tests")

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / ".ci_support" / "pyproject_bounds.py"

try:
    spec = importlib.util.spec_from_file_location("pyproject_bounds", MODULE_PATH)
    pyproject_bounds = importlib.util.module_from_spec(spec)
    sys.modules["pyproject_bounds"] = pyproject_bounds
    spec.loader.exec_module(pyproject_bounds)
except ImportError:
    raise unittest.SkipTest("packaging is required for these tests")


FIXTURE_TOML = """\
[project]
name = "example"
dependencies = [
    "pandas>=1.0.0",
]

[project.optional-dependencies]
watchfiles = ["watchfiles>=1.0.0"]

[tool.ruff]
exclude = ["notebooks"]

[tool.pixi.environments]
lower = { features = ["lower"] }
upper-a = { features = ["upper", "a"] }
upper-b = { features = ["upper", "b"] }
"""


def write_fixture(tmp_path):
    path = tmp_path / "pyproject.toml"
    path.write_text(FIXTURE_TOML)
    return path


class TestVersionsFromPixiListJson(unittest.TestCase):
    def test_parses_name_and_version(self):
        json_text = (
            '[{"name": "pandas", "version": "1.5.3", "kind": "conda"},'
            ' {"name": "watchfiles", "version": "1.0.4", "kind": "conda"}]'
        )
        versions = pyproject_bounds.versions_from_pixi_list_json(json_text)
        self.assertEqual(versions, {"pandas": "1.5.3", "watchfiles": "1.0.4"})


class TestDependencyNames(unittest.TestCase):
    def test_strips_version_specifiers(self):
        names = pyproject_bounds.dependency_names(["pandas>=1.5.3,<=3.0.6", "watchfiles==1.2.0"])
        self.assertEqual(names, ["pandas", "watchfiles"])


class TestComputeRange(unittest.TestCase):
    def test_normal_range(self):
        self.assertEqual(
            pyproject_bounds.compute_range("pandas", "1.5.3", "3.0.6"),
            "pandas>=1.5.3,<=3.0.6",
        )

    def test_lower_equals_upper(self):
        self.assertEqual(
            pyproject_bounds.compute_range("pandas", "1.5.3", "1.5.3"),
            "pandas>=1.5.3,<=1.5.3",
        )

    def test_lower_greater_than_upper_raises(self):
        with self.assertRaises(pyproject_bounds.BoundsError):
            pyproject_bounds.compute_range("pandas", "3.0.6", "1.5.3")


class TestMergeConsistentVersions(unittest.TestCase):
    def test_agreeing_environments(self):
        version = pyproject_bounds.merge_consistent_versions(
            "pandas", {"upper-a": {"pandas": "3.0.6"}, "upper-b": {"pandas": "3.0.6"}}
        )
        self.assertEqual(version, "3.0.6")

    def test_inconsistent_environments_raise(self):
        with self.assertRaises(pyproject_bounds.BoundsError):
            pyproject_bounds.merge_consistent_versions(
                "pandas", {"upper-a": {"pandas": "3.0.6"}, "upper-b": {"pandas": "3.0.5"}}
            )

    def test_missing_dependency_raises(self):
        with self.assertRaises(pyproject_bounds.BoundsError):
            pyproject_bounds.merge_consistent_versions(
                "pandas", {"upper-a": {"pandas": "3.0.6"}, "upper-b": {}}
            )


class TestGenerate(unittest.TestCase):
    def setUp(self):
        import tempfile

        self._tmpdir = tempfile.TemporaryDirectory()
        self.pyproject_path = write_fixture(Path(self._tmpdir.name))
        self.lower_versions = {"pandas": "1.5.3", "watchfiles": "1.0.4"}
        self.upper_versions_by_environment = {
            "upper-a": {"pandas": "3.0.6", "watchfiles": "1.2.0"},
            "upper-b": {"pandas": "3.0.6", "watchfiles": "1.2.0"},
        }

    def tearDown(self):
        self._tmpdir.cleanup()

    def _generate(self):
        return pyproject_bounds.generate(
            pyproject_path=self.pyproject_path,
            lower_versions=self.lower_versions,
            upper_versions_by_environment=self.upper_versions_by_environment,
        )

    def test_generates_normal_dependency_range(self):
        doc = self._generate()
        self.assertEqual(doc["project"]["dependencies"][0], "pandas>=1.5.3,<=3.0.6")

    def test_generates_optional_dependency_range(self):
        doc = self._generate()
        self.assertEqual(
            doc["project"]["optional-dependencies"]["watchfiles"][0],
            "watchfiles>=1.0.4,<=1.2.0",
        )

    def test_discovers_upper_environments_by_prefix(self):
        with open(self.pyproject_path) as f:
            doc = tomlkit.parse(f.read())
        self.assertEqual(
            pyproject_bounds.discover_environments(doc, "upper"), ["upper-a", "upper-b"]
        )

    def test_missing_dependency_in_lower_raises(self):
        del self.lower_versions["watchfiles"]
        with self.assertRaises(pyproject_bounds.BoundsError):
            self._generate()

    def test_inconsistent_upper_environments_raise(self):
        self.upper_versions_by_environment["upper-b"]["pandas"] = "2.9.9"
        with self.assertRaises(pyproject_bounds.BoundsError):
            self._generate()

    def test_no_upper_environments_raises(self):
        with self.assertRaises(pyproject_bounds.BoundsError):
            pyproject_bounds.generate(
                pyproject_path=self.pyproject_path,
                lower_versions=self.lower_versions,
                upper_versions_by_environment={},
                upper_environments=[],
            )

    def test_idempotent(self):
        doc_first = self._generate()
        self.pyproject_path.write_text(tomlkit.dumps(doc_first))
        doc_second = self._generate()
        self.assertEqual(tomlkit.dumps(doc_first), tomlkit.dumps(doc_second))

    def test_preserves_unrelated_toml_content(self):
        doc = self._generate()
        self.assertEqual(doc["tool"]["ruff"]["exclude"], ["notebooks"])
        self.assertEqual(doc["project"]["name"], "example")


class TestMainCLI(unittest.TestCase):
    def setUp(self):
        import tempfile

        self._tmpdir = tempfile.TemporaryDirectory()
        self.pyproject_path = write_fixture(Path(self._tmpdir.name))

    def tearDown(self):
        self._tmpdir.cleanup()

    def _run(self, extra_args, monkeypatch_versions):
        original = pyproject_bounds.pixi_list_versions
        pyproject_bounds.pixi_list_versions = lambda env, manifest_path=None: monkeypatch_versions[env]
        try:
            return pyproject_bounds.main(
                ["--pyproject", str(self.pyproject_path), *extra_args]
            )
        finally:
            pyproject_bounds.pixi_list_versions = original

    def test_check_mode_fails_when_out_of_date(self):
        versions = {
            "lower": {"pandas": "1.5.3", "watchfiles": "1.0.4"},
            "upper-a": {"pandas": "3.0.6", "watchfiles": "1.2.0"},
            "upper-b": {"pandas": "3.0.6", "watchfiles": "1.2.0"},
        }
        exit_code = self._run(["--check"], versions)
        self.assertEqual(exit_code, 1)

    def test_check_mode_passes_once_written(self):
        versions = {
            "lower": {"pandas": "1.5.3", "watchfiles": "1.0.4"},
            "upper-a": {"pandas": "3.0.6", "watchfiles": "1.2.0"},
            "upper-b": {"pandas": "3.0.6", "watchfiles": "1.2.0"},
        }
        self.assertEqual(self._run([], versions), 0)
        self.assertEqual(self._run(["--check"], versions), 0)


if __name__ == "__main__":
    unittest.main()
