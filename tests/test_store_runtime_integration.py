"""Integration contract for transparent Flatpak runtime verification."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class StoreRuntimeIntegrationTests(unittest.TestCase):
    def test_install_verification_reads_flatpak_application_metadata(self):
        source = (ROOT / "shop/controller.py").read_text(encoding="utf-8")
        self.assertIn('"--show-metadata"', source)
        self.assertIn('runtime_summary(stdout)', source)
        self.assertIn('def verificationDetails(self) -> str:', source)

    def test_runtime_details_are_visible_before_final_install_confirmation(self):
        qml = (ROOT / "shop/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn('text: store.verificationDetails', qml)
        self.assertIn('store.confirmInstall(window.selectedRow)', qml)
        self.assertIn('INSTALLER MAINTENANT', qml)

    def test_install_flow_keeps_explicit_confirmation_after_source_check(self):
        source = (ROOT / "shop/controller.py").read_text(encoding="utf-8")
        qml = (ROOT / "shop/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn('self._action = "verified"', source)
        self.assertIn('self._action != "verified"', source)
        self.assertIn('operationDialog.open()', qml)
        self.assertIn('verifyDialog.open()', qml)

    def test_catalog_selection_and_filters_are_locked_during_flatpak_operations(self):
        qml = (ROOT / "shop/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn("enabled: !store.busy", qml)
        self.assertIn("model: catalogModel\n                        enabled: !store.busy", qml)


if __name__ == "__main__":
    unittest.main()
