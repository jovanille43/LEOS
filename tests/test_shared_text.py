"""Tests for shared LEOS text normalization."""

import unittest

from leos_core.text import normalize_search_text


class SharedTextTests(unittest.TestCase):
    def test_search_is_case_and_accent_insensitive(self):
        self.assertEqual(normalize_search_text("CAFÉ"), "cafe")

    def test_search_collapses_repeated_whitespace(self):
        self.assertEqual(normalize_search_text("  Leos   Gaming  "), "leos gaming")

    def test_search_uses_compatibility_normalization(self):
        self.assertEqual(normalize_search_text("ＡＢＣ"), "abc")

    def test_non_string_values_are_safe(self):
        self.assertEqual(normalize_search_text(None), "")
        self.assertEqual(normalize_search_text(123), "")


if __name__ == "__main__":
    unittest.main()
