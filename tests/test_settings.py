"""Tests for shared LEOS settings."""

import json
import os
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
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
            self.assertEqual(settings.get("transition_app_policy"), "ask")
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
    def test_transition_policy_requires_confirmation_and_rejects_close_or_keep(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            settings = SettingsStore(path)
            for policy in ("keep", "close", "automatic"):
                with self.subTest(policy=policy):
                    with self.assertRaises(ValueError):
                        settings.set("transition_app_policy", policy)
            settings.set("transition_app_policy", "ask")
            self.assertEqual(SettingsStore(path).get("transition_app_policy"), "ask")

    def test_legacy_automatic_transition_policy_falls_back_to_ask(self) -> None:
        import json

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            path.write_text(
                json.dumps({"transition_app_policy": "close"}),
                encoding="utf-8",
            )
            settings = SettingsStore(path)
            self.assertEqual(settings.get("transition_app_policy"), "ask")

    def test_concurrent_updates_from_separate_instances_are_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            first = SettingsStore(path)
            second = SettingsStore(path)
            with ThreadPoolExecutor(max_workers=2) as executor:
                list(executor.map(
                    lambda item: item[0].set(item[1], item[2]),
                    [
                        (first, "theme", "magenta"),
                        (second, "sounds_enabled", False),
                    ],
                ))
            final = SettingsStore(path)
            self.assertEqual(final.get("theme"), "magenta")
            self.assertFalse(final.get("sounds_enabled"))

    def test_corrupt_settings_are_not_overwritten_by_update(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            invalid = "{broken json"
            path.write_text(invalid, encoding="utf-8")
            with self.assertRaises(ValueError):
                SettingsStore(path).set("theme", "cyan")
            self.assertEqual(path.read_text(encoding="utf-8"), invalid)

    def test_invalid_utf8_settings_are_preserved_during_read_and_update(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            invalid = bytes((0xFF, 0xFE, 0x80))
            path.write_bytes(invalid)

            settings = SettingsStore(path)
            self.assertEqual(settings.get("last_mode"), "desktop")
            self.assertEqual(path.read_bytes(), invalid)

            with self.assertRaises(ValueError):
                settings.set("theme", "cyan")
            self.assertEqual(path.read_bytes(), invalid)

    def test_oversized_settings_are_ignored_and_never_overwritten(self) -> None:
        from leos_core.settings import MAX_SETTINGS_BYTES

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            invalid = b" " * (MAX_SETTINGS_BYTES + 1)
            path.write_bytes(invalid)

            settings = SettingsStore(path)
            self.assertEqual(settings.get("theme"), "leos-original")
            self.assertEqual(path.read_bytes(), invalid)

            with self.assertRaisesRegex(ValueError, "too large"):
                settings.set("theme", "cyan")
            self.assertEqual(path.read_bytes(), invalid)

    def test_corrupt_reload_resets_values_to_safe_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            settings = SettingsStore(path)
            settings.set("theme", "magenta")
            self.assertEqual(settings.get("theme"), "magenta")

            path.write_text("{broken", encoding="utf-8")
            self.assertEqual(settings.get("theme"), "leos-original")
            self.assertEqual(settings.get("last_mode"), "desktop")

    def test_symbolic_link_settings_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "settings.json"
            target = root / "target.json"
            target.write_text('{"theme":"magenta"}', encoding="utf-8")
            try:
                path.symlink_to(target)
            except (OSError, NotImplementedError):
                self.skipTest("Symbolic links unavailable")
            with self.assertRaises(OSError):
                SettingsStore(path).set("theme", "cyan")
            self.assertEqual(target.read_text(encoding="utf-8"), '{"theme":"magenta"}')

    def test_settings_lock_file_is_private(self) -> None:
        if os.name != "posix":
            self.skipTest("POSIX permissions unavailable")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            SettingsStore(path).set("theme", "cyan")
            lock_path = path.with_name(path.name + ".lock")
            self.assertEqual(lock_path.stat().st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()
