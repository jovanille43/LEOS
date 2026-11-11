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

    def test_qprocess_streams_stdout_and_stderr_while_flatpak_runs(self):
        source = (ROOT / "shop/controller.py").read_text(encoding="utf-8")
        self.assertIn("readyReadStandardOutput.connect(self._read_output)", source)
        self.assertIn("readyReadStandardError.connect(self._read_output)", source)
        self.assertIn("self._stdout.extend(self._process.readAllStandardOutput().data())", source)
        self.assertIn("self._stderr.extend(self._process.readAllStandardError().data())", source)

    def test_store_search_normalizes_accents_spaces_and_searches_metadata(self):
        qml = (ROOT / "shop/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn("function normalizedSearchText(value)", qml)
        self.assertIn('.normalize("NFKD")', qml)
        self.assertIn('.replace(/[\\u0300-\\u036f]/g, "")', qml)
        self.assertIn(".replace(/\\s+/g, \" \")", qml)
        self.assertIn("[name, appId, category, description, source].join", qml)
        self.assertIn("window.matchesSearch(name, appId, category, description, source)", qml)


if __name__ == "__main__":
    unittest.main()
