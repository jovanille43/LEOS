"""Tests for system/user Flatpak inventory parsing."""

import unittest

from shop.flatpak_inventory import parse_flatpak_inventory


class FlatpakInventoryTests(unittest.TestCase):
    def test_parses_flatpak_application_and_installation_columns(self):
        output = (
            "Application                 Installation\n"
            "com.brave.Browser           system\n"
            "org.gimp.GIMP               user\n"
            "org.videolan.VLC            system\n"
        )
        user, system = parse_flatpak_inventory(output)
        self.assertEqual(user, {"org.gimp.GIMP"})
        self.assertEqual(system, {"com.brave.Browser", "org.videolan.VLC"})

    def test_ignores_headers_invalid_rows_and_empty_lines(self):
        output = (
            "Application Installation\n"
            "\n"
            "not-an-app-id user\n"
            "org.example.Editor\n"
            "org.example.Valid user\n"
        )
        user, system = parse_flatpak_inventory(output)
        self.assertEqual(user, {"org.example.Valid"})
        self.assertEqual(system, set())

    def test_named_system_installations_are_system_scope(self):
        user, system = parse_flatpak_inventory(
            "Application Installation\norg.example.App external-games\n"
        )
        self.assertEqual(user, set())
        self.assertEqual(system, {"org.example.App"})


if __name__ == "__main__":
    unittest.main()
