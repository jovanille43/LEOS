"""Tests for the bounded, symlink-safe emulator folder browser."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from gaming.backend.emulator_folder_browser import (
    MAX_BROWSE_DIRECTORY_ENTRIES,
    list_child_directories,
    parent_directory,
    resolve_browsable_directory,
    resolve_child_directory,
)


class EmulatorFolderBrowserTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "Library"
        self.root.mkdir()
        (self.root / "Nintendo").mkdir()
        (self.root / "PlayStation").mkdir()
        (self.root / ".hidden").mkdir()

    def tearDown(self):
        self.temporary.cleanup()

    def test_lists_visible_directories_only_in_casefolded_order(self):
        self.assertEqual(
            list_child_directories(self.root),
            ["Nintendo", "PlayStation"],
        )

    def test_child_resolution_rejects_traversal_and_path_separators(self):
        for invalid in ("", ".", "..", "../outside", "a/b", "a\\b", "\x00"):
            with self.subTest(name=invalid):
                self.assertIsNone(resolve_child_directory(self.root, invalid))

    def test_child_resolution_requires_a_real_immediate_child(self):
        nested = self.root / "Nintendo" / "GameCube"
        nested.mkdir()
        self.assertEqual(
            resolve_child_directory(self.root, "Nintendo"),
            (self.root / "Nintendo").resolve(),
        )
        self.assertIsNone(resolve_child_directory(self.root, "Nintendo/GameCube"))

    def test_symlinked_directories_are_not_listed_or_entered(self):
        outside = Path(self.temporary.name) / "Outside"
        outside.mkdir()
        link = self.root / "Linked"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("Symbolic links unavailable")
        self.assertNotIn("Linked", list_child_directories(self.root))
        self.assertIsNone(resolve_child_directory(self.root, "Linked"))
        self.assertIsNone(resolve_browsable_directory(link))

    def test_parent_navigation_stops_at_filesystem_root(self):
        self.assertEqual(parent_directory(self.root), self.root.parent.resolve())
        self.assertIsNone(parent_directory(Path("/")))

    def test_directory_listing_is_bounded(self):
        for index in range(12):
            (self.root / f"Folder-{index:02d}").mkdir()
        with patch(
            "gaming.backend.emulator_folder_browser.MAX_BROWSE_DIRECTORY_ENTRIES", 5
        ):
            listed = list_child_directories(self.root)
        self.assertLessEqual(len(listed), 5)
        self.assertEqual(listed, sorted(listed, key=str.casefold))

    def test_unreadable_or_missing_directories_fail_closed(self):
        self.assertEqual(list_child_directories(self.root / "missing"), [])
        self.assertIsNone(resolve_browsable_directory(self.root / "missing"))


if __name__ == "__main__":
    unittest.main()
