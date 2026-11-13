"""Tests for recoloring official LEOS branding without changing source assets."""

import tempfile
import unittest
from pathlib import Path

from desktop.branding_assets import (
    _transform_svg,
    build_color_matrix,
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
