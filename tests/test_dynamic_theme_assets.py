"""Tests for LEOS two-accent logo, wallpaper and video asset preparation."""

from __future__ import annotations

import colorsys
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
    recolor_kde_svg_markup,
    recolor_svg_markup,
    render_logo_theme,
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

    def test_gradient_midpoint_is_interpolated_between_the_selected_accents(self):
        source_mid_rgb = colorsys.hsv_to_rgb(241.0 / 360.0, 1.0, 1.0)
        source_mid = "#{:02x}{:02x}{:02x}".format(
            *(round(channel * 255) for channel in source_mid_rgb)
        )
        mapped = recolor_hex_color(source_mid, "#00ff66", "#ff9900")
        mapped_rgb = tuple(
            int(mapped[index:index + 2], 16) / 255.0 for index in (1, 3, 5)
        )
        mapped_hue = colorsys.rgb_to_hsv(*mapped_rgb)[0]
        # Target accents are at 144° and 36°; their smooth midpoint is 90°.
        self.assertLess(abs((mapped_hue - 0.25 + 0.5) % 1.0 - 0.5), 0.01)
        self.assertNotEqual(mapped.lower(), "#00ff66")
        self.assertNotEqual(mapped.lower(), "#ff9900")

    def test_gradient_hue_progression_remains_smooth_across_the_full_transition(self):
        expected_hues = (117.0, 90.0, 63.0)
        for position, expected_hue in zip((0.25, 0.5, 0.75), expected_hues):
            source_hue = (190.0 + 102.0 * position) / 360.0
            source_rgb = colorsys.hsv_to_rgb(source_hue, 1.0, 1.0)
            source = "#{:02x}{:02x}{:02x}".format(
                *(round(channel * 255) for channel in source_rgb)
            )
            mapped = recolor_hex_color(source, "#00ff66", "#ff9900")
            mapped_rgb = tuple(
                int(mapped[index:index + 2], 16) / 255.0 for index in (1, 3, 5)
            )
            mapped_hue = colorsys.rgb_to_hsv(*mapped_rgb)[0]
            expected = expected_hue / 360.0
            error = abs((mapped_hue - expected + 0.5) % 1.0 - 0.5)
            self.assertLess(error, 0.01)

    def test_png_render_preserves_alpha_neutrals_and_smooth_gradient(self):
        try:
            from PySide6.QtGui import QColor, QImage
        except ImportError:
            self.skipTest("PySide6 is part of the LEOS desktop runtime, not Python CI")

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.png"
            output = root / "themed.png"
            image = QImage(5, 1, QImage.Format_ARGB32)
            image.fill(QColor("#000000"))
            primary = QColor("#00d9ff")
            primary.setAlpha(128)
            image.setPixelColor(0, 0, primary)

            middle = colorsys.hsv_to_rgb(241.0 / 360.0, 1.0, 1.0)
            middle_color = QColor(
                round(middle[0] * 255),
                round(middle[1] * 255),
                round(middle[2] * 255),
                180,
            )
            image.setPixelColor(1, 0, middle_color)

            secondary = QColor("#e33bff")
            secondary.setAlpha(200)
            image.setPixelColor(2, 0, secondary)
            image.setPixelColor(3, 0, QColor("#777777"))
            transparent = QColor("#00d9ff")
            transparent.setAlpha(0)
            image.setPixelColor(4, 0, transparent)
            self.assertTrue(image.save(str(source), "PNG"))

            render_logo_theme(
                source,
                output,
                {
                    "accent_primary": "#00ff66",
                    "accent_secondary": "#ff9900",
                },
            )
            rendered = QImage(str(output))
            self.assertFalse(rendered.isNull())
            self.assertEqual(rendered.pixelColor(0, 0).name(), "#00ff66")
            self.assertEqual(rendered.pixelColor(0, 0).alpha(), 128)
            self.assertNotIn(
                rendered.pixelColor(1, 0).name(),
                {"#00ff66", "#ff9900"},
            )
            self.assertEqual(rendered.pixelColor(1, 0).alpha(), 180)
            self.assertEqual(rendered.pixelColor(2, 0).name(), "#ff9900")
            self.assertEqual(rendered.pixelColor(2, 0).alpha(), 200)
            self.assertEqual(rendered.pixelColor(3, 0).name(), "#777777")
            self.assertEqual(rendered.pixelColor(4, 0).alpha(), 0)

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

    def test_default_lut_uses_a_fine_grid_for_smoother_video_gradients(self):
        lines = lut_cube_text("#00ff66", "#ff9900").splitlines()
        self.assertIn("LUT_3D_SIZE 49", lines)
        self.assertEqual(len(lines), 4 + 49 ** 3)

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
            self.assertIs(kwargs["shell"], False)

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


    def test_kde_svg_recoloring_keeps_dark_surfaces_and_inactive_slate(self):
        source = (
            '<svg><defs><linearGradient id="g">'
            '<stop stop-color="#00D9FF"/><stop stop-color="#8C9BFF"/>'
            '<stop stop-color="#E33BFF"/></linearGradient></defs>'
            '<path stroke="#00D9FF"/><path stroke="#71809B"/>'
            '<rect fill="#111827"/></svg>'
        )
        result = recolor_kde_svg_markup(source, "#006B83", "#A329B5")
        self.assertIn('stop-color="#006b83"', result)
        self.assertIn('stop-color="#a329b5"', result)
        self.assertIn('stroke="#006b83"', result)
        self.assertIn('stroke="#71809B"', result)
        self.assertIn('fill="#111827"', result)

    def test_kde_resource_packages_are_named_recolored_and_source_immutable(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            branding = root / "branding"
            branding.mkdir()
            icon_root = root / "source-icons" / "leos"
            plasma_root = root / "source-plasma" / "leos"
            aurorae_root = root / "source-aurorae" / "leos"
            (icon_root / "scalable" / "apps").mkdir(parents=True)
            (plasma_root / "widgets").mkdir(parents=True)
            aurorae_root.mkdir(parents=True)

            svg = (
                '<svg><defs><linearGradient id="g">'
                '<stop stop-color="#00D9FF"/><stop stop-color="#8C9BFF"/>'
                '<stop stop-color="#E33BFF"/></linearGradient></defs>'
                '<path stroke="url(#g)"/><path stroke="#71809B"/>'
                '<rect fill="#111827"/></svg>'
            )
            icon_svg = icon_root / "scalable" / "apps" / "leos-example.svg"
            plasma_svg = plasma_root / "widgets" / "background.svg"
            aurorae_svg = aurorae_root / "decoration.svg"
            icon_svg.write_text(svg, encoding="utf-8")
            plasma_svg.write_text(svg, encoding="utf-8")
            aurorae_svg.write_text(svg, encoding="utf-8")

            icon_index = (
                "[Icon Theme]\nName=LEOS\nComment=Original icons\n"
                "Inherits=breeze,hicolor\n"
            )
            plasma_metadata = {
                "KPlugin": {
                    "Id": "leos",
                    "Name": "LEOS",
                    "Description": "Original Plasma style",
                }
            }
            aurorae_metadata = (
                "[Desktop Entry]\nName=LEOS\nComment=Original decoration\n"
                "X-KDE-PluginInfo-Name=leos\n"
            )
            (icon_root / "index.theme").write_text(icon_index, encoding="utf-8")
            (plasma_root / "metadata.json").write_text(
                json.dumps(plasma_metadata), encoding="utf-8"
            )
            (aurorae_root / "metadata.desktop").write_text(
                aurorae_metadata, encoding="utf-8"
            )

            originals = {
                icon_svg: icon_svg.read_bytes(),
                plasma_svg: plasma_svg.read_bytes(),
                aurorae_svg: aurorae_svg.read_bytes(),
                icon_root / "index.theme": (icon_root / "index.theme").read_bytes(),
                plasma_root / "metadata.json": (plasma_root / "metadata.json").read_bytes(),
                aurorae_root / "metadata.desktop": (aurorae_root / "metadata.desktop").read_bytes(),
            }
            manager = ThemeAssetManager(
                branding_dir=branding,
                cache_dir=root / "cache",
                icon_theme_dir=icon_root,
                plasma_theme_dir=plasma_root,
                aurorae_theme_dir=aurorae_root,
            )

            paths = manager.kde_resource_paths_for_theme("light")
            self.assertEqual(paths["icon_theme_name"], "leos-light")
            self.assertEqual(paths["plasma_theme_name"], "leos-light")
            self.assertEqual(paths["aurorae_theme_name"], "leos-light")

            generated_icon = Path(paths["icon_theme_path"])
            generated_plasma = Path(paths["plasma_theme_path"])
            generated_aurorae = Path(paths["aurorae_theme_path"])
            self.assertTrue((generated_icon / "index.theme").is_file())
            self.assertTrue((generated_plasma / "metadata.json").is_file())
            self.assertTrue((generated_aurorae / "metadata.desktop").is_file())

            icon_meta = (generated_icon / "index.theme").read_text(encoding="utf-8")
            self.assertIn("Name=LEOS — Light", icon_meta)
            self.assertIn("Comment=LEOS icon theme — Light", icon_meta)

            plasma_meta = json.loads(
                (generated_plasma / "metadata.json").read_text(encoding="utf-8")
            )["KPlugin"]
            self.assertEqual(plasma_meta["Id"], "leos-light")
            self.assertEqual(plasma_meta["Name"], "LEOS — Light")

            aurora_meta = (generated_aurorae / "metadata.desktop").read_text(
                encoding="utf-8"
            )
            self.assertIn("Name=LEOS — Light", aurora_meta)
            self.assertIn("X-KDE-PluginInfo-Name=leos-light", aurora_meta)

            for generated_svg in (
                generated_icon / "scalable" / "apps" / "leos-example.svg",
                generated_plasma / "widgets" / "background.svg",
                generated_aurorae / "decoration.svg",
            ):
                rendered = generated_svg.read_text(encoding="utf-8")
                self.assertIn('stop-color="#006b83"', rendered)
                self.assertIn('stop-color="#a329b5"', rendered)
                self.assertIn('stroke="#71809B"', rendered)
                self.assertIn('fill="#111827"', rendered)

            for path, original in originals.items():
                self.assertEqual(path.read_bytes(), original)

    def test_kde_resource_package_rejects_symbolic_link_entries(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            icon_root = root / "icons" / "leos"
            icon_root.mkdir(parents=True)
            (icon_root / "index.theme").write_text(
                "[Icon Theme]\nName=LEOS\nComment=Icons\n",
                encoding="utf-8",
            )
            outside = root / "outside.svg"
            outside.write_text('<svg/>', encoding="utf-8")
            try:
                (icon_root / "unsafe.svg").symlink_to(outside)
            except OSError:
                self.skipTest("Symbolic links are unavailable on this runner")

            manager = ThemeAssetManager(
                branding_dir=root / "branding",
                cache_dir=root / "cache",
                icon_theme_dir=icon_root,
                plasma_theme_dir=root / "missing-plasma",
                aurorae_theme_dir=root / "missing-aurorae",
            )
            with self.assertRaises(ValueError):
                manager.kde_resource_paths_for_theme("light")


    def test_repository_kde_packages_generate_from_real_source_trees(self):
        repository = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary:
            manager = ThemeAssetManager(
                branding_dir=repository / "branding",
                cache_dir=Path(temporary) / "cache",
                icon_theme_dir=repository / "icons" / "leos",
                plasma_theme_dir=repository / "plasma-theme" / "leos",
                aurorae_theme_dir=repository / "aurorae" / "leos",
            )
            paths = manager.kde_resource_paths_for_theme("light")
            for key in ("icon_theme_path", "plasma_theme_path", "aurorae_theme_path"):
                with self.subTest(package=key):
                    generated = Path(paths[key])
                    self.assertTrue(generated.is_dir())
                    self.assertTrue((generated / ".leos-theme-package.json").is_file())

            icon_name = (Path(paths["icon_theme_path"]) / "index.theme").read_text(
                encoding="utf-8"
            )
            self.assertIn("Name=LEOS — Light", icon_name)

            plasma_metadata = json.loads(
                (Path(paths["plasma_theme_path"]) / "metadata.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(plasma_metadata["KPlugin"]["Id"], "leos-light")

            aurorae = (
                Path(paths["aurorae_theme_path"]) / "decoration.svg"
            ).read_text(encoding="utf-8")
            self.assertNotIn("#65E5FF", aurorae)
            self.assertIn("#71809B", aurorae)
            self.assertIn("#080D18", aurorae)


    def test_kde_packages_export_to_xdg_user_data_without_activation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            branding = root / "branding"
            branding.mkdir()
            icon_root = root / "source-icons" / "leos"
            plasma_root = root / "source-plasma" / "leos"
            aurorae_root = root / "source-aurorae" / "leos"
            (icon_root / "scalable" / "apps").mkdir(parents=True)
            (plasma_root / "widgets").mkdir(parents=True)
            aurorae_root.mkdir(parents=True)

            svg = (
                '<svg><defs><linearGradient id="g">'
                '<stop stop-color="#00D9FF"/><stop stop-color="#E33BFF"/>'
                '</linearGradient></defs><path stroke="url(#g)"/></svg>'
            )
            (icon_root / "scalable" / "apps" / "leos-test.svg").write_text(
                svg, encoding="utf-8"
            )
            (plasma_root / "widgets" / "background.svg").write_text(
                svg, encoding="utf-8"
            )
            (aurorae_root / "decoration.svg").write_text(svg, encoding="utf-8")
            (icon_root / "index.theme").write_text(
                "[Icon Theme]\nName=LEOS\nComment=LEOS icons\nInherits=breeze,hicolor\n",
                encoding="utf-8",
            )
            (plasma_root / "metadata.json").write_text(
                json.dumps({"KPlugin": {"Id": "leos", "Name": "LEOS"}}),
                encoding="utf-8",
            )
            (aurorae_root / "metadata.desktop").write_text(
                "[Desktop Entry]\nName=LEOS\nComment=LEOS Aurorae\n"
                "X-KDE-PluginInfo-Name=leos\n",
                encoding="utf-8",
            )

            data_home = root / "user-data"
            manager = ThemeAssetManager(
                branding_dir=branding,
                cache_dir=root / "cache",
                icon_theme_dir=icon_root,
                plasma_theme_dir=plasma_root,
                aurorae_theme_dir=aurorae_root,
            )
            exported = manager.export_kde_resource_packages_for_theme(
                "light", data_directory=data_home
            )
            self.assertEqual(set(exported), {
                "icon_theme_path", "plasma_theme_path", "aurorae_theme_path"
            })
            icon_destination = data_home / "icons" / "leos-light"
            plasma_destination = data_home / "plasma" / "desktoptheme" / "leos-light"
            aurorae_destination = data_home / "aurorae" / "themes" / "leos-light"
            self.assertEqual(Path(exported["icon_theme_path"]), icon_destination)
            self.assertEqual(Path(exported["plasma_theme_path"]), plasma_destination)
            self.assertEqual(Path(exported["aurorae_theme_path"]), aurorae_destination)
            self.assertTrue((icon_destination / "index.theme").is_file())
            self.assertTrue((plasma_destination / "metadata.json").is_file())
            self.assertTrue((aurorae_destination / "metadata.desktop").is_file())

            # Export is idempotent when the exact package is already present.
            self.assertEqual(
                manager.export_kde_resource_packages_for_theme(
                    "light", data_directory=data_home
                ),
                exported,
            )

            # A modified package with a LEOS manifest must never be overwritten.
            existing_svg = icon_destination / "scalable" / "apps" / "leos-test.svg"
            existing_svg.write_text("<svg><!-- user modification --></svg>", encoding="utf-8")
            preserved = existing_svg.read_text(encoding="utf-8")
            with self.assertRaises(FileExistsError):
                manager.export_kde_resource_packages_for_theme(
                    "light", data_directory=data_home
                )
            self.assertEqual(existing_svg.read_text(encoding="utf-8"), preserved)

    def test_kde_package_export_refuses_symlinked_xdg_data_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "target"
            target.mkdir()
            linked = root / "linked-data"
            try:
                linked.symlink_to(target, target_is_directory=True)
            except OSError:
                self.skipTest("Symbolic links are unavailable on this runner")

            repository = Path(__file__).resolve().parents[1]
            manager = ThemeAssetManager(
                branding_dir=repository / "branding",
                cache_dir=root / "cache",
                icon_theme_dir=repository / "icons" / "leos",
                plasma_theme_dir=repository / "plasma-theme" / "leos",
                aurorae_theme_dir=repository / "aurorae" / "leos",
            )
            with self.assertRaises(ValueError):
                manager.export_kde_resource_packages_for_theme(
                    "light", data_directory=linked
                )


if __name__ == "__main__":
    unittest.main()
