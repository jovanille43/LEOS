# LEOS icon theme — alpha

LEOS follows the visual reference selected for the project: luminous outline icons on a deep black interface, with a smooth cyan-to-blue-to-violet-to-magenta gradient and a restrained outer glow. Shapes stay simple and recognizable at small sizes.

## Included first-party symbols

**Applications**
- `leos-mode-desktop`, `leos-mode-gaming`, `leos-mode-selector`
- `leos-control-center`, `leos-controller-center`, `leos-store`
- `leos-network`, `leos-files`, `leos-display`, `leos-audio`
- `leos-security`, `leos-updates`

**Actions and status**
- `leos-performance`, `leos-library`
- `leos-power`, `leos-search`, `leos-lock`
- `leos-update-available`

The theme inherits from Breeze and hicolor so unprovided names resolve to the host desktop theme rather than displaying missing icons.

These are LEOS-specific symbolic assets, not replacements for the full KDE application icon catalogue. The official lion artwork is deliberately not recreated here; it will be integrated from the supplied source asset when it is available in the repository.

## Installation

Packaged at `/usr/share/icons/leos`. Select **LEOS** from KDE System Settings → Colors & Themes → Icons. Missing icon names fall back through Breeze and hicolor.

This is an initial alpha pack. Validate rendering, glow performance and fallback behavior on a real Bazzite KDE session before making it the default.
