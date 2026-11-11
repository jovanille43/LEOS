"""Read-only Linux gamepad discovery and event monitoring."""

from __future__ import annotations

from typing import Any

try:
    from evdev import InputDevice, ecodes, list_devices
except ImportError:  # Keep the UI launchable when the optional backend is missing.
    InputDevice = None  # type: ignore[assignment,misc]
    ecodes = None  # type: ignore[assignment]
    list_devices = None  # type: ignore[assignment]


def backend_available() -> bool:
    return InputDevice is not None and ecodes is not None and list_devices is not None


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
                device = InputDevice(path)
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
            except (OSError, PermissionError):
                continue
            finally:
                if device is not None:
                    device.close()
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
        self.device = InputDevice(path)
        if not _is_gamepad(self.device):
            self.close()
            raise ValueError("This input device is not a game controller")
        self.axes = {}
        self.axis_ranges = {}
        for code in self.device.capabilities().get(ecodes.EV_ABS, []):
            name = ecodes.ABS.get(code, f"AXIS_{code}")
            if isinstance(name, list):
                name = name[0]
            info = self.device.absinfo(code)
            axis_name = str(name)
            self.axes[axis_name] = int(info.value)
            self.axis_ranges[axis_name] = {
                "minimum": int(info.min),
                "maximum": int(info.max),
            }

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
        if self.device is not None:
            self.device.close()
            self.device = None
        self.axes = {}
        self.axis_ranges = {}
