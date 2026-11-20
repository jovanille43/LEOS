"""Structural integration checks for the explicitly selected emulator folders."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class EmulatorFolderIntegrationTests(unittest.TestCase):
    def test_user_can_browse_and_choose_a_local_folder_in_gaming_mode(self):
        qml = (ROOT / "gaming/qml/Main.qml").read_text(encoding="utf-8")
        controller = (ROOT / "gaming/backend/controller.py").read_text(encoding="utf-8")
        self.assertIn("id: emulatorFolderDialog", qml)
        self.assertIn("leos.beginEmulatorFolderBrowse", qml)
        self.assertIn("leos.emulatorFolderDirectories", qml)
        self.assertIn("leos.enterEmulatorFolder", qml)
        self.assertIn("leos.useCurrentEmulatorFolder", qml)
        self.assertIn("def beginEmulatorFolderBrowse", controller)
        self.assertIn("def useCurrentEmulatorFolder", controller)

    def test_only_persisted_user_selected_sources_are_added_to_library(self):
        library = (ROOT / "gaming/backend/library.py").read_text(encoding="utf-8")
        self.assertIn("def addEmulatorFolder", library)
        self.assertIn("self._emulator_sources_file", library)
        self.assertIn("write_bounded_json(self._emulator_sources_file", library)
        self.assertIn("for source in self._load_emulator_source_folders()", library)
        self.assertIn("scan_emulator_folder(", library)

    def test_flatpak_launch_is_limited_to_the_selected_directory_read_only(self):
        scanner = (ROOT / "gaming/backend/emulator_games.py").read_text(encoding="utf-8")
        self.assertIn('f"--filesystem={folder}:ro"', scanner)
        self.assertIn("build_emulator_launch_command", scanner)
        self.assertIn("game_file.relative_to(root)", scanner)
        self.assertIn("content_path.is_symlink()", scanner)
        self.assertIn("selected_root.is_symlink()", scanner)

    def test_scanner_does_not_globally_search_or_invoke_shell_commands(self):
        scanner = (ROOT / "gaming/backend/emulator_games.py").read_text(encoding="utf-8")
        self.assertIn("os.scandir(resolved_directory)", scanner)
        self.assertIn("MAX_SCAN_DEPTH", scanner)
        self.assertIn("MAX_SCAN_ENTRIES", scanner)
        self.assertNotIn("os.walk(", scanner)
        self.assertNotIn("subprocess", scanner)
        self.assertNotIn("urlopen(", scanner)

    def test_qml_toolbar_remains_controller_navigable_after_adding_import_action(self):
        qml = (ROOT / "gaming/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn("Math.min(3, index)", qml)
        self.assertIn("importEmulatorFolderButton.forceActiveFocus()", qml)
        self.assertIn("addGameButton.forceActiveFocus()", qml)
        self.assertIn("emulatorImportDialog.open()", qml)

    def test_gamepad_and_keyboard_can_navigate_the_custom_folder_browser(self):
        qml = (ROOT / "gaming/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn('action === "up" || action === "down"', qml)
        self.assertIn('action === "left"', qml)
        self.assertIn('action === "confirm" || action === "right"', qml)
        self.assertIn('action === "menu"', qml)
        self.assertIn("Keys.onUpPressed", qml)
        self.assertIn("Keys.onDownPressed", qml)
        self.assertIn("leos.browseEmulatorFolderParent()", qml)
        self.assertIn("leos.useCurrentEmulatorFolder()", qml)

    def test_game_launch_revalidates_emulator_and_source_file(self):
        library = (ROOT / "gaming/backend/library.py").read_text(encoding="utf-8")
        source = library[library.index("def launchGame"):library.index("def launchGame") + 2400]
        self.assertIn("build_emulator_launch_command(", source)
        self.assertIn("self._last_launch_status", source)
        self.assertIn("process.setArguments(command[1:])", library)


if __name__ == "__main__":
    unittest.main()
