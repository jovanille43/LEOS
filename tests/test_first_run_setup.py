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
            '  [[ -n "$EXISTING_APP" && "$*" == *"$EXISTING_APP"* ]] && exit 0\n'
            '  exit 1\n'
            'fi\n'
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
            "PATH": f"{bindir}:/usr/bin:/bin",
            "FLATPAK_LOG": str(root / "flatpak.log"),
            "PROMPT_LOG": str(root / "prompt.log"),
            "KDLG_RESULT": "1",
            "EXISTING_APP": "",
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
