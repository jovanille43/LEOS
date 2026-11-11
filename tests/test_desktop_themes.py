"""Tests for LEOS interface theme palettes."""

import unittest

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


if __name__ == "__main__":
    unittest.main()
