"""Tests for recoloring official LEOS branding without changing source assets."""

import os
import tempfile
import unittest
import xml.etree.ElementTree as ET
from unittest.mock import patch
from pathlib import Path

from desktop.themes import DEFAULT_COLOR_A, DEFAULT_COLOR_B, SOURCE_COLOR_A, SOURCE_COLOR_B
from desktop.branding_assets import (
    _cache_directory,
    _available_video_encoder,
    only_recolored_asset_urls,
    _transform_svg,
    build_color_matrix,
    cached_themed_branding_asset_urls,
    source_asset_urls,
    transform_rgb,
    _remove_dark_edge_matte,
    _crop_transparent_bounds,
)



class _FakeColor:
    def __init__(self, red, green, blue, alpha=255):
        self._red, self._green, self._blue, self._alpha = red, green, blue, alpha

    def red(self):
        return self._red

    def green(self):
        return self._green

    def blue(self):
        return self._blue

    def alpha(self):
        return self._alpha

    def setAlpha(self, value):
        self._alpha = value

    def clone(self):
        return _FakeColor(self._red, self._green, self._blue, self._alpha)


class _FakeImage:
    def __init__(self, width, height, fill=(0, 0, 0, 255), pixels=None):
        self._width, self._height = width, height
        self._pixels = pixels or [
            [_FakeColor(*fill) for _ in range(width)] for _ in range(height)
        ]

    def width(self):
        return self._width

    def height(self):
        return self._height

    def pixelColor(self, x, y):
        return self._pixels[y][x].clone()

    def setPixelColor(self, x, y, color):
        self._pixels[y][x] = color.clone()

    def copy(self, x, y, width, height):
        pixels = [
            [self._pixels[row][column].clone() for column in range(x, x + width)]
            for row in range(y, y + height)
        ]
        return _FakeImage(width, height, pixels=pixels)


def _rgb(hex_color):
    value = hex_color.lstrip("#")
    return tuple(int(value[index:index + 2], 16) / 255 for index in (0, 2, 4))


class BrandingAssetTests(unittest.TestCase):
    def test_neutral_preview_is_separate_from_original_artwork_endpoints(self):
        self.assertNotEqual(DEFAULT_COLOR_A, SOURCE_COLOR_A)
        self.assertNotEqual(DEFAULT_COLOR_B, SOURCE_COLOR_B)

    def test_color_matrix_maps_both_original_endpoints_to_the_custom_pair(self):
        color_a = "#FF8800"
        color_b = "#0055CC"
        matrix = build_color_matrix(color_a, color_b)

        mapped_a = transform_rgb(_rgb(SOURCE_COLOR_A), matrix)
        mapped_b = transform_rgb(_rgb(SOURCE_COLOR_B), matrix)
        for actual, expected in zip(mapped_a, _rgb(color_a)):
            self.assertAlmostEqual(actual, expected, places=6)
        for actual, expected in zip(mapped_b, _rgb(color_b)):
            self.assertAlmostEqual(actual, expected, places=6)

    def test_unrecolored_source_files_are_not_returned_as_visual_fallbacks(self):
        originals = source_asset_urls()
        self.assertEqual(only_recolored_asset_urls(originals), {})
        custom = dict(originals)
        custom["desktopLogoUrl"] = "file:///home/user/.cache/leos/custom-desktop.png"
        self.assertEqual(only_recolored_asset_urls(custom), {"desktopLogoUrl": custom["desktopLogoUrl"]})

    def test_color_matrix_preserves_neutral_metallic_greys(self):
        matrix = build_color_matrix("#FF00AA", "#00D060")
        for value in (0.0, 0.15, 0.5, 0.85, 1.0):
            mapped = transform_rgb((value, value, value), matrix)
            for channel in mapped:
                self.assertAlmostEqual(channel, value, places=6)

    def test_svg_variant_recolors_accents_and_references_derived_emblem(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "desktop-leos.svg"
            output = root / "desktop-themed.svg"
            emblem = root / "desktop-logo.png"
            emblem.write_bytes(b"derived image placeholder")
            source.write_text(
                '<svg><stop stop-color="#00D9FF"/>'
                '<stop stop-color="#E33BFF"/>'
                '<image href="../desktop-logo.jpeg" '
                'xlink:href="../desktop-logo.jpeg"/></svg>',
                encoding="utf-8",
            )
            matrix = build_color_matrix("#00FF00", "#FF0000")
            self.assertTrue(_transform_svg(source, output, matrix, emblem))
            result = output.read_text(encoding="utf-8")
            self.assertIn("#00FF00", result)
            self.assertIn("#FF0000", result)
            self.assertIn(emblem.resolve().as_uri(), result)
            self.assertNotIn("../desktop-logo.jpeg", result)
            self.assertIn("#00D9FF", source.read_text(encoding="utf-8"))

    def test_desktop_background_is_neutral_while_the_official_lion_keeps_ab_recoloring(self):
        root = Path(__file__).resolve().parents[1]
        wallpaper = root / "branding" / "wallpapers" / "desktop-leos.svg"
        svg = wallpaper.read_text(encoding="utf-8")
        ET.fromstring(svg)
        self.assertIn("graphite et argent", svg)
        self.assertIn("../desktop-logo.jpeg", svg)
        self.assertIn("#171C23", svg)
        # The SVG background is deliberately neutral, but the official lion
        # is transformed separately by _image_transform using the same A/B
        # matrix before _transform_svg links the generated transparent PNG.
        self.assertNotIn("#00D9FF", svg.upper())
        self.assertNotIn("#E33BFF", svg.upper())
        color_a, color_b = "#F0A030", "#7C68E8"
        matrix = build_color_matrix(color_a, color_b)
        for actual, expected in (
            (transform_rgb(_rgb(SOURCE_COLOR_A), matrix), _rgb(color_a)),
            (transform_rgb(_rgb(SOURCE_COLOR_B), matrix), _rgb(color_b)),
        ):
            for channel, target in zip(actual, expected):
                self.assertAlmostEqual(channel, target, places=6)
        builder = __import__("inspect").getsource(
            __import__("desktop.branding_assets", fromlist=["build_themed_branding_assets"]).build_themed_branding_assets
        )
        self.assertIn("_image_transform(source, output, matrix)", builder)
        self.assertIn("_transform_svg(source, output, matrix, logo_paths[emblem_key])", builder)

    def test_cached_variants_are_discovered_without_regenerating_them(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "branding"
            (root / "wallpapers").mkdir(parents=True)
            (root / "animations").mkdir()
            for relative in (
                "desktop-logo.jpeg", "gaming-logo.jpeg",
                "wallpapers/desktop-leos.svg", "wallpapers/gaming-leos.svg",
                "animations/desktop-intro.mov", "animations/gaming-intro.mp4",
            ):
                (root / relative).write_bytes(b"official source")
            cache_home = Path(directory) / "cache"
            with patch.dict(os.environ, {"XDG_CACHE_HOME": str(cache_home)}):
                cache = _cache_directory("#FF8800", "#0055CC", root)
                cache.mkdir(parents=True, mode=0o700)
                generated = cache / "desktop-logo.png"
                generated.write_bytes(b"generated variant")
                urls = cached_themed_branding_asset_urls("#FF8800", "#0055CC", root)
                self.assertEqual(urls["desktopLogoUrl"], generated.as_uri())
                self.assertTrue(urls["gamingLogoUrl"].endswith("/gaming-logo.jpeg"))
                self.assertTrue(urls["desktopIntroUrl"].endswith("/animations/desktop-intro.mov"))

    def test_dark_edge_matte_becomes_transparent_without_keying_enclosed_black_details(self):
        image = _FakeImage(64, 64)
        for y in range(12, 52):
            for x in range(14, 50):
                image.setPixelColor(x, y, _FakeColor(230, 230, 230))
        # An enclosed black eye/detail must remain opaque.
        image.setPixelColor(32, 30, _FakeColor(0, 0, 0))

        self.assertTrue(_remove_dark_edge_matte(image))
        self.assertEqual(image.pixelColor(0, 0).alpha(), 0)
        self.assertEqual(image.pixelColor(32, 20).alpha(), 255)
        self.assertEqual(image.pixelColor(32, 30).alpha(), 255)

        cropped = _crop_transparent_bounds(image)
        self.assertLess(cropped.width(), image.width())
        self.assertLess(cropped.height(), image.height())
        self.assertEqual(cropped.pixelColor(0, 0).alpha(), 0)

    def test_bright_edge_artwork_is_not_modified_by_dark_matte_removal(self):
        image = _FakeImage(12, 12, fill=(220, 220, 220, 255))
        self.assertFalse(_remove_dark_edge_matte(image))
        self.assertEqual(image.pixelColor(0, 0).alpha(), 255)

    def test_cache_fingerprint_changes_when_an_official_source_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "branding"
            (root / "wallpapers").mkdir(parents=True)
            (root / "animations").mkdir()
            paths = [
                "desktop-logo.jpeg", "gaming-logo.jpeg",
                "wallpapers/desktop-leos.svg", "wallpapers/gaming-leos.svg",
                "animations/desktop-intro.mov", "animations/gaming-intro.mp4",
            ]
            for relative in paths:
                (root / relative).write_bytes(b"source-v1")
            before = _cache_directory("#FF8800", "#0055CC", root)
            (root / "gaming-logo.jpeg").write_bytes(b"source-v2-with-different-size")
            after = _cache_directory("#FF8800", "#0055CC", root)
            self.assertNotEqual(before, after)

    def test_video_encoder_selection_uses_only_available_supported_encoders(self):
        listing = """ V..... libopenh264 OpenH264 H.264 / AVC
 V..... mpeg4 MPEG-4 part 2
"""
        # Keep the parser decision separate from the local machine's codecs.
        from unittest.mock import patch
        from types import SimpleNamespace
        with patch("desktop.branding_assets.subprocess.run", return_value=SimpleNamespace(
            returncode=0, stdout=listing, stderr=""
        )):
            self.assertEqual(_available_video_encoder("/usr/bin/ffmpeg"), "libopenh264")

    def test_video_encoder_selection_returns_none_when_no_video_encoder_exists(self):
        from unittest.mock import patch
        from types import SimpleNamespace
        with patch("desktop.branding_assets.subprocess.run", return_value=SimpleNamespace(
            returncode=0, stdout=" A..... aac AAC (Advanced Audio Coding)", stderr=""
        )):
            self.assertIsNone(_available_video_encoder("/usr/bin/ffmpeg"))

    def test_fallback_asset_urls_point_to_official_source_files(self):
        root = Path("/usr/share/leos/branding")
        urls = source_asset_urls(root)
        self.assertTrue(urls["desktopLogoUrl"].endswith("/desktop-logo.jpeg"))
        self.assertTrue(urls["gamingLogoUrl"].endswith("/gaming-logo.jpeg"))
        self.assertTrue(urls["desktopWallpaperUrl"].endswith("/wallpapers/desktop-leos.svg"))
        self.assertTrue(urls["gamingWallpaperUrl"].endswith("/wallpapers/gaming-leos.svg"))
        self.assertTrue(urls["desktopIntroUrl"].endswith("/animations/desktop-intro.mov"))
        self.assertTrue(urls["gamingIntroUrl"].endswith("/animations/gaming-intro.mp4"))


if __name__ == "__main__":
    unittest.main()
