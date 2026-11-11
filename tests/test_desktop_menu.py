"""Structural tests for the LEOS application menu."""
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DesktopMenuTests(unittest.TestCase):
    def test_menu_entry_is_packaged_as_a_desktop_application(self):
        entry = (ROOT / "desktop/applications/leos-menu.desktop").read_text(encoding="utf-8")
        self.assertIn("Name=LEOS — Applications", entry)
        self.assertIn("/usr/share/leos/desktop/menu_main.py", entry)
        self.assertIn("Terminal=false", entry)

    def test_menu_launcher_is_included_in_the_image_recipe(self):
        recipe = (ROOT / "recipes/recipe.yml").read_text(encoding="utf-8")
        self.assertIn("src: desktop/applications/leos-menu.desktop", recipe)
        self.assertIn("dest: /usr/share/applications/", recipe)

    def test_catalog_uses_desktop_entries_and_never_a_shell(self):
        source = (ROOT / "desktop/menu_controller.py").read_text(encoding="utf-8")
        self.assertIn("/usr/share/applications", source)
        self.assertIn(".local/share/applications", source)
        self.assertIn("parse_desktop_exec", source)
        self.assertIn("QProcess.startDetached", source)
        self.assertIn("QProcess.startDetached", source)
        self.assertNotIn("shell=True", source)
        self.assertNotIn("os.system(", source)

    def test_favourites_are_exposed_and_toggleable_from_the_menu(self):
        source = (ROOT / "desktop/menu_controller.py").read_text(encoding="utf-8")
        qml = (ROOT / "desktop/qml/Menu.qml").read_text(encoding="utf-8")
        self.assertIn("DockFavourites()", source)
        self.assertIn("def toggleFavourite", source)
        self.assertIn("applicationCatalog.toggleFavourite(desktopId)", qml)
        self.assertIn("required property bool isPinned", qml)

    def test_menu_has_quick_access_to_modes_and_control_centre(self):
        qml = (ROOT / "desktop/qml/Menu.qml").read_text(encoding="utf-8")
        self.assertIn('applicationCatalog.launch("leos-mode-selector.desktop")', qml)
        self.assertIn('applicationCatalog.launch("leos-control-center.desktop")', qml)

    def test_menu_has_quick_access_to_notification_centre(self):
        source = (ROOT / "desktop/menu_controller.py").read_text(encoding="utf-8")
        qml = (ROOT / "desktop/qml/Menu.qml").read_text(encoding="utf-8")
        self.assertIn('applicationCatalog.launch("leos-notifications.desktop")', qml)
        self.assertIn("def unreadNotificationCount", source)
        self.assertIn("def refreshNotificationCount", source)
        self.assertIn("self._notification_timer.start()", source)
        self.assertIn("applicationCatalog.unreadNotificationCount", qml)

    def test_menu_qml_exposes_search_categories_and_empty_state(self):
        qml = (ROOT / "desktop/qml/Menu.qml").read_text(encoding="utf-8")
        for feature in ("Rechercher une application", "applicationCatalog.categories()",
                        "applicationCatalog.setSearch(text)", "applicationCatalog.launch(desktopId)",
                        "Aucune application trouvée"):
            self.assertIn(feature, qml)

    def test_menu_entry_point_loads_its_qml(self):
        main = (ROOT / "desktop/menu_main.py").read_text(encoding="utf-8")
        self.assertIn("ApplicationCatalog()", main)
        self.assertIn(' / "qml" / "Menu.qml"', main)

    def test_menu_uses_a_dedicated_desktop_exec_field_code_parser(self):
        source = (ROOT / "desktop/menu_controller.py").read_text(encoding="utf-8")
        self.assertIn("from desktop.desktop_exec import parse_desktop_exec", source)
        self.assertIn('desktop_file=item["path"]', source)
        self.assertIn("args = argv[1:]", source)
        self.assertIn("QProcess.startDetached(program, args", source)
        self.assertNotIn("shlex.split(item[", source)

    def test_catalog_respects_tryexec_and_hides_terminal_only_entries(self):
        source = (ROOT / "desktop/menu_controller.py").read_text(encoding="utf-8")
        self.assertIn('values.get("Terminal", "false").casefold() == "true"', source)
        self.assertIn('try_exec = values.get("TryExec", "").strip()', source)
        self.assertIn("os.access(try_exec, os.X_OK)", source)

    def test_desktop_menu_uses_shared_accent_insensitive_search(self):
        source = (ROOT / "desktop/menu_controller.py").read_text(encoding="utf-8")
        self.assertIn("from leos_core.text import normalize_search_text", source)
        self.assertIn("item[\"desktopId\"]", source)
        self.assertIn("normalize_search_text(self._query)", source)

    def test_menu_uses_validated_desktop_entry_working_directory(self):
        source = (ROOT / "desktop/menu_controller.py").read_text(encoding="utf-8")
        self.assertIn("resolve_desktop_working_directory(values.get(\"Path\", \"\"))", source)
        self.assertIn('"workingDirectory": working_directory', source)
        self.assertIn('QProcess.startDetached(program, args, item["workingDirectory"])', source)

    def test_menu_registers_kde_icon_provider(self):
        main = (ROOT / "desktop/menu_main.py").read_text(encoding="utf-8")
        qml = (ROOT / "desktop/qml/Menu.qml").read_text(encoding="utf-8")
        self.assertIn("DesktopIconProvider()", main)
        self.assertIn('engine.addImageProvider("desktop-icons"', main)
        self.assertIn("image://desktop-icons/", qml)
        self.assertIn("encodeURIComponent(icon)", qml)


if __name__ == "__main__":
    unittest.main()
