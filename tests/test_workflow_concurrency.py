"""Tests for bounded and non-stale GitHub Actions validation workflows."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class WorkflowConcurrencyTests(unittest.TestCase):
    def test_python_checks_cancel_stale_runs_and_have_timeout(self):
        source = (ROOT / ".github/workflows/python-checks.yml").read_text(encoding="utf-8")
        self.assertIn("group: leos-python-${{ github.ref }}", source)
        self.assertIn("cancel-in-progress: true", source)
        self.assertIn("timeout-minutes: 15", source)

    def test_recipe_checks_cancel_stale_runs_and_have_timeout(self):
        source = (ROOT / ".github/workflows/recipe-checks.yml").read_text(encoding="utf-8")
        self.assertIn("group: leos-bluebuild-${{ github.ref }}", source)
        self.assertIn("cancel-in-progress: true", source)
        self.assertIn("timeout-minutes: 15", source)

    def test_recipe_generation_retries_transient_schema_fetch_failures(self):
        source = (ROOT / ".github/workflows/recipe-checks.yml").read_text(encoding="utf-8")
        self.assertIn("for recipe in recipe.yml recipe-nvidia.yml", source)
        self.assertIn("max_attempts=3", source)
        self.assertIn('until bluebuild generate "recipes/${recipe}"', source)
        self.assertIn('sleep "$((attempt * 3))"', source)
        self.assertIn("could not generate ${recipe} after", source)
        self.assertIn('test -s "$output"', source)

    def test_workflow_groups_are_separate(self):
        python = (ROOT / ".github/workflows/python-checks.yml").read_text(encoding="utf-8")
        recipe = (ROOT / ".github/workflows/recipe-checks.yml").read_text(encoding="utf-8")
        self.assertNotEqual(
            "leos-python-${{ github.ref }}",
            "leos-bluebuild-${{ github.ref }}",
        )


if __name__ == "__main__":
    unittest.main()
