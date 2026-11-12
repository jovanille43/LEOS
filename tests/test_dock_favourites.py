"""Tests for LEOS dock favourites storage."""
import os
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
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

    def test_oversized_dock_file_is_not_loaded_or_overwritten(self):
        from desktop.dock_favourites import MAX_DOCK_FILE_BYTES

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dock.json"
            raw = b" " * (MAX_DOCK_FILE_BYTES + 1)
            path.write_bytes(raw)
            store = DockFavourites(path)
            self.assertEqual(store.items(), list(DEFAULT_PINNED_APPS))
            with self.assertRaises(ValueError):
                store.pin("org.example.Safe.desktop")
            self.assertEqual(path.read_bytes(), raw)

    def test_saved_file_is_private(self):
        if os.name != "posix":
            self.skipTest("POSIX permissions unavailable")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dock.json"
            DockFavourites(path).pin("org.kde.konsole.desktop")
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_long_lived_instances_observe_changes_from_other_windows(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dock.json"
            first = DockFavourites(path)
            second = DockFavourites(path)
            first.pin("org.example.One.desktop")
            self.assertIn("org.example.One.desktop", second.items())
            second.pin("org.example.Two.desktop")
            self.assertIn("org.example.Two.desktop", first.items())

    def test_concurrent_pins_from_separate_instances_do_not_overwrite_each_other(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dock.json"
            first = DockFavourites(path)
            second = DockFavourites(path)
            operations = (
                (first, "org.example.First.desktop"),
                (second, "org.example.Second.desktop"),
            )
            with ThreadPoolExecutor(max_workers=2) as executor:
                list(executor.map(lambda item: item[0].pin(item[1]), operations))
            restored = DockFavourites(path)
            self.assertIn("org.example.First.desktop", restored.items())
            self.assertIn("org.example.Second.desktop", restored.items())

    def test_invalid_existing_file_is_never_overwritten_by_mutations(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dock.json"
            invalid = '{"items":["../../evil.desktop"]}'
            path.write_text(invalid, encoding="utf-8")
            store = DockFavourites(path)
            self.assertEqual(store.items(), list(DEFAULT_PINNED_APPS))
            with self.assertRaises(ValueError):
                store.pin("org.example.Safe.desktop")
            self.assertEqual(path.read_text(encoding="utf-8"), invalid)

    def test_deeply_nested_json_is_ignored_without_crashing(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dock.json"
            path.write_text("[" * 2000 + "]" * 2000, encoding="utf-8")
            store = DockFavourites(path)
            self.assertEqual(store.items(), list(DEFAULT_PINNED_APPS))
            with self.assertRaises(ValueError):
                store.pin("org.example.Safe.desktop")

    def test_lock_file_is_private(self):
        if os.name != "posix":
            self.skipTest("POSIX permissions unavailable")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dock.json"
            DockFavourites(path).pin("org.example.Safe.desktop")
            lock_path = path.with_name(path.name + ".lock")
            self.assertEqual(lock_path.stat().st_mode & 0o777, 0o600)

    def test_symlink_store_is_not_followed_or_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target.json"
            target.write_text('{"schema_version":1,"items":[]}', encoding="utf-8")
            link = root / "dock.json"
            try:
                link.symlink_to(target)
            except (OSError, NotImplementedError):
                self.skipTest("Symbolic links unavailable")
            store = DockFavourites(link)
            self.assertEqual(store.items(), list(DEFAULT_PINNED_APPS))
            with self.assertRaises((OSError, ValueError)):
                store.pin("org.example.Safe.desktop")
            self.assertEqual(
                target.read_text(encoding="utf-8"),
                '{"schema_version":1,"items":[]}',
            )

    def test_atomic_toggle_returns_new_pin_state(self):
        with tempfile.TemporaryDirectory() as directory:
            store = DockFavourites(Path(directory) / "dock.json")
            self.assertTrue(store.toggle("org.example.Toggle.desktop"))
            self.assertIn("org.example.Toggle.desktop", store.items())
            self.assertFalse(store.toggle("org.example.Toggle.desktop"))
            self.assertNotIn("org.example.Toggle.desktop", store.items())

    def test_concurrent_toggles_from_two_instances_are_serialized(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dock.json"
            first = DockFavourites(path)
            second = DockFavourites(path)
            with ThreadPoolExecutor(max_workers=2) as executor:
                results = list(executor.map(
                    lambda store: store.toggle("org.example.Toggle.desktop"),
                    (first, second),
                ))
            self.assertEqual(sorted(results), [False, True])
            self.assertNotIn("org.example.Toggle.desktop", DockFavourites(path).items())

    def test_move_by_reorders_one_step_and_rejects_invalid_targets(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dock.json"
            store = DockFavourites(path)
            original = store.items()
            self.assertTrue(store.move_by("steam.desktop", -1))
            moved = store.items()
            self.assertEqual(moved.index("steam.desktop"), original.index("steam.desktop") - 1)
            self.assertFalse(store.move_by("org.kde.dolphin.desktop", -1))
            with self.assertRaises(ValueError):
                store.move_by("org.example.Missing.desktop", 1)
            with self.assertRaises(ValueError):
                store.move_by("steam.desktop", 0)


if __name__ == "__main__":
    unittest.main()
