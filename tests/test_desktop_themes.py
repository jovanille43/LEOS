"""Tests for LEOS interface theme palettes."""

import unittest
from pathlib import Path

from desktop.themes import (
    DEFAULT_THEME,
    REQUIRED_TOKENS,
    THEME_PALETTES,
    palette_for_theme,
    validate_palette,
)


class DesktopThemeTests(unittest.TestCase):
    def test_all_builtin_palettes_have_complete_valid_tokens(self):
        self.assertEqual(
            set(THEME_PALETTES),
            {"leos-original", "light", "cyan", "magenta", "gaming"},
        )
        for palette in THEME_PALETTES.values():
            self.assertEqual(set(palette), REQUIRED_TOKENS)
            self.assertTrue(validate_palette(palette))

    def test_unknown_theme_falls_back_to_leos_original(self):
        self.assertEqual(palette_for_theme("not-a-theme"), THEME_PALETTES[DEFAULT_THEME])

    def test_palette_is_a_defensive_copy(self):
        palette = palette_for_theme("leos-original")
        palette["background"] = "#FFFFFF"
        self.assertEqual(
            palette_for_theme("leos-original")["background"],
            THEME_PALETTES[DEFAULT_THEME]["background"],
        )

    def test_invalid_or_incomplete_custom_palette_is_rejected(self):
        self.assertFalse(validate_palette(None))
        self.assertFalse(validate_palette({"background": "#FFFFFF"}))
        invalid = palette_for_theme(DEFAULT_THEME)
        invalid["accent_primary"] = "cyan"
        self.assertFalse(validate_palette(invalid))

    def test_control_center_is_bound_to_live_theme_tokens(self):
        root = Path(__file__).resolve().parents[1]
        qml = (root / "control_center" / "qml" / "Main.qml").read_text(encoding="utf-8")
        controller = (root / "control_center" / "controller.py").read_text(encoding="utf-8")
        self.assertIn("property var themeColors: controlCenter.themePalette", qml)
        self.assertIn("color: themeColors.background", qml)
        self.assertIn("window.themeColors.accent_primary", qml)
        self.assertIn("property color cyan: themeColors.accent_primary", qml)
        self.assertIn("def themePalette(self)", controller)
        self.assertIn("palette_for_theme(self.theme)", controller)
        self.assertNotIn("#121720", qml)
        self.assertNotIn("#293342", qml)

    def test_theme_selector_refreshes_when_shared_settings_change(self):
        root = Path(__file__).resolve().parents[1]
        qml = (root / "control_center" / "qml" / "Main.qml").read_text(encoding="utf-8")
        self.assertIn("function onSettingsChanged()", qml)
        self.assertIn('const themes = ["leos-original", "light", "cyan", "magenta", "gaming"]', qml)
        self.assertIn("themeBox.currentIndex = Math.max(0, themes.indexOf(controlCenter.theme))", qml)


if __name__ == "__main__":
    unittest.main()
