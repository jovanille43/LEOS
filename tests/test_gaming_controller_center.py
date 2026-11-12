"""Integration contract for opening Controller Center from Gaming Mode."""

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class GamingControllerCenterTests(unittest.TestCase):
    def test_backend_opens_packaged_controller_center_without_a_shell(self):
        source = (ROOT / "gaming/backend/controller.py").read_text(encoding="utf-8")
        method = source[source.index("def openControllerCenter"):source.index("def openNotificationCentre")]
        self.assertIn('parents[2] / "controller_center" / "main.py"', method)
        self.assertIn("if not entry.is_file()", method)
        self.assertIn('QProcess.startDetached("python3", [str(entry)], str(Path.home()))', method)
        self.assertNotIn("shell=True", method)
        self.assertNotIn("os.system", method)

    def test_controller_center_is_packaged_for_the_installed_image(self):
        desktop_entry = (ROOT / "desktop/applications/leos-controller-center.desktop").read_text(encoding="utf-8")
        recipe = (ROOT / "recipes/common-modules.yml").read_text(encoding="utf-8")
        self.assertIn("/usr/share/leos/controller_center/main.py", desktop_entry)
        self.assertIn("src: controller_center", recipe)

    def test_gaming_quick_panel_offers_controller_setup_to_gamepad_users(self):
        qml = (ROOT / "gaming/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn("leos.openControllerCenter()", qml)
        self.assertIn('text: "CONFIGURER MANETTE"', qml)
        self.assertIn("quickPanelFocusIndex === profileCount + 1", qml)


if __name__ == "__main__":
    unittest.main()
