"""Regression tests for the LEOS first-run onboarding contract."""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class FirstRunOnboardingTests(unittest.TestCase):
    def test_desktop_choice_completes_onboarding_in_desktop_branch(self):
        source = (ROOT / "launcher/main.py").read_text(encoding="utf-8")
        handler = source.split("    def handle_mode(mode: str) -> None:", 1)[1].split(
            "\n    selected_mode =", 1
        )[0]
        gaming_branch = handler.split('        if mode == "gaming":', 1)[1].split(
            '        if mode == "desktop":', 1
        )[0]
        desktop_branch = handler.split('        if mode == "desktop":', 1)[1]
        self.assertNotIn("completeOnboarding()", gaming_branch)
        self.assertIn("manager.rememberMode(\"desktop\")", desktop_branch)
        self.assertIn("selector_controller.completeOnboarding()", desktop_branch)

    def test_gaming_choice_does_not_finish_onboarding_when_only_spawned(self):
        source = (ROOT / "launcher/main.py").read_text(encoding="utf-8")
        gaming_branch = source.split('        if mode == "gaming":', 1)[1].split(
            '        if mode == "desktop":', 1
        )[0]
        self.assertIn("start_gaming()", gaming_branch)
        self.assertIn("child-process spawn is not proof of readiness", gaming_branch)
        self.assertNotIn("completeOnboarding()", gaming_branch)

    def test_gaming_mode_and_onboarding_persist_only_after_qml_load(self):
        source = (ROOT / "gaming/main.py").read_text(encoding="utf-8")
        qml_failure = source.index("if not engine.rootObjects():")
        settings_write = source.index("controller.settings.set_many({")
        self.assertLess(qml_failure, settings_write)
        self.assertIn('"last_mode": "gaming"', source)
        self.assertIn('"onboarding_complete": True', source)

    def test_returning_to_desktop_from_gaming_offers_optional_apps(self):
        source = (ROOT / "gaming/main.py").read_text(encoding="utf-8")
        self.assertIn("controller.desktopRequested.connect(handle_desktop_request)", source)
        self.assertIn('returned_to_desktop["value"] = True', source)
        self.assertIn('if returned_to_desktop["value"]:', source)
        self.assertIn("_start_optional_default_apps_setup()", source)
        self.assertIn("/usr/libexec/leos-default-apps-setup", source)
        self.assertLess(source.index("exit_code = app.exec()"), source.index(
            "if returned_to_desktop[\"value\"]:"
        ))


if __name__ == "__main__":
    unittest.main()
