# LEOS icon theme — base template

LEOS uses luminous outline icons on a deep neutral interface. The packaged
SVGs contain legacy preview accents only. They are not an imposed cyan/blue/
violet/magenta palette.

On activation, LEOS creates a uniquely named copy in the user's
`XDG_DATA_HOME/icons`, recolors the SVG resources with the same freely
chosen A/B gradient used by Desktop, Gaming, wallpaper and the Plasma Style,
and applies that per-user variant. The official source files under
`/usr/share/icons/leos` remain unchanged.

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

The theme inherits from Breeze and hicolor so unprovided names resolve to
the host desktop theme rather than displaying missing icons. The official
lion artwork is handled separately and is never replaced with a generic
symbol.

Packaged at `/usr/share/icons/leos`; user-selected variants are installed
under `XDG_DATA_HOME/icons/leos-custom-<id>`. The Control Center can generate
and apply a new variant after either accent color changes.
