"""Regression tests for freely selected LEOS accent colors."""

import unittest

from desktop.themes import normalize_color, palette_for_colors, validate_palette


class DynamicThemeTests(unittest.TestCase):
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

    def test_hex_colors_are_trimmed_and_normalized(self):
        self.assertEqual(normalize_color(" #ab12EF "), "#AB12EF")

    def test_invalid_hex_values_are_rejected(self):
        for value in ("cyan", "#123", "#GG0000", "#11223344", ""):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    normalize_color(value)


if __name__ == "__main__":
    unittest.main()
