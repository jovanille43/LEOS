"""Checks for the declarative LEOS desktop defaults."""

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DesktopDefaultsTests(unittest.TestCase):
    def test_desktop_foundation_matches_the_neutral_graphite_runtime_palette(self):
        defaults = json.loads(
            (ROOT / "files/config/desktop-defaults.json").read_text(encoding="utf-8")
        )
        appearance = defaults["appearance"]
        expected = {
            "background": "#0B0B0B",
            "surface": "#151515",
            "surface_elevated": "#202020",
            "border": "#3A3A3A",
            "text": "#F5F5F5",
            "muted_text": "#A6A6A6",
        }
        for key, value in expected.items():
            self.assertEqual(appearance[key], value)
        for key in ("background", "surface", "surface_elevated", "border"):
            value = appearance[key]
            self.assertEqual(value[1:3], value[3:5])
            self.assertEqual(value[3:5], value[5:7])

    def test_declared_dock_favourites_use_real_desktop_file_ids_and_keep_mode_switch(self):
        defaults = json.loads(
            (ROOT / "files/config/desktop-defaults.json").read_text(encoding="utf-8")
        )
        pinned = defaults["desktop"]["dock"]["pinned_applications"]
        self.assertEqual(
            pinned,
            [
                "leos-menu.desktop",
                "leos-mode-selector.desktop",
                "org.kde.dolphin.desktop",
                "firefox.desktop",
                "steam.desktop",
                "leos-control-center.desktop",
            ],
        )
        self.assertTrue(all(item.endswith(".desktop") for item in pinned))


if __name__ == "__main__":
    unittest.main()
