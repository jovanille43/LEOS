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
        recipe = (ROOT / "recipes/common-modules.yml").read_text(encoding="utf-8")
        self.assertIn("src: desktop/applications/leos-menu.desktop", recipe)
        self.assertIn("dest: /usr/share/applications/", recipe)

    def test_catalog_uses_desktop_entries_and_never_a_shell(self):
        source = (ROOT / "desktop/menu_controller.py").read_text(encoding="utf-8")
        self.assertIn("APP_DIRS = desktop_application_dirs()", source)
        self.assertIn("desktop_entry_paths(APP_DIRS)", source)
        entries = (ROOT / "desktop/desktop_entries.py").read_text(encoding="utf-8")
        self.assertIn('["/usr/local/share", "/usr/share"]', entries)
        self.assertIn('xdg_data_home() / "applications"', entries)
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
        self.assertIn('window.launchApplication("leos-mode-selector.desktop"', qml)
        self.assertIn('window.launchApplication("leos-control-center.desktop"', qml)

    def test_menu_has_quick_access_to_notification_centre(self):
        source = (ROOT / "desktop/menu_controller.py").read_text(encoding="utf-8")
        qml = (ROOT / "desktop/qml/Menu.qml").read_text(encoding="utf-8")
        self.assertIn('window.launchApplication("leos-notifications.desktop"', qml)
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
        filters = (ROOT / "desktop/desktop_entries.py").read_text(encoding="utf-8")
        self.assertIn("from desktop.desktop_entries import", source)
        self.assertIn("filter_desktop_applications(", source)
        self.assertIn("from leos_core.text import normalize_search_text", filters)
        self.assertIn("normalize_search_text(search_query)", filters)
        self.assertIn('str(item.get("desktopId", ""))', filters)

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

    def test_catalog_uses_pure_desktop_entry_helpers(self):
        source = (ROOT / "desktop/menu_controller.py").read_text(encoding="utf-8")
        self.assertIn("from desktop.desktop_entries import (", source)
        self.assertIn("desktop_application_dirs, desktop_entry_is_visible, desktop_entry_paths,", source)
        self.assertIn("filter_desktop_applications, localized_desktop_value,", source)
        self.assertIn("desktop_entry_is_visible(values, current_desktops)", source)
        self.assertIn('localized_desktop_value(values, "Name", locale_name)', source)
        self.assertIn('localized_desktop_value(values, "Comment", locale_name)', source)

    def test_menu_exposes_a_favourites_category_in_addition_to_app_categories(self):
        source = (ROOT / "desktop/menu_controller.py").read_text(encoding="utf-8")
        filters = (ROOT / "desktop/desktop_entries.py").read_text(encoding="utf-8")
        self.assertIn('return ["Tout", "Favoris", "Récemment utilisées"] + sorted', source)
        self.assertIn('if category == "Favoris":', filters)
        self.assertIn("selected.sort(key=lambda item: pinned_order.index", filters)
        self.assertIn("filter_desktop_applications(", source)

    def test_menu_exposes_recent_applications_and_records_only_successful_launches(self):
        source = (ROOT / "desktop/menu_controller.py").read_text(encoding="utf-8")
        self.assertIn("RecentApplications()", source)
        self.assertIn('"Récemment utilisées"', source)
        self.assertIn("self.recentApplications.record(desktop_id)", source)
        self.assertIn("if not ok:", source)
        self.assertIn("self._apply_filter()", source)

    def test_favourite_toggle_reapplies_filter_and_updates_membership(self):
        source = (ROOT / "desktop/menu_controller.py").read_text(encoding="utf-8")
        start = source.index("def toggleFavourite")
        end = source.index("def clearRecentApplications", start)
        block = source[start:end]
        self.assertIn("self._apply_filter()", block)
        self.assertNotIn("self.dataChanged.emit", block)

    def test_menu_exposes_current_category_for_the_results_heading(self):
        source = (ROOT / "desktop/menu_controller.py").read_text(encoding="utf-8")
        qml = (ROOT / "desktop/qml/Menu.qml").read_text(encoding="utf-8")
        self.assertIn("@Property(str, notify=categoryChanged)", source)
        self.assertIn("def currentCategory(self)", source)
        self.assertIn("if category not in self.categories():", source)
        self.assertIn("applicationCatalog.currentCategory", qml)

    def test_menu_rejects_unknown_category_filter_values(self):
        source = (ROOT / "desktop/menu_controller.py").read_text(encoding="utf-8")
        self.assertIn("if category not in self.categories():", source)

    def test_application_grid_supports_keyboard_navigation_and_activation(self):
        qml = (ROOT / "desktop/qml/Menu.qml").read_text(encoding="utf-8")
        self.assertIn("keyNavigationEnabled: true", qml)
        self.assertIn("keyNavigationWraps: false", qml)
        self.assertIn("activeFocusOnTab: true", qml)
        self.assertIn("Keys.onPressed", qml)
        self.assertIn("Qt.Key_Return", qml)
        self.assertIn("Qt.Key_Enter", qml)
        self.assertIn("Qt.Key_Space", qml)
        self.assertIn("function activateApplication()", qml)

    def test_menu_offers_explicit_recent_history_clear_action(self):
        source = (ROOT / "desktop/menu_controller.py").read_text(encoding="utf-8")
        qml = (ROOT / "desktop/qml/Menu.qml").read_text(encoding="utf-8")
        self.assertIn("def clearRecentApplications(self)", source)
        self.assertIn("self.recentApplications.clear()", source)
        self.assertIn('applicationCatalog.clearRecentApplications()', qml)
        self.assertIn('applicationCatalog.currentCategory === "Récemment utilisées"', qml)

    def test_menu_polls_shared_favourites_and_recent_lists(self):
        source = (ROOT / "desktop/menu_controller.py").read_text(encoding="utf-8")
        self.assertIn("self._notification_timer.timeout.connect(self.refreshSharedStores)", source)
        self.assertIn("def refreshSharedStores(self)", source)
        self.assertIn("if favourites == self._favourites_snapshot and recent == self._recent_snapshot:", source)
        self.assertIn("self._apply_filter()", source)

    def test_keyboard_activation_uses_shared_launch_close_behavior(self):
        qml = (ROOT / "desktop/qml/Menu.qml").read_text(encoding="utf-8")
        start = qml.index("function activateApplication()")
        end = qml.index("Keys.onPressed", start)
        self.assertIn("window.launchApplication(desktopId, name)", qml[start:end])

    def test_menu_preserves_precise_backend_launch_errors(self):
        qml = (ROOT / "desktop/qml/Menu.qml").read_text(encoding="utf-8")
        start = qml.index("function launchApplication(")
        end = qml.index("Shortcut {", start)
        helper = qml[start:end]
        self.assertNotIn("Impossible de lancer", helper)
        self.assertIn("function onLaunchFailed(message) { status.text = message }", qml)

    def test_desktop_menu_header_uses_official_emblem_with_text_fallback(self):
        qml = (ROOT / "desktop/qml/Menu.qml").read_text(encoding="utf-8")
        self.assertIn("../../branding/desktop-logo.jpeg", qml)
        self.assertIn("asynchronous: true", qml)
        self.assertIn("visible: desktopMenuLogo.status !== Image.Ready", qml)

    def test_menu_button_content_uses_explicit_button_ids(self):
        qml = (ROOT / "desktop/qml/Menu.qml").read_text(encoding="utf-8")
        self.assertIn("categoryMenuButton.text", qml)
        self.assertIn("categoryMenuButton.down", qml)
        self.assertIn("favouriteMoveUpButton.text", qml)
        self.assertIn("favouriteMoveDownButton.text", qml)
        self.assertIn("favouritePinButton.text", qml)
        self.assertNotIn("parent.text", qml)
        self.assertNotIn("parent.down", qml)
        self.assertNotIn("parent.enabled", qml)

    def test_menu_closes_after_successful_launch_and_on_escape(self):
        qml = (ROOT / "desktop/qml/Menu.qml").read_text(encoding="utf-8")
        self.assertIn("function launchApplication(desktopId, applicationName)", qml)
        self.assertIn("if (!applicationCatalog.launch(desktopId))", qml)
        self.assertIn("window.close()", qml)
        self.assertIn('sequence: "Escape"', qml)
        self.assertIn("context: Qt.WindowShortcut", qml)
        self.assertIn("Component.onCompleted: search.forceActiveFocus()", qml)

    def test_application_cards_and_quick_actions_share_the_launch_helper(self):
        qml = (ROOT / "desktop/qml/Menu.qml").read_text(encoding="utf-8")
        self.assertIn('window.launchApplication("leos-mode-selector.desktop"', qml)
        self.assertIn('window.launchApplication("leos-control-center.desktop"', qml)
        self.assertIn('window.launchApplication("leos-notifications.desktop"', qml)
        self.assertIn("window.launchApplication(desktopId, name)", qml)

    def test_favourite_toggle_captures_previous_state_before_model_reset(self):
        qml = (ROOT / "desktop/qml/Menu.qml").read_text(encoding="utf-8")
        start = qml.index('text: isPinned ? "★" : "☆"')
        end = qml.index("contentItem: Label", start)
        handler = qml[start:end]
        self.assertIn("const wasPinned = isPinned", handler)
        self.assertLess(
            handler.index("const wasPinned = isPinned"),
            handler.index("applicationCatalog.toggleFavourite(desktopId)"),
        )
        self.assertIn("status.text = wasPinned ?", handler)

    def test_favourites_view_exposes_relative_reordering_controls(self):
        source = (ROOT / "desktop/menu_controller.py").read_text(encoding="utf-8")
        store = (ROOT / "desktop/dock_favourites.py").read_text(encoding="utf-8")
        qml = (ROOT / "desktop/qml/Menu.qml").read_text(encoding="utf-8")
        self.assertIn("def moveFavourite(self, desktop_id: str, offset: int)", source)
        self.assertIn("self.favourites.move_by(desktop_id, offset)", source)
        self.assertIn("def move_by(self, desktop_id: str, offset: int)", store)
        self.assertIn('applicationCatalog.currentCategory === "Favoris"', qml)
        self.assertIn("applicationCatalog.moveFavourite(desktopId, -1)", qml)
        self.assertIn("applicationCatalog.moveFavourite(desktopId, 1)", qml)
        self.assertIn("search.text.length === 0", qml)

    def test_catalog_discovers_nested_application_entries_with_desktop_ids(self):
        source = (ROOT / "desktop/menu_controller.py").read_text(encoding="utf-8")
        entries = (ROOT / "desktop/desktop_entries.py").read_text(encoding="utf-8")
        entries = (ROOT / "desktop/desktop_entries.py").read_text(encoding="utf-8")
        self.assertIn("desktop_entry_paths(APP_DIRS)", source)
        self.assertIn("for desktop_id, path in desktop_entry_paths(APP_DIRS):", source)
        self.assertIn('directory.rglob("*.desktop")', entries)
        self.assertIn("desktop_file_id(path, directory)", entries)
        self.assertIn('"desktopId": desktop_id or path.name', source)
        self.assertIn('return "-".join(relative.parts)', entries)


if __name__ == "__main__":
    unittest.main()
