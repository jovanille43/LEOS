"""Regression tests for Control Center QProcess completion handling."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ControlCenterProcessLifecycleTests(unittest.TestCase):
    def test_runtime_errors_wait_for_finished_before_releasing_process_slot(self):
        source = (ROOT / "control_center/controller.py").read_text(encoding="utf-8")
        deployment = source[
            source.index("def _on_deployment_status_error"):
            source.index("@Slot()", source.index("def _on_deployment_status_error"))
        ]
        updates = source[
            source.index("def _on_system_update_check_error"):
            source.index("@Slot(result=bool)", source.index("def _on_system_update_check_error"))
        ]

        for handler in (deployment, updates):
            with self.subTest(handler=handler.splitlines()[0]):
                self.assertIn("QProcess.ProcessError.FailedToStart", handler)
                self.assertIn("error !=", handler)
                self.assertNotIn("ProcessError.Crashed", handler)

    def test_finished_handlers_finalize_timeouts_after_kill_completes(self):
        source = (ROOT / "control_center/controller.py").read_text(encoding="utf-8")
        deployment_finished = source[
            source.index("def _on_deployment_status_finished"):
            source.index("def _on_deployment_status_error")
        ]
        update_finished = source[
            source.index("def _on_system_update_check_finished"):
            source.index("def _on_system_update_check_error")
        ]

        self.assertIn("self._deployment_check_running = False", deployment_finished)
        self.assertIn("if self._deployment_timed_out:", deployment_finished)
        self.assertIn("self._system_update_check_running = False", update_finished)
        self.assertIn("if self._system_update_timed_out:", update_finished)


if __name__ == "__main__":
    unittest.main()
