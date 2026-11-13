"""Tests for LEOS two-accent logo, wallpaper and video asset preparation."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from desktop.theme_assets import (
    ThemeAssetManager,
    lut_cube_text,
    recolor_hex_color,
    recolor_svg_markup,
    render_svg_theme,
    render_video_theme,
)


class DynamicThemeAssetTests(unittest.TestCase):
    def test_primary_and_secondary_source_colors_map_to_different_target_colors(self):
        primary = recolor_hex_color("#00d9ff", "#00ff66", "#ff9900")
        secondary = recolor_hex_color("#e33bff", "#00ff66", "#ff9900")
        self.assertEqual(primary, "#00ff66")
        self.assertEqual(secondary, "#ff9900")
        self.assertNotEqual(primary, secondary)

    def test_neutral_and_unrelated_colors_are_preserved(self):
        for source in ("#777777", "#05070b", "#ffffff", "#44aa22"):
            with self.subTest(source=source):
                self.assertEqual(
                    recolor_hex_color(source, "#00ff66", "#ff9900"),
                    source.lower(),
                )

    def test_svg_recoloring_keeps_neutral_base_and_changes_both_accents(self):
        source = (
            '<svg><rect fill="#00d9ff"/><path stroke="#e33bff"/>'
            '<rect fill="#05070b"/></svg>'
        )
        result = recolor_svg_markup(source, "#00ff66", "#ff9900")
        self.assertIn('fill="#00ff66"', result)
        self.assertIn('stroke="#ff9900"', result)
        self.assertIn('fill="#05070b"', result)

    def test_svg_render_uses_a_sibling_emblem_reference_and_keeps_source_unchanged(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.svg"
            source.write_text(
                '<svg><image href="../desktop-logo-alpha.png"/>'
                '<rect fill="#00d9ff"/></svg>',
                encoding="utf-8",
            )
            output_dir = root / "cache"
            output_dir.mkdir()
            emblem = output_dir / "desktop-logo.png"
            emblem.write_bytes(b"placeholder")
            output = output_dir / "desktop.svg"
            original = source.read_bytes()

            render_svg_theme(
                source,
                output,
                {
                    "accent_primary": "#00ff66",
                    "accent_secondary": "#ff9900",
                },
                emblem,
            )
            rendered = output.read_text(encoding="utf-8")
            self.assertIn('href="desktop-logo.png"', rendered)
            self.assertIn('fill="#00ff66"', rendered)
            self.assertNotIn("file://", rendered)
            self.assertEqual(source.read_bytes(), original)

    def test_lut_has_valid_dimensions_and_expected_entry_count(self):
        size = 5
        cube = lut_cube_text("#00ff66", "#ff9900", size=size)
        lines = cube.splitlines()
        self.assertIn(f"LUT_3D_SIZE {size}", lines)
        self.assertEqual(len(lines), 4 + size ** 3)
        self.assertEqual(lines[2], "DOMAIN_MIN 0.0 0.0 0.0")
        self.assertEqual(lines[3], "DOMAIN_MAX 1.0 1.0 1.0")

    def test_lut_rejects_invalid_colors_and_dimensions(self):
        with self.assertRaises(ValueError):
            lut_cube_text("green", "#ff9900")
        with self.assertRaises(ValueError):
            lut_cube_text("#00ff66", "#ff9900", size=1)

    def test_video_renderer_preserves_audio_mapping_and_uses_no_shell(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "intro.mov"
            output = root / "intro.mp4"
            lut = root / "theme.cube"
            source.write_bytes(b"video-source")
            lut.write_text("LUT_3D_SIZE 2\n", encoding="utf-8")

            calls = []

            def fake_run(args, **kwargs):
                calls.append((args, kwargs))
                Path(args[-1]).write_bytes(b"encoded-video")
                return SimpleNamespace(returncode=0, stderr="")

            with (
                mock.patch("desktop.theme_assets.shutil.which", return_value="/usr/bin/ffmpeg"),
                mock.patch("desktop.theme_assets.subprocess.run", side_effect=fake_run),
            ):
                result = render_video_theme(source, output, lut)

            self.assertEqual(result, output)
            self.assertTrue(output.is_file())
            args, kwargs = calls[0]
            self.assertIn("lut3d=file=theme.cube:interp=tetrahedral", args)
            self.assertIn("0:a?", args)
            self.assertIn("aac", args)
            self.assertEqual(kwargs["cwd"], root)
            self.assertEqual(kwargs["timeout"], 420)

    def test_video_renderer_requires_ffmpeg_and_leaves_source_untouched(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "intro.mov"
            output = root / "intro.mp4"
            lut = root / "theme.cube"
            source.write_bytes(b"original-video")
            lut.write_text("LUT_3D_SIZE 2\n", encoding="utf-8")

            with mock.patch("desktop.theme_assets.shutil.which", return_value=None):
                with self.assertRaises(FileNotFoundError):
                    render_video_theme(source, output, lut)
            self.assertEqual(source.read_bytes(), b"original-video")
            self.assertFalse(output.exists())

    def test_video_cache_records_original_fallback_when_ffmpeg_is_unavailable(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            branding = root / "branding"
            animations = branding / "animations"
            animations.mkdir(parents=True)
            desktop_source = animations / "desktop-intro.mov"
            gaming_source = animations / "gaming-intro.mp4"
            desktop_source.write_bytes(b"desktop-source")
            gaming_source.write_bytes(b"gaming-source")
            manager = ThemeAssetManager(
                branding_dir=branding,
                cache_dir=root / "cache",
            )

            with mock.patch("desktop.theme_assets.shutil.which", return_value=None):
                assets = manager.video_paths_for_theme("light")

            self.assertEqual(assets["videos_recolored"], "false")
            self.assertEqual(assets["desktop_intro"], desktop_source.resolve().as_uri())
            self.assertEqual(assets["gaming_intro"], gaming_source.resolve().as_uri())
            cached = manager.cached_video_paths_for_theme("light")
            self.assertIsNotNone(cached)
            self.assertEqual(cached["videos_recolored"], "false")
            self.assertEqual(cached["desktop_intro"], desktop_source.resolve().as_uri())

    def test_video_status_json_is_parseable_and_bound_to_theme(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            branding = root / "branding"
            animations = branding / "animations"
            animations.mkdir(parents=True)
            (animations / "desktop-intro.mov").write_bytes(b"desktop-source")
            (animations / "gaming-intro.mp4").write_bytes(b"gaming-source")
            manager = ThemeAssetManager(branding_dir=branding, cache_dir=root / "cache")
            with mock.patch("desktop.theme_assets.shutil.which", return_value=None):
                manager.video_paths_for_theme("light")
            output_dir = manager._output_dir_for_theme("light")
            status_path = output_dir / ".videos-ready.json"
            status = json.loads(status_path.read_text(encoding="utf-8"))
            self.assertEqual(status["theme"], "light")
            self.assertIs(status["videos_recolored"], False)
            self.assertIsNone(manager.cached_video_paths_for_theme("gaming"))


if __name__ == "__main__":
    unittest.main()
