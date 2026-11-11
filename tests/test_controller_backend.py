"""Ensure controller discovery never opens Linux input devices for writing."""

import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import controller_center.backend as backend


class FakeGamepad:
    def __init__(self, path, readonly=False):
        self.path = path
        self.readonly = readonly
        self.name = "Test Gamepad"
        self.phys = "usb-test"
        self.uniq = "test-serial"
        self.info = SimpleNamespace(vendor=1, product=2)
        self.closed = False

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

    def test_monitor_opens_read_only_without_extra_nonblocking_api(self):
        monitor = backend.GamepadBackend()
        monitor.open("/dev/input/event0")
        self.assertTrue(self.devices[-1].readonly)
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


    def test_legacy_evdev_opens_descriptor_strictly_read_only(self):
        class LegacyInputDevice:
            def __init__(self, _path):
                raise AssertionError("Legacy constructor must be bypassed")

            def close(self):
                if self.fd >= 0:
                    os.close(self.fd)
                    self.fd = -1

            def capabilities(self):
                return self._rawcapabilities

        helpers = SimpleNamespace(
            ioctl_devinfo=lambda _fd: (3, 1, 2, 1, "Legacy Gamepad", "usb", "serial"),
            ioctl_EVIOCGVERSION=lambda _fd: 1,
            ioctl_capabilities=lambda _fd: {},
            ioctl_EVIOCGEFFECTS=lambda _fd: 0,
        )
        with (
            patch.object(backend, "InputDevice", LegacyInputDevice),
            patch.object(backend, "_input", helpers),
            patch.object(
                backend, "DeviceInfo",
                lambda *values: SimpleNamespace(vendor=values[1], product=values[2]),
            ),
            patch.object(backend.os, "open", return_value=42) as open_mock,
            patch.object(backend.os, "close") as close_mock,
        ):
            device = backend._open_readonly_input_device("/dev/input/event0")
            self.assertEqual(device.fd, 42)
            self.assertEqual(device.name, "Legacy Gamepad")
            self.assertEqual(
                open_mock.call_args.args[1],
                os.O_RDONLY | os.O_NONBLOCK,
            )
            device.close()
            close_mock.assert_called_once_with(42)


if __name__ == "__main__":
    unittest.main()
