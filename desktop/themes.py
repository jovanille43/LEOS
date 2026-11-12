"""Validated, user-selectable LEOS interface palettes.

These palettes are presentation tokens for LEOS-owned interfaces. They do not
rewrite KDE Plasma colors, themes, or other existing user configuration.
"""

from __future__ import annotations

import re

DEFAULT_THEME = "leos-original"

THEME_PALETTES: dict[str, dict[str, str]] = {
    "leos-original": {
        "background": "#090B10",
        "surface": "#121720",
        "surface_elevated": "#182732",
        "border": "#293342",
        "text": "#F4F7FB",
        "muted_text": "#909AAC",
        "accent_primary": "#00D9FF",
        "accent_secondary": "#E33BFF",
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
        "accent_primary": "#00D9FF",
        "accent_secondary": "#E33BFF",
    },
}

REQUIRED_TOKENS = frozenset(
    {
        "background",
        "surface",
        "surface_elevated",
        "border",
        "text",
        "muted_text",
        "accent_primary",
        "accent_secondary",
    }
)
_COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")


def palette_for_theme(theme: str) -> dict[str, str]:
    """Return a defensive copy of a known palette; unknown names use LEOS Original."""
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
