"""Ensure controller discovery never opens Linux input devices for writing."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

import controller_center.backend as backend


class FakeGamepad:
    def __init__(self, path, readonly=False):
        self.path = path
        self.readonly = readonly
        self.nonblocking = False
        self.name = "Test Gamepad"
        self.phys = "usb-test"
        self.uniq = "test-serial"
        self.info = SimpleNamespace(vendor=1, product=2)
        self.closed = False

    def set_nonblocking(self, value=True):
        self.nonblocking = value

    def capabilities(self):
        return {
            backend.ecodes.EV_KEY: [backend.ecodes.BTN_GAMEPAD],
            backend.ecodes.EV_ABS: [backend.ecodes.ABS_X],
        }

    def absinfo(self, _code):
        return SimpleNamespace(value=0, min=-32768, max=32767)

    def read(self):
        return []

    def close(self):
        self.closed = True


class ReadOnlyGamepadBackendTests(unittest.TestCase):
    def setUp(self):
        self.ecodes = SimpleNamespace(
            EV_KEY=1,
            EV_ABS=3,
            BTN_GAMEPAD=0x130,
            BTN_JOYSTICK=0x120,
            BTN_THUMBR=0x13e,
            BTN_DPAD_UP=0x220,
            BTN_DPAD_DOWN=0x221,
            BTN_DPAD_LEFT=0x222,
            BTN_DPAD_RIGHT=0x223,
            ABS_X=0,
            ABS={0: "ABS_X"},
            BTN={0x130: "BTN_GAMEPAD"},
        )
        self.devices = []

        def factory(path, readonly=False):
            device = FakeGamepad(path, readonly)
            self.devices.append(device)
            return device

        self.patches = [
            patch.object(backend, "InputDevice", factory),
            patch.object(backend, "ecodes", self.ecodes),
            patch.object(backend, "list_devices", lambda: ["/dev/input/event0"]),
        ]
        for item in self.patches:
            item.start()
        self.addCleanup(self.stop_patches)

    def stop_patches(self):
        for item in reversed(self.patches):
            item.stop()

    def test_scan_opens_controller_read_only_and_closes_it(self):
        result = backend.GamepadBackend().scan()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "Test Gamepad")
        self.assertTrue(self.devices[0].readonly)
        self.assertTrue(self.devices[0].closed)

    def test_monitor_opens_read_only_and_sets_nonblocking_mode(self):
        monitor = backend.GamepadBackend()
        monitor.open("/dev/input/event0")
        self.assertTrue(self.devices[-1].readonly)
        self.assertTrue(self.devices[-1].nonblocking)
        self.assertEqual(monitor.poll(), [])
        monitor.close()
        self.assertTrue(self.devices[-1].closed)

    def test_open_rejects_paths_outside_input_event_nodes(self):
        monitor = backend.GamepadBackend()
        with self.assertRaises(ValueError):
            monitor.open("/dev/input/js0")
        self.assertEqual(self.devices, [])

    def test_invalid_device_is_closed_after_open_failure(self):
        class NotAGamepad(FakeGamepad):
            def capabilities(self):
                return {backend.ecodes.EV_KEY: [], backend.ecodes.EV_ABS: []}

        with patch.object(backend, "InputDevice", NotAGamepad):
            monitor = backend.GamepadBackend()
            with self.assertRaises(ValueError):
                monitor.open("/dev/input/event0")
        self.assertTrue(monitor.device is None)


if __name__ == "__main__":
    unittest.main()
