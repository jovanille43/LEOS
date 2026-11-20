"""Shared, validated LEOS interface colors.

The LEOS visual identity supports light and dark neutral foundations while
keeping one continuous A-to-B gradient across every LEOS-owned interface.
"""
from __future__ import annotations

import re
from datetime import datetime

DEFAULT_THEME = "leos-original"  # retained for older settings and KDE schemes
# Neutral metallic placeholders are used only until the user chooses A and B.
DEFAULT_COLOR_A = "#A0A0A0"
DEFAULT_COLOR_B = "#D0D0D0"
# Original artwork endpoints are transform inputs only, never user defaults.
SOURCE_COLOR_A = "#00D9FF"
SOURCE_COLOR_B = "#E33BFF"
DEFAULT_APPEARANCE = "dark"
APPEARANCE_MODES = frozenset({"dark", "light", "auto"})
AUTO_LIGHT_START_HOUR = 7
AUTO_DARK_START_HOUR = 19

_BASE_PALETTE: dict[str, str] = {
    "background": "#090B10",
    "surface": "#121720",
    "surface_elevated": "#182732",
    "border": "#293342",
    "text": "#F4F7FB",
    "muted_text": "#909AAC",
}

_LIGHT_BASE_PALETTE: dict[str, str] = {
    "background": "#F4F6FA",
    "surface": "#FFFFFF",
    "surface_elevated": "#E9EEF4",
    "border": "#D3DCE7",
    "text": "#1C2430",
    "muted_text": "#596575",
}


def resolve_appearance_mode(mode: str = DEFAULT_APPEARANCE, now: datetime | None = None) -> str:
    """Resolve dark/light/auto; automatic mode is light 07:00–18:59 local time."""
    if mode not in APPEARANCE_MODES:
        raise ValueError(f"Mode d'apparence inconnu : {mode}")
    if mode != "auto":
        return mode
    local_time = now or datetime.now().astimezone()
    return "light" if AUTO_LIGHT_START_HOUR <= local_time.hour < AUTO_DARK_START_HOUR else "dark"


def _relative_luminance(color: str) -> float:
    channels = [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [
        value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
        for value in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast_ratio(first: str, second: str) -> float:
    first_luminance = _relative_luminance(first)
    second_luminance = _relative_luminance(second)
    return (max(first_luminance, second_luminance) + 0.05) / (
        min(first_luminance, second_luminance) + 0.05
    )


def _accent_text_color(accent: str, palette: dict[str, str]) -> str:
    """Keep an accent as text only when it meets WCAG AA on every LEOS surface."""
    surfaces = ("background", "surface", "surface_elevated")
    if all(_contrast_ratio(accent, palette[surface]) >= 4.5 for surface in surfaces):
        return accent
    return palette["text"]


def _with_accent_text_tokens(palette: dict[str, str]) -> dict[str, str]:
    """Add readable text variants without changing the visual A/B endpoints."""
    result = dict(palette)
    result["accent_primary_text"] = _accent_text_color(result["accent_primary"], result)
    result["accent_secondary_text"] = _accent_text_color(result["accent_secondary"], result)
    return result

# Legacy named palettes remain readable for existing KDE scheme files and old
# preferences, but the interface no longer asks users to choose among them.
_LEGACY_THEME_PALETTES: dict[str, dict[str, str]] = {
    "leos-original": {**_BASE_PALETTE, "accent_primary": SOURCE_COLOR_A, "accent_secondary": SOURCE_COLOR_B},
    "light": {
        "background": "#F3F6FA", "surface": "#FFFFFF", "surface_elevated": "#E8EEF5",
        "border": "#CFD8E3", "text": "#18202B", "muted_text": "#5D6978",
        "accent_primary": "#006B83", "accent_secondary": "#A329B5",
    },
    "cyan": {
        "background": "#071116", "surface": "#0E1D25", "surface_elevated": "#14303C",
        "border": "#245064", "text": "#EAFBFF", "muted_text": "#8CAAB5",
        "accent_primary": "#00D9FF", "accent_secondary": "#5DEBD2",
    },
    "magenta": {
        "background": "#120B16", "surface": "#1C1222", "surface_elevated": "#2C1933",
        "border": "#4B2A57", "text": "#FFF4FF", "muted_text": "#B49AB9",
        "accent_primary": "#E33BFF", "accent_secondary": "#00D9FF",
    },
    "gaming": {
        "background": "#070910", "surface": "#101522", "surface_elevated": "#1A2436",
        "border": "#303D55", "text": "#F5F7FF", "muted_text": "#929DB4",
        "accent_primary": SOURCE_COLOR_A, "accent_secondary": SOURCE_COLOR_B,
    },
}

THEME_PALETTES: dict[str, dict[str, str]] = {
    name: _with_accent_text_tokens(palette)
    for name, palette in _LEGACY_THEME_PALETTES.items()
}

REQUIRED_TOKENS = frozenset({
    "background", "surface", "surface_elevated", "border",
    "text", "muted_text", "accent_primary", "accent_secondary",
    "accent_primary_text", "accent_secondary_text",
})
_COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")


def normalize_color(value: object) -> str:
    """Return a normalized opaque #RRGGBB color or reject the input."""
    if not isinstance(value, str) or _COLOR_PATTERN.fullmatch(value.strip()) is None:
        raise ValueError("Une couleur doit respecter le format #RRGGBB.")
    return value.strip().upper()


def palette_for_colors(
    color_a: str = DEFAULT_COLOR_A,
    color_b: str = DEFAULT_COLOR_B,
    appearance: str = DEFAULT_APPEARANCE,
) -> dict[str, str]:
    """Build the light or dark LEOS palette without changing the selected A/B colors."""
    resolved_appearance = resolve_appearance_mode(appearance)
    base_palette = _LIGHT_BASE_PALETTE if resolved_appearance == "light" else _BASE_PALETTE
    palette = {
        **base_palette,
        "accent_primary": normalize_color(color_a),
        "accent_secondary": normalize_color(color_b),
    }
    return _with_accent_text_tokens(palette)


def palette_for_theme(theme: str) -> dict[str, str]:
    """Return a defensive copy of a legacy named palette."""
    selected = THEME_PALETTES.get(theme, THEME_PALETTES[DEFAULT_THEME])
    return dict(selected)


def validate_palette(palette: object) -> bool:
    """Check that a palette has precisely the required tokens and valid hex colors."""
    if not isinstance(palette, dict) or set(palette) != REQUIRED_TOKENS:
        return False
    return all(
        isinstance(value, str) and _COLOR_PATTERN.fullmatch(value) is not None
        for value in palette.values()
    )


if not all(validate_palette(palette) for palette in THEME_PALETTES.values()):
    raise RuntimeError("A built-in LEOS theme contains invalid color tokens")
