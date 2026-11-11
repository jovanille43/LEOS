"""Tests for the safe LEOS system update integration."""
import unittest

from control_center.system_updates import (
    interpret_update_check_exit_code,
    system_update_check_command,
    system_updater_command,
)


class SystemUpdateCommandTests(unittest.TestCase):
    def test_unprivileged_check_uses_polkit_and_uupd_check_only(self):
        tools = {"uupd": "/usr/bin/uupd", "pkexec": "/usr/bin/pkexec"}
        command = system_update_check_command(tools.get, lambda: 1000)
        self.assertEqual(command, ["/usr/bin/pkexec", "/usr/bin/uupd", "update-check"])

    def test_root_check_does_not_wrap_uupd_with_polkit(self):
        tools = {"uupd": "/usr/bin/uupd", "pkexec": "/usr/bin/pkexec"}
        command = system_update_check_command(tools.get, lambda: 0)
        self.assertEqual(command, ["/usr/bin/uupd", "update-check"])

    def test_check_is_unavailable_without_required_tools(self):
        self.assertIsNone(system_update_check_command(lambda _name: None, lambda: 1000))
        self.assertIsNone(
            system_update_check_command(
                lambda name: "/usr/bin/uupd" if name == "uupd" else None,
                lambda: 1000,
            )
        )

    def test_official_updater_is_opened_only_when_installed(self):
        self.assertEqual(
            system_updater_command(lambda name: "/usr/bin/bazzite-updater" if name == "bazzite-updater" else None),
            ["/usr/bin/bazzite-updater"],
        )
        self.assertIsNone(system_updater_command(lambda _name: None))

    def test_uupd_exit_codes_are_interpreted_correctly(self):
        self.assertEqual(interpret_update_check_exit_code(0), "available")
        self.assertEqual(interpret_update_check_exit_code(77), "up_to_date")
        self.assertEqual(interpret_update_check_exit_code(126), "cancelled")
        self.assertEqual(interpret_update_check_exit_code(1), "error")


if __name__ == "__main__":
    unittest.main()
