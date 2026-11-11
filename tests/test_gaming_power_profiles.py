"""Tests for the optional native power profile integration."""

import unittest
from unittest.mock import patch

from gaming.backend import power_profiles


class PowerProfileTests(unittest.TestCase):
    @patch("gaming.backend.power_profiles.shutil.which", return_value="/usr/bin/powerprofilesctl")
    @patch("gaming.backend.power_profiles._run", side_effect=["balanced", "* balanced:\n  power-saver:\n  performance:"])
    def test_discovers_only_profiles_advertised_by_daemon(self, _run, _which):
        state = power_profiles.inspect_power_profiles()
        self.assertTrue(state.available)
        self.assertEqual(state.active, "balanced")
        self.assertEqual(state.profiles, ("balanced", "power-saver", "performance"))

    @patch("gaming.backend.power_profiles.shutil.which", return_value=None)
    def test_missing_daemon_is_reported_without_guessing(self, _which):
        state = power_profiles.inspect_power_profiles()
        self.assertFalse(state.available)
        self.assertEqual(state.profiles, ())

    @patch("gaming.backend.power_profiles.inspect_power_profiles")
    def test_unsupported_profile_is_not_applied(self, inspect):
        inspect.return_value = power_profiles.PowerProfileState(
            True, "balanced", ("balanced",), "available"
        )
        with patch("gaming.backend.power_profiles.subprocess.run") as run:
            ok, message = power_profiles.set_power_profile("performance")
        self.assertFalse(ok)
        self.assertIn("pas proposé", message)
        run.assert_not_called()

    @patch("gaming.backend.power_profiles.shutil.which", return_value="/usr/bin/powerprofilesctl")
    @patch("gaming.backend.power_profiles.inspect_power_profiles")
    @patch("gaming.backend.power_profiles.subprocess.run")
    def test_profile_change_uses_native_daemon(self, run, inspect, _which):
        inspect.return_value = power_profiles.PowerProfileState(
            True, "balanced", ("balanced", "performance"), "available"
        )
        run.return_value.returncode = 0
        run.return_value.stderr = ""
        ok, message = power_profiles.set_power_profile("performance")
        self.assertTrue(ok)
        self.assertIn("Performance", message)
        self.assertEqual(run.call_args.args[0], ["/usr/bin/powerprofilesctl", "set", "performance"])
        self.assertEqual(run.call_args.kwargs["timeout"], 4.0)


if __name__ == "__main__":
    unittest.main()
