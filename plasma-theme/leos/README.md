# LEOS Plasma Style — alpha

This is an original, minimal Plasma 6 desktop theme package. It deliberately
provides only a small set of SVG assets and lets Plasma fall back to Breeze
for elements not yet customized.

- `metadata.json`: Plasma 6 style metadata.
- `plasmarc`: subtle background contrast and blur settings.
- `widgets/panel-background.svg`: dark glass-like panel with restrained cyan
  to magenta edge lighting.
- `dialogs/background.svg`: matching widget popup and KRunner surface.
- `widgets/background.svg`: desktop widget surface.
- `widgets/button.svg`: normal, hover, pressed and focus states, including
  borderless toolbutton states.

The package does not include the official LEOS lion artwork because the source
assets have not yet been added to the repository. It must not substitute a
generic lion or fabricate a replacement emblem.

Install path in the image: `/usr/share/plasma/desktoptheme/leos`.
The style is packaged but is not automatically selected. It must first be
tested on a real Bazzite KDE session. Missing SVG elements intentionally use
the installed Breeze fallback.

The Plasma Style affects Plasma surfaces, not all Qt application controls.
The separate LEOS KDE color scheme continues to control compatible app colors.
