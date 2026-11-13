"""Tests for safe recoloring of LEOS SVG and emblem assets."""

import unittest

from desktop.theme_assets import recolor_hex_color, recolor_svg_markup


class ThemeAssetTransformTests(unittest.TestCase):
    def setUp(self):
        self.primary = "#7B2CBF"
        self.secondary = "#2A9D8F"

    def test_historical_cyan_pixel_maps_to_exact_primary_swatch(self):
        self.assertEqual(
            recolor_hex_color("#00D9FF", self.primary, self.secondary),
            self.primary.lower(),
        )

    def test_historical_magenta_pixel_maps_to_exact_secondary_swatch(self):
        self.assertEqual(
            recolor_hex_color("#E33BFF", self.primary, self.secondary),
            self.secondary.lower(),
        )

    def test_metallic_neutral_black_and_white_are_preserved(self):
        for neutral in ("#8b8b8b", "#05070b", "#ffffff"):
            with self.subTest(color=neutral):
                self.assertEqual(
                    recolor_hex_color(neutral, self.primary, self.secondary),
                    neutral,
                )

    def test_svg_keeps_geometry_neutral_colors_and_both_accent_roles(self):
        source = (
            '<svg viewBox="0 0 10 10">'
            '<linearGradient id="g">'
            '<stop stop-color="#00d9ff"/>'
            '<stop stop-color="#e33bff"/>'
            '</linearGradient>'
            '<rect width="10" height="10" fill="#05070b"/>'
            '</svg>'
        )
        rendered = recolor_svg_markup(source, self.primary, self.secondary)
        self.assertIn('viewBox="0 0 10 10"', rendered)
        self.assertIn('stop-color="#7b2cbf"', rendered)
        self.assertIn('stop-color="#2a9d8f"', rendered)
        self.assertIn('fill="#05070b"', rendered)

    def test_invalid_accent_colors_are_rejected(self):
        with self.assertRaises(ValueError):
            recolor_hex_color("#00D9FF", "purple", self.secondary)
        with self.assertRaises(ValueError):
            recolor_svg_markup("<svg/>", self.primary, "#12345")


if __name__ == "__main__":
    unittest.main()
