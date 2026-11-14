"""Pure state tracking for currently pressed controller buttons."""

from __future__ import annotations

from typing import Any


def normalize_axis_value(
    value: object,
    minimum: object,
    maximum: object,
    center: object | None = None,
    deadzone: object = 0,
) -> int:
    """Map one raw evdev axis to a deadzone-adjusted -100..100 preview value."""
    if any(type(item) is not int for item in (value, minimum, maximum)):
        return 0
    if maximum <= minimum:
        return 0
    midpoint = (minimum + maximum) // 2
    calibrated_center = (
        center if type(center) is int and minimum < center < maximum
        else midpoint
    )
    if value >= calibrated_center:
        span = maximum - calibrated_center
        normalized = (value - calibrated_center) / span if span else 0.0
    else:
        span = calibrated_center - minimum
        normalized = (value - calibrated_center) / span if span else 0.0
    normalized = max(-1.0, min(1.0, normalized))
    zone = max(0, min(40, deadzone if type(deadzone) is int else 0)) / 100.0
    magnitude = abs(normalized)
    if magnitude <= zone:
        return 0
    adjusted = (magnitude - zone) / (1.0 - zone) if zone < 1.0 else 0.0
    return int(round((1 if normalized >= 0 else -1) * adjusted * 100))


class ControllerInputState:
    """Track held buttons independently of the last event displayed by the UI."""

    def __init__(self) -> None:
        self._pressed_buttons: set[str] = set()

    def consume(self, event: dict[str, Any]) -> str | None:
        kind = event.get("kind")
        name = event.get("name")
        if not isinstance(name, str) or not name:
            return None

        if kind == "button":
            value = event.get("value")
            if value == 1:
                self._pressed_buttons.add(name)
                return f"Bouton pressé : {name}"
            if value == 0:
                self._pressed_buttons.discard(name)
                return f"Bouton relâché : {name}"
            return None

        if kind == "axis":
            return f"Axe {name} : {event.get('value', '—')}"
        return None

    def consume_all(self, events: list[dict[str, Any]]) -> str | None:
        """Apply every queued event and return the last user-visible description."""
        last_description = None
        for event in events:
            description = self.consume(event)
            if description:
                last_description = description
        return last_description

    @property
    def pressed_buttons(self) -> tuple[str, ...]:
        return tuple(sorted(self._pressed_buttons))

    @property
    def buttons_text(self) -> str:
        if not self._pressed_buttons:
            return "Aucun bouton maintenu."
        return "Maintenus : " + " · ".join(sorted(self._pressed_buttons))

    def clear(self) -> None:
        self._pressed_buttons.clear()
