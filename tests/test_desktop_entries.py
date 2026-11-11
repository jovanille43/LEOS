"""Tests for pure Desktop Entry visibility and localization helpers."""

import unittest

from desktop.desktop_entries import desktop_entry_is_visible, localized_desktop_value


class DesktopEntriesTests(unittest.TestCase):
    def test_localized_value_prefers_country_then_language(self):
        values = {
            "Name": "Generic name",
            "Name[fr]": "Nom français",
            "Name[fr_FR]": "Nom français France",
        }
        self.assertEqual(localized_desktop_value(values, "Name", "fr_FR"), "Nom français France")
        self.assertEqual(localized_desktop_value(values, "Name", "fr_CA"), "Nom français")
        self.assertEqual(localized_desktop_value(values, "Name", "C"), "Generic name")

    def test_localized_value_ignores_empty_translation(self):
        values = {"Comment": "Generic comment", "Comment[fr_FR]": "   "}
        self.assertEqual(localized_desktop_value(values, "Comment", "fr_FR"), "Generic comment")

    def test_only_show_in_requires_an_intersecting_desktop(self):
        self.assertTrue(desktop_entry_is_visible(
            {"OnlyShowIn": "KDE;GNOME;"}, {"KDE", "Plasma"}
        ))
        self.assertFalse(desktop_entry_is_visible(
            {"OnlyShowIn": "GNOME;"}, {"KDE", "Plasma"}
        ))

    def test_not_show_in_hides_matching_desktop(self):
        self.assertFalse(desktop_entry_is_visible(
            {"NotShowIn": "KDE;"}, {"KDE", "Plasma"}
        ))
        self.assertTrue(desktop_entry_is_visible(
            {"NotShowIn": "GNOME;"}, {"KDE", "Plasma"}
        ))

    def test_hidden_and_nodisplay_entries_are_not_visible(self):
        self.assertFalse(desktop_entry_is_visible({"Hidden": "true"}, {"KDE"}))
        self.assertFalse(desktop_entry_is_visible({"NoDisplay": "true"}, {"KDE"}))
        self.assertTrue(desktop_entry_is_visible({}, {"KDE"}))


if __name__ == "__main__":
    unittest.main()
