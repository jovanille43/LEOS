"""Tests for truthful imported-game installation states."""

from pathlib import Path
import tempfile
import unittest

from gaming.backend.install_state import installation_status


class InstallationStateTests(unittest.TestCase):
    def test_existing_install_directory_is_installed(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(
                installation_status({"install_path": directory}),
                "Installé",
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
