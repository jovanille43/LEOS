"""Pure normalization helpers for live analog-stick readouts."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def _normalized_axis(
    axes: Mapping[str, Any],
    ranges: Mapping[str, Mapping[str, Any]],
    name: str,
) -> float | None:
    """Map one evdev absolute axis to [-1, 1], or return None when unavailable."""
    if name not in axes:
        return None
    try:
        value = int(axes[name])
        limits = ranges.get(name, {})
        minimum = int(limits.get("minimum", -32768))
        maximum = int(limits.get("maximum", 32767))
    except (TypeError, ValueError, OverflowError, AttributeError):
        return None
    if maximum <= minimum:
        return None
    normalized = ((value - minimum) / (maximum - minimum)) * 2.0 - 1.0
    return round(max(-1.0, min(1.0, normalized)), 4)


def build_stick_visuals(
    axes: Mapping[str, Any],
    ranges: Mapping[str, Mapping[str, Any]],
) -> dict[str, bool | float]:
    """Return stable QML properties for the two conventional evdev stick pairs."""
    left_x = _normalized_axis(axes, ranges, "ABS_X")
    left_y = _normalized_axis(axes, ranges, "ABS_Y")
    right_x = _normalized_axis(axes, ranges, "ABS_RX")
    right_y = _normalized_axis(axes, ranges, "ABS_RY")
    return {
        "leftAvailable": left_x is not None and left_y is not None,
        "leftX": left_x if left_x is not None else 0.0,
        "leftY": left_y if left_y is not None else 0.0,
        "rightAvailable": right_x is not None and right_y is not None,
        "rightX": right_x if right_x is not None else 0.0,
        "rightY": right_y if right_y is not None else 0.0,
    }
