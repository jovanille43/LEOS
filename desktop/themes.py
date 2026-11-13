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
    "emerald-gold": "LEOS Émeraude & Or",
    "yellow-red": "LEOS Jaune & Rouge",
    "electric-blue-orange": "LEOS Bleu électrique & Orange",
    "violet-gold": "LEOS Violet & Or",
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
    "emerald-gold": {
        "background": "#090B10",
        "surface": "#121720",
        "surface_elevated": "#182732",
        "border": "#293342",
        "text": "#F4F7FB",
        "muted_text": "#909AAC",
        "accent_primary": "#00F0A0",
        "accent_secondary": "#FFD84D",
    },
    "yellow-red": {
        "background": "#090B10",
        "surface": "#121720",
        "surface_elevated": "#182732",
        "border": "#293342",
        "text": "#F4F7FB",
        "muted_text": "#909AAC",
        "accent_primary": "#FFF000",
        "accent_secondary": "#FF335A",
    },
    "electric-blue-orange": {
        "background": "#090B10",
        "surface": "#121720",
        "surface_elevated": "#182732",
        "border": "#293342",
        "text": "#F4F7FB",
        "muted_text": "#909AAC",
        "accent_primary": "#168BFF",
        "accent_secondary": "#FF7A1A",
    },
    "violet-gold": {
        "background": "#090B10",
        "surface": "#121720",
        "surface_elevated": "#182732",
        "border": "#293342",
        "text": "#F4F7FB",
        "muted_text": "#909AAC",
        "accent_primary": "#A855F7",
        "accent_secondary": "#FFD84D",
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


CUSTOM_THEME_PREFIX = "custom-"
_CUSTOM_THEME_PATTERN = re.compile(r"^custom-([0-9A-Fa-f]{6})([0-9A-Fa-f]{6})$")


def custom_theme_id(accent_primary: str, accent_secondary: str) -> str:
    """Encode any opaque two-color pair in a stable, settings-safe theme ID."""
    if not isinstance(accent_primary, str) or not _COLOR_PATTERN.fullmatch(accent_primary):
        raise ValueError("La couleur A doit être au format #RRGGBB.")
    if not isinstance(accent_secondary, str) or not _COLOR_PATTERN.fullmatch(accent_secondary):
        raise ValueError("La couleur B doit être au format #RRGGBB.")
    return CUSTOM_THEME_PREFIX + accent_primary[1:].lower() + accent_secondary[1:].lower()


def custom_colors_from_theme(theme: str) -> tuple[str, str] | None:
    """Decode a custom pair without consulting settings or mutable global state."""
    if not isinstance(theme, str):
        return None
    match = _CUSTOM_THEME_PATTERN.fullmatch(theme)
    if match is None:
        return None
    return f"#{match.group(1).upper()}", f"#{match.group(2).upper()}"


def is_valid_theme_id(theme: str) -> bool:
    """Accept built-in presets and syntactically valid unrestricted custom pairs."""
    return isinstance(theme, str) and (
        theme in THEME_PALETTES or custom_colors_from_theme(theme) is not None
    )


def theme_display_name(theme: str) -> str:
    """Return a readable label for either a preset or a custom pair."""
    return THEME_NAMES.get(theme, "LEOS Personnalisé")


def palette_for_theme(theme: str) -> dict[str, str]:
    """Return a defensive copy of a preset or a custom two-accent palette."""
    selected = THEME_PALETTES.get(theme)
    if selected is not None:
        return dict(selected)
    custom_pair = custom_colors_from_theme(theme)
    if custom_pair is None:
        return dict(THEME_PALETTES[DEFAULT_THEME])
    return {
        **_NEUTRAL_TOKENS,
        "accent_primary": custom_pair[0],
        "accent_secondary": custom_pair[1],
    }


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


def _relative_luminance(color: str) -> float:
    channels = [int(color[index:index + 2], 16) / 255.0 for index in (1, 3, 5)]
    linear = [
        value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
        for value in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast_ratio(first: str, second: str) -> float:
    """Calculate the WCAG contrast ratio between two six-digit colors."""
    first_luminance = _relative_luminance(first)
    second_luminance = _relative_luminance(second)
    return (max(first_luminance, second_luminance) + 0.05) / (min(first_luminance, second_luminance) + 0.05)


def _best_text_color(background: str) -> str:
    """Choose black or white for legible text placed on a colored accent fill."""
    return "#000000" if contrast_ratio("#000000", background) >= contrast_ratio("#FFFFFF", background) else "#FFFFFF"


def visual_tokens_for_theme(theme: str) -> dict[str, object]:
    """Expose selected accents, stable gradient roles and contrast-aware text tokens."""
    palette = palette_for_theme(theme)
    white = "#FFFFFF"
    primary = palette["accent_primary"]
    secondary = palette["accent_secondary"]
    primary_ratio = contrast_ratio(primary, palette["surface"])
    secondary_ratio = contrast_ratio(secondary, palette["surface"])
    pair_ratio = contrast_ratio(primary, secondary)
    warnings = []
    if primary_ratio < 3.0 or secondary_ratio < 3.0:
        warnings.append("Un accent risque d'être peu visible sur les surfaces sombres.")
    if pair_ratio < 1.5:
        warnings.append("Les deux accents sont très proches visuellement.")
    return {
        **palette,
        "accent_primary_glow": _mix_hex(primary, white, 0.34),
        "accent_secondary_glow": _mix_hex(secondary, white, 0.34),
        "accent_primary_soft": _mix_hex(primary, palette["background"], 0.68),
        "accent_secondary_soft": _mix_hex(secondary, palette["background"], 0.68),
        "accent_gradient_mid": _mix_hex(primary, secondary, 0.5),
        "accent_primary_text": primary if primary_ratio >= 4.5 else palette["text"],
        "accent_secondary_text": secondary if secondary_ratio >= 4.5 else palette["text"],
        "accent_primary_on_fill": _best_text_color(primary),
        "accent_secondary_on_fill": _best_text_color(secondary),
        "accent_primary_surface_contrast": round(primary_ratio, 2),
        "accent_secondary_surface_contrast": round(secondary_ratio, 2),
        "accent_pair_contrast": round(pair_ratio, 2),
        "contrast_warning": bool(warnings),
        "contrast_warning_text": " ".join(warnings) + (" Tes couleurs restent inchangées : choisis librement." if warnings else ""),
    }


def theme_options(current_theme: str | None = None) -> list[dict[str, str]]:
    """Return presets and the active custom pair, when the player has one selected."""
    options = [
        {
            "id": theme_id,
            "name": THEME_NAMES[theme_id],
            "accent_primary": palette["accent_primary"],
            "accent_secondary": palette["accent_secondary"],
        }
        for theme_id, palette in THEME_PALETTES.items()
    ]
    custom_pair = custom_colors_from_theme(current_theme or "")
    if custom_pair is not None:
        options.append({
            "id": current_theme or "",
            "name": "LEOS Personnalisé",
            "accent_primary": custom_pair[0],
            "accent_secondary": custom_pair[1],
        })
    return options


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
