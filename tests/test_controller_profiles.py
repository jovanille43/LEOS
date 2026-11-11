"""Tests for local controller preference storage."""

import json
import tempfile
import unittest
from pathlib import Path

from controller_center.profiles import (
    ControllerProfileStore,
    detect_controller_profile,
    device_profile_id,
)


class ControllerProfileTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.path = Path(self.temp_dir.name) / "controllers.json"
        self.store = ControllerProfileStore(self.path)
        self.device_id = device_profile_id(
            "Example Gamepad", vendor=0x045e, product=0x028e, phys="usb-1-2"
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_defaults_are_returned_for_unknown_device(self):
        self.assertEqual(
            self.store.get(self.device_id),
            {"profile": "auto", "deadzone": 8, "axis_centers": {}},
        )

    def test_preferences_persist_per_device(self):
        self.store.update(
            self.device_id,
            profile="xbox",
            deadzone=12,
            axis_centers={"ABS_X": 25, "ABS_Y": -12},
        )
        self.assertEqual(
            self.store.get(self.device_id),
            {
                "profile": "xbox",
                "deadzone": 12,
                "axis_centers": {"ABS_X": 25, "ABS_Y": -12},
            },
        )
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)

    def test_invalid_profile_and_deadzone_are_rejected(self):
        with self.assertRaises(ValueError):
            self.store.update(self.device_id, profile="unknown")
        with self.assertRaises(ValueError):
            self.store.update(self.device_id, deadzone=90)

    def test_corrupt_file_falls_back_to_defaults(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("{not valid json", encoding="utf-8")
        self.assertEqual(self.store.get(self.device_id)["profile"], "auto")

    def test_detects_known_controller_families_by_usb_identity(self):
        self.assertEqual(
            detect_controller_profile("USB Gamepad", vendor=0x057E, product=0x2009),
            "nintendo",
        )
        self.assertEqual(
            detect_controller_profile("Wireless Controller", vendor=0x054C, product=0x0CE6),
            "playstation",
        )
        self.assertEqual(
            detect_controller_profile("Xbox Wireless Controller", vendor=0x045E),
            "xbox",
        )

    def test_unknown_controller_is_not_misclassified(self):
        self.assertIsNone(
            detect_controller_profile("Generic USB Gamepad", vendor=0x1234, product=0x5678)
        )

    def test_device_id_is_stable_for_same_identity(self):
        first = device_profile_id("Gamepad", 1, 2, phys="usb-port-1")
        second = device_profile_id("Gamepad", 1, 2, phys="usb-port-1")
        self.assertEqual(first, second)

    def test_hardware_serial_keeps_profile_when_usb_port_changes(self):
        first = device_profile_id("Gamepad", 1, 2, phys="usb-port-1", uniq="serial-123")
        second = device_profile_id("Gamepad", 1, 2, phys="usb-port-2", uniq="serial-123")
        self.assertEqual(first, second)

    def test_physical_path_is_fallback_when_serial_is_unavailable(self):
        first = device_profile_id("Gamepad", 1, 2, phys="usb-port-1")
        second = device_profile_id("Gamepad", 1, 2, phys="usb-port-2")
        self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
