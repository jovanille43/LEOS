"""Checks that official LEOS marks are transparent and use mode-appropriate framing."""

from pathlib import Path
import struct
import unittest
import zlib


ROOT = Path(__file__).resolve().parents[1]
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _decode_png_alpha(path):
    data = path.read_bytes()
    if not data.startswith(PNG_SIGNATURE):
        raise AssertionError(f"{path} is not a PNG")
    offset = len(PNG_SIGNATURE)
    compressed = bytearray()
    width = height = bit_depth = color_type = interlace = None
    while offset < len(data):
        length = struct.unpack_from(">I", data, offset)[0]
        kind = data[offset + 4:offset + 8]
        content = data[offset + 8:offset + 8 + length]
        offset += length + 12
        if kind == b"IHDR":
            width, height, bit_depth, color_type, _compression, _filter, interlace = struct.unpack(
                ">IIBBBBB", content
            )
        elif kind == b"IDAT":
            compressed.extend(content)
        elif kind == b"IEND":
            break
    if bit_depth != 8 or color_type != 6 or interlace != 0:
        raise AssertionError(f"{path} must be a non-interlaced 8-bit RGBA PNG")

    decoded = zlib.decompress(compressed)
    stride = width * 4
    previous = bytearray(stride)
    transparent = opaque = 0

    def paeth(left, above, upper_left):
        predictor = left + above - upper_left
        distances = (abs(predictor - left), abs(predictor - above), abs(predictor - upper_left))
        return (left, above, upper_left)[distances.index(min(distances))]

    cursor = 0
    for _row in range(height):
        filter_kind = decoded[cursor]
        encoded = decoded[cursor + 1:cursor + 1 + stride]
        cursor += stride + 1
        row = bytearray(stride)
        for index, value in enumerate(encoded):
            left = row[index - 4] if index >= 4 else 0
            above = previous[index]
            upper_left = previous[index - 4] if index >= 4 else 0
            if filter_kind == 1:
                value += left
            elif filter_kind == 2:
                value += above
            elif filter_kind == 3:
                value += (left + above) // 2
            elif filter_kind == 4:
                value += paeth(left, above, upper_left)
            elif filter_kind != 0:
                raise AssertionError(f"Unsupported PNG filter {filter_kind}")
            row[index] = value & 0xFF
        for alpha in row[3::4]:
            transparent += alpha == 0
            opaque += alpha == 255
        previous = row
    return width, height, transparent, opaque


class LogoAssetTests(unittest.TestCase):
    def test_interface_marks_are_transparent_and_tightly_framed(self):
        for name in ("desktop-logo.png", "gaming-logo.png"):
            with self.subTest(name=name):
                width, height, transparent, opaque = _decode_png_alpha(ROOT / "branding" / name)
                ratio = width / height
                self.assertGreaterEqual(ratio, 0.82)
                self.assertLessEqual(ratio, 1.02)
                self.assertGreater(transparent, 0)
                self.assertGreater(opaque, width * height // 3)

    def test_wallpaper_marks_keep_the_original_wide_canvas_without_black_mattes(self):
        for name in ("desktop-wallpaper-logo.png", "gaming-wallpaper-logo.png"):
            with self.subTest(name=name):
                width, height, transparent, opaque = _decode_png_alpha(ROOT / "branding" / name)
                self.assertEqual((width, height), (1376, 768))
                self.assertAlmostEqual(width / height, 1376 / 768, places=5)
                self.assertGreater(transparent, 0)
                self.assertGreater(opaque, width * height // 10)


if __name__ == "__main__":
    unittest.main()
