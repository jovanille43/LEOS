"""Tests for the KDE-session download organizer startup and XDG folder policy."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from gaming.download_organizer_service import resolve_leos_download_inbox


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


if __name__ == "__main__":
    unittest.main()
