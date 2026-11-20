"""Tests for safe user-scoped A/B variants of KDE theme resources."""

import json
import tempfile
import unittest
from pathlib import Path

from desktop.theme_asset_variants import create_recolored_theme_variant


class ThemeAssetVariantTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        (self.source / "widgets").mkdir(parents=True)
        (self.source / "widgets" / "edge.svg").write_text(
            '<svg><stop stop-color="#00D9FF"/><stop stop-color="#E33BFF"/>'
            '<path fill="#808080"/></svg>',
            encoding="utf-8",
        )
        (self.source / "metadata.json").write_text(
            json.dumps({"KPlugin": {"Id": "leos", "Name": "LEOS"}}),
            encoding="utf-8",
        )
        (self.source / "index.theme").write_text(
            "[Icon Theme]\nName=LEOS\nComment=LEOS icons\nInherits=breeze,hicolor\n",
            encoding="utf-8",
        )
        self.destination = self.root / "user-themes"

    def tearDown(self):
        self.temp.cleanup()

    def test_plasma_variant_recolors_accent_endpoints_and_preserves_neutrals(self):
        variant = create_recolored_theme_variant(
            self.source, self.destination, "leos", "#FF8800", "#0055CC",
            metadata_kind="plasma",
        )
        directory = self.destination / variant
        metadata = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["KPlugin"]["Id"], variant)
        self.assertEqual(metadata["KPlugin"]["Name"], "LEOS personnalisé")
        svg = (directory / "widgets" / "edge.svg").read_text(encoding="utf-8")
        self.assertIn("#FF8800", svg)
        self.assertIn("#0055CC", svg)
        self.assertIn("#808080", svg)
        self.assertIn("#00D9FF", (self.source / "widgets" / "edge.svg").read_text(encoding="utf-8"))

    def test_icon_variant_gets_its_own_id_and_recolored_svg(self):
        variant = create_recolored_theme_variant(
            self.source, self.destination, "leos", "#FF8800", "#0055CC",
            metadata_kind="icons",
        )
        directory = self.destination / variant
        index = (directory / "index.theme").read_text(encoding="utf-8")
        self.assertIn(f"Name=LEOS personnalisé {variant[-12:]}", index)
        svg = (directory / "widgets" / "edge.svg").read_text(encoding="utf-8")
        self.assertIn("#FF8800", svg)
        self.assertIn("#0055CC", svg)
        self.assertIn("#808080", svg)

    def test_variant_is_reused_for_same_sources_and_colors(self):
        first = create_recolored_theme_variant(
            self.source, self.destination, "leos", "#FF8800", "#0055CC",
            metadata_kind="plasma",
        )
        second = create_recolored_theme_variant(
            self.source, self.destination, "leos", "#FF8800", "#0055CC",
            metadata_kind="plasma",
        )
        self.assertEqual(first, second)

    def test_source_symlinks_are_rejected(self):
        link = self.source / "widgets" / "outside.svg"
        outside = self.root / "outside.svg"
        outside.write_text("<svg/>", encoding="utf-8")
        try:
            link.symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest("Symbolic links are unavailable")
        with self.assertRaisesRegex(OSError, "Symbolic links"):
            create_recolored_theme_variant(
                self.source, self.destination, "leos", "#FF8800", "#0055CC",
                metadata_kind="plasma",
            )
        self.assertFalse(self.destination.exists())


if __name__ == "__main__":
    unittest.main()
