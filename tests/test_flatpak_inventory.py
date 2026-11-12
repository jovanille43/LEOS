"""Tests for system/user Flatpak inventory parsing."""

import unittest

from shop.flatpak_inventory import (
    flatpak_uninstall_args,
    is_trusted_flathub_remote,
    trusted_flathub_remote_url,
    parse_flatpak_inventory,
)


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

    def test_uninstall_arguments_match_user_or_system_installation(self):
        self.assertEqual(
            flatpak_uninstall_args("org.example.App", "user"),
            ["uninstall", "--user", "--assumeyes", "org.example.App"],
        )
        self.assertEqual(
            flatpak_uninstall_args("org.example.App", "system"),
            ["uninstall", "--system", "--assumeyes", "org.example.App"],
        )

    def test_uninstall_arguments_reject_invalid_ids_and_scopes(self):
        with self.assertRaises(ValueError):
            flatpak_uninstall_args("bad-id", "user")
        with self.assertRaises(ValueError):
            flatpak_uninstall_args("org.example.App", "external")

    def test_accepts_canonical_flathub_repository_urls(self):
        self.assertTrue(
            is_trusted_flathub_remote(
                "Name URL\nflathub https://dl.flathub.org/repo/\n"
            )
        )
        self.assertTrue(
            is_trusted_flathub_remote(
                "Name URL\nflathub https://flathub.org/repo/flathub.flatpakrepo\n"
            )
        )
        self.assertEqual(
            trusted_flathub_remote_url(
                "Name URL\nflathub https://dl.flathub.org/repo/\n"
            ),
            "https://dl.flathub.org/repo/",
        )

    def test_rejects_untrusted_or_malformed_flathub_urls(self):
        for url in (
            "https://example.com/repo/",
            "http://dl.flathub.org/repo/",
            "https://dl.flathub.org.evil.example/repo/",
            "https://user@dl.flathub.org/repo/",
            "https://dl.flathub.org:8443/repo/",
            "https://dl.flathub.org/other/",
        ):
            with self.subTest(url=url):
                self.assertFalse(is_trusted_flathub_remote(f"flathub {url}"))
        self.assertFalse(is_trusted_flathub_remote(""))
        self.assertEqual(trusted_flathub_remote_url("flathub https://example.com/repo/"), "")

    def test_named_system_installations_are_system_scope(self):
        user, system = parse_flatpak_inventory(
            "Application Installation\norg.example.App external-games\n"
        )
        self.assertEqual(user, set())
        self.assertEqual(system, {"org.example.App"})


if __name__ == "__main__":
    unittest.main()
