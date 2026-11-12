"""Tests for local controller preference storage."""

import json
import os
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
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

    def test_deeply_nested_profile_json_is_ignored_and_never_overwritten(self):
        invalid = "[" * 2000 + "0" + "]" * 2000
        self.path.write_text(invalid, encoding="utf-8")

        self.assertEqual(
            self.store.get(self.device_id),
            {"profile": "auto", "deadzone": 8, "axis_centers": {}},
        )
        with self.assertRaisesRegex(ValueError, "unreadable or too large"):
            self.store.update(self.device_id, profile="xbox")
        self.assertEqual(self.path.read_text(encoding="utf-8"), invalid)

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

    def test_concurrent_updates_preserve_both_settings(self):
        first = ControllerProfileStore(self.path)
        second = ControllerProfileStore(self.path)
        operations = (
            (first, {"profile": "xbox"}),
            (second, {"deadzone": 17}),
        )
        with ThreadPoolExecutor(max_workers=2) as executor:
            list(executor.map(
                lambda item: item[0].update(self.device_id, **item[1]),
                operations,
            ))
        self.assertEqual(
            ControllerProfileStore(self.path).get(self.device_id),
            {"profile": "xbox", "deadzone": 17, "axis_centers": {}},
        )

    def test_corrupt_file_is_not_overwritten_by_update(self):
        invalid = "{not valid json"
        self.path.write_text(invalid, encoding="utf-8")
        with self.assertRaises(ValueError):
            self.store.update(self.device_id, profile="xbox")
        self.assertEqual(self.path.read_text(encoding="utf-8"), invalid)

    def test_oversized_profile_file_is_rejected_and_never_overwritten(self):
        from controller_center.profiles import MAX_PROFILE_FILE_BYTES

        raw = b" " * (MAX_PROFILE_FILE_BYTES + 1)
        self.path.write_bytes(raw)
        self.assertEqual(self.store.get(self.device_id)["profile"], "auto")
        with self.assertRaisesRegex(ValueError, "too large"):
            self.store.update(self.device_id, profile="xbox")
        self.assertEqual(self.path.read_bytes(), raw)

    def test_loaded_profile_axis_centres_are_capped(self):
        from controller_center.profiles import MAX_AXIS_CENTERS

        record = {
            "profile": "custom",
            "deadzone": 8,
            "axis_centers": {f"ABS_{index}": index for index in range(MAX_AXIS_CENTERS + 20)},
        }
        validated = self.store._validated_record(record)
        self.assertEqual(len(validated["axis_centers"]), MAX_AXIS_CENTERS)

    def test_device_identity_hashing_bounds_untrusted_descriptor_fields(self):
        from controller_center.profiles import device_profile_id

        first = device_profile_id("X" * 10000, phys="P" * 10000)
        second = device_profile_id("X" * 256, phys="P" * 256)
        self.assertEqual(first, second)

    def test_number_of_saved_controller_profiles_is_bounded(self):
        from controller_center.profiles import MAX_CONTROLLER_PROFILES

        devices = {
            f"device-{index}": {"profile": "auto", "deadzone": 8, "axis_centers": {}}
            for index in range(MAX_CONTROLLER_PROFILES)
        }
        self.path.write_text(json.dumps({"version": 1, "devices": devices}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Too many"):
            self.store.update("new-controller", profile="xbox")
        saved = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(len(saved["devices"]), MAX_CONTROLLER_PROFILES)

    def test_axis_centres_are_bounded_and_names_are_validated(self):
        with self.assertRaises(ValueError):
            self.store.update(self.device_id, axis_centers={"": 0})
        with self.assertRaises(ValueError):
            self.store.update(self.device_id, axis_centers={"X" * 49: 0})
        centres = {f"ABS_{index}": 0 for index in range(65)}
        with self.assertRaisesRegex(ValueError, "Too many"):
            self.store.update(self.device_id, axis_centers=centres)

    def test_symbolic_link_profile_file_is_rejected(self):
        target = self.path.with_name("target.json")
        target.write_text('{"version":1,"devices":{}}', encoding="utf-8")
        try:
            self.path.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("Symbolic links unavailable")
        with self.assertRaises(OSError):
            self.store.update(self.device_id, profile="xbox")
        self.assertEqual(target.read_text(encoding="utf-8"), '{"version":1,"devices":{}}')

    def test_existing_profile_directory_is_restricted_before_write(self):
        if os.name != "posix":
            self.skipTest("POSIX permissions unavailable")
        parent = self.path.parent / "config"
        parent.mkdir(mode=0o755)
        parent.chmod(0o755)
        store = ControllerProfileStore(parent / "controllers.json")
        store.update(self.device_id, profile="xbox")
        self.assertEqual(parent.stat().st_mode & 0o777, 0o700)

    def test_lock_file_is_private(self):
        if os.name != "posix":
            self.skipTest("POSIX permissions unavailable")
        self.store.update(self.device_id, profile="xbox")
        lock_path = self.path.with_name(self.path.name + ".lock")
        self.assertEqual(lock_path.stat().st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()
