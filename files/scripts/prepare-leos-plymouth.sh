#!/usr/bin/env bash
set -euo pipefail

SOURCE="/usr/share/leos/branding/desktop-logo.png"
THEME_DIR="/usr/share/plymouth/themes/leos"
DESTINATION="${THEME_DIR}/watermark.png"

if [[ ! -s "${SOURCE}" ]]; then
    echo "::error::LEOS Desktop emblem missing at ${SOURCE}; checking copied branding paths:"
    find /usr/share/leos -maxdepth 3 -type f -name 'desktop-logo.png' -print >&2 || true
    exit 1
fi
if ! python3 -c 'from PySide6.QtCore import Qt; from PySide6.QtGui import QImage' >/dev/null 2>&1; then
    echo "::error::PySide6 QtGui image support is unavailable; cannot prepare the Plymouth watermark."
    exit 1
fi
install -d -m 0755 "${THEME_DIR}"

python3 - <<'PY'
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage

source = Path("/usr/share/leos/branding/desktop-logo.png")
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
