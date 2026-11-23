# LEOS Plasma Style — metallic base theme

This original Plasma 6 style gives LEOS a coordinated, near-black metallic
surface system with restrained A/B accent details. It includes native SVG
assets for panels, widget backgrounds, dialogs, buttons, line edits, selections,
tooltips, widget headers and footers, task-manager states, and panel editing
controls. Less-common Plasma elements continue to use the Breeze fallback
until they receive a dedicated LEOS treatment.

The accent endpoints in the source artwork are transformation inputs only.
On first-run Desktop activation, LEOS creates a uniquely named copy in the
user's `XDG_DATA_HOME/plasma/desktoptheme`, recolors all supported SVG accents
with the user's exact A/B pair, and applies that per-user variant. The neutral
metallic surfaces remain intact. The original files under
`/usr/share/plasma/desktoptheme/leos` are never modified.

Key files:
- `metadata.json`: Plasma 6 style metadata.
- `plasmarc`: restrained background contrast and blur settings.
- `dialogs/background.svg`: panel popup and widget dialog surfaces.
- `widgets/panel-background.svg` and `widgets/background.svg`: panel and desktop widget surfaces.
- `widgets/button.svg`, `lineedit.svg`, and `viewitem.svg`: controls, input fields, and selection states.
- `widgets/plasmoidheading.svg`: native widget headers and footers.
- `widgets/tasks.svg`: task-manager states, including keyboard focus and hover.
- `widgets/containment-controls.svg`: panel edit-mode and resize controls.
- `widgets/arrows.svg` and `widgets/tooltip.svg`: matching navigation and task tooltips.

The package does not include or fabricate the official LEOS lion artwork;
branding resources are generated separately from the supplied source assets.

Install path in the image: `/usr/share/plasma/desktoptheme/leos`.
The base template is not selected directly by the first-run flow. LEOS first
creates the user's A/B variant and then applies it. The Control Center can
regenerate and apply a new variant after the user changes A or B.
