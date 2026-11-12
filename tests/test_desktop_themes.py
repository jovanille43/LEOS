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


def _relative_luminance(color: str) -> float:
    channels = [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [
        value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
        for value in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast_ratio(foreground: str, background: str) -> float:
    first = _relative_luminance(foreground)
    second = _relative_luminance(background)
    return (max(first, second) + 0.05) / (min(first, second) + 0.05)


class DesktopThemeTests(unittest.TestCase):
    def test_all_builtin_palettes_have_complete_valid_tokens(self):
        self.assertEqual(
            set(THEME_PALETTES),
            {"leos-original", "light", "cyan", "magenta", "gaming"},
        )
        for palette in THEME_PALETTES.values():
            self.assertEqual(set(palette), REQUIRED_TOKENS)
            self.assertTrue(validate_palette(palette))

    def test_text_and_muted_text_meet_wcag_aa_on_all_palette_surfaces(self):
        surfaces = ("background", "surface", "surface_elevated")
        text_tokens = ("text", "muted_text")
        for theme_name, palette in THEME_PALETTES.items():
            for text_token in text_tokens:
                for surface_token in surfaces:
                    with self.subTest(
                        theme=theme_name,
                        text=text_token,
                        surface=surface_token,
                    ):
                        self.assertGreaterEqual(
                            _contrast_ratio(palette[text_token], palette[surface_token]),
                            4.5,
                        )

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

    def test_all_shared_combo_selectors_refresh_after_external_settings_changes(self):
        root = Path(__file__).resolve().parents[1]
        qml = (root / "control_center" / "qml" / "Main.qml").read_text(encoding="utf-8")
        for expression in (
            "themeBox.currentIndex =",
            "desktopLayoutBox.currentIndex =",
            "dockPositionBox.currentIndex =",
            "dockAlignmentBox.currentIndex =",
            "profileBox.currentIndex =",
            "notificationDurationBox.currentIndex =",
            "notificationPriorityBox.currentIndex =",
        ):
            with self.subTest(expression=expression):
                self.assertIn(expression, qml)


if __name__ == "__main__":
    unittest.main()
