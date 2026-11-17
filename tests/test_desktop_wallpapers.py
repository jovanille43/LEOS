"""Tests for safe generation of user-scoped A/B LEOS wallpapers."""

import hashlib
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from desktop.wallpapers import generate_user_wallpapers, user_wallpaper_directory
from leos_core.settings import SettingsStore

ROOT = Path(__file__).resolve().parents[1]
BRANDING = ROOT / "branding"


class UserWallpaperGenerationTests(unittest.TestCase):
    def test_custom_pair_generates_two_svg_copies_and_preserves_sources(self):
        source_files = (
            BRANDING / "wallpapers/desktop-leos.svg",
            BRANDING / "wallpapers/gaming-leos.svg",
            BRANDING / "desktop-logo-alpha.png",
            BRANDING / "gaming-logo-alpha.png",
        )
        before = {
            path: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in source_files
        }

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            settings = SettingsStore(root / "settings.json")
            settings.set_many({
                "theme": "custom",
                "custom_accent_primary": "#11aa77",
                "custom_accent_secondary": "#d9a521",
            })
            output = root / "data" / "leos" / "wallpapers"

            result = generate_user_wallpapers(
                settings,
                destination=output,
                source_root=BRANDING,
            )

            self.assertEqual(set(result), {"desktop", "gaming"})
            variant_directory = user_wallpaper_directory(settings, output)
            self.assertEqual(
                Path(result["desktop"]).parent,
                variant_directory,
            )
            self.assertEqual(Path(result["gaming"]).parent, variant_directory)

            for kind, filename, logo in (
                ("desktop", "desktop-leos.svg", "desktop-logo-alpha.png"),
                ("gaming", "gaming-leos.svg", "gaming-logo-alpha.png"),
            ):
                with self.subTest(kind=kind):
                    generated = Path(result[kind])
                    self.assertEqual(generated, variant_directory / filename)
                    self.assertTrue(generated.is_file())
                    self.assertTrue((variant_directory / logo).is_file())
                    self.assertEqual(
                        (variant_directory / logo).read_bytes(),
                        (BRANDING / logo).read_bytes(),
                    )
                    root_svg = ET.parse(generated).getroot()
                    image = root_svg.find("{http://www.w3.org/2000/svg}image")
                    self.assertIsNotNone(image)
                    relative = image.attrib.get("href")
                    self.assertEqual(relative, logo)
                    self.assertTrue((generated.parent / relative).resolve().is_file())

            desktop_svg = Path(result["desktop"]).read_text(encoding="utf-8")
            gaming_svg = Path(result["gaming"]).read_text(encoding="utf-8")
            for svg in (desktop_svg, gaming_svg):
                self.assertIn("#11AA77", svg)
                self.assertIn("#D9A521", svg)
            self.assertNotIn("#00b9e8", desktop_svg.lower())
            self.assertNotIn("#d32ce8", desktop_svg.lower())
            self.assertNotIn("#00d9ff", gaming_svg.lower())
            self.assertNotIn("#e33bff", gaming_svg.lower())

        after = {
            path: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in source_files
        }
        self.assertEqual(before, after)

    def test_second_color_pair_does_not_overwrite_first_generated_wallpaper(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            settings = SettingsStore(root / "settings.json")
            settings.set_many({
                "theme": "custom",
                "custom_accent_primary": "#11AA77",
                "custom_accent_secondary": "#D9A521",
            })
            output = root / "data" / "wallpapers"
            first = generate_user_wallpapers(settings, output, BRANDING)
            first_bytes = {
                key: Path(path).read_bytes() for key, path in first.items()
            }

            settings.set_many({
                "theme": "custom",
                "custom_accent_primary": "#0071CE",
                "custom_accent_secondary": "#D9A521",
            })
            second = generate_user_wallpapers(settings, output, BRANDING)

            self.assertNotEqual(
                Path(first["desktop"]).parent,
                Path(second["desktop"]).parent,
            )
            for kind in ("desktop", "gaming"):
                self.assertEqual(Path(first[kind]).read_bytes(), first_bytes[kind])
                self.assertNotEqual(first[kind], second[kind])

    def test_custom_wallpaper_generation_rejects_symlink_output_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            real = root / "real"
            real.mkdir()
            link = root / "linked"
            link.symlink_to(real, target_is_directory=True)
            settings = SettingsStore(root / "settings.json")
            with self.assertRaises(OSError):
                generate_user_wallpapers(
                    settings,
                    destination=link / "wallpapers",
                    source_root=BRANDING,
                )

    def test_wallpaper_generator_is_exposed_in_control_center(self):
        controller = (ROOT / "control_center/controller.py").read_text(encoding="utf-8")
        qml = (ROOT / "control_center/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn("generate_user_wallpapers(self.settings)", controller)
        self.assertIn("def generateThemeWallpapers(self)", controller)
        self.assertIn("def desktopWallpaperPreviewUrl(self)", controller)
        self.assertIn("def gamingWallpaperPreviewUrl(self)", controller)
        self.assertIn("controlCenter.generateThemeWallpapers()", qml)
        self.assertIn("controlCenter.desktopWallpaperPreviewUrl", qml)
        self.assertIn("controlCenter.gamingWallpaperPreviewUrl", qml)
        self.assertIn('controlCenter.openSettingsModule("wallpaper")', qml)


if __name__ == "__main__":
    unittest.main()
