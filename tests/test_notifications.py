"""Tests for notification emission from LEOS components."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from desktop.notifications import post_notification
from desktop.notification_store import NotificationStore


class NotificationEmissionTests(unittest.TestCase):
    def test_post_notification_persists_to_xdg_state_home(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict("os.environ", {"XDG_STATE_HOME": directory}):
                identifier = post_notification("Installation terminée", "Steam est prêt.", "success")
                self.assertIsNotNone(identifier)
                path = Path(directory) / "leos" / "notifications.json"
                data = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(data["items"][0]["id"], identifier)
                self.assertEqual(data["items"][0]["level"], "success")

    def test_desktop_notification_uses_native_service_when_available(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict("os.environ", {"XDG_STATE_HOME": directory}):
                with patch("desktop.notifications.shutil.which", return_value="/usr/bin/notify-send"):
                    with patch("desktop.notifications.subprocess.Popen") as run:
                        self.assertIsNotNone(post_notification("Desktop notice", "Body", "warning"))
                        args = run.call_args.args[0]
                        self.assertEqual(args[0], "/usr/bin/notify-send")
                        self.assertIn("--urgency=normal", args)
                        self.assertIn("--", args)
                        self.assertEqual(args[-2:], ["Desktop notice", "Body"])

    def test_gaming_can_persist_without_showing_native_popup(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict("os.environ", {"XDG_STATE_HOME": directory}):
                with patch("desktop.notifications.subprocess.Popen") as run:
                    identifier = post_notification("Gaming event", "Saved locally", native=False)
                    self.assertIsNotNone(identifier)
                    run.assert_not_called()

    def test_native_notifications_are_spawned_without_blocking(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict("os.environ", {"XDG_STATE_HOME": directory}):
                with patch("desktop.notifications.shutil.which", return_value="/usr/bin/notify-send"):
                    with patch("desktop.notifications.subprocess.Popen") as process:
                        self.assertIsNotNone(post_notification("Asynchrone", "Test", "info"))
                        kwargs = process.call_args.kwargs
                        self.assertTrue(kwargs["start_new_session"])
                        self.assertTrue(kwargs["close_fds"])
                        self.assertIs(kwargs["stdin"], __import__("subprocess").DEVNULL)
                        self.assertIs(kwargs["stdout"], __import__("subprocess").DEVNULL)
                        self.assertIs(kwargs["stderr"], __import__("subprocess").DEVNULL)

    def test_native_notification_failure_does_not_break_persistence(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict("os.environ", {"XDG_STATE_HOME": directory}):
                with patch("desktop.notifications.shutil.which", return_value="/usr/bin/notify-send"):
                    with patch("desktop.notifications.subprocess.Popen", side_effect=OSError("no service")):
                        self.assertIsNotNone(post_notification("Still saved", "Inbox fallback"))

    def test_post_notification_does_not_raise_for_invalid_events(self):
        self.assertIsNone(post_notification("", "Contenu", "info"))
        self.assertIsNone(post_notification("Titre", "", "unknown"))

    def test_component_controllers_emit_notifications(self):
        root = Path(__file__).resolve().parents[1]
        shop = (root / "shop/controller.py").read_text(encoding="utf-8")
        control = (root / "control_center/controller.py").read_text(encoding="utf-8")
        self.assertIn("from desktop.notifications import post_notification", shop)
        self.assertIn('post_notification("Boutique LEOS", message, "success")', shop)
        self.assertIn("from desktop.notifications import post_notification", control)
        self.assertIn('post_notification("Thème KDE appliqué", message, "success")', control)
        self.assertIn('post_notification("Sauvegarde Plasma créée", message, "success")', control)

    def test_invalid_existing_history_is_never_overwritten_by_new_event(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "notifications.json"
            original = '{"schema_version":99,"items":[]}'
            path.write_text(original, encoding="utf-8")
            store = NotificationStore(path)
            with self.assertRaises(OSError):
                store.add("Ne pas écraser")
            self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_malformed_level_does_not_crash_validation(self):
        record = {
            "id": "ea7ebf0f-1ff9-4cb9-bc37-d0c8f60acfa4",
            "title": "Titre",
            "body": "",
            "level": [],
            "created_at": "2026-11-11T09:00:00+00:00",
            "read": False,
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "notifications.json"
            path.write_text(json.dumps({"schema_version": 1, "items": [record]}), encoding="utf-8")
            store = NotificationStore(path)
            self.assertEqual(store.items(), [])
            self.assertFalse(store.load())


    def test_native_notification_uses_saved_duration_and_sound_preference(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict("os.environ", {"XDG_STATE_HOME": directory, "XDG_CONFIG_HOME": directory}):
                from leos_core.settings import SettingsStore
                settings = SettingsStore()
                settings.set("notification_duration_seconds", 8)
                settings.set("notification_sounds_enabled", False)
                with patch("desktop.notifications.shutil.which", return_value="/usr/bin/notify-send"):
                    with patch("desktop.notifications.subprocess.Popen") as run:
                        post_notification("Réglage", "Test", "info")
                        args = run.call_args.args[0]
                        self.assertIn("--expire-time=8000", args)
                        self.assertIn("--hint=boolean:suppress-sound:true", args)

    def test_priority_filter_keeps_event_in_history_without_popup(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict("os.environ", {"XDG_STATE_HOME": directory, "XDG_CONFIG_HOME": directory}):
                from leos_core.settings import SettingsStore
                SettingsStore().set("notification_minimum_priority", "critical")
                with patch("desktop.notifications.shutil.which", return_value="/usr/bin/notify-send"):
                    with patch("desktop.notifications.subprocess.Popen") as run:
                        identifier = post_notification("Information", "Conservée", "info")
                        run.assert_not_called()
                self.assertIsNotNone(identifier)
                self.assertEqual(len(NotificationStore().items()), 1)

    def test_silent_gaming_mode_suppresses_native_popup(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict("os.environ", {"XDG_STATE_HOME": directory, "XDG_CONFIG_HOME": directory}):
                from leos_core.settings import SettingsStore
                settings = SettingsStore()
                settings.set("last_mode", "gaming")
                settings.set("silent_notifications_in_gaming", True)
                with patch("desktop.notifications.shutil.which", return_value="/usr/bin/notify-send"):
                    with patch("desktop.notifications.subprocess.Popen") as run:
                        self.assertIsNotNone(post_notification("Jeu", "Événement", "error"))
                        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
