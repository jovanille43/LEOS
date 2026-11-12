"""Safety checks for the manual image publication workflow."""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class BuildWorkflowTests(unittest.TestCase):
    def test_image_workflow_is_manual_only(self):
        source = (ROOT / ".github/workflows/build.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", source)
        self.assertNotIn("branches: [main]", source)

    def test_image_workflow_verifies_original_branding_assets_before_publication(self):
        source = (ROOT / ".github/workflows/build.yml").read_text(encoding="utf-8")
        sums = (ROOT / "branding/SHA256SUMS").read_text(encoding="utf-8")
        self.assertIn("Verify official LEOS branding assets", source)
        self.assertLess(
            source.index("Verify official LEOS branding assets"),
            source.index("Check signing prerequisites"),
        )
        expected = (
            "branding/desktop-logo.jpeg",
            "branding/gaming-logo.jpeg",
            "branding/reference-comparison.jpeg",
            "branding/animations/desktop-intro.mov",
            "branding/animations/gaming-intro.mp4",
            "branding/animations/gaming-roar-reference.mp4",
            "branding/wallpapers/desktop-leos.svg",
            "branding/wallpapers/gaming-leos.svg",
        )
        for path in expected:
            with self.subTest(path=path):
                self.assertIn(path, source)

    def test_branding_checksum_manifest_has_six_unique_valid_entries(self):
        sums = (ROOT / "branding/SHA256SUMS").read_text(encoding="utf-8").splitlines()
        sums = [line for line in sums if line and not line.startswith("#")]
        self.assertEqual(len(sums), 6)
        parsed = []
        for line in sums:
            if line.startswith("#"):
                continue
            match = re.fullmatch(r"([0-9a-f]{64})  (SOURCE_[A-Za-z0-9_.-]+)", line)
            self.assertIsNotNone(match, line)
            parsed.append(match.groups())
        self.assertEqual(len({path for _digest, path in parsed}), 6)
        self.assertEqual(len({digest for digest, _path in parsed}), 6)

    def test_manual_build_required_asset_list_matches_checksum_manifest(self):
        source = (ROOT / ".github/workflows/build.yml").read_text(encoding="utf-8")
        sums = (ROOT / "branding/SHA256SUMS").read_text(encoding="utf-8")
        block_start = source.index("required_assets=(")
        block_end = source.index(")", block_start)
        listed = re.findall(r"branding/[A-Za-z0-9_./-]+", source[block_start:block_end])
        self.assertEqual(set(listed), {
            "branding/desktop-logo.jpeg",
            "branding/gaming-logo.jpeg",
            "branding/reference-comparison.jpeg",
            "branding/animations/desktop-intro.mov",
            "branding/animations/gaming-intro.mp4",
            "branding/animations/gaming-roar-reference.mp4",
            "branding/wallpapers/desktop-leos.svg",
            "branding/wallpapers/gaming-leos.svg",
        })
        self.assertEqual(len(listed), 8)

    def test_image_workflow_checks_both_cosign_materials_before_build(self):
        source = (ROOT / ".github/workflows/build.yml").read_text(encoding="utf-8")
        self.assertIn("Check out repository", source)
        self.assertIn("Check signing prerequisites", source)
        self.assertLess(source.index("Check out repository"), source.index("Check signing prerequisites"))
        self.assertIn("SIGNING_SECRET: ${{ secrets.SIGNING_SECRET }}", source)
        self.assertIn('[[ -z "${SIGNING_SECRET}" ]]', source)
        self.assertIn("[[ ! -s cosign.pub ]]", source)
        self.assertLess(source.index("Check signing prerequisites"), source.index("Build and publish LEOS"))

    def test_image_workflow_cryptographically_verifies_cosign_key_pair(self):
        source = (ROOT / ".github/workflows/build.yml").read_text(encoding="utf-8")
        self.assertIn("sigstore/cosign-installer@v3", source)
        self.assertIn("Verify private and public signing keys match", source)
        self.assertIn('cosign sign-blob --key "$workdir/cosign.key"', source)
        self.assertIn('cosign verify-blob --key cosign.pub', source)
        self.assertLess(
            source.index("Verify private and public signing keys match"),
            source.index("Build and publish LEOS"),
        )
        self.assertIn('chmod 600 "$workdir/cosign.key"', source)
        self.assertIn("trap 'rm -rf \"$workdir\"' EXIT", source)

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
        self.assertIn("animations/desktop-intro.mov", manifest)
        self.assertIn("animations/gaming-intro.mp4", manifest)
        self.assertIn("pistes audio des vidéos", manifest.lower())
        self.assertNotIn("desktop-intro.ogg", manifest)
        self.assertNotIn("gaming-intro.ogg", manifest)

    def test_recipe_installs_qt_multimedia_for_intro_playback(self):
        recipe = (ROOT / "recipes/recipe.yml").read_text(encoding="utf-8")
        self.assertIn("qt6-qtmultimedia", recipe)

    def test_branding_manifest_documents_secondary_gaming_animation(self):
        manifest = (ROOT / "branding/ASSET_MANIFEST.md").read_text(encoding="utf-8")
        self.assertIn("gaming-roar-reference.mp4", manifest)
        self.assertIn("non jouée automatiquement", manifest)

    def test_branding_readme_does_not_require_nonexistent_separate_audio_files(self):
        readme = (ROOT / "branding/README.md").read_text(encoding="utf-8")
        self.assertIn("pistes audio intégrées", readme)
        self.assertIn("sons", readme)

    def test_private_cosign_key_is_ignored_but_public_key_is_trackable(self):
        source = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("/cosign.key", source)
        self.assertIn("/cosign.key.*", source)
        self.assertNotIn("/cosign.pub", source)


    def test_recipe_checks_validate_and_decode_all_branding_video_audio(self):
        source = (ROOT / ".github/workflows/recipe-checks.yml").read_text(encoding="utf-8")
        self.assertIn("Validate branding video and audio streams", source)
        self.assertIn("ffprobe -v error -select_streams v:0", source)
        self.assertIn("ffprobe -v error -select_streams a:0", source)
        self.assertIn('ffmpeg -v error -i "${video}" -f null -', source)
        for path in (
            "branding/animations/desktop-intro.mov",
            "branding/animations/gaming-intro.mp4",
            "branding/animations/gaming-roar-reference.mp4",
        ):
            with self.subTest(path=path):
                self.assertIn(path, source)


if __name__ == "__main__":
    unittest.main()
