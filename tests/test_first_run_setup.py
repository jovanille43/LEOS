"""Consent and safety tests for the optional first-run application setup."""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "packaging" / "leos-default-apps-setup"


class FirstRunSetupTests(unittest.TestCase):
    def _environment(self, root: Path, *, include_kdialog: bool = True) -> dict[str, str]:
        bindir = root / "bin"
        bindir.mkdir()
        flatpak = bindir / "flatpak"
        flatpak.write_text(
            "#!/usr/bin/bash\n"
            'printf "%s\\n" "$*" >> "$FLATPAK_LOG"\n'
            'if [[ "$1" == info ]]; then\n'
            '  app_id="${@: -1}"\n'
            '  [[ -n "$EXISTING_APP" && "$app_id" == "$EXISTING_APP" ]] && exit 0\n'
            '  [[ -f "$INSTALLED_LOG" ]] && grep -Fqx "$app_id" "$INSTALLED_LOG" && exit 0\n'
            '  exit 1\n'
            'fi\n'
            'if [[ "$1" == install && -n "$FAIL_APP" && "$*" == *"$FAIL_APP"* ]]; then exit 2; fi\n'
            'if [[ "$1" == install ]]; then printf "%s\\n" "${@: -1}" >> "$INSTALLED_LOG"; fi\n'
            "exit 0\n",
            encoding="utf-8",
        )
        flatpak.chmod(0o755)
        if include_kdialog:
            kdialog = bindir / "kdialog"
            kdialog.write_text(
                "#!/usr/bin/bash\n"
                'printf "prompt\\n" >> "$PROMPT_LOG"\n'
                'exit "$KDLG_RESULT"\n',
                encoding="utf-8",
            )
            kdialog.chmod(0o755)
        env = os.environ.copy()
        env.update({
            "HOME": str(root / "home"),
            "XDG_STATE_HOME": str(root / "state"),
            "PATH": f"{bindir}:/usr/bin:/bin" if include_kdialog else str(bindir),
            "FLATPAK_LOG": str(root / "flatpak.log"),
            "INSTALLED_LOG": str(root / "installed.log"),
            "PROMPT_LOG": str(root / "prompt.log"),
            "KDLG_RESULT": "1",
            "EXISTING_APP": "",
            "FAIL_APP": "",
        })
        Path(env["HOME"]).mkdir()
        return env

    def _run(self, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["/usr/bin/bash", str(SCRIPT)],
            check=False,
            capture_output=True,
            text=True,
            env=env,
            cwd=str(Path(env["HOME"]).parent),
            timeout=10,
        )

    def test_declining_never_calls_flatpak_and_remembers_choice(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            env = self._environment(root)
            env["KDLG_RESULT"] = "1"
            result = self._run(env)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((root / "flatpak.log").exists())
            self.assertTrue((root / "state/leos/default-apps-seeded").is_file())
            self.assertEqual((root / "prompt.log").read_text().splitlines(), ["prompt"])
            second = self._run(env)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual((root / "prompt.log").read_text().splitlines(), ["prompt"])

    def test_accepting_adds_flathub_and_installs_only_missing_apps(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            env = self._environment(root)
            env["KDLG_RESULT"] = "0"
            env["EXISTING_APP"] = "org.videolan.VLC"
            result = self._run(env)
            self.assertEqual(result.returncode, 0, result.stderr)
            commands = (root / "flatpak.log").read_text().splitlines()
            self.assertIn(
                "remote-add --user --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo",
                commands,
            )
            self.assertIn(
                "install --user --noninteractive --or-update flathub com.brave.Browser",
                commands,
            )
            self.assertIn(
                "install --user --noninteractive --or-update flathub org.libreoffice.LibreOffice",
                commands,
            )
            self.assertFalse(
                any("install " in command and "org.videolan.VLC" in command for command in commands)
            )
            self.assertTrue((root / "state/leos/default-apps-seeded").is_file())
            self.assertFalse((root / "state/leos/default-apps-consent-v1").exists())

    def test_failed_app_does_not_block_other_installs_or_mark_setup_complete(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            env = self._environment(root)
            env["KDLG_RESULT"] = "0"
            env["FAIL_APP"] = "com.brave.Browser"
            result = self._run(env)
            self.assertNotEqual(result.returncode, 0)
            commands = (root / "flatpak.log").read_text().splitlines()
            self.assertTrue(any("com.brave.Browser" in command and command.startswith("install ") for command in commands))
            self.assertTrue(any("org.libreoffice.LibreOffice" in command and command.startswith("install ") for command in commands))
            self.assertTrue(any("org.videolan.VLC" in command and command.startswith("install ") for command in commands))
            self.assertFalse((root / "state/leos/default-apps-seeded").exists())
            consent = root / "state/leos/default-apps-consent-v1"
            self.assertTrue(consent.is_file())

            # A later Desktop entry resumes the approved list without asking again.
            env["FAIL_APP"] = ""
            retry = self._run(env)
            self.assertEqual(retry.returncode, 0, retry.stderr)
            self.assertTrue((root / "state/leos/default-apps-seeded").is_file())
            self.assertFalse(consent.exists())
            self.assertEqual((root / "prompt.log").read_text().splitlines(), ["prompt"])
            commands_after_retry = (root / "flatpak.log").read_text().splitlines()
            brave_installs = [
                command for command in commands_after_retry
                if command.startswith("install ") and "com.brave.Browser" in command
            ]
            libreoffice_installs = [
                command for command in commands_after_retry
                if command.startswith("install ") and "org.libreoffice.LibreOffice" in command
            ]
            vlc_installs = [
                command for command in commands_after_retry
                if command.startswith("install ") and "org.videolan.VLC" in command
            ]
            self.assertEqual(len(brave_installs), 2)
            self.assertEqual(len(libreoffice_installs), 1)
            self.assertEqual(len(vlc_installs), 1)

    def test_relative_xdg_state_home_falls_back_to_home_state_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            env = self._environment(root)
            env["XDG_STATE_HOME"] = "relative-state"
            env["KDLG_RESULT"] = "1"
            result = self._run(env)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((root / "home/.local/state/leos/default-apps-seeded").is_file())
            self.assertFalse((root / "relative-state").exists())

    def test_missing_graphical_confirmation_never_installs_or_marks_complete(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            env = self._environment(root, include_kdialog=False)
            result = self._run(env)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((root / "flatpak.log").exists())
            self.assertFalse((root / "state/leos/default-apps-seeded").exists())


if __name__ == "__main__":
    unittest.main()
