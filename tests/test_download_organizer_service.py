"""Tests for the KDE-session download organizer startup and XDG folder policy."""

import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from gaming.download_organizer_service import _acquire_lock, _poll_once, resolve_leos_download_inbox


class DownloadOrganizerServiceTests(unittest.TestCase):
    def _config(self, home: Path, value: str) -> Path:
        config = home / ".config"
        config.mkdir(parents=True)
        (config / "user-dirs.dirs").write_text(
            f'XDG_DOWNLOAD_DIR="{value}"' + "\n",
            encoding="utf-8",
        )
        return config

    @patch("gaming.download_organizer_service.subprocess.run")
    @patch("gaming.download_organizer_service.shutil.which")
    def test_default_downloads_folder_is_switched_to_jeux(
        self, which, run
    ):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            config = self._config(home, "$HOME/Downloads")
            which.return_value = "/usr/bin/xdg-user-dirs-update"
            run.return_value.returncode = 0

            result = resolve_leos_download_inbox(home, config)

            self.assertEqual(result, home / "Jeux")
            which.assert_called_once_with("xdg-user-dirs-update")
            run.assert_called_once_with(
                [
                    "/usr/bin/xdg-user-dirs-update",
                    "--set",
                    "DOWNLOAD",
                    str(home / "Jeux"),
                ],
                check=False,
                timeout=5,
                stdout=unittest.mock.ANY,
                stderr=unittest.mock.ANY,
            )

    @patch("gaming.download_organizer_service.subprocess.run")
    @patch("gaming.download_organizer_service.shutil.which")
    def test_french_default_downloads_folder_is_switched_to_jeux(
        self, which, run
    ):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            config = self._config(home, "$HOME/Téléchargements")
            which.return_value = "/usr/bin/xdg-user-dirs-update"
            run.return_value.returncode = 0

            self.assertEqual(
                resolve_leos_download_inbox(home, config),
                home / "Jeux",
            )
            run.assert_called_once()

    @patch("gaming.download_organizer_service.subprocess.run")
    @patch("gaming.download_organizer_service.shutil.which")
    def test_existing_custom_download_folder_is_preserved(
        self, which, run
    ):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            home = root / "home"
            home.mkdir()
            custom = root / "external-downloads"
            config = self._config(home, str(custom))

            result = resolve_leos_download_inbox(home, config)

            self.assertEqual(result, custom)
            which.assert_not_called()
            run.assert_not_called()

    @patch("gaming.download_organizer_service.subprocess.run")
    @patch("gaming.download_organizer_service.shutil.which")
    def test_missing_xdg_user_dirs_tool_keeps_the_existing_default(
        self, which, run
    ):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            config = self._config(home, "$HOME/Downloads")
            which.return_value = None

            self.assertEqual(
                resolve_leos_download_inbox(home, config),
                home / "Downloads",
            )
            run.assert_not_called()

    @patch("gaming.download_organizer_service.subprocess.run")
    @patch("gaming.download_organizer_service.shutil.which")
    def test_failed_xdg_update_does_not_break_existing_downloads(
        self, which, run
    ):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            config = self._config(home, "$HOME/Downloads")
            which.return_value = "/usr/bin/xdg-user-dirs-update"
            run.return_value.returncode = 1

            self.assertEqual(
                resolve_leos_download_inbox(home, config),
                home / "Downloads",
            )

    def test_already_configured_jeux_folder_needs_no_reconfiguration(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            config = self._config(home, "$HOME/Jeux")
            with patch("gaming.download_organizer_service.shutil.which") as which:
                self.assertEqual(
                    resolve_leos_download_inbox(home, config),
                    home / "Jeux",
                )
                which.assert_not_called()


    def test_poll_failure_is_logged_without_exposing_download_paths(self):
        class BrokenOrganizer:
            def poll(self):
                raise OSError("/home/private-user/Jeux/secret-game.rom")

        with self.assertLogs("leos.download-organizer", level="WARNING") as captured:
            self.assertEqual(_poll_once(BrokenOrganizer()), [])
        self.assertIn("OSError", captured.output[0])
        self.assertNotIn("secret-game.rom", captured.output[0])
        self.assertNotIn("private-user", captured.output[0])

    def test_successful_poll_notifies_and_returns_moved_items(self):
        item = {"system": "Nintendo", "console": "NES", "archive": ""}
        class WorkingOrganizer:
            def poll(self):
                return [item]

        with patch("gaming.download_organizer_service._notify") as notify:
            self.assertEqual(_poll_once(WorkingOrganizer()), [item])
        notify.assert_called_once_with([item])

    def test_runtime_lock_is_private_and_prevents_a_second_instance(self):
        with tempfile.TemporaryDirectory() as temporary:
            runtime = Path(temporary) / "runtime"
            runtime.mkdir(mode=0o700)
            runtime.chmod(0o700)
            with patch.dict(os.environ, {"XDG_RUNTIME_DIR": str(runtime)}):
                descriptor = _acquire_lock()
                self.assertIsNotNone(descriptor)
                try:
                    self.assertEqual(stat.S_IMODE(os.fstat(descriptor).st_mode), 0o600)
                    self.assertIsNone(_acquire_lock())
                finally:
                    os.close(descriptor)

    def test_runtime_lock_rejects_relative_runtime_directory(self):
        with patch.dict(os.environ, {"XDG_RUNTIME_DIR": "relative/runtime"}):
            self.assertIsNone(_acquire_lock())

    def test_runtime_lock_rejects_group_or_world_accessible_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            runtime = Path(temporary) / "runtime"
            runtime.mkdir(mode=0o700)
            runtime.chmod(0o755)
            with patch.dict(os.environ, {"XDG_RUNTIME_DIR": str(runtime)}):
                self.assertIsNone(_acquire_lock())
            self.assertFalse((runtime / "leos-download-organizer.lock").exists())

    def test_runtime_lock_rejects_symlinked_runtime_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runtime = root / "runtime"
            runtime.mkdir(mode=0o700)
            runtime.chmod(0o700)
            link = root / "runtime-link"
            link.symlink_to(runtime, target_is_directory=True)
            with patch.dict(os.environ, {"XDG_RUNTIME_DIR": str(link)}):
                self.assertIsNone(_acquire_lock())
            self.assertFalse((runtime / "leos-download-organizer.lock").exists())

    def test_runtime_lock_rejects_symlinked_lock_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runtime = root / "runtime"
            runtime.mkdir(mode=0o700)
            runtime.chmod(0o700)
            target = root / "target"
            target.write_text("do not modify", encoding="utf-8")
            (runtime / "leos-download-organizer.lock").symlink_to(target)
            with patch.dict(os.environ, {"XDG_RUNTIME_DIR": str(runtime)}):
                self.assertIsNone(_acquire_lock())
            self.assertEqual(target.read_text(encoding="utf-8"), "do not modify")

    def test_runtime_lock_rejects_hardlinked_lock_file_without_chmodding_target(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runtime = root / "runtime"
            runtime.mkdir(mode=0o700)
            runtime.chmod(0o700)
            target = root / "target"
            target.write_text("do not modify", encoding="utf-8")
            target.chmod(0o640)
            (runtime / "leos-download-organizer.lock").hardlink_to(target)
            with patch.dict(os.environ, {"XDG_RUNTIME_DIR": str(runtime)}):
                self.assertIsNone(_acquire_lock())
            self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o640)
            self.assertEqual(target.read_text(encoding="utf-8"), "do not modify")

    def test_runtime_lock_requires_the_current_user_to_own_the_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            runtime = Path(temporary) / "runtime"
            runtime.mkdir(mode=0o700)
            runtime.chmod(0o700)
            current_uid = os.getuid()
            with (
                patch.dict(os.environ, {"XDG_RUNTIME_DIR": str(runtime)}),
                patch("gaming.download_organizer_service.os.getuid", return_value=current_uid + 1),
            ):
                self.assertIsNone(_acquire_lock())
            self.assertFalse((runtime / "leos-download-organizer.lock").exists())


if __name__ == "__main__":
    unittest.main()
