"""Behavioural tests for adding/removing selected Gaming emulator roots."""

import json
import tempfile
import unittest
from pathlib import Path

from gaming.backend.emulator_sources import remove_emulator_source_folder


class EmulatorSourceManagementTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.state_file = self.root / "config" / "leos" / "emulator-sources.json"
        self.state_file.parent.mkdir(parents=True)

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

        removed = remove_emulator_source_folder(
            self.state_file, "eden", str(game_folder)
        )

        self.assertTrue(removed)
        self.assertEqual(
            self.read_sources(),
            [{"platform": "ps2", "path": missing_external_folder}],
        )
        self.assertEqual(game_file.read_bytes(), b"personal game data")

    def test_disconnected_removable_drive_source_can_still_be_forgotten(self):
        disconnected = str(self.root / "USB Drive" / "Games")
        self.assertFalse(Path(disconnected).exists())
        self.write_sources([{"platform": "eden", "path": disconnected}])

        removed = remove_emulator_source_folder(
            self.state_file, "eden", disconnected
        )

        self.assertTrue(removed)
        self.assertEqual(self.read_sources(), [])

    def test_rejects_invalid_requests_without_rewriting_the_catalogue(self):
        source = str(self.root / "Games")
        original = [{"platform": "eden", "path": source}]
        self.write_sources(original)

        self.assertFalse(remove_emulator_source_folder(
            self.state_file, "unknown", source
        ))
        self.assertFalse(remove_emulator_source_folder(
            self.state_file, "eden", "relative/Games"
        ))
        self.assertFalse(remove_emulator_source_folder(
            self.state_file, "eden", source + "\x00"
        ))
        self.assertFalse(remove_emulator_source_folder(
            self.state_file, "eden", str(self.root / "Other Games")
        ))
        self.assertEqual(self.read_sources(), original)

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

        self.assertFalse(remove_emulator_source_folder(
            self.state_file, "eden", source
        ))
        self.assertEqual(
            json.loads(target.read_text(encoding="utf-8")),
            [{"platform": "eden", "path": source}],
        )



if __name__ == "__main__":
    unittest.main()
