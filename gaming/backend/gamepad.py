"""Translate Linux gamepad events into safe, app-local UI actions."""

from __future__ import annotations

from typing import Any


BUTTON_ACTIONS = {
    "BTN_DPAD_UP": "up",
    "BTN_DPAD_DOWN": "down",
    "BTN_DPAD_LEFT": "left",
    "BTN_DPAD_RIGHT": "right",
    "BTN_SOUTH": "confirm",
    "BTN_EAST": "back",
    "BTN_START": "menu",
    "BTN_MODE": "menu",
    "BTN_SELECT": "back",
}


class GamepadActionMapper:
    """Convert button presses and calibrated stick movement into UI actions."""

    def __init__(
        self,
        deadzone_percent: int = 8,
        axis_centers: dict[str, int] | None = None,
        profile: str = "standard",
    ) -> None:
        self._hat_x = 0
        self._hat_y = 0
        self.deadzone_percent = max(0, min(40, int(deadzone_percent)))
        self.axis_centers = dict(axis_centers or {})
        self.profile = profile if profile in {"standard", "xbox", "playstation", "nintendo", "custom"} else "standard"
        self._stick_states = {"ABS_X": 0, "ABS_Y": 0}

    def _button_action(self, name: str) -> str | None:
        if self.profile == "nintendo":
            if name == "BTN_SOUTH":
                return "back"
            if name == "BTN_EAST":
                return "confirm"
        return BUTTON_ACTIONS.get(name)

    def feed(self, event: dict[str, Any]) -> str | None:
        kind = event.get("kind")
        name = event.get("name")
        value = event.get("value")
        if kind == "button" and value == 1:
            return self._button_action(str(name))
        if kind != "axis":
            return None

        axis_name = str(name)
        if axis_name in {"ABS_HAT0X", "ABS_HAT0Y"}:
            return self._hat_action(axis_name, int(value))
        if axis_name in {"ABS_X", "ABS_Y"}:
            return self._stick_action(axis_name, event)
        return None

    def _hat_action(self, name: str, value: int) -> str | None:
        if name == "ABS_HAT0X":
            self._hat_x = max(-1, min(1, value))
            return "left" if self._hat_x < 0 else "right" if self._hat_x > 0 else None
        self._hat_y = max(-1, min(1, value))
        return "up" if self._hat_y < 0 else "down" if self._hat_y > 0 else None

    def _stick_action(self, name: str, event: dict[str, Any]) -> str | None:
        minimum = int(event.get("minimum", -32768))
        maximum = int(event.get("maximum", 32767))
        if maximum <= minimum:
            return None
        default_center = (minimum + maximum) // 2
        center = int(self.axis_centers.get(name, default_center))
        center = max(minimum, min(maximum, center))
        value = max(minimum, min(maximum, int(event["value"])))
        span = (maximum - center) if value >= center else (center - minimum)
        if span <= 0:
            return None
        normalized = (value - center) / span
        threshold = self.deadzone_percent / 100.0
        state = 0 if abs(normalized) <= threshold else (1 if normalized > 0 else -1)
        previous = self._stick_states[name]
        self._stick_states[name] = state
        if state == 0 or state == previous:
            return None
        if name == "ABS_X":
            return "right" if state > 0 else "left"
        return "down" if state > 0 else "up"
