"""Tests for the bounded, shell-free Plasma D-Bus runner."""
import subprocess
import unittest
from unittest.mock import patch

from desktop.plasma_runner import (
    MAX_PLASMA_SCRIPT_BYTES,
    execute_plasma_script,
    plasma_script_command,
)


class PlasmaRunnerTests(unittest.TestCase):
    def test_builds_fixed_busctl_command_without_a_shell(self):
        command = plasma_script_command('print("LEOS");', executable="/usr/bin/busctl")
        self.assertEqual(command[:7], [
            "/usr/bin/busctl", "--user", "call", "org.kde.plasmashell",
            "/PlasmaShell", "org.kde.PlasmaShell", "evaluateScript",
        ])
        self.assertEqual(command[7], "s")
        self.assertEqual(command[8], 'print("LEOS");')

    def test_rejects_empty_nul_and_oversized_scripts(self):
        for value in ("", "   ", "x" + chr(0) + "y"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                plasma_script_command(value, executable="/usr/bin/busctl")
        with self.assertRaises(ValueError):
            plasma_script_command("x" * (MAX_PLASMA_SCRIPT_BYTES + 1), executable="/usr/bin/busctl")

    def test_missing_busctl_is_reported_without_execution(self):
        with patch("desktop.plasma_runner.shutil.which", return_value=None):
            success, message = execute_plasma_script("print(1);")
        self.assertFalse(success)
        self.assertIn("introuvable", message)

    def test_success_is_returned_only_for_zero_exit_status(self):
        completed = subprocess.CompletedProcess(args=[], returncode=0, stdout="()", stderr="")
        success, message = execute_plasma_script(
            "print(1);",
            executable="/usr/bin/busctl",
            runner=lambda *args, **kwargs: completed,
        )
        self.assertTrue(success)
        self.assertIn("acceptée", message)

    def test_dbus_error_is_reported(self):
        completed = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="No such method")
        success, message = execute_plasma_script(
            "print(1);",
            executable="/usr/bin/busctl",
            runner=lambda *args, **kwargs: completed,
        )
        self.assertFalse(success)
        self.assertIn("refusé", message)
        self.assertIn("No such method", message)

    def test_timeout_is_reported(self):
        def timeout(*args, **kwargs):
            raise subprocess.TimeoutExpired(args[0], kwargs["timeout"])
        success, message = execute_plasma_script(
            "print(1);",
            executable="/usr/bin/busctl",
            runner=timeout,
        )
        self.assertFalse(success)
        self.assertIn("délai", message)


if __name__ == "__main__":
    unittest.main()
