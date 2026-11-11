# LEOS icon theme — alpha

LEOS uses a restrained neon-symbolic direction: clean, legible outlines with a cyan accent and restrained magenta details. The icon theme inherits from Breeze and hicolor so unprovided names resolve to the host desktop theme rather than displaying missing icons.

## Included first-party symbols

- `leos-mode-desktop`
- `leos-mode-gaming`
- `leos-control-center`
- `leos-store`
- `leos-performance`
- `leos-library`

These are LEOS-specific symbolic assets, not replacements for the full KDE application icon catalogue. The official lion artwork is deliberately not recreated here; it will be integrated from the supplied source asset when it is available in the repository.

## Installation

Packaged at `/usr/share/icons/leos`. Select **LEOS** from KDE System Settings → Colors & Themes → Icons. Missing icon names fall back through Breeze and hicolor.

This is an initial alpha pack. Validate rendering and fallback behavior on a real Bazzite KDE session before making it the default.
