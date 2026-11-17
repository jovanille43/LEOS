"""Tests for dynamic, user-scoped LEOS Plasma and Aurorae accents."""

import hashlib
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from types import SimpleNamespace

from desktop.plasma_assets import _recolor_svg, accent_color_map, generate_user_theme_assets
from desktop.plasma_style import PlasmaStyleManager
from leos_core.settings import SettingsStore

ROOT = Path(__file__).resolve().parents[1]
SVG_NS = "{http://www.w3.org/2000/svg}"


class DynamicPlasmaAssetTests(unittest.TestCase):
    def _settings(self, root: Path) -> SettingsStore:
        settings = SettingsStore(root / "settings.json")
        settings.set_many({
            "theme": "custom",
            "custom_accent_primary": "#11AA77",
            "custom_accent_secondary": "#D9A521",
        })
        return settings

    def test_inline_css_and_svg_presentation_attributes_are_recolored(self):
        source = (
            b'<svg xmlns="http://www.w3.org/2000/svg">'
            b'<rect fill="#00D9FF" stroke="#E33BFF" '
            b'style="fill:#00D9FF;stroke:#E33BFF"/>'
            b'</svg>'
        )
        mapping = accent_color_map("#11AA77", "#D9A521")
        result = _recolor_svg(source, mapping, Path("synthetic.svg")).decode("utf-8")
        self.assertEqual(result.count("#11AA77"), 2)
        self.assertEqual(result.count("#D9A521"), 2)
        self.assertNotIn("#00D9FF", result)
        self.assertNotIn("#E33BFF", result)

    def test_plasma_and_aurorae_assets_are_generated_without_modifying_sources(self):
        source_files = [
            path for base in (ROOT / "plasma-theme/leos", ROOT / "aurorae/leos")
            for path in base.rglob("*") if path.is_file()
        ]
        before = {
            path: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in source_files
        }

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            settings = self._settings(root)
            output = generate_user_theme_assets(
                settings, data_root=root / "data", source_root=ROOT
            )
            plasma = Path(output["plasma"])
            aurorae = Path(output["aurorae"])
            self.assertTrue((plasma / "metadata.json").is_file())
            self.assertTrue((plasma / "widgets/button.svg").is_file())
            self.assertTrue((aurorae / "metadata.desktop").is_file())
            self.assertTrue((aurorae / "decoration.svg").is_file())

            all_svg = list(plasma.rglob("*.svg")) + list(aurorae.rglob("*.svg"))
            self.assertGreaterEqual(len(all_svg), 10)
            for svg in all_svg:
                with self.subTest(svg=svg.relative_to(root)):
                    generated_root = ET.parse(svg).getroot()
                    self.assertEqual(generated_root.tag, f"{SVG_NS}svg")
            combined = "\n".join(svg.read_text(encoding="utf-8") for svg in all_svg)
            self.assertIn("#11AA77", combined)
            self.assertIn("#D9A521", combined)
            for original_accent in (
                "#00D9FF", "#E33BFF", "#67DFF8", "#E66BD5",
                "#6BE6FF", "#EF70D9", "#65E5FF", "#F078D7",
                "#899BFF", "#A28CFF", "#83BFFF",
            ):
                self.assertNotIn(original_accent, combined)

            generated_metadata = (plasma / "metadata.json").read_text(encoding="utf-8")
            self.assertIn('"Id": "leos"', generated_metadata)
            self.assertIn("selected A/B accent colors", generated_metadata)
            self.assertIn(
                "selected A/B accent colors",
                (aurorae / "metadata.desktop").read_text(encoding="utf-8"),
            )

        after = {
            path: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in source_files
        }
        self.assertEqual(before, after)

    def test_output_refuses_symbolic_link_theme_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            linked = root / "linked"
            real = root / "real"
            real.mkdir()
            linked.symlink_to(real, target_is_directory=True)
            settings = self._settings(root)
            with self.assertRaises(OSError):
                generate_user_theme_assets(
                    settings, data_root=linked, source_root=ROOT
                )

    def test_plasma_style_apply_generates_dynamic_assets_before_selection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            settings = self._settings(root)
            config = root / "config"
            config.mkdir()
            (config / "plasmarc").write_text(
                "[Theme]\nname=breeze\n", encoding="utf-8"
            )
            manager = PlasmaStyleManager(
                data_home=root / "data",
                config_home=config,
                state_home=root / "state",
                apply_executable="plasma-apply-desktoptheme",
                runner=lambda *args, **kwargs: SimpleNamespace(
                    returncode=0, stderr=""
                ),
                settings=settings,
            )
            message = manager.apply_style()
            self.assertIn("A/B", message)
            self.assertTrue(
                (root / "data/plasma/desktoptheme/leos/metadata.json").is_file()
            )
            self.assertTrue(
                (root / "data/aurorae/themes/leos/decoration.svg").is_file()
            )
            self.assertEqual(manager.current_style(), "leos")


if __name__ == "__main__":
    unittest.main()
