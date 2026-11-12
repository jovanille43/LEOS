"""Tests for the consent-based LEOS starter application offer."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "packaging" / "leos-default-apps-setup"


class DefaultAppsSetupTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.home = self.root / "home"
        self.home.mkdir()
        self.bin_dir = self.root / "bin"
        self.bin_dir.mkdir()
        self.log = self.root / "commands.log"

        flatpak = self.bin_dir / "flatpak"
        flatpak.write_text(
            """#!/usr/bin/bash
printf 'flatpak %s\\n' "$*" >> "$COMMAND_LOG"
if [[ "$1" == "info" ]]; then exit 1; fi
if [[ "$FAIL_REMOTE" == "1" && "$1" == "remote-add" ]]; then exit 1; fi
if [[ "$FAIL_INSTALL" == "1" && "$1" == "install" ]]; then exit 1; fi
exit 0
""",
            encoding="utf-8",
        )
        flatpak.chmod(0o755)

        kdialog = self.bin_dir / "kdialog"
        kdialog.write_text(
            """#!/usr/bin/bash
printf 'kdialog %s\\n' "$*" >> "$COMMAND_LOG"
[[ "$K_DIALOG_ACCEPT" == "1" ]]
""",
            encoding="utf-8",
        )
        kdialog.chmod(0o755)

    def tearDown(self):
        self.temp_dir.cleanup()

    def run_setup(self, accept=False, fail_remote=False, fail_install=False, no_kdialog=False):
        env = os.environ.copy()
        path = str(self.bin_dir)
        if no_kdialog:
            path = ":".join(part for part in env.get("PATH", "").split(":") if part != str(self.bin_dir))
            # Keep the fake Flatpak available while hiding only kdialog.
            hidden = self.root / "flatpak-only"
            hidden.mkdir()
            (hidden / "flatpak").symlink_to(self.bin_dir / "flatpak")
            path = f"{hidden}:{env.get('PATH', '')}"
        env.update({
            "HOME": str(self.home),
            "XDG_STATE_HOME": str(self.home / ".local/state"),
            "PATH": f"{path}:{env.get('PATH', '')}",
            "COMMAND_LOG": str(self.log),
            "K_DIALOG_ACCEPT": "1" if accept else "0",
            "FAIL_REMOTE": "1" if fail_remote else "0",
            "FAIL_INSTALL": "1" if fail_install else "0",
        })
        return subprocess.run(
            ["/usr/bin/bash", str(SCRIPT)],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

    @property
    def marker(self):
        return self.home / ".local/state/leos/default-apps-seeded"

    def test_declining_never_adds_flathub_or_installs_apps(self):
        result = self.run_setup(accept=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.marker.is_file())
        calls = self.log.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(calls), 1)
        self.assertTrue(calls[0].startswith("kdialog "))
        self.assertFalse(any("remote-add" in line or "install " in line for line in calls))

        second = self.run_setup(accept=True)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(self.log.read_text(encoding="utf-8").splitlines(), calls)

    def test_accepting_installs_optional_apps_once(self):
        first = self.run_setup(accept=True)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertTrue(self.marker.is_file())
        calls = self.log.read_text(encoding="utf-8").splitlines()
        self.assertEqual(sum("remote-add " in line for line in calls), 1)
        self.assertEqual(sum("install " in line for line in calls), 3)

        second = self.run_setup(accept=True)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(self.log.read_text(encoding="utf-8").splitlines(), calls)

    def test_install_failure_does_not_write_completion_marker(self):
        result = self.run_setup(accept=True, fail_install=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.marker.exists())

    def test_remote_failure_does_not_write_completion_marker(self):
        result = self.run_setup(accept=True, fail_remote=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.marker.exists())

    def test_missing_graphical_confirmation_never_installs(self):
        result = self.run_setup(accept=True, no_kdialog=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.log.exists())
        self.assertFalse(self.marker.exists())


if __name__ == "__main__":
    unittest.main()
