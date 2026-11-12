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

    def test_manual_image_build_runs_python_suite_before_publishing(self):
        source = (ROOT / ".github/workflows/build.yml").read_text(encoding="utf-8")
        self.assertIn("Run LEOS Python test suite", source)
        self.assertIn('python -m unittest discover -s tests -v', source)
        self.assertIn("python-version: \"3.12\"", source)
        self.assertLess(
            source.index("Run LEOS Python test suite"),
            source.index("Build and publish LEOS"),
        )

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

    def test_image_workflow_validates_wallpaper_geometry_and_emblem_links(self):
        source = (ROOT / ".github/workflows/build.yml").read_text(encoding="utf-8")
        self.assertIn("Validate wallpaper SVG assets and official emblem links", source)
        self.assertIn('root.attrib.get("viewBox") != "0 0 3840 2160"', source)
        self.assertIn('images[0].attrib.get("href") != emblem', source)
        self.assertIn('images[0].attrib.get(xlink_href) != emblem', source)
        self.assertIn('Path("branding/wallpapers/desktop-leos.svg"): "../desktop-logo.jpeg"', source)
        self.assertIn('Path("branding/wallpapers/gaming-leos.svg"): "../gaming-logo.jpeg"', source)
        self.assertIn("target = (wallpaper.parent / emblem).resolve()", source)
        self.assertIn("if not target.is_file()", source)

    def test_recipe_ci_checks_deployed_branding_hashes_before_reporting(self):
        source = (ROOT / ".github/workflows/recipe-checks.yml").read_text(encoding="utf-8")
        self.assertIn("sha256sum --check branding/DEPLOYED_SHA256SUMS", source)
        self.assertLess(
            source.index("Verify deployed branding SHA-256 fingerprints"),
            source.index("Report deployed branding SHA-256 fingerprints"),
        )

    def test_image_workflow_checks_deployed_branding_hashes(self):
        source = (ROOT / ".github/workflows/build.yml").read_text(encoding="utf-8")
        self.assertIn("sha256sum --check branding/DEPLOYED_SHA256SUMS", source)
        deployed = (ROOT / "branding/DEPLOYED_SHA256SUMS").read_text(encoding="utf-8")
        entries = [
            line for line in deployed.splitlines()
            if line and not line.startswith("#")
        ]
        self.assertEqual(len(entries), 8)
        for line in entries:
            self.assertRegex(line, r"^[0-9a-f]{64}  branding/.+")

    def test_deployed_checksum_manifest_matches_build_asset_allowlist(self):
        source = (ROOT / ".github/workflows/build.yml").read_text(encoding="utf-8")
        manifest = (ROOT / "branding/DEPLOYED_SHA256SUMS").read_text(encoding="utf-8")
        start = source.index("required_assets=(")
        end = source.index(")", start)
        required = set(re.findall(r"branding/[A-Za-z0-9_./-]+", source[start:end]))
        recorded = {
            line.split("  ", 1)[1]
            for line in manifest.splitlines()
            if line and not line.startswith("#")
        }
        expected = {
            "branding/desktop-logo.jpeg",
            "branding/gaming-logo.jpeg",
            "branding/reference-comparison.jpeg",
            "branding/animations/desktop-intro.mov",
            "branding/animations/gaming-intro.mp4",
            "branding/animations/gaming-roar-reference.mp4",
            "branding/wallpapers/desktop-leos.svg",
            "branding/wallpapers/gaming-leos.svg",
        }
        self.assertEqual(required, expected)
        self.assertEqual(recorded, expected)
        self.assertLess(
            source.index("sha256sum --check branding/DEPLOYED_SHA256SUMS"),
            source.index("Check signing prerequisites"),
        )

    def test_manual_image_build_lints_qml_before_signature_and_publish(self):
        source = (ROOT / ".github/workflows/build.yml").read_text(encoding="utf-8")
        self.assertIn("Lint Qt Quick and QML sources", source)
        self.assertIn("qt6-qtdeclarative-devel qt6-qtmultimedia qt6-qtsvg", source)
        self.assertIn('qmllint-qt6 "${file}"', source)
        self.assertLess(
            source.index("Lint Qt Quick and QML sources"),
            source.index("Check signing prerequisites"),
        )
        self.assertLess(
            source.index("Lint Qt Quick and QML sources"),
            source.index("Build and publish LEOS"),
        )

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
        self.assertIn("recipe: recipe-nvidia.yml", source)
        self.assertIn("recipe: recipe-nvidia-open.yml", source)
        self.assertTrue((ROOT / "recipes/recipe.yml").is_file())
        self.assertTrue((ROOT / "recipes/recipe-nvidia.yml").is_file())
        self.assertTrue((ROOT / "recipes/recipe-nvidia-open.yml").is_file())
        self.assertTrue((ROOT / "recipes/common-modules.yml").is_file())
        self.assertFalse((ROOT / "recipes/recipes/recipe.yml").exists())

    def test_standard_and_nvidia_recipes_share_the_same_modules(self):
        standard = (ROOT / "recipes/recipe.yml").read_text(encoding="utf-8")
        nvidia = (ROOT / "recipes/recipe-nvidia.yml").read_text(encoding="utf-8")
        modern_nvidia = (ROOT / "recipes/recipe-nvidia-open.yml").read_text(encoding="utf-8")
        common = (ROOT / "recipes/common-modules.yml").read_text(encoding="utf-8")
        self.assertIn("name: leos", standard)
        self.assertIn("base-image: ghcr.io/ublue-os/bazzite", standard)
        self.assertIn("name: leos-nvidia", nvidia)
        self.assertIn("base-image: ghcr.io/ublue-os/bazzite-nvidia", nvidia)
        self.assertIn("name: leos-nvidia-open", modern_nvidia)
        self.assertIn("base-image: ghcr.io/ublue-os/bazzite-nvidia-open", modern_nvidia)
        self.assertEqual(standard.count("from-file: common-modules.yml"), 1)
        self.assertEqual(nvidia.count("from-file: common-modules.yml"), 1)
        self.assertEqual(modern_nvidia.count("from-file: common-modules.yml"), 1)
        self.assertIn("type: signing", common)
        self.assertIn("src: branding", common)

    def test_branding_assets_are_copied_into_the_runtime_share_tree(self):
        recipe = (ROOT / "recipes/common-modules.yml").read_text(encoding="utf-8")
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
        recipe = (ROOT / "recipes/common-modules.yml").read_text(encoding="utf-8")
        self.assertIn("qt6-qtmultimedia", recipe)

    def test_recipe_installs_vulkan_tools_for_hardware_preflight(self):
        recipe = (ROOT / "recipes/common-modules.yml").read_text(encoding="utf-8")
        self.assertIn("vulkan-tools", recipe)

    def test_recipe_installs_qt_svg_for_wallpaper_previews(self):
        recipe = (ROOT / "recipes/common-modules.yml").read_text(encoding="utf-8")
        self.assertIn("qt6-qtsvg", recipe)
        control_center = (ROOT / "control_center/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn('source: "../../branding/wallpapers/desktop-leos.svg"', control_center)
        self.assertIn('source: "../../branding/wallpapers/gaming-leos.svg"', control_center)

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


    def test_recipe_ci_validates_and_generates_all_hardware_variants(self):
        source = (ROOT / ".github/workflows/recipe-checks.yml").read_text(encoding="utf-8")
        for recipe in ("recipe.yml", "recipe-nvidia.yml", "recipe-nvidia-open.yml"):
            with self.subTest(recipe=recipe):
                self.assertIn(f"bluebuild validate recipes/{recipe}", source)
                self.assertIn(recipe, source[source.index("for recipe in"):source.index("output=")])

    def test_iso_workflow_is_manual_and_selects_all_hardware_variants(self):
        source = (ROOT / ".github/workflows/iso.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", source)
        self.assertIn("type: choice", source)
        for variant in ("standard", "nvidia-legacy", "nvidia-modern"):
            with self.subTest(variant=variant):
                self.assertIn(variant, source)
        self.assertIn('standard) image_name="leos"', source)
        self.assertIn('nvidia-legacy) image_name="leos-nvidia"', source)
        self.assertIn('nvidia-modern) image_name="leos-nvidia-open"', source)

    def test_iso_workflow_uses_published_image_and_generates_checksum(self):
        source = (ROOT / ".github/workflows/iso.yml").read_text(encoding="utf-8")
        self.assertIn("generate-iso --iso-name", source)
        self.assertIn('image "$IMAGE_REF"', source)
        self.assertIn('sha256sum "$ISO_NAME"', source)
        self.assertIn("actions/upload-artifact@v4", source)
        self.assertIn("packages: read", source)
        self.assertIn("retention-days: 14", source)

    def test_iso_workflow_validates_image_tag_before_building(self):
        source = (ROOT / ".github/workflows/iso.yml").read_text(encoding="utf-8")
        self.assertIn('if [[ ! "$IMAGE_TAG" =~ ^[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$ ]]', source)
        self.assertIn("Unknown image variant.", source)
        self.assertIn("Authenticate to GitHub Container Registry", source)
        self.assertIn("sigstore/cosign-installer@v3", source)
        self.assertIn("cosign verify --key cosign.pub", source)
        self.assertIn("Verify published LEOS image signature", source)

    def test_recipe_ci_lints_all_qml_with_qt6_tooling(self):
        source = (ROOT / ".github/workflows/recipe-checks.yml").read_text(encoding="utf-8")
        self.assertIn("Lint Qt Quick and QML sources", source)
        self.assertIn("fedora:45", source)
        self.assertIn("qt6-qtdeclarative-devel", source)
        self.assertIn("qt6-qtmultimedia", source)
        self.assertIn("qt6-qtsvg", source)
        self.assertIn('find launcher gaming control_center controller_center desktop shop -type f -name "*.qml"', source)
        self.assertIn('qmllint-qt6 "${file}"', source)
        self.assertIn('if [[ "${#qml_files[@]}" -eq 0 ]]', source)

    def test_qml_layout_warnings_are_prevented_in_known_areas(self):
        selector = (ROOT / "launcher/qml/ModeSelector.qml").read_text(encoding="utf-8")
        gaming = (ROOT / "gaming/qml/Main.qml").read_text(encoding="utf-8")
        controllers = (ROOT / "controller_center/qml/Main.qml").read_text(encoding="utf-8")
        shop = (ROOT / "shop/qml/Main.qml").read_text(encoding="utf-8")

        self.assertIn("id: modeSelectorContent", selector)
        self.assertIn("focus: true", selector)
        self.assertNotIn("    focus: true", selector.split("ApplicationWindow {", 1)[1].split("id: modeSelectorContent", 1)[0])
        self.assertIn('Layout.preferredWidth: 1; Layout.fillHeight: true; color: "#374253"', gaming)
        self.assertIn("Layout.preferredWidth: 54", controllers)
        self.assertIn("Layout.preferredHeight: 54", controllers)
        self.assertIn("Layout.preferredHeight: 1", controllers)
        self.assertIn("Layout.preferredWidth: 42", shop)
        self.assertIn("Layout.preferredHeight: 42", shop)

    def test_qml_button_content_items_use_typed_button_ids(self):
        selector = (ROOT / "launcher/qml/ModeSelector.qml").read_text(encoding="utf-8")
        gaming = (ROOT / "gaming/qml/Main.qml").read_text(encoding="utf-8")
        shop = (ROOT / "shop/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn("text: continueGamingButton.text", selector)
        self.assertIn("text: powerProfileButton.text", gaming)
        self.assertIn("text: categoryButton.text", gaming)
        self.assertIn("text: addGameButton.text", gaming)
        self.assertIn("text: favoriteGameButton.text", gaming)
        self.assertIn("launchSelectedGameButton.enabled", gaming)
        self.assertIn("text: launchSelectedGameButton.text", gaming)
        self.assertIn("text: confirmPowerProfileButton.text", gaming)
        self.assertIn("text: installRemoveButton.text", shop)

    def test_recipe_ci_reports_hashes_for_all_deployed_branding_assets(self):
        source = (ROOT / ".github/workflows/recipe-checks.yml").read_text(encoding="utf-8")
        self.assertIn("Report deployed branding SHA-256 fingerprints", source)
        self.assertIn("sha256sum", source)
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
        start = source.index("Report deployed branding SHA-256 fingerprints")
        end = source.index("Validate wallpaper SVG", start)
        block = source[start:end]
        for path in expected:
            with self.subTest(path=path):
                self.assertIn(path, block)

    def test_recipe_ci_validates_both_wallpaper_svg_emblem_links(self):
        source = (ROOT / ".github/workflows/recipe-checks.yml").read_text(encoding="utf-8")
        self.assertIn("Validate wallpaper SVG assets and official emblem links", source)
        self.assertIn('root.attrib.get("viewBox") != "0 0 3840 2160"', source)
        self.assertIn('images[0].attrib.get(xlink_href) != emblem', source)
        self.assertIn('Path("branding/wallpapers/desktop-leos.svg"): "../desktop-logo.jpeg"', source)
        self.assertIn('Path("branding/wallpapers/gaming-leos.svg"): "../gaming-logo.jpeg"', source)
        self.assertIn("target = (wallpaper.parent / emblem).resolve()", source)
        self.assertIn("if not target.is_file()", source)
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
