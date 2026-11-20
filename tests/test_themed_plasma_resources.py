"""Tests for user-scoped, recolored Plasma Style and icon resources."""

import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from desktop.themed_plasma_resources import install_themed_plasma_resources


class ThemedPlasmaResourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.data = root / "data"
        self.plasma = root / "system" / "plasma" / "leos"
        self.icons = root / "system" / "icons" / "leos"
        self.aurorae = root / "system" / "aurorae" / "leos"
        (self.plasma / "widgets").mkdir(parents=True)
        (self.icons / "scalable" / "apps").mkdir(parents=True)
        self.aurorae.mkdir(parents=True)
        (self.plasma / "metadata.json").write_text(json.dumps({
            "KPlugin": {
                "Id": "leos",
                "Name": "LEOS",
                "Description": "Legacy preview accents",
                "Version": "1.0",
                "License": "GPL-3.0-or-later",
            }
        }), encoding="utf-8")
        (self.plasma / "widgets" / "panel.svg").write_text(
            '<svg xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="g">'
            '<stop stop-color="#00D9FF"/><stop stop-color="#E33BFF"/></linearGradient>'
            '</defs><rect fill="#FFFFFF"/></svg>',
            encoding="utf-8",
        )
        (self.icons / "index.theme").write_text(
            "[Icon Theme]\nName=LEOS\nInherits=breeze,hicolor\n"
            "[scalable]\nSize=48\nType=Scalable\n",
            encoding="utf-8",
        )
        (self.icons / "scalable" / "apps" / "demo.svg").write_text(
            '<svg xmlns="http://www.w3.org/2000/svg"><path stroke="#00D9FF"/>'
            '<path stroke="#E33BFF"/></svg>',
            encoding="utf-8",
        )
        (self.aurorae / "metadata.desktop").write_text(
            "[Desktop Entry]\nName=LEOS\nX-KDE-PluginInfo-Name=leos\n",
            encoding="utf-8",
        )
        (self.aurorae / "leosrc").write_text(
            "[General]\nTitleAlignment=Center\n",
            encoding="utf-8",
        )
        (self.aurorae / "decoration.svg").write_text(
            '<svg xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="g">'
            '<stop stop-color="#00D9FF"/><stop stop-color="#E33BFF"/></linearGradient>'
            '</defs><rect fill="#FFFFFF"/></svg>',
            encoding="utf-8",
        )
        self.original_style = (self.plasma / "widgets" / "panel.svg").read_bytes()
        self.original_icon = (self.icons / "scalable" / "apps" / "demo.svg").read_bytes()
        self.original_aurorae = (self.aurorae / "decoration.svg").read_bytes()

    def tearDown(self):
        self.temp.cleanup()

    def build(self, color_a="#FF8800", color_b="#0055CC"):
        return install_themed_plasma_resources(
            color_a, color_b,
            data_home=self.data,
            plasma_theme_root=self.plasma,
            icon_theme_root=self.icons,
            aurorae_theme_root=self.aurorae,
        )

    def test_installs_matched_user_themes_with_exact_a_b_endpoints(self):
        result = self.build()
        style_id = result["plasmaStyleId"]
        icon_id = result["iconThemeId"]
        aurorae_id = result["auroraeThemeId"]
        self.assertEqual(style_id, icon_id)
        self.assertEqual(style_id, aurorae_id)
        style_root = Path(result["plasmaStylePath"])
        icon_root = Path(result["iconThemePath"])
        aurorae_root = Path(result["auroraeThemePath"])
        metadata = json.loads((style_root / "metadata.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["KPlugin"]["Id"], style_id)
        self.assertEqual(metadata["KPlugin"]["Name"], "LEOS personnalisé")
        svg = ET.parse(style_root / "widgets" / "panel.svg").getroot()
        colors = [item.attrib["stop-color"] for item in svg.iter() if "stop-color" in item.attrib]
        self.assertEqual(colors, ["#FF8800", "#0055CC"])
        self.assertEqual(
            [item.attrib["fill"] for item in svg.iter() if "fill" in item.attrib],
            ["#FFFFFF"],
        )
        icon_svg = ET.parse(icon_root / "scalable" / "apps" / "demo.svg").getroot()
        strokes = [item.attrib["stroke"] for item in icon_svg.iter() if "stroke" in item.attrib]
        self.assertEqual(strokes, ["#FF8800", "#0055CC"])
        self.assertEqual((style_root / ".leos-theme.json").is_file(), True)
        self.assertEqual((icon_root / ".leos-theme.json").is_file(), True)
        self.assertEqual((aurorae_root / ".leos-theme.json").is_file(), True)
        aurorae_metadata = aurorae_root / "metadata.desktop"
        self.assertIn(f"X-KDE-PluginInfo-Name={aurorae_id}", aurorae_metadata.read_text(encoding="utf-8"))
        self.assertTrue((aurorae_root / f"{aurorae_id}rc").is_file())
        self.assertFalse((aurorae_root / "leosrc").exists())
        aurorae_svg = ET.parse(aurorae_root / "decoration.svg").getroot()
        aurorae_colors = [item.attrib["stop-color"] for item in aurorae_svg.iter() if "stop-color" in item.attrib]
        self.assertEqual(aurorae_colors, ["#FF8800", "#0055CC"])

    def test_source_assets_are_never_modified(self):
        self.build()
        self.assertEqual((self.plasma / "widgets" / "panel.svg").read_bytes(), self.original_style)
        self.assertEqual((self.icons / "scalable" / "apps" / "demo.svg").read_bytes(), self.original_icon)
        self.assertEqual((self.aurorae / "decoration.svg").read_bytes(), self.original_aurorae)
        self.assertEqual(
            json.loads((self.plasma / "metadata.json").read_text(encoding="utf-8"))["KPlugin"]["Id"],
            "leos",
        )

    def test_same_pair_reuses_variants_and_different_pair_gets_new_ids(self):
        first = self.build("#FF8800", "#0055CC")
        again = self.build("#FF8800", "#0055CC")
        other = self.build("#12AB34", "#AB1234")
        self.assertEqual(first["plasmaStyleId"], again["plasmaStyleId"])
        self.assertEqual(first["auroraeThemeId"], again["auroraeThemeId"])
        self.assertNotEqual(first["plasmaStyleId"], other["plasmaStyleId"])
        self.assertNotEqual(first["auroraeThemeId"], other["auroraeThemeId"])

    def test_identical_a_and_b_colors_are_supported(self):
        result = self.build("#444444", "#444444")
        self.assertTrue((Path(result["plasmaStylePath"]) / "metadata.json").is_file())
        self.assertTrue((Path(result["auroraeThemePath"]) / f"{result['auroraeThemeId']}rc").is_file())

    def test_source_symlinks_are_rejected(self):
        extra = self.plasma / "widgets" / "unsafe.svg"
        extra.symlink_to(self.plasma / "widgets" / "panel.svg")
        with self.assertRaisesRegex(OSError, "Symlink"):
            self.build()

    def test_existing_conflicting_user_theme_is_never_overwritten(self):
        result = self.build()
        style_path = Path(result["plasmaStylePath"])
        metadata = style_path / ".leos-theme.json"
        metadata.write_text("{}", encoding="utf-8")
        before = metadata.read_bytes()
        with self.assertRaises(FileExistsError):
            self.build()
        self.assertEqual(metadata.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
