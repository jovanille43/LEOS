"""Regression tests ensuring ISO publication is gated by structural validation."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class InstallerIsoWorkflowTests(unittest.TestCase):
    def test_iso_workflow_installs_inspection_tools_and_validates_before_upload(self):
        workflow = (ROOT / ".github/workflows/iso.yml").read_text(encoding="utf-8")
        self.assertIn("xorriso libarchive-tools squashfs-tools qemu-system-x86 qemu-system-gui ovmf xvfb imagemagick tesseract-ocr socat", workflow)
        self.assertIn("Validate ISO boot structure, checksum, and source digest", workflow)
        self.assertIn("generate-iso --variant server --web-ui", workflow)
        self.assertIn('bash tools/validate-installer-iso.sh "$ISO_NAME" "$VERIFIED_DIGEST"', workflow)
        self.assertIn("Boot installer ISO with UEFI firmware in QEMU", workflow)
        self.assertIn("pull_request:", workflow)
        self.assertIn("github.event_name != 'pull_request'", workflow)
        self.assertIn("qemu-system-x86_64", workflow)
        self.assertIn("-cpu max -m 6144 -smp 4", workflow)
        self.assertIn("deadline=$((SECONDS + 900))", workflow)
        self.assertIn('-monitor "unix:$monitor_socket,server=on,wait=off"', workflow)
        self.assertIn('grep -aFq "Test this media & install" "$serial_log"', workflow)
        self.assertIn("sendkey up", workflow)
        self.assertIn("sendkey ret", workflow)
        self.assertIn("socat -t 1", workflow)
        self.assertIn(r'printf "sendkey up\n"', workflow)
        self.assertIn(r'printf "sendkey ret\n"', workflow)
        self.assertIn('sleep 10', workflow)
        self.assertIn('QEMU exited immediately after selecting the direct installer entry.', workflow)
        self.assertNotIn('Booting .Install leos', workflow)
        self.assertIn("LEOS-installer-UEFI-monitor.log", workflow)
        self.assertIn("OVMF_CODE", workflow)
        self.assertIn("xvfb-run", workflow)
        self.assertIn("tesseract", workflow)
        qemu_step = workflow.split("      - name: Boot installer ISO with UEFI firmware in QEMU", 1)[1].split(
            "      - name: Upload UEFI boot diagnostics", 1
        )[0]
        continuations = [line.rstrip() for line in qemu_step.splitlines() if line.rstrip().endswith("\\")]
        self.assertTrue(continuations, "QEMU command must use shell line continuations")
        self.assertFalse(any(line.endswith("\\\\") for line in continuations))
        self.assertIn('2>"$qemu_error_log" &', qemu_step)
        self.assertIn("Welcome.*install Fedora Linux now|Installation method|Storage configuration|Review and install|Anaconda WebUI", workflow)
        self.assertIn("LEOS-installer-UEFI-screens/", workflow)
        self.assertLess(
            workflow.index("Validate ISO boot structure, checksum, and source digest"),
            workflow.index("Boot installer ISO with UEFI firmware in QEMU"),
        )
        self.assertLess(
            workflow.index("Boot installer ISO with UEFI firmware in QEMU"),
            workflow.index("Upload installer ISO and checksum"),
        )

    def test_push_to_main_rebuilds_iso_when_validator_changes(self):
        workflow = (ROOT / ".github/workflows/iso.yml").read_text(encoding="utf-8")
        push_trigger = workflow.split("  push:", 1)[1].split("permissions:", 1)[0]
        self.assertIn('      - "tools/validate-installer-iso.sh"', push_trigger)

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
            "unsquashfs -cat",
            "fedora-server.conf",
            "variant_id",
            "visible account-setup configuration",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, validator)


if __name__ == "__main__":
    unittest.main()
