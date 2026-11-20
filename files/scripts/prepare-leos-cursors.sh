#!/usr/bin/env bash
set -euo pipefail

OUTPUT_ROOT="${LEOS_CURSOR_THEME_ROOT:-/usr/share/icons/leos/cursors_scalable}"
export LEOS_CURSOR_THEME_ROOT="${OUTPUT_ROOT}"

python3 - <<'PY'
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

root = Path(os.environ["LEOS_CURSOR_THEME_ROOT"])
if root.is_symlink():
    raise SystemExit("LEOS cursor theme output cannot be a symbolic link")
root.mkdir(parents=True, exist_ok=True, mode=0o755)

def svg(body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32">
  <defs>
    <linearGradient id="leosCursorAccent" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#00D9FF"/>
      <stop offset="1" stop-color="#E33BFF"/>
    </linearGradient>
  </defs>
  {body}
</svg>
'''

def stroke_path(path: str) -> str:
    return (
        f'<path d="{path}" fill="none" stroke="#18202B" stroke-width="4.5" '
        f'stroke-linecap="round" stroke-linejoin="round"/>'
        f'<path d="{path}" fill="none" stroke="url(#leosCursorAccent)" stroke-width="2.6" '
        f'stroke-linecap="round" stroke-linejoin="round"/>'
    )

def arrow_path(path: str) -> str:
    return (
        f'<path d="{path}" fill="#F4F6F8" stroke="#18202B" stroke-width="1.8" stroke-linejoin="round"/>'
        f'<path d="{path}" fill="url(#leosCursorAccent)" opacity="0.32"/>'
    )

cursors = {
    "pointer": (8, 7, svg(
        '<path d="M9 4 C6 1 2 4 4 8 L9 23 C10 26 14 26 15 23 L16 18 '
        'L21 25 C24 29 29 25 26 21 L21 14 L25 13 C29 12 28 8 24 7 Z" '
        'fill="#F4F6F8" stroke="#18202B" stroke-width="1.8" stroke-linejoin="round"/>'
        '<path d="M9 5 C7 3 5 5 6 8 L11 22 L13 17 L20 24 C22 26 24 24 22 22 '
        'L16 14 L23 12 L9 5 Z" fill="url(#leosCursorAccent)" opacity="0.4"/>'
    )),
    "text": (16, 16, svg(
        stroke_path("M10 5 H22 M16 5 V27 M10 27 H22")
        + '<path d="M12 5 V10 M20 5 V10 M12 22 V27 M20 22 V27" fill="none" stroke="#F4F6F8" stroke-width="1.4"/>'
    )),
    "wait": (16, 16, svg(
        '<circle cx="16" cy="16" r="10.5" fill="none" stroke="#18202B" stroke-width="5"/>'
        '<circle cx="16" cy="16" r="10.5" fill="none" stroke="url(#leosCursorAccent)" stroke-width="2.6" '
        'stroke-dasharray="43 23" stroke-linecap="round"/>'
        '<circle cx="16" cy="16" r="3" fill="#F4F6F8" stroke="#18202B" stroke-width="1.5"/>'
    )),
    "progress": (4, 3, svg(
        arrow_path("M4 3 L4 22 L9 17 L13 26 L17 24 L13 15 L21 15 Z")
        + '<circle cx="24" cy="24" r="5.5" fill="#101720" stroke="#18202B" stroke-width="1.4"/>'
        + '<path d="M24 21 V24 L26 25" fill="none" stroke="url(#leosCursorAccent)" stroke-width="1.8" stroke-linecap="round"/>'
    )),
    "crosshair": (16, 16, svg(
        '<circle cx="16" cy="16" r="8" fill="#101720" stroke="#18202B" stroke-width="4"/>'
        '<circle cx="16" cy="16" r="8" fill="none" stroke="url(#leosCursorAccent)" stroke-width="2"/>'
        + stroke_path("M16 2 V11 M16 21 V30 M2 16 H11 M21 16 H30")
    )),
    "not-allowed": (16, 16, svg(
        '<circle cx="16" cy="16" r="11" fill="#101720" stroke="#18202B" stroke-width="4"/>'
        '<circle cx="16" cy="16" r="11" fill="none" stroke="url(#leosCursorAccent)" stroke-width="2.3"/>'
        '<path d="M8 24 L24 8" stroke="#F4F6F8" stroke-width="4" stroke-linecap="round"/>'
        '<path d="M8 24 L24 8" stroke="#18202B" stroke-width="1.5" stroke-linecap="round"/>'
    )),
    "move": (16, 16, svg(
        arrow_path("M16 3 L11 9 H14 V14 H9 V11 L3 16 L9 21 V18 H14 V23 H11 L16 29 L21 23 H18 V18 H23 V21 L29 16 L23 11 V14 H18 V9 H21 Z")
    )),
    "ew-resize": (16, 16, svg(stroke_path("M3 16 H29 M3 16 L9 10 M3 16 L9 22 M29 16 L23 10 M29 16 L23 22"))),
    "ns-resize": (16, 16, svg(stroke_path("M16 3 V29 M16 3 L10 9 M16 3 L22 9 M16 29 L10 23 M16 29 L22 23"))),
    "nwse-resize": (16, 16, svg(stroke_path("M5 5 L27 27 M5 5 L14 5 M5 5 L5 14 M27 27 L18 27 M27 27 L27 18"))),
    "nesw-resize": (16, 16, svg(stroke_path("M27 5 L5 27 M27 5 L18 5 M27 5 L27 14 M5 27 L14 27 M5 27 L5 18"))),
}

def atomic_write(path: Path, content: bytes) -> None:
    if path.is_symlink():
        raise SystemExit(f"LEOS cursor output file is a symbolic link: {path.name}")
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        os.fchmod(fd, 0o644)
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass

for name, (hotspot_x, hotspot_y, image) in cursors.items():
    directory = root / name
    if directory.is_symlink():
        raise SystemExit(f"LEOS cursor output directory is a symbolic link: {name}")
    directory.mkdir(parents=True, exist_ok=True, mode=0o755)
    metadata = [{
        "filename": f"{name}.svg",
        "hotspot_x": hotspot_x,
        "hotspot_y": hotspot_y,
        "nominal_size": 32,
    }]
    atomic_write(directory / f"{name}.svg", image.encode("utf-8"))
    atomic_write(
        directory / "metadata.json",
        (json.dumps(metadata, indent=2) + "\n").encode("utf-8"),
    )

print(f"Generated {len(cursors)} LEOS scalable cursor shapes in {root}")
PY
