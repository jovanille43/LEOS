"""Smoke test the actual Qt image recoloring path in Fedora CI."""

from __future__ import annotations

import tempfile
from pathlib import Path

from PySide6.QtGui import QColor, QImage

from desktop.branding_assets import _image_transform, build_color_matrix


def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source = root / "source.png"
        output = root / "derived.png"
        image = QImage(3, 1, QImage.Format.Format_ARGB32)
        image.setPixelColor(0, 0, QColor(0, 217, 255))
        image.setPixelColor(1, 0, QColor(227, 59, 255))
        image.setPixelColor(2, 0, QColor(128, 128, 128))
        if not image.save(str(source), "PNG"):
            raise SystemExit("Could not create the image transform fixture")

        matrix = build_color_matrix("#FF8800", "#0055CC")
        if not _image_transform(source, output, matrix):
            raise SystemExit("LEOS logo recoloring did not produce an image")

        result = QImage(str(output))
        expected = ((255, 136, 0), (0, 85, 204), (128, 128, 128))
        for column, rgb in enumerate(expected):
            actual = result.pixelColor(column, 0)
            if (actual.red(), actual.green(), actual.blue()) != rgb:
                raise SystemExit(
                    f"Unexpected recolored pixel at x={column}: {actual.name()}"
                )

    print("Validated derived logo endpoints and neutral metallic grey.")


if __name__ == "__main__":
    main()
