"""Static contracts for LEOS pre-login and Plasma visual identity assets."""

import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class LeosIdentityAssetTests(unittest.TestCase):
    def test_sddm_uses_official_desktop_mark_and_qt6(self):
        metadata = (ROOT / "branding/sddm/leos/metadata.desktop").read_text(encoding="utf-8")
        qml = (ROOT / "branding/sddm/leos/Main.qml").read_text(encoding="utf-8")
        self.assertIn("QtVersion=6", metadata)
        self.assertIn("file:///usr/share/leos/branding/desktop-logo.jpeg", qml)
        self.assertIn("sddm.login(", qml)
        self.assertIn("sessionModel", qml)
        self.assertNotIn("#00D9FF", qml)
        self.assertNotIn("#E33BFF", qml)

    def test_plymouth_theme_is_neutral_and_references_official_emblem_generator(self):
        theme = (ROOT / "branding/plymouth/leos/leos.plymouth").read_text(encoding="utf-8")
        script = (ROOT / "files/scripts/prepare-leos-plymouth.sh").read_text(encoding="utf-8")
        self.assertIn("ModuleName=two-step", theme)
        self.assertIn("BackgroundStartColor=0x090B10", theme)
        self.assertIn("ImageDir=/usr/share/plymouth/themes/leos", theme)
        self.assertIn("WatermarkHorizontalAlignment=.5", theme)
        self.assertIn("watermark.png", script)
        self.assertIn("desktop-logo.jpeg", script)
        self.assertIn("QImage", script)

    def test_plasma_splash_package_is_valid_and_neutral_before_user_colors(self):
        package = ROOT / "plasma-theme/look-and-feel/org.leos.desktop"
        manifest = json.loads((package / "manifest.json").read_text(encoding="utf-8"))
        qml = (package / "contents/splash/Splash.qml").read_text(encoding="utf-8")
        self.assertEqual(manifest["KPackageStructure"], "Plasma/LookAndFeel")
        self.assertEqual(manifest["KPlugin"]["Id"], "org.leos.desktop")
        self.assertIn("desktop-logo.jpeg", qml)
        self.assertIn("#090B10", qml)
        self.assertNotIn("#00D9FF", qml)
        self.assertNotIn("#E33BFF", qml)

    def test_cursor_svg_has_metadata_and_safe_breeze_fallback(self):
        metadata = json.loads(
            (ROOT / "icons/leos/cursors_scalable/default/metadata.json").read_text(encoding="utf-8")
        )
        ET.parse(ROOT / "icons/leos/cursors_scalable/default/default.svg")
        index = (ROOT / "icons/leos/index.theme").read_text(encoding="utf-8")
        self.assertEqual(metadata[0]["filename"], "default.svg")
        self.assertEqual(metadata[0]["nominal_size"], 32)
        self.assertIn("breeze_cursors", index)

    def test_recipe_installs_all_prelogin_themes_and_rebuilds_initramfs_last(self):
        recipe = (ROOT / "recipes/common-modules.yml").read_text(encoding="utf-8")
        self.assertIn("google-noto-sans-fonts", recipe)
        self.assertIn("plymouth-plugin-two-step", recipe)
        self.assertIn("branding/sddm", recipe)
        self.assertIn("plasma-theme/look-and-feel", recipe)
        self.assertIn("prepare-leos-plymouth.sh", recipe)
        self.assertIn("type: initramfs", recipe)
        self.assertLess(recipe.index("type: initramfs"), recipe.index("type: signing"))
        self.assertIn("Current=leos", (ROOT / "files/sddm/90-leos-theme.conf").read_text(encoding="utf-8"))

    def test_control_center_updates_and_restores_splash_and_cursor_with_ab_palette(self):
        controller = (ROOT / "control_center/controller.py").read_text(encoding="utf-8")
        qml = (ROOT / "control_center/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn("PlasmaVisualChromeManager", controller)
        self.assertIn("self.visualChrome.apply", controller)
        self.assertIn("self.visualChrome.restore_previous", controller)
        self.assertIn("écran de chargement", qml)
        self.assertIn("curseur", qml)

    def test_first_run_profile_activates_and_restores_splash_and_cursor_preferences(self):
        source = (ROOT / "desktop/first_run_appearance.py").read_text(encoding="utf-8")
        self.assertIn("PlasmaVisualChromeManager", source)
        self.assertIn("visual_chrome.apply", source)
        self.assertIn("visual_chrome.restore_previous", source)


if __name__ == "__main__":
    unittest.main()
