# LEOS Plasma Style — base template

This is an original, minimal Plasma 6 desktop theme package. It deliberately
provides only a small set of SVG assets and lets Plasma fall back to Breeze
for elements not yet customized.

The packaged files are immutable base templates. On first-run Desktop
activation, LEOS creates a uniquely named copy in the user's
`XDG_DATA_HOME/plasma/desktoptheme`, recolors its SVG assets from the user's
freely selected A/B accent pair, and applies that per-user variant. The
metallic neutral axis and dark surfaces are preserved. The original files
under `/usr/share/plasma/desktoptheme/leos` are never modified.

- `metadata.json`: Plasma 6 style metadata.
- `plasmarc`: subtle background contrast and blur settings.
- `widgets/` and `dialogs/`: dark glass-like Plasma surfaces and controls.
- Missing SVG elements intentionally use the installed Breeze fallback.

The package does not include the official LEOS lion artwork; branding assets
are generated separately from the official source artwork and are never
fabricated here.

Install path in the image: `/usr/share/plasma/desktoptheme/leos`.
The base template is not selected directly by the first-run flow. LEOS first
creates the user's A/B variant and then applies it. The Control Center can
regenerate and apply a new variant after the user changes A or B.

The panel treatment now includes a dedicated `widgets/tasks.svg`: task tiles
remain graphite at rest, lift subtly on hover, and use a narrow A/B indicator
for the active or attention state. The indicator uses the same two source
endpoints as the other LEOS surfaces so the first-run recoloring keeps the
user's chosen accents. A newly created dock uses the LEOS menu launcher from
the task manager rather than adding a second, unrelated Kickoff menu.

A dedicated `widgets/plasmoidheading.svg` also styles the two orientations
of Plasma widget popups: LEOS graphite headers with a restrained A/B lower
edge, and matching graphite footers with a neutral metallic separator.

The style version is incremented whenever packaged SVG resources change so
Plasma can refresh its cached assets. A dedicated `widgets/tabbar.svg` now
provides active-tab frames for north, east, south and west orientations, with
the active edge carrying the same subtle, user-recolored A/B accent.

Native Plasma controls are now covered by `widgets/slider.svg`,
`widgets/radiobutton.svg` and `widgets/checkmarks.svg`. Sliders use a
neutral graphite rail, a low-intensity A/B active segment and a metallic
handle with visible hover/focus rings. Radio and check marks remain legible
without introducing a fixed accent color. The Plasma style version is raised
to invalidate cached theme resources.
