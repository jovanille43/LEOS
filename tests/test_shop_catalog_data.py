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
            path.write_bytes(bytes((0xFF,)))
            with self.assertRaisesRegex(ValueError, "UTF-8"):
                load_catalog(path)
            path.write_text("{broken", encoding="utf-8")
            with self.assertRaises(ValueError):
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
            control_character["name"] = "Bad\x00Name"
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

    def test_catalogue_rejects_sources_not_supported_by_the_store(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "catalog.json"
            item = valid_item()
            item["source"] = "OtherStore"
            path.write_text(json.dumps([item]), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Source de catalogue"):
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


    def test_store_catalogue_entries_are_keyboard_accessible_buttons(self):
        qml = (ROOT / "shop" / "qml" / "Main.qml").read_text(encoding="utf-8")
        self.assertIn('Accessible.name: "Catalogue d\'applications LEOS"', qml)
        self.assertIn("id: appRowButton", qml)
        self.assertIn("activeFocusOnTab: true", qml)
        self.assertIn("Accessible.selected: window.selectedRow === index", qml)
        self.assertIn("appRowButton.activeFocus", qml)
        self.assertNotIn("MouseArea {", qml)

    def test_store_search_and_category_filters_reset_stale_details(self):
        qml = (ROOT / "shop" / "qml" / "Main.qml").read_text(encoding="utf-8")
        self.assertIn("onTextChanged: window.clearSelection()", qml)
        self.assertIn("onCurrentTextChanged: window.clearSelection()", qml)
        self.assertIn("function clearSelection()", qml)
        self.assertIn("function selectApp(", qml)

    def test_store_details_action_and_controls_expose_accessible_focus_states(self):
        qml = (ROOT / "shop" / "qml" / "Main.qml").read_text(encoding="utf-8")
        self.assertIn('Accessible.name: "Rechercher dans la Boutique LEOS"', qml)
        self.assertIn('Accessible.name: "Filtrer par catégorie"', qml)
        self.assertIn("installRemoveButton.activeFocus", qml)
        self.assertIn("Une confirmation sera demandée avant toute modification.", qml)

    def test_store_window_and_catalogue_details_adapt_to_compact_widths(self):
        qml = (ROOT / "shop" / "qml" / "Main.qml").read_text(encoding="utf-8")
        self.assertIn("minimumWidth: 900", qml)
        self.assertIn("window.width < 1080 ? 18 : 30", qml)
        self.assertIn("Layout.preferredWidth: window.width < 1080 ? 300 : 360", qml)
        self.assertIn("Layout.minimumWidth: 280", qml)
        self.assertIn('text: "DÉCOUVRIR · INSTALLER · GÉRER"', qml)
        self.assertIn('text: appList.count + " APPLICATIONS"', qml)
        self.assertIn('text: "IDENTIFIANT"', qml)
        self.assertIn('text: detailsPane.appId || "—"', qml)
        self.assertIn("opacity: 0.05", qml)
        self.assertIn("opacity: 0.04", qml)
        self.assertIn("window.themeColors.accent_primary", qml)
        self.assertIn("window.themeColors.accent_secondary", qml)

    def test_store_categories_are_derived_from_the_validated_catalogue(self):
        from shop.catalog import CatalogModel

        model = CatalogModel()
        expected = sorted({item["category"] for item in load_catalog(ROOT / "shop" / "catalog.json")}, key=str.casefold)
        self.assertEqual(model.availableCategories, expected)
        qml = (ROOT / "shop" / "qml" / "Main.qml").read_text(encoding="utf-8")
        self.assertIn('model: ["Toutes"].concat(catalogModel.availableCategories)', qml)
        self.assertNotIn('["Toutes", "Gaming", "Émulation", "Multimedia"', qml)

    def test_store_shows_visible_result_count_and_recoverable_empty_state(self):
        qml = (ROOT / "shop" / "qml" / "Main.qml").read_text(encoding="utf-8")
        self.assertIn("function visibleApplicationCount()", qml)
        self.assertIn("window.visibleApplicationCount() + \" / \" + catalogModel.rowCount()", qml)
        self.assertIn("Aucun résultat pour ces filtres", qml)
        self.assertIn("function clearFilters()", qml)
        self.assertIn("Effacer la recherche et le filtre de catégorie", qml)
        self.assertIn("item.compatibility, item.operation_note", qml)

    def test_v2_emulator_catalogue_has_curated_automatic_flathub_apps(self):
        items = load_catalog(ROOT / "shop" / "catalog.json")
        emulators = {
            item["id"]: item
            for item in items
            if item["category"] == "Émulation"
        }
        self.assertEqual(set(emulators), {
            "org.libretro.RetroArch",
            "org.DolphinEmu.dolphin-emu",
            "net.pcsx2.PCSX2",
            "org.ppsspp.PPSSPP",
            "net.kuribo64.melonDS",
            "net.rpcs3.RPCS3",
            "dev.eden_emu.eden",
        })
        self.assertTrue(all(item.get("bundled") is True for item in emulators.values()))
        self.assertTrue(all("automatiquement" in item["operation_note"].casefold() for item in emulators.values()))
        self.assertTrue(all("Flathub" == item["source"] for item in emulators.values()))
        self.assertIn("non vérifié", emulators["org.DolphinEmu.dolphin-emu"]["compatibility"])
        self.assertIn("non vérifié", emulators["net.rpcs3.RPCS3"]["compatibility"])
        self.assertIn("non vérifié", emulators["dev.eden_emu.eden"]["compatibility"])
        self.assertIn("x86-64-v3", emulators["dev.eden_emu.eden"]["compatibility"])

if __name__ == "__main__":
    unittest.main()
