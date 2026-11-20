# LEOS KWin window decoration — alpha

Aurorae theme for KWin window frames and titlebar controls.

## Visual direction

A near-black metallic frame with a restrained accent line. The packaged artwork is a transformation template only: during Desktop profile activation, LEOS recolors the complete SVG set using the user's exact A/B pair. Active windows receive the brighter accent; inactive windows use a quieter slate outline. Close, minimize and maximize controls retain recognizable shapes and provide active, inactive, hover, pressed and disabled SVG states.

## Contents

- `metadata.desktop`: Aurorae plugin metadata.
- `leosrc`: titlebar layout, text color, button placement and shadow padding.
- `decoration.svg`: active and inactive nine-slice window frames.
- `close.svg`, `minimize.svg`, `maximize.svg`, `restore.svg`: KWin titlebar controls.

## Installation

System-wide image path: `/usr/share/aurorae/themes/leos/`.

The packaged Aurorae template is not selected automatically. The Desktop profile creates a matching user-scoped Aurorae variant alongside the Plasma Style and icon theme, then activates it only after explicit consent. The Control Center updates the decoration when A/B changes and offers a guarded restoration to the previous theme. The original source under /usr/share remains untouched.

## Scope and validation

This decorates KWin window frames; it does not style Plasma panels or application widgets. The companion Plasma Style handles those surfaces separately.

SVG structure and metadata are checked in CI. A real Bazzite KDE session is still required to confirm rendering, button hitboxes, compositor shadows and behavior on maximized windows before enabling it by default.
