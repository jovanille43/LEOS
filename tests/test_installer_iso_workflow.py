"""Regression tests ensuring ISO publication is gated by structural validation."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class InstallerIsoWorkflowTests(unittest.TestCase):
    def test_iso_workflow_installs_inspection_tools_and_validates_before_upload(self):
        workflow = (ROOT / ".github/workflows/iso.yml").read_text(encoding="utf-8")
        self.assertIn("xorriso libarchive-tools squashfs-tools qemu-system-x86 qemu-system-gui ovmf xvfb imagemagick tesseract-ocr", workflow)
        self.assertIn("Validate ISO boot structure, checksum, and source digest", workflow)
        self.assertIn('bash tools/validate-installer-iso.sh "$ISO_NAME" "$VERIFIED_DIGEST"', workflow)
        self.assertIn("Boot installer ISO with UEFI firmware in QEMU", workflow)
        self.assertIn("pull_request:", workflow)
        self.assertIn("github.event_name != 'pull_request'", workflow)
        self.assertIn("qemu-system-x86_64", workflow)
        self.assertIn("OVMF_CODE", workflow)
        self.assertIn("xvfb-run", workflow)
        self.assertIn("tesseract", workflow)
        self.assertIn("Installation Summary|Installation Destination|Installation Progress|Anaconda WebUI", workflow)
        self.assertIn("LEOS-installer-UEFI-screens/", workflow)
        self.assertLess(
            workflow.index("Validate ISO boot structure, checksum, and source digest"),
            workflow.index("Boot installer ISO with UEFI firmware in QEMU"),
        )
        self.assertLess(
            workflow.index("Boot installer ISO with UEFI firmware in QEMU"),
            workflow.index("Upload installer ISO and checksum"),
        )

    def test_validator_checks_digest_checksum_uefi_and_installer_payload(self):
        validator = (ROOT / "tools/validate-installer-iso.sh").read_text(encoding="utf-8")
        for expected in (
            "sha256sum --check --strict",
            "source_digest_file",
            "Platform Id",
            "0xef",
            "El Torito boot img",
            "UEFI",
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
