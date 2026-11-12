"""Tests for the validated LEOS Store catalogue loader."""

import json
import os
import tempfile
import unittest
from pathlib import Path

from shop.catalog_data import MAX_CATALOG_BYTES, MAX_CATALOG_ITEMS, load_catalog


ROOT = Path(__file__).resolve().parents[1]


def valid_item(app_id="org.example.App"):
    return {
        "id": app_id,
        "name": "Example",
        "category": "Utilities",
        "description": "A safe example app.",
        "source": "Flathub",
        "compatibility": "Flatpak",
        "operation_note": "Flatpak resolves dependencies after confirmation.",
    }


class StoreCatalogueLoaderTests(unittest.TestCase):
    def test_loads_and_validates_the_shipped_catalogue(self):
        items = load_catalog(ROOT / "shop" / "catalog.json")
        self.assertGreater(len(items), 0)
        self.assertEqual(len({item["id"] for item in items}), len(items))
        self.assertTrue(all(item["id"].count(".") >= 1 for item in items))

    def test_rejects_oversized_catalogue(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "catalog.json"
            path.write_bytes(b" " * (MAX_CATALOG_BYTES + 1))
            with self.assertRaisesRegex(ValueError, "taille"):
                load_catalog(path)

    def test_rejects_invalid_utf8_and_malformed_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "catalog.json"
            path.write_bytes(b"\\xff")
            with self.assertRaisesRegex(ValueError, "UTF-8"):
                load_catalog(path)
            path.write_text("{broken", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "JSON invalide"):
                load_catalog(path)

    def test_rejects_deeply_nested_catalogue_data(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "catalog.json"
            path.write_text("[" + "[" * 200 + "0" + "]" * 200 + "]", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "profonde"):
                load_catalog(path)

    def test_rejects_non_list_and_excessive_catalogue_sizes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "catalog.json"
            path.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "nombre limité"):
                load_catalog(path)
            path.write_text(json.dumps([valid_item(str(i) + ".App") for i in range(MAX_CATALOG_ITEMS + 1)]), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "nombre limité"):
                load_catalog(path)

    def test_rejects_missing_unknown_and_invalid_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "catalog.json"
            cases = []
            missing = valid_item()
            missing.pop("description")
            cases.append(missing)
            unknown = valid_item()
            unknown["command"] = "rm -rf /"
            cases.append(unknown)
            empty_name = valid_item()
            empty_name["name"] = "  "
            cases.append(empty_name)
            long_description = valid_item()
            long_description["description"] = "x" * 2049
            cases.append(long_description)
            control_character = valid_item()
            control_character["name"] = "Bad\\x00Name"
            cases.append(control_character)
            for item in cases:
                with self.subTest(item=item):
                    path.write_text(json.dumps([item]), encoding="utf-8")
                    with self.assertRaises(ValueError):
                        load_catalog(path)

    def test_rejects_invalid_or_duplicate_application_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "catalog.json"
            for invalid_id in ("invalid", "org..example", "org.example/Bad", "org.example."):
                path.write_text(json.dumps([valid_item(invalid_id)]), encoding="utf-8")
                with self.subTest(app_id=invalid_id):
                    with self.assertRaisesRegex(ValueError, "Identifiant"):
                        load_catalog(path)
            path.write_text(json.dumps([valid_item(), valid_item()]), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "dupliqué"):
                load_catalog(path)

    def test_bundled_flag_must_be_a_real_boolean(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "catalog.json"
            item = valid_item()
            item["bundled"] = 1
            path.write_text(json.dumps([item]), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "booléen"):
                load_catalog(path)

    def test_rejects_symlinked_catalogue(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target.json"
            target.write_text(json.dumps([valid_item()]), encoding="utf-8")
            link = root / "catalog.json"
            try:
                link.symlink_to(target)
            except (OSError, NotImplementedError):
                self.skipTest("Symbolic links unavailable")
            with self.assertRaisesRegex(ValueError, "symboliquement"):
                load_catalog(link)

    def test_rejects_non_regular_catalogue_files_without_blocking(self):
        if not hasattr(os, "mkfifo"):
            self.skipTest("Named pipes unavailable")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "catalog.json"
            os.mkfifo(path)
            with self.assertRaisesRegex(ValueError, "fichier régulier"):
                load_catalog(path)


if __name__ == "__main__":
    unittest.main()
