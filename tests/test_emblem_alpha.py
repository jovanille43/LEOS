"""Les emblèmes transparents des fonds d'écran dérivent des JPEG officiels."""
import struct
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BRANDING = ROOT / "branding"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
SVG_NS = "{http://www.w3.org/2000/svg}"


def png_header(path: Path):
    data = path.read_bytes()
    assert data[:8] == PNG_SIGNATURE, f"{path.name} n'est pas un PNG"
    width, height, depth, color_type = struct.unpack(">IIBB", data[16:26])
    return width, height, depth, color_type


def jpeg_size(path: Path):
    data = path.read_bytes()
    pos = 2
    while pos < len(data):
        if data[pos] != 0xFF:
            pos += 1
            continue
        marker = data[pos + 1]
        if marker in (0xC0, 0xC1, 0xC2):
            height, width = struct.unpack(">HH", data[pos + 5:pos + 9])
            return width, height
        pos += 2 + struct.unpack(">H", data[pos + 2:pos + 4])[0]
    raise AssertionError(f"Dimensions JPEG introuvables : {path.name}")


class EmblemAlphaTests(unittest.TestCase):
    def test_alpha_pngs_are_rgba_with_same_size_as_official_jpeg(self):
        for name in ("desktop", "gaming"):
            width, height, depth, color_type = png_header(BRANDING / f"{name}-logo-alpha.png")
            self.assertEqual((depth, color_type), (8, 6), f"{name} : PNG 8 bits RGBA attendu")
            self.assertEqual((width, height), jpeg_size(BRANDING / f"{name}-logo.jpeg"))

    def test_wallpapers_use_transparent_emblem_not_opaque_jpeg(self):
        for name in ("desktop", "gaming"):
            root = ET.parse(BRANDING / "wallpapers" / f"{name}-leos.svg").getroot()
            images = root.findall(f".//{SVG_NS}image")
            self.assertEqual(len(images), 1)
            self.assertEqual(images[0].attrib["href"], f"../{name}-logo-alpha.png")

    def test_official_jpeg_sources_are_kept(self):
        for name in ("desktop", "gaming"):
            self.assertTrue((BRANDING / f"{name}-logo.jpeg").is_file())

    def test_generator_script_is_documented_in_manifest(self):
        manifest = (BRANDING / "ASSET_MANIFEST.md").read_text(encoding="utf-8")
        self.assertIn("tools/derive_emblem_alpha.py", manifest)
        self.assertTrue((ROOT / "tools" / "derive_emblem_alpha.py").is_file())

    def test_alpha_pngs_match_generator_output(self):
        try:
            import numpy as np
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow/numpy absents : vérification pixel à lancer en local")
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "derive_emblem_alpha", ROOT / "tools" / "derive_emblem_alpha.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for name in ("desktop", "gaming"):
            expected = np.asarray(module.derive(BRANDING / f"{name}-logo.jpeg"), dtype=np.int16)
            current = np.asarray(Image.open(BRANDING / f"{name}-logo-alpha.png").convert("RGBA"), dtype=np.int16)
            self.assertLessEqual(int(np.abs(expected - current).max()), 1, name)
            self.assertEqual(int(current[:40, :40, 3].max()), 0, f"{name} : coin non transparent")


if __name__ == "__main__":
    unittest.main()
