"""Read-only Linux gamepad discovery and event monitoring."""

from __future__ import annotations

import inspect
import os
from typing import Any

try:
    from evdev import InputDevice, _input, ecodes, list_devices
    from evdev.device import DeviceInfo
except ImportError:  # Keep the UI launchable when the optional backend is missing.
    InputDevice = None  # type: ignore[assignment,misc]
    _input = None  # type: ignore[assignment]
    DeviceInfo = None  # type: ignore[assignment,misc]
    ecodes = None  # type: ignore[assignment]
    list_devices = None  # type: ignore[assignment]


def backend_available() -> bool:
    return InputDevice is not None and ecodes is not None and list_devices is not None


def _supports_readonly_open() -> bool:
    if not backend_available():
        return False
    try:
        return "readonly" in inspect.signature(InputDevice).parameters
    except (TypeError, ValueError):
        return False


def _open_readonly_input_device(path: str) -> Any:
    """Open an input event node with O_RDONLY across python-evdev versions.

    python-evdev 2.0 added InputDevice(readonly=True). Fedora's packaged
    1.9.x API does not expose that argument, so use its low-level ioctl helpers
    with an explicitly O_RDONLY descriptor rather than silently opening O_RDWR.
    """
    if _supports_readonly_open():
        return InputDevice(path, readonly=True)

    if _input is None or DeviceInfo is None:
        raise RuntimeError("Read-only evdev support is unavailable")

    device = InputDevice.__new__(InputDevice)
    device.path = path
    device.fd = -1
    fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
    device.fd = fd
    try:
        info = _input.ioctl_devinfo(fd)
        device.info = DeviceInfo(*info[:4])
        device.name = info[4]
        device.phys = info[5]
        device.uniq = info[6]
        device.version = _input.ioctl_EVIOCGVERSION(fd)
        device._rawcapabilities = _input.ioctl_capabilities(fd)
        device.ff_effects_count = _input.ioctl_EVIOCGEFFECTS(fd)
    except Exception:
        os.close(fd)
        device.fd = -1
        raise
    return device


def _is_gamepad(device: Any) -> bool:
    capabilities = device.capabilities()
    keys = set(capabilities.get(ecodes.EV_KEY, []))
    has_gamepad_buttons = any(
        getattr(ecodes, "BTN_JOYSTICK", ecodes.BTN_GAMEPAD) <= code <= ecodes.BTN_THUMBR
        for code in keys
    )
    dpad = any(
        getattr(ecodes, name, -1) in keys
        for name in ("BTN_DPAD_UP", "BTN_DPAD_DOWN", "BTN_DPAD_LEFT", "BTN_DPAD_RIGHT")
    )
    return bool(capabilities.get(ecodes.EV_ABS)) and (has_gamepad_buttons or dpad)


class GamepadBackend:
    """Enumerate controllers and read events without issuing output events."""

    def __init__(self) -> None:
        self.device = None
        self.axes: dict[str, int] = {}
        self.axis_ranges: dict[str, dict[str, int]] = {}

    def scan(self) -> list[dict[str, Any]]:
        if not backend_available():
            return []
        found: list[dict[str, Any]] = []
        for path in list_devices():
            device = None
            try:
                device = _open_readonly_input_device(str(path))
                if not _is_gamepad(device):
                    continue
                info = device.info
                found.append({
                    "path": str(path),
                    "name": device.name or "Manette",
                    "vendor": int(info.vendor),
                    "product": int(info.product),
                    "phys": str(device.phys or ""),
                    "uniq": str(device.uniq or ""),
                    "axes": self._axis_names(device),
                })
            except (OSError, PermissionError, ValueError, RuntimeError):
                continue
            finally:
                if device is not None:
                    try:
                        device.close()
                    except OSError:
                        pass
        return found

    @staticmethod
    def _axis_names(device: Any) -> list[str]:
        names: list[str] = []
        for code in device.capabilities().get(ecodes.EV_ABS, []):
            name = ecodes.ABS.get(code, f"AXIS_{code}")
            names.append(name if isinstance(name, str) else str(name[0]))
        return names

    def open(self, path: str) -> None:
        self.close()
        if not backend_available() or not path.startswith("/dev/input/event"):
            raise ValueError("Invalid input device")

        device = _open_readonly_input_device(path)
        try:
            # python-evdev supplies a non-blocking descriptor; the Qt timer can
            # poll read() without freezing the interface while the controller is idle.
            if not _is_gamepad(device):
                raise ValueError("This input device is not a game controller")

            axes: dict[str, int] = {}
            axis_ranges: dict[str, dict[str, int]] = {}
            for code in device.capabilities().get(ecodes.EV_ABS, []):
                name = ecodes.ABS.get(code, f"AXIS_{code}")
                if isinstance(name, list):
                    name = name[0]
                info = device.absinfo(code)
                axis_name = str(name)
                axes[axis_name] = int(info.value)
                axis_ranges[axis_name] = {
                    "minimum": int(info.min),
                    "maximum": int(info.max),
                }
        except Exception:
            try:
                device.close()
            except OSError:
                pass
            raise

        self.device = device
        self.axes = axes
        self.axis_ranges = axis_ranges

    def poll(self) -> list[dict[str, Any]]:
        if self.device is None:
            return []
        events: list[dict[str, Any]] = []
        try:
            for event in self.device.read():
                if event.type == ecodes.EV_ABS:
                    name = ecodes.ABS.get(event.code, f"AXIS_{event.code}")
                    if isinstance(name, list):
                        name = name[0]
                    self.axes[str(name)] = int(event.value)
                    limits = self.axis_ranges.get(str(name), {})
                    events.append({
                        "kind": "axis",
                        "name": str(name),
                        "value": int(event.value),
                        "minimum": limits.get("minimum", -32768),
                        "maximum": limits.get("maximum", 32767),
                    })
                elif event.type == ecodes.EV_KEY:
                    name = ecodes.BTN.get(event.code, f"BUTTON_{event.code}")
                    if isinstance(name, list):
                        name = name[0]
                    events.append({
                        "kind": "button",
                        "name": str(name),
                        "value": int(event.value),
                    })
        except BlockingIOError:
            return []
        except OSError:
            self.close()
            return []
        return events

    def close(self) -> None:
        device, self.device = self.device, None
        if device is not None:
            try:
                device.close()
            except OSError:
                # A USB/Bluetooth controller may vanish between poll and close.
                pass
        self.axes = {}
        self.axis_ranges = {}
