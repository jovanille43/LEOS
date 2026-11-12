"""Structural checks for the LEOS Aurorae KWin window decoration."""
import configparser
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "aurorae" / "leos"
SVG_NS = "{http://www.w3.org/2000/svg}"


class AuroraeWindowDecorationTests(unittest.TestCase):
    def test_metadata_and_config_names_match_theme_id(self):
        metadata = configparser.ConfigParser(interpolation=None)
        metadata.read(THEME / "metadata.desktop", encoding="utf-8")
        self.assertIn("Desktop Entry", metadata)
        entry = metadata["Desktop Entry"]
        self.assertEqual(entry["X-KDE-PluginInfo-Name"], "leos")
        self.assertEqual(entry["Name"], "LEOS")
        self.assertTrue(entry["X-KDE-PluginInfo-Version"])
        self.assertTrue(entry["X-KDE-PluginInfo-License"])
        self.assertTrue((THEME / "leosrc").is_file())

    def test_window_decoration_svg_has_active_and_inactive_frames(self):
        root = ET.parse(THEME / "decoration.svg").getroot()
        self.assertEqual(root.tag, f"{SVG_NS}svg")
        ids = {element.attrib.get("id") for element in root.iter()}
        parts = (
            "topleft", "top", "topright", "left", "center",
            "right", "bottomleft", "bottom", "bottomright",
        )
        for prefix in ("decoration", "decoration-inactive"):
            for part in parts:
                self.assertIn(f"{prefix}-{part}", ids)

    def test_each_window_button_has_required_active_center_and_all_states(self):
        states = (
            "active", "inactive", "hover", "pressed", "deactivated",
            "hover-inactive", "pressed-inactive", "deactivated-inactive",
        )
        for button in ("close", "minimize", "maximize", "restore"):
            with self.subTest(button=button):
                root = ET.parse(THEME / f"{button}.svg").getroot()
                self.assertEqual(root.tag, f"{SVG_NS}svg")
                ids = {element.attrib.get("id") for element in root.iter()}
                for state in states:
                    self.assertIn(f"{state}-center", ids)

    def test_configuration_uses_supported_aurorae_keys_and_button_layout(self):
        config = configparser.ConfigParser(interpolation=None)
        config.read(THEME / "leosrc", encoding="utf-8")
        self.assertIn("General", config)
        self.assertIn("Layout", config)
        general = config["General"]
        layout = config["Layout"]
        self.assertEqual(general["TitleAlignment"], "Center")
        self.assertEqual(general["RightButtons"], "IAX")
        self.assertEqual(general["LeftButtons"], "M")
        self.assertIn("PaddingTop", layout)
        self.assertIn("PaddingBottom", layout)
        self.assertIn("PaddingLeft", layout)
        self.assertIn("PaddingRight", layout)
        self.assertEqual(layout["TitleHeight"], "36")

    def test_bluebuild_installs_aurorae_runtime_and_theme(self):
        recipe = (ROOT / "recipes/common-modules.yml").read_text(encoding="utf-8")
        self.assertIn("- aurorae", recipe)
        self.assertIn("src: aurorae/leos", recipe)
        self.assertIn("dest: /usr/share/aurorae/themes/leos/", recipe)

    def test_theme_documentation_warns_about_real_session_validation(self):
        readme = (THEME / "README.md").read_text(encoding="utf-8")
        self.assertIn("real Bazzite KDE session", readme)
        self.assertIn("not selected automatically", readme)


if __name__ == "__main__":
    unittest.main()
