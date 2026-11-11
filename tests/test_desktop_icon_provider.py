"""Tests for LEOS desktop application icon provider wiring."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class DesktopIconProviderTests(unittest.TestCase):
    def test_provider_uses_the_existing_kde_icon_theme_and_has_fallbacks(self):
        source = (ROOT / "desktop/icon_provider.py").read_text(encoding="utf-8")
        self.assertIn("QIcon.fromTheme(icon_name)", source)
        self.assertIn('QIcon.fromTheme("application-x-executable")', source)
        self.assertIn("QIcon(str(candidate))", source)
        self.assertNotIn("subprocess", source)
        self.assertNotIn("flatpak install", source.casefold())

    def test_image_provider_is_registered_before_qml_load(self):
        main = (ROOT / "desktop/menu_main.py").read_text(encoding="utf-8")
        self.assertLess(
            main.index('engine.addImageProvider("desktop-icons"'),
            main.index("engine.load("),
        )


if __name__ == "__main__":
    unittest.main()
