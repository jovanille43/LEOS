"""Validated, user-selectable LEOS two-accent palettes.

A theme is always a pair of distinct accents. Derived highlight, glow and soft
surface tokens are computed from that pair so UI components do not need to
invent their own shades or collapse both accents into a single color.
"""
from __future__ import annotations

import re

DEFAULT_THEME = "leos-original"

THEME_NAMES: dict[str, str] = {
    "leos-original": "LEOS Original",
    "light": "LEOS Light",
    "cyan": "LEOS Cyan",
    "magenta": "LEOS Magenta",
    "gaming": "LEOS Gaming",
}

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

# The player selects an accent pair, not a different desktop design.
# Keep the original LEOS dark surfaces and typography identical in every palette.
_NEUTRAL_TOKENS = {
    key: THEME_PALETTES[DEFAULT_THEME][key]
    for key in (
        "background",
        "surface",
        "surface_elevated",
        "border",
        "text",
        "muted_text",
    )
}
for _palette in THEME_PALETTES.values():
    _palette.update(_NEUTRAL_TOKENS)


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


def _mix_hex(first: str, second: str, second_weight: float) -> str:
    if not 0.0 <= second_weight <= 1.0:
        raise ValueError("Color mix weight must be between zero and one")
    first_rgb = tuple(int(first[index:index + 2], 16) for index in (1, 3, 5))
    second_rgb = tuple(int(second[index:index + 2], 16) for index in (1, 3, 5))
    result = tuple(
        round(a * (1.0 - second_weight) + b * second_weight)
        for a, b in zip(first_rgb, second_rgb)
    )
    return "#" + "".join(f"{channel:02X}" for channel in result)


def visual_tokens_for_theme(theme: str) -> dict[str, str]:
    """Expose the base pair plus consistent glow, soft and gradient color roles."""
    palette = palette_for_theme(theme)
    white = "#FFFFFF"
    return {
        **palette,
        "accent_primary_glow": _mix_hex(palette["accent_primary"], white, 0.24),
        "accent_secondary_glow": _mix_hex(palette["accent_secondary"], white, 0.24),
        "accent_primary_soft": _mix_hex(
            palette["accent_primary"], palette["background"], 0.68
        ),
        "accent_secondary_soft": _mix_hex(
            palette["accent_secondary"], palette["background"], 0.68
        ),
        "accent_gradient_mid": _mix_hex(
            palette["accent_primary"], palette["accent_secondary"], 0.5
        ),
    }


def theme_options() -> list[dict[str, str]]:
    """Return display metadata for selectors; future palettes appear automatically."""
    return [
        {
            "id": theme_id,
            "name": THEME_NAMES[theme_id],
            "accent_primary": palette["accent_primary"],
            "accent_secondary": palette["accent_secondary"],
        }
        for theme_id, palette in THEME_PALETTES.items()
    ]


def validate_palette(palette: object) -> bool:
    """Check that all required tokens exist and contain valid six-digit hex colors."""
    if not isinstance(palette, dict) or set(palette) != REQUIRED_TOKENS:
        return False
    return all(
        isinstance(value, str) and _COLOR_PATTERN.fullmatch(value) is not None
        for value in palette.values()
    )


if set(THEME_NAMES) != set(THEME_PALETTES):
    raise RuntimeError("LEOS theme names and palettes are out of sync")
if not all(validate_palette(palette) for palette in THEME_PALETTES.values()):
    raise RuntimeError("A built-in LEOS theme contains invalid color tokens")
if any(
    palette["accent_primary"].lower() == palette["accent_secondary"].lower()
    for palette in THEME_PALETTES.values()
):
    raise RuntimeError("Every LEOS theme must contain two distinct accent colors")
