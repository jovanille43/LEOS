"""Tests for the shared A/B LEOS gradient palette."""

import unittest
from pathlib import Path

from desktop.themes import (
    DEFAULT_COLOR_A,
    DEFAULT_COLOR_B,
    DEFAULT_THEME,
    REQUIRED_TOKENS,
    THEME_PALETTES,
    normalize_color,
    palette_for_colors,
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
    def test_legacy_palettes_remain_valid_for_existing_kde_schemes(self):
        self.assertIn(DEFAULT_THEME, THEME_PALETTES)
        for palette in THEME_PALETTES.values():
            self.assertEqual(set(palette), REQUIRED_TOKENS)
            self.assertTrue(validate_palette(palette))

    def test_custom_colors_replace_only_the_two_gradient_endpoints(self):
        first = palette_for_colors("#00ffff", "#ff8800")
        second = palette_for_colors("#00AA44", "#AABBCC")
        self.assertEqual(first["accent_primary"], "#00FFFF")
        self.assertEqual(first["accent_secondary"], "#FF8800")
        self.assertEqual(second["accent_primary"], "#00AA44")
        self.assertEqual(second["accent_secondary"], "#AABBCC")
        for token in ("background", "surface", "surface_elevated", "border", "text", "muted_text"):
            self.assertEqual(first[token], second[token])

    def test_default_custom_palette_preserves_original_leos_gradient(self):
        palette = palette_for_colors()
        self.assertEqual(palette["accent_primary"], DEFAULT_COLOR_A)
        self.assertEqual(palette["accent_secondary"], DEFAULT_COLOR_B)

    def test_text_contrast_remains_wcag_aa_on_all_dark_and_light_surfaces(self):
        palettes = list(THEME_PALETTES.values()) + [
            palette_for_colors("#00FFFF", "#FF8800"),
            palette_for_colors("#FF00AA", "#00FF33"),
            palette_for_colors("#808080", "#FFFFFF"),
        ]
        for palette in palettes:
            for foreground in ("text", "muted_text"):
                for background in ("background", "surface", "surface_elevated"):
                    with self.subTest(foreground=foreground, background=background, palette=palette):
                        self.assertGreaterEqual(
                            _contrast_ratio(palette[foreground], palette[background]),
                            4.5,
                        )

    def test_color_normalization_and_validation(self):
        self.assertEqual(normalize_color(" #aBcDeF "), "#ABCDEF")
        for value in ("cyan", "#FFF", "#12345678", "123456", "", None, 123):
            with self.subTest(value=value), self.assertRaises(ValueError):
                normalize_color(value)

    def test_unknown_legacy_theme_falls_back_to_leos_original(self):
        self.assertEqual(palette_for_theme("not-a-theme"), THEME_PALETTES[DEFAULT_THEME])

    def test_palette_is_a_defensive_copy(self):
        palette = palette_for_theme(DEFAULT_THEME)
        palette["background"] = "#FFFFFF"
        self.assertEqual(
            palette_for_theme(DEFAULT_THEME)["background"],
            THEME_PALETTES[DEFAULT_THEME]["background"],
        )

    def test_invalid_or_incomplete_custom_palette_is_rejected(self):
        self.assertFalse(validate_palette(None))
        self.assertFalse(validate_palette({"background": "#FFFFFF"}))
        invalid = palette_for_colors()
        invalid["accent_primary"] = "cyan"
        self.assertFalse(validate_palette(invalid))

    def test_control_center_is_bound_to_live_custom_theme_tokens(self):
        root = Path(__file__).resolve().parents[1]
        qml = (root / "control_center" / "qml" / "Main.qml").read_text(encoding="utf-8")
        controller = (root / "control_center" / "controller.py").read_text(encoding="utf-8")
        self.assertIn("property var themeColors: controlCenter.themePalette", qml)
        self.assertIn("color: themeColors.background", qml)
        self.assertIn("property color cyan: themeColors.accent_primary", qml)
        self.assertIn("ColorDialog", qml)
        self.assertIn("controlCenter.setThemeColors", qml)
        self.assertIn("def themePalette(self)", controller)
        self.assertIn("palette_for_colors(self.themeColorA, self.themeColorB)", controller)
        self.assertNotIn("themeBox", qml)

    def test_control_center_exposes_two_editable_color_endpoints(self):
        root = Path(__file__).resolve().parents[1]
        qml = (root / "control_center" / "qml" / "Main.qml").read_text(encoding="utf-8")
        self.assertIn("id: themeColorAField", qml)
        self.assertIn("id: themeColorBField", qml)
        self.assertIn("GradientStop", qml)
        self.assertIn("themeColorAField.text = controlCenter.themeColorA", qml)
        self.assertIn("themeColorBField.text = controlCenter.themeColorB", qml)

    def test_all_leos_qml_applications_use_the_shared_gradient(self):
        root = Path(__file__).resolve().parents[1]
        qml_files = (
            "control_center/qml/Main.qml",
            "controller_center/qml/Main.qml",
            "desktop/qml/Menu.qml",
            "desktop/qml/Notifications.qml",
            "gaming/qml/Main.qml",
            "launcher/qml/ModeSelector.qml",
            "shop/qml/Main.qml",
        )
        for relative in qml_files:
            source = (root / relative).read_text(encoding="utf-8")
            with self.subTest(qml=relative):
                self.assertIn("themeColors.accent_primary", source)
                self.assertIn("themeColors.accent_secondary", source)
                self.assertIn("property color cyan: themeColors.accent_primary", source)
                self.assertIn("property color magenta: themeColors.accent_secondary", source)

    def test_all_desktop_qml_entry_points_inject_the_live_theme_controller(self):
        root = Path(__file__).resolve().parents[1]
        entry_points = (
            "desktop/menu_main.py",
            "desktop/notifications_main.py",
            "controller_center/main.py",
            "launcher/main.py",
            "shop/main.py",
        )
        for relative in entry_points:
            source = (root / relative).read_text(encoding="utf-8")
            with self.subTest(entry_point=relative):
                self.assertIn("ThemeController", source)
                self.assertIn('setContextProperty("leosTheme", theme)', source)

    def test_shared_desktop_theme_controller_refreshes_user_preferences(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "desktop" / "theme_controller.py").read_text(encoding="utf-8")
        self.assertIn("SettingsStore()", source)
        self.assertIn("theme_color_a", source)
        self.assertIn("theme_color_b", source)
        self.assertIn("def refresh(self)", source)
        self.assertIn("self.themeChanged.emit()", source)

    def test_gaming_uses_the_same_live_palette(self):
        root = Path(__file__).resolve().parents[1]
        qml = (root / "gaming" / "qml" / "Main.qml").read_text(encoding="utf-8")
        controller = (root / "gaming" / "backend" / "controller.py").read_text(encoding="utf-8")
        self.assertIn("property var themeColors: leos.themePalette", qml)
        self.assertIn("property color cyan: themeColors.accent_primary", qml)
        self.assertIn("property color magenta: themeColors.accent_secondary", qml)
        self.assertIn("def refreshSharedTheme(self)", controller)
        self.assertIn("palette_for_colors(", controller)


if __name__ == "__main__":
    unittest.main()
