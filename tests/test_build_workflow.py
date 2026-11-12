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
        self.assertIn("Check out repository", source)
        self.assertIn("Check signing prerequisites", source)
        self.assertLess(source.index("Check out repository"), source.index("Check signing prerequisites"))
        self.assertIn("SIGNING_SECRET: ${{ secrets.SIGNING_SECRET }}", source)
        self.assertIn('[[ -z "${SIGNING_SECRET}" ]]', source)
        self.assertIn("[[ ! -s cosign.pub ]]", source)
        self.assertLess(source.index("Check signing prerequisites"), source.index("Build and publish LEOS"))

    def test_image_workflow_uses_recipe_path_relative_to_recipes_directory(self):
        source = (ROOT / ".github/workflows/build.yml").read_text(encoding="utf-8")
        self.assertIn("recipe: recipe.yml", source)
        self.assertTrue((ROOT / "recipes/recipe.yml").is_file())
        self.assertFalse((ROOT / "recipes/recipes/recipe.yml").exists())

    def test_branding_assets_are_copied_into_the_runtime_share_tree(self):
        recipe = (ROOT / "recipes/recipe.yml").read_text(encoding="utf-8")
        self.assertIn("src: branding", recipe)
        self.assertIn("dest: /usr/share/leos/", recipe)

    def test_branding_contract_preserves_original_media_formats(self):
        manifest = (ROOT / "branding/ASSET_MANIFEST.md").read_text(encoding="utf-8")
        self.assertIn("desktop-logo.jpeg", manifest)
        self.assertIn("gaming-logo.jpeg", manifest)
        self.assertIn("animations/desktop-intro.mp4", manifest)
        self.assertIn("animations/gaming-intro.mp4", manifest)
        self.assertIn("pistes audio aac", manifest.lower())
        self.assertNotIn("desktop-intro.ogg", manifest)
        self.assertNotIn("gaming-intro.ogg", manifest)

    def test_private_cosign_key_is_ignored_but_public_key_is_trackable(self):
        source = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("/cosign.key", source)
        self.assertIn("/cosign.key.*", source)
        self.assertNotIn("/cosign.pub", source)


if __name__ == "__main__":
    unittest.main()
