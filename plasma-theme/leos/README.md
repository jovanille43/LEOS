# LEOS Plasma Style — alpha

This is an original, minimal Plasma 6 desktop theme package. It deliberately
provides only a small set of SVG assets and lets Plasma fall back to Breeze
for elements not yet customized.

- `metadata.json`: Plasma 6 style metadata.
- `plasmarc`: subtle background contrast and blur settings.
- `widgets/panel-background.svg`: dark glass-like panel template with legacy
  starter accents; LEOS recolors a per-user variant from the selected A/B pair.
- `dialogs/background.svg`: matching widget popup and KRunner surface; its
  accent gradient is recolored in the same per-user variant.
- `widgets/background.svg`: desktop widget surface.
- `widgets/button.svg`: normal, hover, pressed and focus states, including
  borderless toolbutton states.
- `widgets/tooltip.svg`: matching nine-slice tooltip surface.
- `widgets/lineedit.svg`: base, hover and focus field states.
- `widgets/menubaritem.svg`: normal, hover and pressed menu-item states.
- `widgets/viewitem.svg`: normal, hover and selected list/result states.
- `widgets/arrows.svg`: navigation arrows recolored from the same A/B pair.

The package does not include the official LEOS lion artwork because the source
assets have not yet been added to the repository. It must not substitute a
generic lion or fabricate a replacement emblem.

Install path in the image: `/usr/share/plasma/desktoptheme/leos`.
The style is packaged but is not automatically selected. It must first be
tested on a real Bazzite KDE session. Missing SVG elements intentionally use
the installed Breeze fallback.

The Plasma Style affects Plasma surfaces, not all Qt application controls.
The separate LEOS KDE color scheme continues to control compatible app colors.

## Custom A/B variants

The packaged `leos` directory is an immutable source template. During Desktop activation, LEOS creates a deterministic per-user Plasma Style variant under `$XDG_DATA_HOME/plasma/desktoptheme/` and applies its unique `leos-custom-*` identifier. SVG accent colors are transformed from the chosen A/B pair while neutral metallic greys remain neutral. Files under `/usr/share` are never edited; the previous Plasma Style can still be restored through LEOS.
