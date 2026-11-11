"""Safety checks for the manual image publication workflow."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class BuildWorkflowTests(unittest.TestCase):
    def test_image_workflow_is_manual_only(self):
        source = (ROOT / ".github/workflows/build.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", source)
        self.assertNotIn("branches: [main]", source)

    def test_image_workflow_checks_both_cosign_materials_before_build(self):
        source = (ROOT / ".github/workflows/build.yml").read_text(encoding="utf-8")
        self.assertIn("Check signing prerequisites", source)
        self.assertIn("SIGNING_SECRET: ${{ secrets.SIGNING_SECRET }}", source)
        self.assertIn('[[ -z "${SIGNING_SECRET}" ]]', source)
        self.assertIn("[[ ! -s cosign.pub ]]", source)
        self.assertLess(source.index("Check signing prerequisites"), source.index("Build and publish LEOS"))


if __name__ == "__main__":
    unittest.main()
