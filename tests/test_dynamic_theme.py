"""Regression tests for freely selected LEOS accent colors."""

import json
import tempfile
import unittest
from pathlib import Path

from leos_core.settings import SettingsStore
from desktop.themes import DEFAULT_COLOR_A, DEFAULT_COLOR_B, SOURCE_COLOR_A, SOURCE_COLOR_B, normalize_color, palette_for_colors, validate_palette


class DynamicThemeTests(unittest.TestCase):
    def test_unconfigured_preview_is_neutral_not_the_historical_source_gradient(self):
        self.assertNotEqual(DEFAULT_COLOR_A, SOURCE_COLOR_A)
        self.assertNotEqual(DEFAULT_COLOR_B, SOURCE_COLOR_B)
        for color in (DEFAULT_COLOR_A, DEFAULT_COLOR_B):
            self.assertEqual(color[1:3], color[3:5])
            self.assertEqual(color[3:5], color[5:7])

    def test_gaming_uses_selected_accents_and_shared_neutral_surfaces(self):
        root = Path(__file__).resolve().parents[1]
        qml = (root / "gaming" / "qml" / "Main.qml").read_text(encoding="utf-8")
        self.assertIn("color: window.accentA; opacity: 0.075", qml)
        self.assertIn("color: window.accentB; opacity: 0.065", qml)
        for legacy in ('#102331', '#2a1232', '#123847', '#17313d'):
            self.assertNotIn(legacy, qml)
        self.assertIn("window.themeColors.surface_elevated", qml)
        self.assertIn("window.themeColors.border", qml)

    def test_selected_endpoints_are_never_replaced_for_low_contrast(self):
        palette = palette_for_colors("#111111", "#111111")
        self.assertEqual(palette["accent_primary"], "#111111")
        self.assertEqual(palette["accent_secondary"], "#111111")
        self.assertEqual(palette["accent_primary_text"], palette["text"])
        self.assertEqual(palette["accent_secondary_text"], palette["text"])
        self.assertTrue(validate_palette(palette))

    def test_distinct_user_colors_remain_exact_palette_endpoints(self):
        palette = palette_for_colors("#FF8800", "#0055CC")
        self.assertEqual(palette["accent_primary"], "#FF8800")
        self.assertEqual(palette["accent_secondary"], "#0055CC")
        self.assertTrue(validate_palette(palette))

    def test_legacy_unconfigured_settings_migrate_to_neutral_preview(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            path.write_text(json.dumps({
                "theme_color_a": "#00D9FF",
                "theme_color_b": "#E33BFF",
                "theme_colors_configured": False,
            }), encoding="utf-8")
            settings = SettingsStore(path=path)
            self.assertEqual(
                settings.snapshot(("theme_color_a", "theme_color_b")),
                (DEFAULT_COLOR_A, DEFAULT_COLOR_B),
            )

    def test_hex_colors_are_trimmed_and_normalized(self):
        self.assertEqual(normalize_color(" #ab12EF "), "#AB12EF")

    def test_invalid_hex_values_are_rejected(self):
        for value in ("cyan", "#123", "#GG0000", "#11223344", ""):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    normalize_color(value)


if __name__ == "__main__":
    unittest.main()
