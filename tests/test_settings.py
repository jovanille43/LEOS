"""Tests for shared LEOS settings."""

import tempfile
import unittest
from pathlib import Path

from leos_core.settings import SettingsStore


class SettingsStoreTests(unittest.TestCase):
    def test_defaults_are_available_without_creating_a_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            settings = SettingsStore(path)
            self.assertEqual(settings.get("last_mode"), "desktop")
            self.assertEqual(settings.get("theme"), "leos-original")
            self.assertEqual(settings.get("performance_profile"), "balanced")
            self.assertTrue(settings.get("animations_enabled"))
            self.assertTrue(settings.get("notifications_enabled"))
            self.assertEqual(settings.get("notification_duration_seconds"), 5)
            self.assertTrue(settings.get("silent_notifications_in_gaming"))
            self.assertFalse(path.exists())

    def test_values_persist_between_instances(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            settings = SettingsStore(path)
            settings.set("last_mode", "gaming")
            settings.set("sounds_enabled", False)
            settings.set("theme", "cyan")
            settings.set("performance_profile", "quiet")

            reloaded = SettingsStore(path)
            self.assertEqual(reloaded.get("last_mode"), "gaming")
            self.assertFalse(reloaded.get("sounds_enabled"))
            self.assertEqual(reloaded.get("theme"), "cyan")
            self.assertEqual(reloaded.get("performance_profile"), "quiet")

    def test_unknown_keys_and_invalid_values_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            settings = SettingsStore(Path(directory) / "settings.json")
            with self.assertRaises(KeyError):
                settings.set("not_a_setting", True)
            with self.assertRaises(ValueError):
                settings.set("last_mode", "unknown")
            with self.assertRaises(ValueError):
                settings.set("theme", "nonexistent")
            with self.assertRaises(TypeError):
                settings.set("sounds_enabled", "false")
            with self.assertRaises(ValueError):
                settings.set("notification_duration_seconds", 12)
            with self.assertRaises(ValueError):
                settings.set("notification_minimum_priority", "low")


    def test_long_lived_instances_observe_each_others_changes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            desktop = SettingsStore(path)
            gaming = SettingsStore(path)

            desktop.set("notification_duration_seconds", 8)
            self.assertEqual(gaming.get("notification_duration_seconds"), 8)

            gaming.set("silent_notifications_in_gaming", False)
            self.assertFalse(desktop.get("silent_notifications_in_gaming"))
            self.assertEqual(desktop.get("notification_duration_seconds"), 8)

    def test_separate_instances_preserve_unrelated_updates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            first = SettingsStore(path)
            second = SettingsStore(path)

            first.set("theme", "cyan")
            second.set("sounds_enabled", False)

            final = SettingsStore(path)
            self.assertEqual(final.get("theme"), "cyan")
            self.assertFalse(final.get("sounds_enabled"))


    def test_snapshot_refreshes_all_requested_keys_together(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            first = SettingsStore(path)
            second = SettingsStore(path)
            first.set("theme", "magenta")
            first.set("notification_duration_seconds", 3)
            self.assertEqual(
                second.snapshot(("theme", "notification_duration_seconds")),
                ("magenta", 3),
            )

if __name__ == "__main__":
    unittest.main()
