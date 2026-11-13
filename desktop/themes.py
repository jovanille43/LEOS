"""Shared, validated LEOS interface colors.

The LEOS visual identity keeps one dark neutral foundation and one continuous
A-to-B gradient. Users may choose any two opaque RGB colors; every LEOS-owned
interface reads the same pair from the shared settings store.
"""
from __future__ import annotations

import re

DEFAULT_THEME = "leos-original"  # retained for older settings and KDE schemes
DEFAULT_COLOR_A = "#00D9FF"
DEFAULT_COLOR_B = "#E33BFF"

_BASE_PALETTE: dict[str, str] = {
    "background": "#090B10",
    "surface": "#121720",
    "surface_elevated": "#182732",
    "border": "#293342",
    "text": "#F4F7FB",
    "muted_text": "#909AAC",
}

# Legacy named palettes remain readable for existing KDE scheme files and old
# preferences, but the interface no longer asks users to choose among them.
THEME_PALETTES: dict[str, dict[str, str]] = {
    "leos-original": {**_BASE_PALETTE, "accent_primary": DEFAULT_COLOR_A, "accent_secondary": DEFAULT_COLOR_B},
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
        "accent_primary": DEFAULT_COLOR_A, "accent_secondary": DEFAULT_COLOR_B,
    },
}

REQUIRED_TOKENS = frozenset({
    "background", "surface", "surface_elevated", "border",
    "text", "muted_text", "accent_primary", "accent_secondary",
})
_COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")


def normalize_color(value: object) -> str:
    """Return a normalized opaque #RRGGBB color or reject the input."""
    if not isinstance(value, str) or _COLOR_PATTERN.fullmatch(value.strip()) is None:
        raise ValueError("Une couleur doit respecter le format #RRGGBB.")
    return value.strip().upper()


def palette_for_colors(color_a: str = DEFAULT_COLOR_A, color_b: str = DEFAULT_COLOR_B) -> dict[str, str]:
    """Build the shared dark LEOS palette using the selected gradient endpoints."""
    return {
        **_BASE_PALETTE,
        "accent_primary": normalize_color(color_a),
        "accent_secondary": normalize_color(color_b),
    }


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
