"""Tests for safe freedesktop Desktop Entry Exec parsing."""

import unittest

from desktop.desktop_exec import parse_desktop_exec, resolve_desktop_working_directory


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

    def test_rejects_control_characters_and_oversized_exec_fields(self):
        from desktop.desktop_exec import MAX_EXEC_FIELD_LENGTH

        for command in ("app bad\\x00arg", "app bad\\x01arg", "app " + "x" * (MAX_EXEC_FIELD_LENGTH + 1)):
            with self.subTest(command=command[:30]), self.assertRaises(ValueError):
                parse_desktop_exec(command)

    def test_rejects_oversized_or_controlled_metadata(self):
        for kwargs in (
            {"name": "x" * 4097},
            {"icon": "icon\\x00bad"},
            {"desktop_file": "/tmp/app\\x01.desktop"},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                parse_desktop_exec("app", **kwargs)

    def test_rejects_excessive_argument_count(self):
        with self.assertRaises(ValueError):
            parse_desktop_exec("app " + " ".join(f"--arg{i}" for i in range(130)))

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

    def test_working_directory_defaults_to_user_home(self):
        from pathlib import Path
        self.assertEqual(
            resolve_desktop_working_directory("", Path.home()),
            str(Path.home().resolve()),
        )

    def test_working_directory_requires_absolute_existing_directory(self):
        from pathlib import Path
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(
                resolve_desktop_working_directory(directory),
                str(Path(directory).resolve()),
            )
            with self.assertRaises(ValueError):
                resolve_desktop_working_directory("relative/path")
            with self.assertRaises(ValueError):
                resolve_desktop_working_directory(str(Path(directory) / "missing"))
            file_path = Path(directory) / "not-a-directory"
            file_path.write_text("file", encoding="utf-8")
            with self.assertRaises(ValueError):
                resolve_desktop_working_directory(str(file_path))


if __name__ == "__main__":
    unittest.main()
