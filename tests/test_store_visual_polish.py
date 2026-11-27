"""Regression checks for the refined LEOS Store visual language."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class StoreVisualPolishTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qml = (ROOT / "shop/qml/Main.qml").read_text(encoding="utf-8")

    def test_store_uses_the_shared_brand_and_neutral_ambient_layers(self):
        self.assertIn("source: leosTheme.desktopLogoUrl", self.qml)
        self.assertIn("window.accentA", self.qml)
        self.assertIn("window.accentB", self.qml)
        self.assertIn("BOUTIQUE D’APPLICATIONS", self.qml)
        self.assertIn("window.themeColors.surface", self.qml)

    def test_catalog_selection_and_installation_state_are_visually_distinct(self):
        self.assertIn("window.selectedRow === index", self.qml)
        self.assertIn("installedScope === \"system\"", self.qml)
        self.assertIn("INCLUSE LEOS", self.qml)
        self.assertIn("INSTALLÉE", self.qml)
        self.assertIn("DISPONIBLE", self.qml)
        self.assertIn("width: window.selectedRow === index ? 3 : 0", self.qml)

    def test_primary_install_action_uses_live_a_b_accents_and_clear_priority(self):
        self.assertIn("installRemoveButton.enabled && !detailsPane.isInstalled", self.qml)
        self.assertIn("window.accentA.r, window.accentA.g, window.accentA.b", self.qml)
        self.assertIn("window.accentB.r, window.accentB.g, window.accentB.b", self.qml)
        self.assertIn("font.weight: Font.Bold", self.qml)

    def test_installed_apps_show_a_separate_update_action(self):
        self.assertIn('visible: detailsPane.isInstalled && !detailsPane.bundled', self.qml)
        self.assertIn('VÉRIFIER LES MISES À JOUR', self.qml)
        self.assertIn('Accessible.name: "Vérifier les mises à jour de " + detailsPane.appName', self.qml)

    def test_store_operations_and_flathub_verification_flow_remain_intact(self):
        for token in (
            "store.refreshInstalled()",
            "store.requestUninstall(window.selectedRow)",
            "store.requestInstall(window.selectedRow)",
            "store.confirmInstall(window.selectedRow)",
            'message.includes("disponible sur Flathub")',
            "store.verificationDetails",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.qml)


if __name__ == "__main__":
    unittest.main()
