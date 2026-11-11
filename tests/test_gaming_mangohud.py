"""Tests for optional MangoHud command wrapping."""

import unittest
from unittest.mock import patch

from gaming.backend.mangohud import build_launch_command, find_mangohud


class MangoHudTests(unittest.TestCase):
    def test_disabled_overlay_keeps_command_unchanged(self):
        self.assertEqual(
            build_launch_command(["/games/example", "--fullscreen"], False, "/usr/bin/mangohud"),
            ["/games/example", "--fullscreen"],
        )

    def test_direct_game_command_is_wrapped_when_enabled(self):
        self.assertEqual(
            build_launch_command(["/games/example", "--fullscreen"], True, "/usr/bin/mangohud"),
            ["/usr/bin/mangohud", "/games/example", "--fullscreen"],
        )

    def test_uri_launcher_is_never_rewritten(self):
        self.assertEqual(
            build_launch_command(["steam://rungameid/123", "--ignored"], True, "/usr/bin/mangohud"),
            ["steam://rungameid/123", "--ignored"],
        )

    def test_missing_mangohud_keeps_original_command(self):
        self.assertEqual(
            build_launch_command(["/games/example"], True, ""),
            ["/games/example"],
        )

    @patch("gaming.backend.mangohud.shutil.which", return_value="/usr/bin/mangohud")
    def test_detects_host_executable(self, _which):
        self.assertEqual(find_mangohud(), "/usr/bin/mangohud")

    @patch("gaming.backend.mangohud.shutil.which", return_value=None)
    def test_reports_missing_host_executable(self, _which):
        self.assertEqual(find_mangohud(), "")


if __name__ == "__main__":
    unittest.main()
