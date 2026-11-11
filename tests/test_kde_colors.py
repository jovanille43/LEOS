"""Tests for LEOS KDE Plasma color-scheme generation and application."""
import configparser
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from desktop.kde_colors import (
    KdeColorSchemeManager,
    MANAGED_BY,
    THEME_NAMES,
    build_colorscheme,
)


class FakeRunner:
    def __init__(self, returncode=0):
        self.returncode = returncode
        self.calls = []

    def __call__(self, args, **kwargs):
        self.calls.append((args, kwargs))
        return SimpleNamespace(returncode=self.returncode, stderr="fake failure")


class KdeColorSchemeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.data = root / "data"
        self.config = root / "config"
        self.state = root / "state"
        self.config.mkdir()
        (self.config / "kdeglobals").write_text(
            "[General]\nColorScheme=BreezeDark\n", encoding="utf-8"
        )
        self.runner = FakeRunner()
        self.manager = KdeColorSchemeManager(
            self.data, self.config, self.state,
            apply_executable="/usr/bin/plasma-apply-colorscheme",
            runner=self.runner,
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_builds_complete_kde_color_scheme_ini(self):
        content = build_colorscheme("leos-original")
        parser = configparser.ConfigParser(interpolation=None)
        parser.read_string(content)
        self.assertEqual(parser["General"]["ColorScheme"], "LEOS-leos-original")
        self.assertEqual(parser["General"]["Name"], "LEOS Original")
        self.assertEqual(parser["LEOS"]["ManagedBy"], MANAGED_BY)
        for group in (
            "Colors:Window", "Colors:View", "Colors:Button",
            "Colors:Selection", "Colors:Tooltip", "Colors:Complementary", "Colors:Header",
        ):
            self.assertIn("BackgroundNormal", parser[group])
            self.assertIn("ForegroundNormal", parser[group])
            self.assertIn("DecorationFocus", parser[group])

    def test_generates_all_five_palettes(self):
        for theme in THEME_NAMES:
            self.assertIn("[LEOS]", build_colorscheme(theme))

    def test_unknown_theme_is_rejected(self):
        with self.assertRaises(ValueError):
            build_colorscheme("../Breeze")

    def test_installs_scheme_to_user_xdg_data_directory(self):
        path = self.manager.install_scheme("leos-original")
        self.assertEqual(path, self.data / "color-schemes" / "LEOS-leos-original.colors")
        self.assertIn(MANAGED_BY, path.read_text(encoding="utf-8"))

    def test_install_is_idempotent(self):
        first = self.manager.install_scheme("cyan")
        second = self.manager.install_scheme("cyan")
        self.assertEqual(first, second)
        self.assertEqual(len(list((self.data / "color-schemes").glob("*.colors"))), 1)

    def test_existing_different_scheme_is_never_overwritten(self):
        directory = self.data / "color-schemes"
        directory.mkdir(parents=True)
        target = directory / "LEOS-light.colors"
        target.write_text("[General]\nName=My custom theme\n", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            self.manager.install_scheme("light")
        self.assertEqual(target.read_text(encoding="utf-8"), "[General]\nName=My custom theme\n")

    def test_scheme_symlinks_are_rejected(self):
        directory = self.data / "color-schemes"
        directory.mkdir(parents=True)
        target = directory / "LEOS-light.colors"
        outside = self.config / "outside"
        outside.write_text("keep", encoding="utf-8")
        target.symlink_to(outside)
        with self.assertRaises(ValueError):
            self.manager.install_scheme("light")
        self.assertEqual(outside.read_text(encoding="utf-8"), "keep")

    def test_apply_runs_allowlisted_executable_without_shell(self):
        result = self.manager.apply_theme("leos-original")
        args, kwargs = self.runner.calls[0]
        self.assertEqual(args, ["/usr/bin/plasma-apply-colorscheme", "LEOS-leos-original"])
        self.assertFalse(kwargs["shell"])
        self.assertIn("appliqué", result)
        self.assertTrue(self.manager.can_restore())
        if os.name == "posix":
            self.assertEqual(self.manager.state_file.stat().st_mode & 0o777, 0o600)

    def test_restore_previous_theme_uses_saved_scheme(self):
        self.manager.apply_theme("leos-original")
        result = self.manager.restore_previous_theme()
        self.assertEqual(self.runner.calls[-1][0], ["/usr/bin/plasma-apply-colorscheme", "BreezeDark"])
        self.assertIn("BreezeDark", result)
        self.assertFalse(self.manager.can_restore())

    def test_apply_keeps_original_scheme_across_multiple_leos_changes(self):
        self.manager.apply_theme("leos-original")
        # Simulate KDE now reporting the LEOS scheme as active.
        (self.config / "kdeglobals").write_text(
            "[General]\nColorScheme=LEOS-leos-original\n", encoding="utf-8"
        )
        self.manager.apply_theme("magenta")
        self.assertEqual(self.manager._read_state()["previous_scheme"], "BreezeDark")
        self.manager.restore_previous_theme()
        self.assertEqual(self.runner.calls[-1][0][-1], "BreezeDark")

    def test_manual_non_leos_change_becomes_the_new_restore_target(self):
        self.manager.apply_theme("leos-original")
        (self.config / "kdeglobals").write_text(
            "[General]\nColorScheme=Nordic\n", encoding="utf-8"
        )
        self.manager.apply_theme("gaming")
        self.assertEqual(self.manager._read_state()["previous_scheme"], "Nordic")

    def test_failed_application_does_not_claim_theme_is_applied(self):
        self.runner.returncode = 1
        with self.assertRaises(RuntimeError):
            self.manager.apply_theme("leos-original")
        self.assertFalse(self.manager.can_restore())

    def test_missing_apply_tool_is_reported(self):
        manager = KdeColorSchemeManager(
            self.data, self.config, self.state, apply_executable=""
        )
        # Empty string intentionally triggers PATH lookup; patch the lookup result below.
        with unittest.mock.patch("desktop.kde_colors.shutil.which", return_value=None):
            with self.assertRaises(FileNotFoundError):
                manager.apply_theme("leos-original")

    def test_current_scheme_is_read_only(self):
        self.assertEqual(self.manager.current_scheme(), "BreezeDark")
        self.assertEqual(
            (self.config / "kdeglobals").read_text(encoding="utf-8"),
            "[General]\nColorScheme=BreezeDark\n",
        )

    def test_corrupt_state_does_not_offer_restore(self):
        self.state.mkdir()
        state_file = self.state / "leos" / "kde-color-scheme.json"
        state_file.parent.mkdir()
        state_file.write_text("{broken", encoding="utf-8")
        self.assertFalse(self.manager.can_restore())

    def test_state_symlink_is_rejected_before_write(self):
        state_dir = self.state / "leos"
        state_dir.mkdir(parents=True)
        outside = self.config / "outside-state"
        outside.write_text("keep", encoding="utf-8")
        (state_dir / "kde-color-scheme.json").symlink_to(outside)
        with self.assertRaises(ValueError):
            self.manager.apply_theme("leos-original")
        self.assertEqual(outside.read_text(encoding="utf-8"), "keep")


if __name__ == "__main__":
    unittest.main()
