"""Tests for bounded and non-stale GitHub Actions validation workflows."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class WorkflowConcurrencyTests(unittest.TestCase):
    def test_python_checks_cancel_stale_runs_and_have_timeout(self):
        source = (ROOT / ".github/workflows/python-checks.yml").read_text(encoding="utf-8")
        self.assertIn("group: ${{ github.workflow }}-${{ github.ref }}", source)
        self.assertIn("cancel-in-progress: true", source)
        self.assertIn("timeout-minutes: 15", source)

    def test_recipe_checks_cancel_stale_runs_and_have_timeout(self):
        source = (ROOT / ".github/workflows/recipe-checks.yml").read_text(encoding="utf-8")
        self.assertIn("group: ${{ github.workflow }}-${{ github.ref }}", source)
        self.assertIn("cancel-in-progress: true", source)
        self.assertIn("timeout-minutes: 15", source)

    def test_workflow_groups_are_separate(self):
        python = (ROOT / ".github/workflows/python-checks.yml").read_text(encoding="utf-8")
        recipe = (ROOT / ".github/workflows/recipe-checks.yml").read_text(encoding="utf-8")
        self.assertNotEqual(
            python.split("group: ", 1)[1].splitlines()[0],
            recipe.split("group: ", 1)[1].splitlines()[0],
        )


if __name__ == "__main__":
    unittest.main()
