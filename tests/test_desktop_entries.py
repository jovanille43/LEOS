"""Tests for pure Desktop Entry visibility and localization helpers."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from desktop.desktop_entries import (
    desktop_application_dirs, desktop_entry_is_visible, desktop_file_id, desktop_entry_paths,
    filter_desktop_applications, localized_desktop_value,
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

    def test_higher_priority_hidden_entry_masks_lower_priority_application(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            system = root / "system" / "applications"
            user = root / "user" / "applications"
            system.mkdir(parents=True)
            user.mkdir(parents=True)
            system_entry = system / "example.desktop"
            user_entry = user / "example.desktop"
            system_entry.write_text(
                "[Desktop Entry]\\nType=Application\\nName=System App\\n",
                encoding="utf-8",
            )
            user_entry.write_text(
                "[Desktop Entry]\\nType=Application\\nHidden=true\\nName=Hidden App\\n",
                encoding="utf-8",
            )

            selected = desktop_entry_paths((system, user))
            self.assertEqual(selected, (user_entry,))

    def test_desktop_entry_paths_keep_distinct_ids_and_last_directory_wins(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            lower = root / "lower"
            higher = root / "higher"
            lower.mkdir()
            higher.mkdir()
            lower_shared = lower / "shared.desktop"
            higher_shared = higher / "shared.desktop"
            distinct = lower / "distinct.desktop"
            for path in (lower_shared, higher_shared, distinct):
                path.write_text("[Desktop Entry]\\n", encoding="utf-8")

            selected = desktop_entry_paths((lower, higher))
            by_name = {path.name: path for path in selected}
            self.assertEqual(by_name["shared.desktop"], higher_shared)
            self.assertEqual(by_name["distinct.desktop"], distinct)
            self.assertEqual(len(selected), 2)

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
                    system_two / "applications",
                    system_one / "applications",
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
                    Path("/usr/share/applications"),
                    Path("/usr/local/share/applications"),
                    root / ".local" / "share" / "applications",
                ),
            )

    def test_desktop_file_ids_flatten_nested_application_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            nested = root / "kde" / "utilities" / "viewer.desktop"
            nested.parent.mkdir(parents=True)
            nested.write_text("[Desktop Entry]", encoding="utf-8")
            self.assertEqual(desktop_file_id(nested, root), "kde-utilities-viewer.desktop")
            flat = root / "browser.desktop"
            flat.write_text("[Desktop Entry]", encoding="utf-8")
            self.assertEqual(desktop_file_id(flat, root), "browser.desktop")
            self.assertEqual(desktop_file_id(root / "missing.desktop", root / "other"), "")
            self.assertEqual(desktop_file_id(root / "not-a-desktop.txt", root), "")


if __name__ == "__main__":
    unittest.main()
