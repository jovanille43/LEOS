"""Structural checks for the LEOS Plasma 6 desktop theme package."""
import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "plasma-theme" / "leos"
SVG_NS = "{http://www.w3.org/2000/svg}"


class PlasmaStylePackageTests(unittest.TestCase):
    def test_plasma6_metadata_is_valid_and_identifies_leos(self):
        metadata = json.loads((THEME / "metadata.json").read_text(encoding="utf-8"))
        plugin = metadata["KPlugin"]
        self.assertEqual(plugin["Id"], "leos")
        self.assertEqual(plugin["Name"], "LEOS")
        self.assertTrue(plugin["Version"])
        self.assertTrue(plugin["License"])

    def test_style_has_plasmarc_effect_settings(self):
        content = (THEME / "plasmarc").read_text(encoding="utf-8")
        self.assertIn("[ContrastEffect]", content)
        self.assertIn("[BlurBehindEffect]", content)

    def test_panel_dialog_and_widget_backgrounds_are_valid_svg(self):
        for relative in (
            "widgets/panel-background.svg",
            "dialogs/background.svg",
            "widgets/background.svg",
        ):
            with self.subTest(relative=relative):
                path = THEME / relative
                root = ET.parse(path).getroot()
                self.assertEqual(root.tag, f"{SVG_NS}svg")
                ids = {node.attrib.get("id") for node in root.iter()}
                for required in (
                    "topleft", "top", "topright", "left", "center",
                    "right", "bottomleft", "bottom", "bottomright",
                    "hint-stretch-borders",
                ):
                    self.assertIn(required, ids)

    def test_button_svg_contains_all_standard_nine_slice_states(self):
        root = ET.parse(THEME / "widgets" / "button.svg").getroot()
        ids = {node.attrib.get("id") for node in root.iter()}
        positions = (
            "topleft", "top", "topright", "left", "center",
            "right", "bottomleft", "bottom", "bottomright",
        )
        for state in ("normal", "hover", "pressed", "focus"):
            for position in positions:
                self.assertIn(f"{state}-{position}", ids)
        for state in ("toolbutton-hover", "toolbutton-pressed", "toolbutton-focus"):
            for position in positions:
                self.assertIn(f"{state}-{position}", ids)

    def test_theme_uses_official_kde_svg_element_names(self):
        # These are the standard nine-slice IDs consumed by Plasma's
        # background SVG renderer; unimplemented assets fall back to Breeze.
        panel = ET.parse(THEME / "widgets" / "panel-background.svg").getroot()
        ids = {node.attrib.get("id") for node in panel.iter()}
        self.assertTrue({"topleft", "top", "topright", "left", "center",
                         "right", "bottomleft", "bottom", "bottomright"} <= ids)


    def test_extended_plasma_assets_have_required_kde_ids(self):
        expected = {
            "widgets/tooltip.svg": {
                "topleft", "top", "topright", "left", "center", "right",
                "bottomleft", "bottom", "bottomright", "hint-stretch-borders",
            },
            "widgets/lineedit.svg": {
                f"{state}-{position}"
                for state in ("base", "hover", "focus")
                for position in (
                    "topleft", "top", "topright", "left", "center", "right",
                    "bottomleft", "bottom", "bottomright",
                )
            },
            "widgets/menubaritem.svg": {
                f"{state}-{position}"
                for state in ("normal", "hover", "pressed")
                for position in (
                    "topleft", "top", "topright", "left", "center", "right",
                    "bottomleft", "bottom", "bottomright",
                )
            },
            "widgets/viewitem.svg": {
                f"{state}-{position}"
                for state in ("normal", "hover", "selected", "selected+hover")
                for position in (
                    "topleft", "top", "topright", "left", "center", "right",
                    "bottomleft", "bottom", "bottomright",
                )
            },
            "widgets/arrows.svg": {
                "up-arrow", "right-arrow", "down-arrow", "left-arrow",
            },
        }
        for relative, required in expected.items():
            with self.subTest(relative=relative):
                root = ET.parse(THEME / relative).getroot()
                self.assertEqual(root.tag, f"{SVG_NS}svg")
                ids = {node.attrib.get("id") for node in root.iter()}
                self.assertTrue(required <= ids, required - ids)

    def test_package_does_not_claim_official_lion_asset_exists(self):
        self.assertFalse((THEME / "widgets" / "branding.svg").exists())
        readme = (THEME / "README.md").read_text(encoding="utf-8")
        self.assertIn("official LEOS lion artwork", readme)

    def test_plasma_surfaces_are_neutral_and_leave_user_accents_dynamic(self):
        accent_sources = {"#00D9FF", "#E33BFF", "#67DFF8", "#A28CFF", "#E66BD5"}
        for relative in (
            "widgets/background.svg", "widgets/panel-background.svg",
            "widgets/button.svg", "widgets/lineedit.svg", "widgets/menubaritem.svg",
            "widgets/tooltip.svg", "widgets/viewitem.svg", "dialogs/background.svg",
        ):
            with self.subTest(relative=relative):
                content = (THEME / relative).read_text(encoding="utf-8")
                colors = set(__import__("re").findall(r"#[0-9A-Fa-f]{6}", content))
                for color in colors - accent_sources:
                    self.assertEqual(color[1:3], color[3:5], f"{relative}: {color} is not neutral")
                    self.assertEqual(color[3:5], color[5:7], f"{relative}: {color} is not neutral")
        self.assertIn("#00D9FF", (THEME / "widgets" / "background.svg").read_text(encoding="utf-8"))
        self.assertIn("#E33BFF", (THEME / "widgets" / "background.svg").read_text(encoding="utf-8"))

    def test_bluebuild_recipe_installs_style_to_plasma_directory(self):
        recipe = (ROOT / "recipes/common-modules.yml").read_text(encoding="utf-8")
        self.assertIn("src: plasma-theme/leos", recipe)
        self.assertIn("dest: /usr/share/plasma/desktoptheme/leos/", recipe)


if __name__ == "__main__":
    unittest.main()
