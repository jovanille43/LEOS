"""Pure state tracking for currently pressed controller buttons."""

from __future__ import annotations

from typing import Any


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
