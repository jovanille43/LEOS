#!/usr/bin/env python3
"""Create transparent LEOS logo marks from the preserved official JPEG sources.

Requires Pillow. The tight PNGs are for interface marks; the matching wide PNGs
preserve the source canvas for wallpaper composition.
"""

from array import array
from pathlib import Path

from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
BRANDING = ROOT / "branding"
BACKGROUND_THRESHOLD = 72
ALPHA_FALLOFF_FLOOR = 3
CROP_PADDING = 0.055
FEATHER_RADIUS = 0.8


def _remove_connected_matte(source: Path) -> tuple[Image.Image, tuple[int, int, int, int]]:
    image = Image.open(source).convert("RGB")
    width, height = image.size
    pixels = image.tobytes()
    background = bytearray(width * height)
    queue = array("I")

    def add_if_background(index: int) -> None:
        offset = index * 3
        if not background[index] and max(pixels[offset:offset + 3]) <= BACKGROUND_THRESHOLD:
            background[index] = 1
            queue.append(index)

    for x in range(width):
        add_if_background(x)
        add_if_background((height - 1) * width + x)
    for y in range(height):
        add_if_background(y * width)
        add_if_background(y * width + width - 1)

    read = 0
    while read < len(queue):
        index = queue[read]
        read += 1
        x = index % width
        if x:
            add_if_background(index - 1)
        if x + 1 < width:
            add_if_background(index + 1)
        if index >= width:
            add_if_background(index - width)
        if index + width < width * height:
            add_if_background(index + width)

    alpha = bytearray(width * height)
    span = BACKGROUND_THRESHOLD - ALPHA_FALLOFF_FLOOR
    for index, is_background in enumerate(background):
        if not is_background:
            alpha[index] = 255
            continue
        offset = index * 3
        brightness = max(pixels[offset:offset + 3])
        alpha[index] = round(max(0, min(255, (brightness - ALPHA_FALLOFF_FLOOR) / span * 255)))

    mask = Image.frombytes("L", image.size, bytes(alpha)).filter(
        ImageFilter.GaussianBlur(FEATHER_RADIUS)
    )
    output = image.convert("RGBA")
    output.putalpha(mask)
    content_bounds = mask.point(lambda value: 255 if value > 4 else 0).getbbox()
    if content_bounds is None:
        raise ValueError(f"No logo content was found in {source}")
    return output, content_bounds


def _write_logo(source_name: str, mode: str) -> None:
    source = BRANDING / source_name
    if source.is_symlink() or not source.is_file():
        raise FileNotFoundError(f"Official source logo is missing: {source}")

    wide, bounds = _remove_connected_matte(source)
    tight_name = source_name.removesuffix(".jpeg") + ".png"
    wide_name = source_name.replace("-logo.jpeg", "-wallpaper-logo.png")
    left, top, right, bottom = bounds
    padding = round(max(right - left, bottom - top) * CROP_PADDING)
    width, height = wide.size
    crop = (
        max(0, left - padding),
        max(0, top - padding),
        min(width, right + padding),
        min(height, bottom + padding),
    )
    tight = wide.crop(crop)
    wide.save(BRANDING / wide_name, "PNG", optimize=True)
    tight.save(BRANDING / tight_name, "PNG", optimize=True)
    print(f"{mode}: {tight.size[0]}×{tight.size[1]} transparent; wallpaper canvas {wide.size[0]}×{wide.size[1]}")


def main() -> None:
    _write_logo("desktop-logo.jpeg", "Desktop")
    _write_logo("gaming-logo.jpeg", "Gaming")


if __name__ == "__main__":
    main()
