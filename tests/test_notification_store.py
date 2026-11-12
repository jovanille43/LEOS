"""Tests for the LEOS private notification inbox."""
import os
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from desktop.notification_store import NotificationStore, MAX_NOTIFICATIONS


class NotificationStoreTests(unittest.TestCase):
    def test_add_and_reload_notification(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "notifications.json"
            store = NotificationStore(path)
            identifier = store.add("Mise à jour disponible", "Une nouvelle version est prête.", "success")
            restored = NotificationStore(path)
            self.assertEqual(restored.items()[0]["id"], identifier)
            self.assertEqual(restored.unread_count(), 1)

    def test_mark_read_dismiss_and_clear(self):
        with tempfile.TemporaryDirectory() as directory:
            store = NotificationStore(Path(directory) / "inbox.json")
            first = store.add("Premier")
            second = store.add("Second")
            self.assertTrue(store.mark_read(first))
            self.assertEqual(store.unread_count(), 1)
            self.assertTrue(store.dismiss(second))
            store.mark_all_read()
            self.assertEqual(store.unread_count(), 0)
            store.clear()
            self.assertEqual(store.items(), [])

    def test_newest_first_and_bounded_history(self):
        with tempfile.TemporaryDirectory() as directory:
            store = NotificationStore(Path(directory) / "inbox.json")
            identifiers = [store.add(f"Événement {i}") for i in range(MAX_NOTIFICATIONS + 3)]
            self.assertEqual(len(store.items()), MAX_NOTIFICATIONS)
            self.assertEqual(store.items()[0]["id"], identifiers[-1])

    def test_rejects_invalid_input(self):
        with tempfile.TemporaryDirectory() as directory:
            store = NotificationStore(Path(directory) / "inbox.json")
            for args in (("", "", "info"), ("x" * 161, "", "info"), ("Titre", "", "critical")):
                with self.assertRaises(ValueError):
                    store.add(*args)
            with self.assertRaises(ValueError):
                store.add("Titre", "x" * 2001)

    def test_corrupt_file_is_not_overwritten_during_load(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "inbox.json"
            path.write_text('{"schema_version":9}', encoding="utf-8")
            store = NotificationStore(path)
            self.assertEqual(store.items(), [])
            self.assertEqual(path.read_text(encoding="utf-8"), '{"schema_version":9}')

    def test_oversized_history_is_ignored_and_preserved(self):
        from desktop.notification_store import MAX_NOTIFICATION_FILE_BYTES

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "inbox.json"
            oversized = b" " * (MAX_NOTIFICATION_FILE_BYTES + 1)
            path.write_bytes(oversized)
            store = NotificationStore(path)
            self.assertEqual(store.items(), [])
            self.assertEqual(path.read_bytes(), oversized)
            with self.assertRaises(OSError):
                store.add("Ne pas écraser")
            self.assertEqual(path.read_bytes(), oversized)

    def test_reload_clears_stale_events_after_external_corruption(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "inbox.json"
            store = NotificationStore(path)
            store.add("Événement valide")
            self.assertEqual(store.unread_count(), 1)
            path.write_text("{broken", encoding="utf-8")
            self.assertEqual(store.items(), [])
            self.assertEqual(store.unread_count(), 0)

    def test_boolean_schema_version_is_not_accepted_as_integer_one(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "inbox.json"
            path.write_text('{"schema_version":true,"items":[]}', encoding="utf-8")
            store = NotificationStore(path)
            self.assertFalse(store.load())
            self.assertEqual(store.items(), [])
            self.assertEqual(path.read_text(encoding="utf-8"), '{"schema_version":true,"items":[]}')

    def test_saved_file_is_private(self):
        if os.name != "posix":
            self.skipTest("POSIX permissions unavailable")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "inbox.json"
            NotificationStore(path).add("Privé")
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(path.parent.stat().st_mode & 0o777, 0o700)

    def test_concurrent_process_style_writes_do_not_lose_notifications(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "notifications.json"

            def add_event(index):
                return NotificationStore(path).add(f"Événement {index}")

            with ThreadPoolExecutor(max_workers=10) as executor:
                identifiers = list(executor.map(add_event, range(50)))

            restored = NotificationStore(path)
            records = restored.items()
            self.assertEqual(len(records), 50)
            self.assertEqual(restored.unread_count(), 50)
            self.assertEqual(len({item["id"] for item in records}), 50)
            self.assertEqual(set(identifiers), {item["id"] for item in records})

    def test_existing_history_directory_is_restricted_before_write(self):
        if os.name != "posix":
            self.skipTest("POSIX permissions unavailable")
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory) / "history"
            parent.mkdir(mode=0o755)
            parent.chmod(0o755)
            path = parent / "notifications.json"
            NotificationStore(path).add("Privé")
            self.assertEqual(parent.stat().st_mode & 0o777, 0o700)

    def test_notification_lock_file_is_private(self):
        if os.name != "posix":
            self.skipTest("POSIX permissions unavailable")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "notifications.json"
            NotificationStore(path).add("Verrouillé")
            lock_path = path.with_name(path.name + ".lock")
            self.assertEqual(lock_path.stat().st_mode & 0o777, 0o600)

    def test_long_lived_instances_refresh_items_and_unread_count(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "inbox.json"
            desktop = NotificationStore(path)
            gaming = NotificationStore(path)
            identifier = desktop.add("Nouveau message")
            self.assertEqual(gaming.unread_count(), 1)
            self.assertEqual(gaming.items()[0]["id"], identifier)
            self.assertTrue(desktop.mark_read(identifier))
            self.assertEqual(gaming.unread_count(), 0)
            self.assertEqual(gaming.items(unread_only=True), [])


if __name__ == "__main__":
    unittest.main()
