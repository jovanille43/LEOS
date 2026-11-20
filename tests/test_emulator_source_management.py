"""Behavioural tests for adding/removing selected Gaming emulator roots."""

import json
import tempfile
import unittest
from pathlib import Path

from gaming.backend.library import GameLibraryModel


class LibraryHarness:
    def __init__(self, state_file: Path):
        self._emulator_sources_file = state_file
        self.refresh_count = 0

    def refresh(self):
        self.refresh_count += 1


class EmulatorSourceManagementTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.state_file = self.root / "config" / "leos" / "emulator-sources.json"
        self.state_file.parent.mkdir(parents=True)
        self.library = LibraryHarness(self.state_file)

    def tearDown(self):
        self.temporary.cleanup()

    def write_sources(self, sources):
        self.state_file.write_text(
            json.dumps(sources, ensure_ascii=False),
            encoding="utf-8",
        )

    def read_sources(self):
        return json.loads(self.state_file.read_text(encoding="utf-8"))

    def test_remove_forgets_only_the_requested_source_and_preserves_game_files(self):
        game_folder = self.root / "Switch Games"
        game_folder.mkdir()
        game_file = game_folder / "My Game.nsp"
        game_file.write_bytes(b"personal game data")
        missing_external_folder = str(self.root / "unmounted-drive" / "PS2")

        self.write_sources([
            {"platform": "eden", "path": str(game_folder)},
            {"platform": "ps2", "path": missing_external_folder},
        ])

        removed = GameLibraryModel.removeEmulatorFolder(
            self.library, "eden", str(game_folder)
        )

        self.assertTrue(removed)
        self.assertEqual(
            self.read_sources(),
            [{"platform": "ps2", "path": missing_external_folder}],
        )
        self.assertEqual(game_file.read_bytes(), b"personal game data")
        self.assertEqual(self.library.refresh_count, 1)

    def test_disconnected_removable_drive_source_can_still_be_forgotten(self):
        disconnected = str(self.root / "USB Drive" / "Games")
        self.assertFalse(Path(disconnected).exists())
        self.write_sources([{"platform": "eden", "path": disconnected}])

        removed = GameLibraryModel.removeEmulatorFolder(
            self.library, "eden", disconnected
        )

        self.assertTrue(removed)
        self.assertEqual(self.read_sources(), [])
        self.assertEqual(self.library.refresh_count, 1)

    def test_rejects_invalid_requests_without_rewriting_the_catalogue(self):
        source = str(self.root / "Games")
        original = [{"platform": "eden", "path": source}]
        self.write_sources(original)

        self.assertFalse(GameLibraryModel.removeEmulatorFolder(
            self.library, "unknown", source
        ))
        self.assertFalse(GameLibraryModel.removeEmulatorFolder(
            self.library, "eden", "relative/Games"
        ))
        self.assertFalse(GameLibraryModel.removeEmulatorFolder(
            self.library, "eden", source + "\x00"
        ))
        self.assertFalse(GameLibraryModel.removeEmulatorFolder(
            self.library, "eden", str(self.root / "Other Games")
        ))
        self.assertEqual(self.read_sources(), original)
        self.assertEqual(self.library.refresh_count, 0)

    def test_refuses_symlinked_source_state_file(self):
        source = str(self.root / "Games")
        self.write_sources([{"platform": "eden", "path": source}])
        target = self.root / "source-state.json"
        target.write_text(self.state_file.read_text(encoding="utf-8"), encoding="utf-8")
        self.state_file.unlink()
        try:
            self.state_file.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("Symbolic links unavailable")

        self.assertFalse(GameLibraryModel.removeEmulatorFolder(
            self.library, "eden", source
        ))
        self.assertEqual(
            json.loads(target.read_text(encoding="utf-8")),
            [{"platform": "eden", "path": source}],
        )
        self.assertEqual(self.library.refresh_count, 0)

    def test_source_list_contains_platform_and_path_labels(self):
        switch_folder = str(self.root / "Switch Games")
        ps2_folder = str(self.root / "PS2")
        self.write_sources([
            {"platform": "eden", "path": switch_folder},
            {"platform": "ps2", "path": ps2_folder},
        ])

        sources = GameLibraryModel.emulatorSourceFolders(self.library)

        self.assertEqual(len(sources), 2)
        self.assertEqual(sources[0]["platform"], "eden")
        self.assertEqual(sources[0]["path"], switch_folder)
        self.assertIn("Eden", sources[0]["label"])
        self.assertIn(switch_folder, sources[0]["label"])
        self.assertIn("PCSX2", sources[1]["label"])


if __name__ == "__main__":
    unittest.main()
