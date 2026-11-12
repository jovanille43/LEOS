"""Contract tests for controller and keyboard navigation in the Gaming library."""

from pathlib import Path
import unittest


class GamingLibraryGamepadNavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qml = (
            Path(__file__).resolve().parents[1] / "gaming/qml/Main.qml"
        ).read_text(encoding="utf-8")

    def test_navigation_exposes_toolbar_and_details_focus_areas(self):
        self.assertIn('property string navigationArea: "categories"', self.qml)
        self.assertIn('navigationArea === "toolbar"', self.qml)
        self.assertIn('navigationArea === "details"', self.qml)
        self.assertIn("property int toolbarFocusIndex: 0", self.qml)
        self.assertIn("property int detailsActionIndex: 0", self.qml)

    def test_toolbar_focus_covers_search_refresh_and_manual_add(self):
        self.assertIn("function focusToolbar(index)", self.qml)
        self.assertIn("searchField.forceActiveFocus()", self.qml)
        self.assertIn("refreshLibraryButton.forceActiveFocus()", self.qml)
        self.assertIn("addGameButton.forceActiveFocus()", self.qml)
        self.assertIn("function activateToolbarFocus()", self.qml)
        self.assertIn("leos.refreshLibrary()", self.qml)
        self.assertIn("addDialog.open()", self.qml)

    def test_grid_boundaries_enter_toolbar_and_game_details(self):
        self.assertIn("selectedIndex < columns", self.qml)
        self.assertIn("selectedIndex % columns === columns - 1", self.qml)
        self.assertIn("focusToolbar(0)", self.qml)
        self.assertIn("focusDetailsAction(0)", self.qml)

    def test_details_actions_have_a_bounded_focus_order(self):
        self.assertIn("function focusDetailsAction(index)", self.qml)
        self.assertIn("Math.max(0, Math.min(1, index))", self.qml)
        self.assertIn("favoriteGameButton.forceActiveFocus()", self.qml)
        self.assertIn("launchSelectedGameButton.forceActiveFocus()", self.qml)
        self.assertIn("function toggleSelectedFavorite()", self.qml)
        self.assertIn("function launchSelectedGame()", self.qml)

    def test_confirm_activates_the_action_for_the_current_navigation_area(self):
        self.assertIn("activateToolbarFocus()", self.qml)
        self.assertIn("if (detailsActionIndex === 0)", self.qml)
        self.assertIn("toggleSelectedFavorite()", self.qml)
        self.assertIn("launchSelectedGame()", self.qml)

    def test_back_returns_from_toolbar_or_details_to_the_grid(self):
        self.assertIn('navigationArea === "details" || navigationArea === "toolbar"', self.qml)
        self.assertIn('navigationArea = "games"', self.qml)
        self.assertIn("gameGrid.forceActiveFocus()", self.qml)

    def test_search_and_toolbar_controls_show_the_controller_focus(self):
        self.assertIn("window.toolbarFocusIndex === 0", self.qml)
        self.assertIn("window.toolbarFocusIndex === 1", self.qml)
        self.assertIn("window.toolbarFocusIndex === 2", self.qml)
        self.assertIn("window.detailsActionIndex === 0", self.qml)
        self.assertIn("window.detailsActionIndex === 1", self.qml)

    def test_keyboard_focus_keeps_toolbar_category_and_detail_state_synchronized(self):
        self.assertIn('window.selectedCategoryIndex = window.categoryNames.indexOf(modelData)', self.qml)
        self.assertIn('window.toolbarFocusIndex = 1', self.qml)
        self.assertIn('window.toolbarFocusIndex = 2', self.qml)
        self.assertIn('window.detailsActionIndex = 0', self.qml)
        self.assertIn('window.detailsActionIndex = 1', self.qml)

    def test_gamepad_can_accept_the_manual_add_dialog(self):
        self.assertIn("if (addDialog.visible)", self.qml)
        self.assertIn("addDialog.accept()", self.qml)


if __name__ == "__main__":
    unittest.main()
