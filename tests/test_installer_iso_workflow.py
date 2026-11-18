"""Regression tests ensuring ISO publication is gated by structural validation."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class InstallerIsoWorkflowTests(unittest.TestCase):
    def test_iso_workflow_installs_inspection_tools_and_validates_before_upload(self):
        workflow = (ROOT / ".github/workflows/iso.yml").read_text(encoding="utf-8")
        self.assertIn("xorriso libarchive-tools squashfs-tools", workflow)
        self.assertIn("Validate ISO boot structure, checksum, and source digest", workflow)
        self.assertIn('bash tools/validate-installer-iso.sh "$ISO_NAME" "$VERIFIED_DIGEST"', workflow)
        self.assertLess(
            workflow.index("Validate ISO boot structure, checksum, and source digest"),
            workflow.index("Upload installer ISO and checksum"),
        )

    def test_validator_checks_digest_checksum_uefi_and_installer_payload(self):
        validator = (ROOT / "tools/validate-installer-iso.sh").read_text(encoding="utf-8")
        for expected in (
            "sha256sum --check --strict",
            "source_digest_file",
            "Platform Id",
            "0xef",
            "EFI/BOOT/BOOTX64.EFI",
            "EFI/BOOT/grub.cfg",
            "images/pxeboot/vmlinuz",
            "images/pxeboot/initrd.img",
            "images/install.img",
            "unsquashfs -ll",
            "usr/lib/systemd/system/webui-cockpit-ws.service",
            "usr/libexec/anaconda/webui-desktop",
            "usr/share/cockpit/anaconda-webui/index.html",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, validator)


if __name__ == "__main__":
    unittest.main()
