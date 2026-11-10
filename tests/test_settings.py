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
            self.assertTrue(settings.get("animations_enabled"))
            self.assertFalse(path.exists())

    def test_values_persist_between_instances(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            settings = SettingsStore(path)
            settings.set("last_mode", "gaming")
            settings.set("sounds_enabled", False)

            reloaded = SettingsStore(path)
            self.assertEqual(reloaded.get("last_mode"), "gaming")
            self.assertFalse(reloaded.get("sounds_enabled"))

    def test_unknown_keys_and_invalid_modes_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            settings = SettingsStore(Path(directory) / "settings.json")
            with self.assertRaises(KeyError):
                settings.set("not_a_setting", True)
            with self.assertRaises(ValueError):
                settings.set("last_mode", "unknown")


if __name__ == "__main__":
    unittest.main()
