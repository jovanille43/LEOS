"""Tests for the automatic, one-time LEOS Gaming Flatpak bootstrap."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "packaging"
    / "leos-default-gaming-apps-setup"
)
EXPECTED_APPS = {
    "com.heroicgameslauncher.hgl",
    "org.libretro.RetroArch",
    "org.DolphinEmu.dolphin-emu",
    "net.pcsx2.PCSX2",
    "org.ppsspp.PPSSPP",
    "net.kuribo64.melonDS",
    "net.rpcs3.RPCS3",
    "dev.eden_emu.eden",
}


class DefaultGamingAppsSetupTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.home = self.root / "home"
        self.home.mkdir()
        self.bin_dir = self.root / "bin"
        self.bin_dir.mkdir()
        self.command_log = self.root / "commands.log"
        self.remote_file = self.root / "remote.txt"
        self.installed_file = self.root / "installed.txt"

        flatpak = self.bin_dir / "flatpak"
        flatpak.write_text(
            """#!/usr/bin/bash
printf 'flatpak %s\n' "$*" >> "$COMMAND_LOG"
case "$1" in
  info)
    case "$2" in
      --user) scope="user" ;;
      --system) scope="system" ;;
      *) exit 2 ;;
    esac
    app_id="$3"
    grep -Fqx "$scope:$app_id" "$INSTALLED_FILE" 2>/dev/null
    exit $?
    ;;
  remotes)
    printf 'Name URL\n'
    [[ -f "$REMOTE_FILE" ]] && cat "$REMOTE_FILE"
    exit 0
    ;;
  remote-add)
    [[ "$FAIL_REMOTE" == "1" ]] && exit 1
    printf 'flathub %s\n' "$REMOTE_URL" > "$REMOTE_FILE"
    exit 0
    ;;
  install)
    app_id="${@: -1}"
    if [[ "$FAIL_APP" == "$app_id" ]]; then exit 1; fi
    grep -Fqx "user:$app_id" "$INSTALLED_FILE" 2>/dev/null || \\
      printf 'user:%s\n' "$app_id" >> "$INSTALLED_FILE"
    exit 0
    ;;
esac
exit 0
""",
            encoding="utf-8",
        )
        flatpak.chmod(0o755)

        # A stub proves the bootstrap does not ask for a second consent dialog.
        kdialog = self.bin_dir / "kdialog"
        kdialog.write_text(
            "#!/usr/bin/bash\nprintf 'kdialog\n' >> \"$COMMAND_LOG\"\nexit 1\n",
            encoding="utf-8",
        )
        kdialog.chmod(0o755)

    def tearDown(self):
        self.temp_dir.cleanup()

    @property
    def state_dir(self):
        return self.home / ".local/state/leos"

    @property
    def marker(self):
        return self.state_dir / "gaming-apps-seeded-v2"

    def run_setup(self, *, fail_app="", fail_remote=False, remote_url="https://dl.flathub.org/repo/"):
        env = os.environ.copy()
        env.update({
            "HOME": str(self.home),
            "XDG_STATE_HOME": str(self.home / ".local/state"),
            "PATH": f"{self.bin_dir}:{env.get('PATH', '')}",
            "COMMAND_LOG": str(self.command_log),
            "REMOTE_FILE": str(self.remote_file),
            "INSTALLED_FILE": str(self.installed_file),
            "FAIL_APP": fail_app,
            "FAIL_REMOTE": "1" if fail_remote else "0",
            "REMOTE_URL": remote_url,
            "DBUS_SESSION_BUS_ADDRESS": "",
        })
        return subprocess.run(
            ["/usr/bin/bash", str(SCRIPT)],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

    def command_lines(self):
        return self.command_log.read_text(encoding="utf-8").splitlines() if self.command_log.exists() else []

    def assert_setup_succeeded(self, result):
        log_file = self.state_dir / "gaming-apps-setup.log"
        details = log_file.read_text(encoding="utf-8") if log_file.exists() else "(journal absent)"
        self.assertEqual(result.returncode, 0, f"{result.stderr}\\n{details}\\nCommands: {self.command_lines()}")

    def install_ids(self):
        result = []
        for line in self.command_lines():
            if line.startswith("flatpak install "):
                result.append(line.rsplit(" ", 1)[-1])
        return result

    def test_catalog_and_bootstrap_share_the_same_default_app_set(self):
        import json
        import re

        root = Path(__file__).resolve().parents[1]
        catalog = json.loads((root / "shop" / "catalog.json").read_text(encoding="utf-8"))
        bundled = {
            item["id"] for item in catalog
            if item.get("bundled") is True
            and "automatiquement" in item.get("operation_note", "").casefold()
        }
        script = SCRIPT.read_text(encoding="utf-8")
        block = re.search(r"(?ms)^apps=\(\n(.*?)^\)", script)
        self.assertIsNotNone(block)
        declared = set(re.findall(r"(?m)^    ([A-Za-z0-9_.-]+)$", block.group(1)))
        self.assertEqual(declared, EXPECTED_APPS)
        self.assertEqual(bundled, EXPECTED_APPS)

    def test_installs_the_eight_starter_apps_without_an_extra_prompt(self):
        result = self.run_setup()
        self.assert_setup_succeeded(result)
        self.assertTrue(self.marker.is_file())
        self.assertEqual(set(self.install_ids()), EXPECTED_APPS)
        self.assertEqual(len(self.install_ids()), len(EXPECTED_APPS))
        self.assertEqual(sum("remote-add " in line for line in self.command_lines()), 1)
        self.assertFalse(any(line.startswith("kdialog ") for line in self.command_lines()))

    def test_v1_upgrade_installs_only_eden_and_preserves_prior_user_uninstalls(self):
        old_apps = EXPECTED_APPS - {"dev.eden_emu.eden"}
        self.state_dir.mkdir(parents=True)
        (self.state_dir / "gaming-apps-seeded-v1").write_text(
            "completed\n", encoding="utf-8"
        )
        # Simulate an app removed by the user after the old starter set completed.
        previously_installed = old_apps - {"net.rpcs3.RPCS3"}
        self.installed_file.write_text(
            "".join(f"user:{app_id}\n" for app_id in sorted(previously_installed)),
            encoding="utf-8",
        )

        result = self.run_setup()

        self.assert_setup_succeeded(result)
        self.assertEqual(self.install_ids(), ["dev.eden_emu.eden"])
        self.assertTrue(self.marker.is_file())
        self.assertTrue((self.state_dir / "gaming-apps-seeded-v1").is_file())

    def test_existing_user_and_system_apps_are_not_reinstalled(self):
        self.installed_file.write_text(
            "user:org.libretro.RetroArch\nsystem:net.pcsx2.PCSX2\n",
            encoding="utf-8",
        )
        result = self.run_setup()
        self.assert_setup_succeeded(result)
        installed = set(self.install_ids())
        self.assertEqual(installed, EXPECTED_APPS - {
            "org.libretro.RetroArch", "net.pcsx2.PCSX2"
        })
        self.assertTrue(self.marker.is_file())

    def test_partial_failure_leaves_no_marker_and_retry_installs_only_missing_app(self):
        failed_app = "net.rpcs3.RPCS3"
        first = self.run_setup(fail_app=failed_app)
        self.assertNotEqual(first.returncode, 0)
        self.assertFalse(self.marker.exists())
        first_installs = self.install_ids()
        self.assertEqual(set(first_installs), EXPECTED_APPS)
        self.assertIn(failed_app, first_installs)

        second = self.run_setup()
        self.assert_setup_succeeded(second)
        self.assertTrue(self.marker.is_file())
        all_installs = self.install_ids()
        self.assertEqual(all_installs.count(failed_app), 2)
        for app_id in EXPECTED_APPS - {failed_app}:
            self.assertEqual(all_installs.count(app_id), 1)

    def test_rejects_a_non_official_remote_named_flathub(self):
        self.remote_file.write_text(
            "flathub https://example.invalid/repo/\n", encoding="utf-8"
        )
        result = self.run_setup()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.marker.exists())
        self.assertEqual(self.install_ids(), [])

    def test_remote_add_failure_is_retryable(self):
        result = self.run_setup(fail_remote=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.marker.exists())
        self.assertEqual(self.install_ids(), [])

    def test_success_marker_prevents_reinstall_after_user_uninstalls_an_app(self):
        first = self.run_setup()
        self.assert_setup_succeeded(first)
        original_commands = self.command_lines()
        # Simulate the user uninstalling one app after the first successful setup.
        lines = self.installed_file.read_text(encoding="utf-8").splitlines()
        self.installed_file.write_text(
            "\n".join(line for line in lines if not line.endswith(":net.rpcs3.RPCS3")) + "\n",
            encoding="utf-8",
        )
        second = self.run_setup()
        self.assert_setup_succeeded(second)
        self.assertEqual(self.command_lines(), original_commands)


if __name__ == "__main__":
    unittest.main()
