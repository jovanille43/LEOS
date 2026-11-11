# LEOS KWin window decoration — alpha

Aurorae theme for KWin window frames and titlebar controls.

## Visual direction

A near-black frame with a restrained cyan → blue-violet → magenta accent line. Active windows receive the brighter gradient; inactive windows use a quieter slate outline. Close, minimize and maximize controls retain recognizable shapes and provide active, inactive, hover, pressed and disabled SVG states.

## Contents

- `metadata.desktop`: Aurorae plugin metadata.
- `leosrc`: titlebar layout, text color, button placement and shadow padding.
- `decoration.svg`: active and inactive nine-slice window frames.
- `close.svg`, `minimize.svg`, `maximize.svg`, `restore.svg`: KWin titlebar controls.

## Installation

System-wide image path: `/usr/share/aurorae/themes/leos/`.

Choose **LEOS** in KDE System Settings → Colors & Themes → Window Decorations. This package is not selected automatically. Users can keep the native Breeze decoration.

## Scope and validation

This decorates KWin window frames; it does not style Plasma panels or application widgets. The companion Plasma Style handles those surfaces separately.

SVG structure and metadata are checked in CI. A real Bazzite KDE session is still required to confirm rendering, button hitboxes, compositor shadows and behavior on maximized windows before enabling it by default.
