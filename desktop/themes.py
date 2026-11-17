"""Validated LEOS palettes with optional user-selected dual accents."""

from __future__ import annotations

import re
from typing import Any

DEFAULT_THEME = "leos-original"
CUSTOM_THEME = "custom"
DEFAULT_ACCENT_PRIMARY = "#00D9FF"
DEFAULT_ACCENT_SECONDARY = "#E33BFF"

THEME_PALETTES: dict[str, dict[str, str]] = {
    "leos-original": {
        "background": "#090B10",
        "surface": "#121720",
        "surface_elevated": "#182732",
        "border": "#293342",
        "text": "#F4F7FB",
        "muted_text": "#909AAC",
        "accent_primary": DEFAULT_ACCENT_PRIMARY,
        "accent_secondary": DEFAULT_ACCENT_SECONDARY,
    },
    "light": {
        "background": "#F3F6FA",
        "surface": "#FFFFFF",
        "surface_elevated": "#E8EEF5",
        "border": "#CFD8E3",
        "text": "#18202B",
        "muted_text": "#5D6978",
        "accent_primary": "#006B83",
        "accent_secondary": "#A329B5",
    },
    "cyan": {
        "background": "#071116",
        "surface": "#0E1D25",
        "surface_elevated": "#14303C",
        "border": "#245064",
        "text": "#EAFBFF",
        "muted_text": "#8CAAB5",
        "accent_primary": "#00D9FF",
        "accent_secondary": "#5DEBD2",
    },
    "magenta": {
        "background": "#120B16",
        "surface": "#1C1222",
        "surface_elevated": "#2C1933",
        "border": "#4B2A57",
        "text": "#FFF4FF",
        "muted_text": "#B49AB9",
        "accent_primary": "#E33BFF",
        "accent_secondary": "#00D9FF",
    },
    "gaming": {
        "background": "#070910",
        "surface": "#101522",
        "surface_elevated": "#1A2436",
        "border": "#303D55",
        "text": "#F5F7FF",
        "muted_text": "#929DB4",
        "accent_primary": DEFAULT_ACCENT_PRIMARY,
        "accent_secondary": DEFAULT_ACCENT_SECONDARY,
    },
}

REQUIRED_TOKENS = frozenset({
    "background",
    "surface",
    "surface_elevated",
    "border",
    "text",
    "muted_text",
    "accent_primary",
    "accent_secondary",
})
_COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")


def normalize_hex_color(value: object) -> str | None:
    """Return a normalized #RRGGBB color or None for invalid input."""
    if not isinstance(value, str) or not _COLOR_PATTERN.fullmatch(value.strip()):
        return None
    return value.strip().upper()


def is_valid_hex_color(value: object) -> bool:
    return normalize_hex_color(value) is not None


def validate_palette(palette: object) -> bool:
    """Check that a palette has precisely the required tokens and valid hex colors."""
    if not isinstance(palette, dict) or set(palette) != REQUIRED_TOKENS:
        return False
    return all(is_valid_hex_color(value) for value in palette.values())


def palette_for_theme(
    theme: str,
    accent_primary: str | None = None,
    accent_secondary: str | None = None,
) -> dict[str, str]:
    """Return a defensive copy of a preset or a custom dual-accent palette."""
    if theme == CUSTOM_THEME:
        selected = dict(THEME_PALETTES[DEFAULT_THEME])
        selected["accent_primary"] = (
            normalize_hex_color(accent_primary) or DEFAULT_ACCENT_PRIMARY
        )
        selected["accent_secondary"] = (
            normalize_hex_color(accent_secondary) or DEFAULT_ACCENT_SECONDARY
        )
        return selected
    selected = THEME_PALETTES.get(theme, THEME_PALETTES[DEFAULT_THEME])
    return dict(selected)


def palette_for_settings(settings: Any) -> dict[str, str]:
    """Build the live palette from one consistent settings snapshot when available."""
    snapshot_reader = getattr(settings, "snapshot", None)
    if callable(snapshot_reader):
        theme, accent_primary, accent_secondary = snapshot_reader((
            "theme",
            "custom_accent_primary",
            "custom_accent_secondary",
        ))
    else:
        # Keep compatibility with simple settings adapters used by integrations
        # and tests that expose only the get(key, default) interface.
        theme = settings.get("theme", DEFAULT_THEME)
        accent_primary = settings.get(
            "custom_accent_primary", DEFAULT_ACCENT_PRIMARY
        )
        accent_secondary = settings.get(
            "custom_accent_secondary", DEFAULT_ACCENT_SECONDARY
        )

    if theme == CUSTOM_THEME:
        return palette_for_theme(CUSTOM_THEME, accent_primary, accent_secondary)
    return palette_for_theme(str(theme))


if not all(validate_palette(palette) for palette in THEME_PALETTES.values()):
    raise RuntimeError("A built-in LEOS theme contains invalid color tokens")
