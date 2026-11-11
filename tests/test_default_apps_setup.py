"""Tests for the one-time LEOS default application installer."""

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
        self.log = self.root / "flatpak.log"
        self.fake_flatpak = self.bin_dir / "flatpak"
        self.fake_flatpak.write_text(
            """#!/usr/bin/bash
printf '%s\\n' "$*" >> "$FLATPAK_LOG"
if [[ "$1" == "info" ]]; then
    exit 1
fi
if [[ "$FAIL_REMOTE" == "1" && "$1" == "remote-add" ]]; then
    exit 1
fi
if [[ "$FAIL_INSTALL" == "1" && "$1" == "install" ]]; then
    exit 1
fi
exit 0
""",
            encoding="utf-8",
        )
        self.fake_flatpak.chmod(0o755)

    def tearDown(self):
        self.temp_dir.cleanup()

    def run_setup(self, fail_remote=False, fail_install=False):
        env = os.environ.copy()
        env.update({
            "HOME": str(self.home),
            "PATH": f"{self.bin_dir}:{env.get('PATH', '')}",
            "FLATPAK_LOG": str(self.log),
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

    def test_installs_default_apps_once_and_persists_marker(self):
        first = self.run_setup()
        self.assertEqual(first.returncode, 0, first.stderr)
        marker = self.home / ".local/state/leos/default-apps-seeded"
        self.assertTrue(marker.is_file())
        calls = self.log.read_text(encoding="utf-8").splitlines()
        self.assertEqual(sum(line.startswith("install ") for line in calls), 3)
        self.assertEqual(sum(line.startswith("remote-add ") for line in calls), 1)

        second = self.run_setup()
        self.assertEqual(second.returncode, 0, second.stderr)
        calls_after_second_run = self.log.read_text(encoding="utf-8").splitlines()
        self.assertEqual(calls_after_second_run, calls)

    def test_does_not_write_marker_when_remote_setup_fails(self):
        result = self.run_setup(fail_remote=True)
        self.assertNotEqual(result.returncode, 0)
        marker = self.home / ".local/state/leos/default-apps-seeded"
        self.assertFalse(marker.exists())

    def test_does_not_write_marker_when_an_application_install_fails(self):
        result = self.run_setup(fail_install=True)
        self.assertNotEqual(result.returncode, 0)
        marker = self.home / ".local/state/leos/default-apps-seeded"
        self.assertFalse(marker.exists())
        calls = self.log.read_text(encoding="utf-8").splitlines()
        self.assertTrue(any(line.startswith("install ") for line in calls))


if __name__ == "__main__":
    unittest.main()
