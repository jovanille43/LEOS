#!/usr/bin/env bash
set -euo pipefail

SOURCE="/usr/share/leos/branding/desktop-logo.jpeg"
THEME_DIR="/usr/share/plymouth/themes/leos"
DESTINATION="${THEME_DIR}/watermark.png"

test -s "${SOURCE}"
install -d -m 0755 "${THEME_DIR}"

python3 - <<'PY'
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage

source = Path("/usr/share/leos/branding/desktop-logo.jpeg")
destination = Path("/usr/share/plymouth/themes/leos/watermark.png")

if source.is_symlink() or not source.is_file():
    raise SystemExit("LEOS Plymouth source emblem is missing or unsafe")

image = QImage(str(source))
if image.isNull():
    raise SystemExit("LEOS Plymouth could not decode the official Desktop emblem")

image = image.scaled(
    640,
    640,
    Qt.AspectRatioMode.KeepAspectRatio,
    Qt.TransformationMode.SmoothTransformation,
)
if not image.save(str(destination), "PNG"):
    raise SystemExit("LEOS Plymouth could not generate its watermark")
destination.chmod(0o644)
PY

test -s "${DESTINATION}"
