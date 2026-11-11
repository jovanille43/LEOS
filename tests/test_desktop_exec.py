"""Tests for safe freedesktop Desktop Entry Exec parsing."""

import unittest

from desktop.desktop_exec import parse_desktop_exec


class DesktopExecTests(unittest.TestCase):
    def test_expands_name_icon_and_desktop_file_codes(self):
        self.assertEqual(
            parse_desktop_exec(
                "player --label %c %i %k",
                name="Lecteur audio",
                icon="audio-player",
                desktop_file="/usr/share/applications/player.desktop",
            ),
            [
                "player", "--label", "Lecteur audio",
                "--icon", "audio-player",
                "/usr/share/applications/player.desktop",
            ],
        )

    def test_omits_each_file_and_url_placeholder_without_launch_targets(self):
        for code in ("%f", "%F", "%u", "%U"):
            with self.subTest(code=code):
                self.assertEqual(parse_desktop_exec("viewer " + code), ["viewer"])

    def test_rejects_more_than_one_file_or_url_placeholder(self):
        with self.assertRaises(ValueError):
            parse_desktop_exec("viewer %f %u")

    def test_omits_deprecated_field_codes(self):
        self.assertEqual(parse_desktop_exec("legacy %d %D %n %N %v %m"), ["legacy"])

    def test_expands_escaped_percent(self):
        self.assertEqual(
            parse_desktop_exec("app --progress=100%% %%x"),
            ["app", "--progress=100%", "%x"],
        )

    def test_rejects_unknown_and_misplaced_field_codes(self):
        for command in ("app %x", "app --file=%f"):
            with self.subTest(command=command):
                with self.assertRaises(ValueError):
                    parse_desktop_exec(command)

    def test_rejects_invalid_quoting(self):
        with self.assertRaises(ValueError):
            parse_desktop_exec('app "unclosed')

    def test_does_not_interpret_shell_metacharacters(self):
        self.assertEqual(
            parse_desktop_exec("app --title 'A; rm -rf /'"),
            ["app", "--title", "A; rm -rf /"],
        )

    def test_rejects_multiple_file_or_url_placeholders(self):
        with self.assertRaises(ValueError):
            parse_desktop_exec("viewer %f %u")

    def test_rejects_field_code_as_executable(self):
        with self.assertRaises(ValueError):
            parse_desktop_exec("%k --option")


if __name__ == "__main__":
    unittest.main()
