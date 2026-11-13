"""Tests for recoloring official LEOS branding without changing source assets."""

import os
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from desktop.branding_assets import (
    _cache_directory,
    _available_video_encoder,
    _transform_svg,
    build_color_matrix,
    cached_themed_branding_asset_urls,
    source_asset_urls,
    transform_rgb,
)


def _rgb(hex_color):
    value = hex_color.lstrip("#")
    return tuple(int(value[index:index + 2], 16) / 255 for index in (0, 2, 4))


class BrandingAssetTests(unittest.TestCase):
    def test_color_matrix_maps_both_original_endpoints_to_the_custom_pair(self):
        color_a = "#FF8800"
        color_b = "#0055CC"
        matrix = build_color_matrix(color_a, color_b)

        mapped_a = transform_rgb(_rgb("#00D9FF"), matrix)
        mapped_b = transform_rgb(_rgb("#E33BFF"), matrix)
        for actual, expected in zip(mapped_a, _rgb(color_a)):
            self.assertAlmostEqual(actual, expected, places=6)
        for actual, expected in zip(mapped_b, _rgb(color_b)):
            self.assertAlmostEqual(actual, expected, places=6)

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
        self.assertEqual(_available_video_encoder.__name__, "_available_video_encoder")
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
