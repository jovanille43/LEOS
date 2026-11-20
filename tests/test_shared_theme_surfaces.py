"""Structural regression checks for the shared A/B identity in all LEOS apps."""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SharedThemeSurfaceTests(unittest.TestCase):
    def test_every_leos_qml_surface_uses_the_shared_dynamic_palette(self):
        surfaces = {
            "launcher/qml/ModeSelector.qml": ("leosTheme.themePalette", "launcher/main.py"),
            "gaming/qml/Main.qml": ("leosTheme.themePalette", "gaming/main.py"),
            "control_center/qml/Main.qml": ("controlCenter.themePalette", "control_center/main.py"),
            "controller_center/qml/Main.qml": ("leosTheme.themePalette", "controller_center/main.py"),
            "desktop/qml/Menu.qml": ("leosTheme.themePalette", "desktop/menu_main.py"),
            "desktop/qml/Notifications.qml": ("leosTheme.themePalette", "desktop/notifications_main.py"),
            "shop/qml/Main.qml": ("leosTheme.themePalette", "shop/main.py"),
        }
        for qml_path, (binding, main_path) in surfaces.items():
            with self.subTest(surface=qml_path):
                qml = (ROOT / qml_path).read_text(encoding="utf-8")
                main = (ROOT / main_path).read_text(encoding="utf-8")
                self.assertIn(binding, qml)
                self.assertIn('setContextProperty("leosTheme", theme)', main)

    def test_no_qml_surface_reintroduces_the_legacy_fixed_accent_pair(self):
        for path in (
            "launcher/qml/ModeSelector.qml",
            "gaming/qml/Main.qml",
            "control_center/qml/Main.qml",
            "controller_center/qml/Main.qml",
            "desktop/qml/Menu.qml",
            "desktop/qml/Notifications.qml",
            "shop/qml/Main.qml",
        ):
            qml = (ROOT / path).read_text(encoding="utf-8").lower()
            with self.subTest(surface=path):
                self.assertNotIn("#00d9ff", qml)
                self.assertNotIn("#e33bff", qml)

    def test_menu_and_control_center_previews_use_generated_branding_urls(self):
        menu = (ROOT / "desktop/qml/Menu.qml").read_text(encoding="utf-8")
        control_center = (ROOT / "control_center/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn("leosTheme.desktopLogoUrl", menu)
        self.assertIn("leosTheme.desktopWallpaperUrl", control_center)
        self.assertIn("leosTheme.gamingWallpaperUrl", control_center)


if __name__ == "__main__":
    unittest.main()
