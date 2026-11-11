"""Integration checks for the selected-game artwork presentation."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class GamingArtworkIntegrationTests(unittest.TestCase):
    def test_library_exposes_only_discovered_local_artwork(self):
        source = (ROOT / "gaming/backend/library.py").read_text(encoding="utf-8")
        self.assertIn('"artwork": str(game.get("artwork", ""))', source)

    def test_qml_passes_artwork_through_game_selection(self):
        source = (ROOT / "gaming/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn('property string selectedArtwork: ""', source)
        self.assertIn('info.artwork, info.installStatus, info.appId)', source)
        self.assertIn('source: window.selectedArtwork', source)
        self.assertIn('window.selectedArtwork.length === 0', source)

    def test_game_details_expose_verified_installation_metadata(self):
        backend = (ROOT / "gaming/backend/library.py").read_text(encoding="utf-8")
        qml = (ROOT / "gaming/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn('"installStatus": (', backend)
        self.assertIn('"appId": str(game.get("app_id", ""))', backend)
        self.assertIn('property string selectedInstallStatus: ""', qml)
        self.assertIn('text: window.selectedInstallStatus || "—"', qml)
        self.assertIn('text: "IDENTIFIANT  ·  " + window.selectedAppId', qml)

    def test_missing_artwork_has_an_explicit_fallback(self):
        source = (ROOT / "gaming/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn('ARTWORK NON DISPONIBLE', source)
        self.assertIn('SÉLECTIONNE UN JEU', source)

    def test_launch_feedback_distinguishes_protocol_and_process_requests(self):
        source = (ROOT / "gaming/backend/library.py").read_text(encoding="utf-8")
        self.assertIn("QDesktopServices.openUrl(QUrl(target))", source)
        self.assertIn("le démarrage du jeu n'est pas confirmé", source)
        self.assertIn("le chargement du jeu n'est pas confirmé", source)
        self.assertIn("shutil.which(target)", source)
        self.assertIn("Lanceur ou exécutable introuvable", source)

    def test_controller_exposes_precise_launch_status(self):
        source = (ROOT / "gaming/backend/controller.py").read_text(encoding="utf-8")
        qml = (ROOT / "gaming/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn("def lastLaunchStatus(self) -> str:", source)
        self.assertIn("self.library.lastLaunchStatus", source)
        self.assertIn("statusText.text = leos.lastLaunchStatus", qml)


    def test_launcher_detection_uses_host_installation_evidence(self):
        backend = (ROOT / "gaming/backend/library.py").read_text(encoding="utf-8")
        controller = (ROOT / "gaming/backend/controller.py").read_text(encoding="utf-8")
        qml = (ROOT / "gaming/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn('shutil.which("steam")', backend)
        self.assertIn("com.valvesoftware.Steam", backend)
        self.assertIn('shutil.which("heroic")', backend)
        self.assertIn("com.heroicgameslauncher.hgl", backend)
        self.assertIn('shutil.which("lutris")', backend)
        self.assertIn("net.lutris.Lutris", backend)
        self.assertIn("def launcherStatuses(self) -> list[str]:", controller)
        self.assertIn("model: leos.launcherStatuses", qml)


if __name__ == "__main__":
    unittest.main()
