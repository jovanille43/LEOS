"""Translate Linux gamepad events into safe, app-local UI actions."""

from __future__ import annotations

from typing import Any
import time

from controller_center.profiles import detect_controller_profile


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


def mapper_from_preferences(
    preferences: dict[str, Any],
    device: dict[str, Any] | None = None,
) -> "GamepadActionMapper":
    """Build Gaming navigation using saved preferences and optional auto-detection."""
    profile = preferences.get("profile", "auto")
    if profile == "auto":
        device = device or {}
        profile = detect_controller_profile(
            str(device.get("name", "")),
            int(device.get("vendor", 0)),
            int(device.get("product", 0)),
        ) or "standard"
    return GamepadActionMapper(
        deadzone_percent=preferences.get("deadzone", 8),
        axis_centers=preferences.get("axis_centers", {}),
        profile=profile,
    )


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
        self._held_directions: dict[str, str] = {}
        self._repeat_delay = 0.38
        self._repeat_interval = 0.12
        self._repeat_started_at = 0.0
        self._repeat_last_at = 0.0

    def _button_action(self, name: str) -> str | None:
        if self.profile == "nintendo":
            if name == "BTN_SOUTH":
                return "back"
            if name == "BTN_EAST":
                return "confirm"
        return BUTTON_ACTIONS.get(name)

    def feed(self, event: dict[str, Any]) -> str | None:
        kind = event.get("kind")
        name = str(event.get("name", ""))
        value = event.get("value")
        now = time.monotonic()

        if kind == "button":
            action = self._button_action(name)
            if value == 1:
                if action in {"up", "down", "left", "right"}:
                    return self._update_held_direction(name, action, now)
                return action
            if value == 0:
                self._update_held_direction(name, None, now)
            return None

        if kind != "axis":
            return None

        if name == "ABS_HAT0X":
            self._hat_x = max(-1, min(1, int(value)))
            action = "left" if self._hat_x < 0 else "right" if self._hat_x > 0 else None
        elif name == "ABS_HAT0Y":
            self._hat_y = max(-1, min(1, int(value)))
            action = "up" if self._hat_y < 0 else "down" if self._hat_y > 0 else None
        elif name in {"ABS_X", "ABS_Y"}:
            action = self._stick_action(name, event)
        else:
            return None

        return self._update_held_direction(name, action, now)

    def _current_held_direction(self) -> str | None:
        if not self._held_directions:
            return None
        return next(reversed(self._held_directions.values()))

    def _update_held_direction(
        self, source: str, action: str | None, now: float
    ) -> str | None:
        previous = self._current_held_direction()
        self._held_directions.pop(source, None)
        if action is not None:
            self._held_directions[source] = action
        current = self._current_held_direction()
        if current != previous:
            self._repeat_started_at = now
            self._repeat_last_at = now
            return current if action is not None else None
        return None

    def repeat_action(self, now: float | None = None) -> str | None:
        """Return a held direction after the initial delay and at a steady rate."""
        current = self._current_held_direction()
        if current is None:
            return None
        now = time.monotonic() if now is None else now
        if now - self._repeat_started_at < self._repeat_delay:
            return None
        if now - self._repeat_last_at < self._repeat_interval:
            return None
        self._repeat_last_at = now
        return current

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
        self._stick_states[name] = state
        if state == 0:
            return None
        if name == "ABS_X":
            return "right" if state > 0 else "left"
        return "down" if state > 0 else "up"
