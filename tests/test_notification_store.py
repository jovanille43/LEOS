"""Tests for the LEOS private notification inbox."""
import os
import tempfile
import unittest
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

    def test_saved_file_is_private(self):
        if os.name != "posix":
            self.skipTest("POSIX permissions unavailable")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "inbox.json"
            NotificationStore(path).add("Privé")
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(path.parent.stat().st_mode & 0o777, 0o700)


if __name__ == "__main__":
    unittest.main()
