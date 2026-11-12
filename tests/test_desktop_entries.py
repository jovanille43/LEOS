"""Tests for pure Desktop Entry visibility and localization helpers."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from desktop.desktop_entries import (
    desktop_entry_is_visible, filter_desktop_applications, localized_desktop_value,
)


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

    def test_favourites_filter_preserves_the_saved_pin_order(self):
        items = [
            {"desktopId": "alpha.desktop", "name": "Alpha", "category": "Utility", "description": ""},
            {"desktopId": "beta.desktop", "name": "Beta", "category": "Internet", "description": ""},
            {"desktopId": "gamma.desktop", "name": "Gamma", "category": "Utility", "description": ""},
        ]
        result = filter_desktop_applications(
            items, "Favoris", ["gamma.desktop", "alpha.desktop"]
        )
        self.assertEqual(
            [item["desktopId"] for item in result],
            ["gamma.desktop", "alpha.desktop"],
        )

    def test_application_filter_supports_category_and_accent_insensitive_search(self):
        items = [
            {"desktopId": "cafe.desktop", "name": "Café Manager", "category": "Utility", "description": "Gestion"},
            {"desktopId": "browser.desktop", "name": "Navigateur", "category": "Internet", "description": "Web"},
        ]
        self.assertEqual(
            [item["desktopId"] for item in filter_desktop_applications(
                items, "Tout", [], "CAFE   manager"
            )],
            ["cafe.desktop"],
        )
        self.assertEqual(
            [item["desktopId"] for item in filter_desktop_applications(
                items, "Internet", [], ""
            )],
            ["browser.desktop"],
        )

    def test_favourites_filter_applies_search_without_reordering_matches(self):
        items = [
            {"desktopId": "alpha.desktop", "name": "Alpha Café", "category": "Utility", "description": ""},
            {"desktopId": "beta.desktop", "name": "Beta", "category": "Utility", "description": ""},
        ]
        result = filter_desktop_applications(
            items, "Favoris", ["beta.desktop", "alpha.desktop"], "cafe"
        )
        self.assertEqual([item["desktopId"] for item in result], ["alpha.desktop"])

    def test_recent_applications_filter_preserves_mru_order(self):
        items = [
            {"desktopId": "alpha.desktop", "name": "Alpha", "category": "Utility", "description": ""},
            {"desktopId": "beta.desktop", "name": "Beta", "category": "Internet", "description": ""},
            {"desktopId": "gamma.desktop", "name": "Gamma", "category": "Utility", "description": ""},
        ]
        result = filter_desktop_applications(
            items, "Récemment utilisées", [], "", ["gamma.desktop", "alpha.desktop"]
        )
        self.assertEqual(
            [item["desktopId"] for item in result],
            ["gamma.desktop", "alpha.desktop"],
        )

    def test_recent_applications_filter_supports_search(self):
        items = [
            {"desktopId": "alpha.desktop", "name": "Café", "category": "Utility", "description": ""},
            {"desktopId": "beta.desktop", "name": "Beta", "category": "Internet", "description": ""},
        ]
        result = filter_desktop_applications(
            items, "Récemment utilisées", [], "cafe", ["beta.desktop", "alpha.desktop"]
        )
        self.assertEqual([item["desktopId"] for item in result], ["alpha.desktop"])

    def test_application_directories_follow_xdg_data_dirs_and_user_override(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            user_data = root / "my-user-data"
            system_one = root / "system-one"
            system_two = root / "system-two"
            with patch.dict(os.environ, {
                "HOME": str(root / "home"),
                "XDG_DATA_HOME": str(user_data),
                "XDG_DATA_DIRS": f"{system_one}{os.pathsep}{system_two}",
            }, clear=True):
                directories = desktop_application_dirs()
            self.assertEqual(
                directories,
                (
                    system_one / "applications",
                    system_two / "applications",
                    user_data / "applications",
                ),
            )

    def test_application_directories_ignore_relative_xdg_data_dirs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.dict(os.environ, {
                "HOME": str(root / "home"),
                "XDG_DATA_HOME": str(root / "user-data"),
                "XDG_DATA_DIRS": f"relative{os.pathsep}{root / 'system'}",
            }, clear=True):
                directories = desktop_application_dirs()
            self.assertEqual(
                directories,
                (root / "system" / "applications", root / "user-data" / "applications"),
            )

    def test_application_directories_use_freedesktop_defaults(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.dict(os.environ, {"HOME": str(root)}, clear=True):
                directories = desktop_application_dirs()
            self.assertEqual(
                directories,
                (
                    Path("/usr/local/share/applications"),
                    Path("/usr/share/applications"),
                    root / ".local" / "share" / "applications",
                ),
            )


if __name__ == "__main__":
    unittest.main()
