"""Tests for safe LEOS desktop layout preference storage."""
import os
import tempfile
import unittest
from pathlib import Path

from desktop.layouts import DesktopLayoutStore, DEFAULT_LAYOUT, PROFILES, validate_layout


class DesktopLayoutTests(unittest.TestCase):
    def test_default_layout_is_valid_and_does_not_enable_widgets(self):
        self.assertTrue(validate_layout(DEFAULT_LAYOUT))
        self.assertFalse(DEFAULT_LAYOUT["widgets_enabled"])

    def test_profiles_are_saved_and_reloaded(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "desktop-layout.json"
            store = DesktopLayoutStore(path)
            store.apply_profile("minimal")
            reloaded = DesktopLayoutStore(path)
            self.assertEqual(reloaded.get("profile"), "minimal")
            self.assertTrue(reloaded.get("dock")["auto_hide"])

    def test_custom_dock_preferences_are_persisted(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "desktop-layout.json"
            store = DesktopLayoutStore(path)
            store.set_dock(position="left", alignment="right", auto_hide=True)
            saved = DesktopLayoutStore(path)
            self.assertEqual(saved.get("profile"), "custom")
            self.assertEqual(saved.get("dock")["position"], "left")
            self.assertEqual(saved.get("dock")["alignment"], "right")
            self.assertTrue(saved.get("dock")["auto_hide"])

    def test_custom_profile_survives_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "desktop-layout.json"
            store = DesktopLayoutStore(path)
            store.set_dock(position="right", auto_hide=True)
            store.set_widgets_enabled(True)
            restored = DesktopLayoutStore(path)
            self.assertEqual(restored.get("profile"), "custom")
            self.assertEqual(restored.get("dock")["position"], "right")
            self.assertTrue(restored.get("dock")["auto_hide"])
            self.assertTrue(restored.get("widgets_enabled"))

    def test_layout_store_returns_a_copy_of_dock_preferences(self):
        with tempfile.TemporaryDirectory() as directory:
            store = DesktopLayoutStore(Path(directory) / "desktop-layout.json")
            dock = store.get("dock")
            dock["position"] = "left"
            self.assertEqual(store.get("dock")["position"], "bottom")

    def test_invalid_layout_schema_is_rejected(self):
        self.assertFalse(validate_layout({"schema_version": 2, "profile": "leos-default"}))

    def test_malformed_layout_types_are_rejected_without_crashing(self):
        malformed = {
            "schema_version": 1,
            "profile": [],
            "dock": {
                "enabled": True,
                "position": [],
                "alignment": "center",
                "auto_hide": False,
            },
            "widgets_enabled": False,
        }
        self.assertFalse(validate_layout(malformed))

    def test_invalid_profile_and_dock_values_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            store = DesktopLayoutStore(Path(directory) / "desktop-layout.json")
            with self.assertRaises(ValueError):
                store.apply_profile("unknown")
            with self.assertRaises(ValueError):
                store.set_dock(position="diagonal")
            with self.assertRaises(TypeError):
                store.set_dock(auto_hide="yes")

    def test_corrupt_or_invalid_file_falls_back_without_overwriting_it(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "desktop-layout.json"
            path.write_text('{"profile":"bad"}', encoding="utf-8")
            store = DesktopLayoutStore(path)
            self.assertEqual(store.get("profile"), DEFAULT_LAYOUT["profile"])
            self.assertEqual(path.read_text(encoding="utf-8"), '{"profile":"bad"}')

    def test_saved_preferences_have_private_permissions(self):
        if os.name != "posix":
            self.skipTest("POSIX permissions are unavailable")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "desktop-layout.json"
            DesktopLayoutStore(path).apply_profile("workspace")
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_all_presets_have_valid_layout_data(self):
        for name, preset in PROFILES.items():
            layout = {
                "schema_version": 1,
                "profile": name,
                "dock": dict(preset["dock"]),
                "widgets_enabled": preset["widgets_enabled"],
            }
            self.assertTrue(validate_layout(layout), name)

    def test_control_center_exposes_saved_desktop_layout_preferences(self):
        root = Path(__file__).resolve().parents[1]
        controller = (root / "control_center" / "controller.py").read_text(encoding="utf-8")
        qml = (root / "control_center" / "qml" / "Main.qml").read_text(encoding="utf-8")
        self.assertIn("DesktopLayoutStore()", controller)
        self.assertIn("def applyDesktopLayout(self, profile: str)", controller)
        self.assertIn("def setDockPosition(self, position: str)", controller)
        self.assertIn("controlCenter.desktopLayoutProfile", qml)
        self.assertIn("Préférences enregistrées localement", qml)
        self.assertIn("KDE Plasma ne sera pas modifié", qml)


if __name__ == "__main__":
    unittest.main()
