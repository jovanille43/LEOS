"""Structural tests for the Control Center system update page."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SystemUpdateIntegrationTests(unittest.TestCase):
    def test_control_center_exposes_check_and_native_updater_actions(self):
        controller = (ROOT / "control_center/controller.py").read_text(encoding="utf-8")
        qml = (ROOT / "control_center/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn("def checkForSystemUpdates", controller)
        self.assertIn("def openSystemUpdater", controller)
        update_module = (ROOT / "control_center/system_updates.py").read_text(encoding="utf-8")
        self.assertIn('"update-check"', update_module)
        self.assertIn("controlCenter.checkForSystemUpdates()", qml)
        self.assertIn("controlCenter.openSystemUpdater()", qml)
        self.assertIn("Mises à jour", qml)
        self.assertIn("refreshPendingSystemUpdate", controller)
        self.assertIn("setInterval(10 * 60 * 1000)", controller)
        self.assertIn('"status", "--json"', update_module)
        self.assertIn("pending_deployment_from_status", update_module)

    def test_failed_deployment_status_reads_discard_cached_recovery_inventory(self):
        controller = (ROOT / "control_center/controller.py").read_text(encoding="utf-8")
        self.assertIn("def _reset_deployment_snapshot", controller)
        self.assertIn("self._reset_deployment_snapshot()", controller)
        self.assertIn("if inventory is None:", controller)
        self.assertIn("if _exit_status != QProcess.ExitStatus.NormalExit or exit_code != 0:", controller)

    def test_system_update_probes_have_bounded_runtime(self):
        controller = (ROOT / "control_center/controller.py").read_text(encoding="utf-8")
        self.assertIn("SYSTEM_UPDATE_CHECK_TIMEOUT_MS = 120_000", controller)
        self.assertIn("DEPLOYMENT_STATUS_TIMEOUT_MS = 20_000", controller)
        self.assertIn("self._system_update_timeout.setSingleShot(True)", controller)
        self.assertIn("self._system_update_timeout.timeout.connect(self._on_system_update_check_timeout)", controller)
        self.assertIn("self._deployment_timeout.setSingleShot(True)", controller)
        self.assertIn("self._deployment_timeout.timeout.connect(self._on_deployment_status_timeout)", controller)
        self.assertIn("self._system_update_process.kill()", controller)
        self.assertIn("self._deployment_process.kill()", controller)
        self.assertIn("a dépassé deux minutes", controller)
        self.assertIn("if self._system_update_timed_out:", controller)
        self.assertIn("if self._deployment_timed_out:", controller)

    def test_crashed_update_processes_are_not_treated_as_successful_checks(self):
        controller = (ROOT / "control_center/controller.py").read_text(encoding="utf-8")
        self.assertIn("if _exit_status != QProcess.ExitStatus.NormalExit or exit_code != 0:", controller)
        self.assertIn("if _exit_status == QProcess.ExitStatus.NormalExit", controller)
        self.assertIn('else "error"', controller)

    def test_update_check_never_calls_install_or_upgrade(self):
        module = (ROOT / "control_center/system_updates.py").read_text(encoding="utf-8")
        controller = (ROOT / "control_center/controller.py").read_text(encoding="utf-8")
        self.assertIn('"update-check"', module)
        self.assertNotIn('"update"', module)
        self.assertNotIn('"upgrade"', module)
        self.assertNotIn("uupd-update", controller)
        self.assertNotIn('"upgrade"', module)
        self.assertNotIn('"deploy"', module)

    def test_control_center_exposes_read_only_ostree_deployment_inventory(self):
        controller = (ROOT / "control_center/controller.py").read_text(encoding="utf-8")
        module = (ROOT / "control_center/system_updates.py").read_text(encoding="utf-8")
        qml = (ROOT / "control_center/qml/Main.qml").read_text(encoding="utf-8")

        self.assertIn("deployment_inventory_from_status", controller)
        self.assertIn("def deploymentSnapshot", controller)
        self.assertIn("deployment_inventory_from_status", module)
        self.assertIn("controlCenter.deploymentSnapshot.bootedVersion", qml)
        self.assertIn("controlCenter.deploymentSnapshot.otherCount", qml)
        self.assertIn("ne lance aucun rollback, nettoyage ni pinning", qml)
        self.assertNotIn('"rollback"', module)
        self.assertNotIn('"pin"', module)

    def test_control_center_offers_a_manual_non_destructive_ostree_recovery_guide(self):
        qml = (ROOT / "control_center/qml/Main.qml").read_text(encoding="utf-8")
        start = qml.index("id: recoveryGuideDialog")
        end = qml.index("anchors.fill: parent", start)
        recovery = qml[start:]
        self.assertIn("OUVRIR LE GUIDE DE RÉCUPÉRATION", qml)
        self.assertIn("recoveryGuideDialog.open()", qml)
        self.assertIn("rpm-ostree status", recovery)
        self.assertIn("sudo rpm-ostree rollback", recovery)
        self.assertIn("LEOS n’exécute aucune commande", recovery)
        self.assertIn("Cette action reste entièrement manuelle", recovery)
        self.assertNotIn("controlCenter.runRollback", qml)

    def test_native_updater_requires_preflight_acknowledgement(self):
        qml = (ROOT / "control_center/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn("id: systemUpdateLaunchDialog", qml)
        self.assertIn("systemUpdateLaunchDialog.open()", qml)
        self.assertIn("OUVRIR BAZZITE UPDATER", qml)
        self.assertIn("ferme les applications importantes", qml)
        self.assertIn("nécessiter un redémarrage", qml)
        dialog = qml[qml.index("id: systemUpdateLaunchDialog"):qml.index("id: recoveryGuideDialog")]
        self.assertIn("controlCenter.openSystemUpdater()", dialog)
        self.assertIn("Aucune installation n'est lancée depuis cette fenêtre", dialog)

    def test_recovery_guide_recommends_actions_from_the_live_ostree_inventory(self):
        qml = (ROOT / "control_center/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn("onOpened: controlCenter.refreshPendingSystemUpdate()", qml)
        self.assertIn("controlCenter.deploymentSnapshot.pendingCount > 0", qml)
        self.assertIn("controlCenter.deploymentSnapshot.otherCount > 0", qml)
        self.assertIn("l'état OSTree n'est pas vérifiable", qml)
        self.assertIn("Aucun autre déploiement n'est actuellement confirmé", qml)
        self.assertIn("Leur présence ne garantit pas qu'ils soient démarrables", qml)

    def test_update_installation_remains_user_controlled(self):
        qml = (ROOT / "control_center/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn("OUVRIR BAZZITE UPDATER", qml)
        self.assertIn("sans lancer de téléchargement ni d’installation", qml)
        self.assertIn('{ label: "Mises à jour", page: 5 }', qml)


if __name__ == "__main__":
    unittest.main()
