"""Tests for LEOS dock favourites storage."""
import os
import tempfile
import unittest
from pathlib import Path

from desktop.dock_favourites import DockFavourites, DEFAULT_PINNED_APPS


class DockFavouritesTests(unittest.TestCase):
    def test_defaults_are_available_without_creating_a_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dock.json"
            store = DockFavourites(path)
            self.assertEqual(store.items(), list(DEFAULT_PINNED_APPS))
            self.assertFalse(path.exists())

    def test_pin_unpin_and_reorder_persist(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dock.json"
            store = DockFavourites(path)
            store.pin("org.kde.konsole.desktop")
            store.move("org.kde.konsole.desktop", 0)
            store.unpin("steam.desktop")
            restored = DockFavourites(path)
            self.assertEqual(restored.items()[0], "org.kde.konsole.desktop")
            self.assertNotIn("steam.desktop", restored.items())

    def test_rejects_paths_and_invalid_desktop_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            store = DockFavourites(Path(directory) / "dock.json")
            for value in ("../../run.desktop", "/tmp/app.desktop", "app", "", "x\\y.desktop"):
                with self.subTest(value=value), self.assertRaises(ValueError):
                    store.pin(value)

    def test_duplicate_pin_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            store = DockFavourites(Path(directory) / "dock.json")
            store.pin("steam.desktop")
            self.assertEqual(store.items().count("steam.desktop"), 1)

    def test_corrupt_file_keeps_safe_defaults(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dock.json"
            path.write_text('{"items":["../../evil.desktop"]}', encoding="utf-8")
            store = DockFavourites(path)
            self.assertEqual(store.items(), list(DEFAULT_PINNED_APPS))

    def test_saved_file_is_private(self):
        if os.name != "posix":
            self.skipTest("POSIX permissions unavailable")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dock.json"
            DockFavourites(path).pin("org.kde.konsole.desktop")
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()
