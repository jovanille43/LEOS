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
    """Convert button presses and D-pad hat changes into one-shot actions."""

    def __init__(self) -> None:
        self._hat_x = 0
        self._hat_y = 0

    def feed(self, event: dict[str, Any]) -> str | None:
        kind = event.get("kind")
        name = event.get("name")
        value = event.get("value")
        if kind == "button" and value == 1:
            return BUTTON_ACTIONS.get(str(name))
        if kind != "axis" or name not in {"ABS_HAT0X", "ABS_HAT0Y"}:
            return None

        if name == "ABS_HAT0X":
            self._hat_x = max(-1, min(1, int(value)))
        else:
            self._hat_y = max(-1, min(1, int(value)))

        if name == "ABS_HAT0X":
            return "left" if self._hat_x < 0 else "right" if self._hat_x > 0 else None
        return "up" if self._hat_y < 0 else "down" if self._hat_y > 0 else None
