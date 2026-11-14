"""CI smoke checks for LEOS theme-aware branding transformations.

Run with --images inside the Fedora/Qt container, --video after installing
FFmpeg, and --svg to validate derived SVG behavior and packaged source assets.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from desktop.branding_assets import (
    _available_video_encoder,
    _image_transform,
    _transform_svg,
    _transform_video,
    build_color_matrix,
)


def validate_images() -> None:
    from PySide6.QtGui import QColor, QImage

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
                raise SystemExit(f"Unexpected recolored pixel: {actual.name()}")
    print("Validated derived logo endpoints and neutral metallic grey.")


def validate_video() -> None:
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise SystemExit("FFmpeg and ffprobe are required for video validation")
    encoder = _available_video_encoder(ffmpeg)
    if not encoder:
        raise SystemExit("No supported FFmpeg video encoder is available")

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source = root / "fixture.mp4"
        output = root / "fixture-themed.mp4"
        command = [
            ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", "testsrc2=size=320x180:rate=10",
            "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=44100",
            "-t", "1",
        ]
        if encoder == "libx264":
            command.extend(["-c:v", encoder, "-preset", "ultrafast", "-crf", "30"])
        elif encoder == "libopenh264":
            command.extend(["-c:v", encoder, "-b:v", "1M"])
        else:
            command.extend(["-c:v", encoder, "-q:v", "8"])
        command.extend(["-c:a", "aac", "-shortest", str(source)])
        subprocess.run(
            command, shell=False, check=True, capture_output=True, timeout=30
        )
        if not _transform_video(
            source, output, build_color_matrix("#FF8800", "#0055CC")
        ):
            raise SystemExit("LEOS could not create a recolored intro video")
        probe = subprocess.run(
            [
                ffprobe, "-v", "error", "-show_entries", "stream=codec_type",
                "-of", "csv=p=0", str(output),
            ],
            shell=False, check=True, capture_output=True, text=True, timeout=20,
        )
        streams = set(probe.stdout.splitlines())
        if not {"video", "audio"}.issubset(streams):
            raise SystemExit(f"Recolored intro lost a stream: {streams}")
    print("Validated recolored intro video with audio retained.")


def validate_svg() -> None:
    import re

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source = root / "desktop-leos.svg"
        output = root / "desktop-themed.svg"
        emblem = root / "desktop-logo.png"
        emblem.write_bytes(b"derived-image-placeholder")
        source.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" '
            'xmlns:xlink="http://www.w3.org/1999/xlink">'
            '<stop stop-color="#00D9FF"/><stop stop-color="#E33BFF"/>'
            '<image href="../desktop-logo.jpeg" '
            'xlink:href="../desktop-logo.jpeg"/></svg>',
            encoding="utf-8",
        )
        matrix = build_color_matrix("#00FF00", "#FF0000")
        if not _transform_svg(source, output, matrix, emblem):
            raise SystemExit("LEOS could not generate a recolored SVG")
        generated = output.read_text(encoding="utf-8")
        if "#00FF00" not in generated or "#FF0000" not in generated:
            raise SystemExit("SVG color endpoints were not transformed")
        if emblem.resolve().as_uri() not in generated:
            raise SystemExit("SVG does not reference its derived emblem")
        if "../desktop-logo.jpeg" in generated:
            raise SystemExit("SVG still references its original emblem")
        if "#00D9FF" not in source.read_text(encoding="utf-8"):
            raise SystemExit("The official SVG source was modified")

    # Verify that packaged, official 4K SVGs still point to their original JPEGs.
    namespace = "{http://www.w3.org/2000/svg}"
    xlink_href = "{http://www.w3.org/1999/xlink}href"
    expected = {
        ROOT / "branding/wallpapers/desktop-leos.svg": "../desktop-logo.jpeg",
        ROOT / "branding/wallpapers/gaming-leos.svg": "../gaming-logo.jpeg",
    }
    for wallpaper, emblem_name in expected.items():
        parsed = ET.parse(wallpaper).getroot()
        if parsed.attrib.get("viewBox") != "0 0 3840 2160":
            raise SystemExit(f"Invalid 4K wallpaper viewBox: {wallpaper}")
        images = parsed.findall(f".//{namespace}image")
        if (
            len(images) != 1
            or images[0].attrib.get("href") != emblem_name
            or images[0].attrib.get(xlink_href) != emblem_name
        ):
            raise SystemExit(f"Unexpected official emblem link: {wallpaper}")
        if not (wallpaper.parent / emblem_name).is_file():
            raise SystemExit(f"Official wallpaper emblem missing: {emblem_name}")
    print("Validated recolored SVG variants and immutable 4K source wallpapers.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--images", action="store_true")
    parser.add_argument("--video", action="store_true")
    parser.add_argument("--svg", action="store_true")
    args = parser.parse_args()
    if not (args.images or args.video or args.svg):
        parser.error("choose at least one of --images, --video or --svg")
    if args.images:
        validate_images()
    if args.video:
        validate_video()
    if args.svg:
        validate_svg()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
