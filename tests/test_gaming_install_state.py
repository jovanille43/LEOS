"""Tests for truthful imported-game installation states."""

from pathlib import Path
import tempfile
import unittest

from gaming.backend.install_state import installation_status

ROOT = Path(__file__).resolve().parents[1]


class InstallationStateTests(unittest.TestCase):
    def test_existing_install_directory_is_installed(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(
                installation_status({"install_path": directory}),
                "Installé",
            )

    def test_install_path_must_be_a_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            file_path = Path(directory) / "not-a-game-folder"
            file_path.write_text("x", encoding="utf-8")
            self.assertEqual(
                installation_status({"install_path": str(file_path)}),
                "Fichiers absents",
            )

    def test_missing_external_drive_path_is_reported_unavailable(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "offline-drive" / "Game"
            self.assertEqual(
                installation_status({"install_path": str(missing)}),
                "Fichiers absents",
            )

    def test_missing_metadata_is_unknown_not_installed(self):
        self.assertEqual(installation_status({}), "État inconnu")

    def test_game_details_highlight_missing_files(self):
        qml = (ROOT / "gaming/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn('window.selectedInstallStatus === "Fichiers absents"', qml)
        self.assertIn("window.magenta", qml)

    def test_existing_executable_is_sufficient_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "game"
            executable.write_text("placeholder", encoding="utf-8")
            self.assertEqual(
                installation_status({"executable": str(executable)}),
                "Installé",
            )


if __name__ == "__main__":
    unittest.main()
