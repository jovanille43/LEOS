"""Tests for the safe LEOS system update integration."""
import unittest

from control_center.system_updates import (
    interpret_update_check_exit_code,
    system_update_check_command,
    system_updater_command,
    pending_deployment_from_status,
    deployment_inventory_from_status,
    rpm_ostree_status_command,
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

    def test_rpm_ostree_status_is_read_only(self):
        self.assertEqual(
            rpm_ostree_status_command(lambda name: "/usr/bin/rpm-ostree" if name == "rpm-ostree" else None),
            ["/usr/bin/rpm-ostree", "status", "--json"],
        )
        self.assertIsNone(rpm_ostree_status_command(lambda _name: None))

    def test_detects_staged_deployment_and_ignores_booted_deployment(self):
        payload = """{"deployments":[
            {"checksum":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","booted":true,"staged":false},
            {"checksum":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb","booted":false,"staged":true,"version":"stable-2026.11"}
        ]}"""
        self.assertEqual(
            pending_deployment_from_status(payload),
            {"checksum": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", "version": "stable-2026.11"},
        )

    def test_deployment_inventory_reports_booted_and_retained_entries(self):
        payload = """{"deployments":[
            {"checksum":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","booted":true,"version":"stable-2026.11"},
            {"checksum":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb","booted":false,"pinned":true,"version":"stable-2026.10"},
            {"checksum":"cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc","booted":false,"staged":true,"version":"stable-2026.12"}
        ]}"""
        self.assertEqual(
            deployment_inventory_from_status(payload),
            {
                "available": True,
                "bootedVersion": "stable-2026.11",
                "bootedChecksum": "aaaaaaaaaaaa",
                "otherCount": 2,
                "pendingCount": 1,
                "pinnedCount": 1,
            },
        )

    def test_deployment_inventory_requires_one_valid_booted_entry(self):
        checksum = "d" * 64
        self.assertIsNone(
            deployment_inventory_from_status(
                '{"deployments":[{"checksum":"' + checksum + '","booted":false}]}'
            )
        )
        self.assertIsNone(
            deployment_inventory_from_status(
                '{"deployments":['
                '{"checksum":"' + checksum + '","booted":true},'
                '{"checksum":"' + checksum + '","booted":true}]}'
            )
        )
        self.assertIsNone(
            deployment_inventory_from_status(
                '{"deployments":[{"checksum":"not-a-checksum","booted":true}]}'
            )
        )

    def test_deployment_inventory_sanitizes_untrusted_version_text(self):
        checksum = "e" * 64
        payload = (
            '{"deployments":[{"checksum":"' + checksum
            + '","booted":true,"version":"bad\\u0001version"}]}'
        )
        result = deployment_inventory_from_status(payload)
        self.assertIsNotNone(result)
        self.assertEqual(result["bootedVersion"], "Version inconnue")

    def test_deployment_inventory_rejects_unbounded_or_invalid_json(self):
        from control_center.system_updates import MAX_RPM_OSTREE_STATUS_CHARS

        self.assertIsNone(deployment_inventory_from_status(" " * (MAX_RPM_OSTREE_STATUS_CHARS + 1)))
        self.assertIsNone(deployment_inventory_from_status("not-json"))
        self.assertIsNone(deployment_inventory_from_status('{"deployments":[]}'))

    def test_pending_deployment_without_version_uses_fallback(self):
        self.assertEqual(
            pending_deployment_from_status(
                '{"deployments":[{"checksum":"cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc","booted":false,"pending":true}]}'
            ),
            {"checksum": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", "version": "Nouvelle version"},
        )

    def test_invalid_or_non_pending_status_is_ignored(self):
        self.assertIsNone(pending_deployment_from_status("not-json"))
        self.assertIsNone(
            pending_deployment_from_status(
                '{"deployments":[{"checksum":"dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd","booted":true,"staged":true}]}'
            )
        )

    def test_status_parser_rejects_oversized_json(self):
        from control_center.system_updates import MAX_RPM_OSTREE_STATUS_CHARS

        self.assertIsNone(pending_deployment_from_status(" " * (MAX_RPM_OSTREE_STATUS_CHARS + 1)))

    def test_status_parser_rejects_deeply_nested_json_fields(self):
        checksum = "f" * 64
        nested = "[" * 200 + "0" + "]" * 200
        payload = (
            '{"deployments":[{"checksum":"' + checksum
            + '","booted":false,"staged":true,"unexpected":' + nested + '}]}'
        )
        self.assertIsNone(pending_deployment_from_status(payload))

    def test_status_parser_rejects_excessive_deployment_lists(self):
        from control_center.system_updates import MAX_RPM_OSTREE_DEPLOYMENTS

        payload = '{"deployments":[' + ",".join("{}" for _ in range(MAX_RPM_OSTREE_DEPLOYMENTS + 1)) + ']}'
        self.assertIsNone(pending_deployment_from_status(payload))

    def test_status_parser_requires_a_sha256_checksum_and_safe_version(self):
        self.assertIsNone(
            pending_deployment_from_status(
                '{"deployments":[{"checksum":"not-a-checksum","booted":false,"staged":true}]}'
            )
        )
        checksum = "e" * 64
        payload = '{"deployments":[{"checksum":"' + checksum + '","booted":false,"staged":true,"version":"bad\\u0001version"}]}'
        self.assertEqual(
            pending_deployment_from_status(payload),
            {"checksum": checksum, "version": "Nouvelle version"},
        )

    def test_uupd_exit_codes_are_interpreted_correctly(self):
        self.assertEqual(interpret_update_check_exit_code(0), "available")
        self.assertEqual(interpret_update_check_exit_code(77), "up_to_date")
        self.assertEqual(interpret_update_check_exit_code(126), "cancelled")
        self.assertEqual(interpret_update_check_exit_code(1), "error")


if __name__ == "__main__":
    unittest.main()
