"""Regression tests ensuring ISO publication is gated by structural validation."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class InstallerIsoWorkflowTests(unittest.TestCase):
    def test_iso_workflow_installs_inspection_tools_and_validates_before_upload(self):
        workflow = (ROOT / ".github/workflows/iso.yml").read_text(encoding="utf-8")
        self.assertIn("CLI_IMAGE: ghcr.io/blue-build/cli:v0.9.42-installer", workflow)
        self.assertIn("xorriso libarchive-tools squashfs-tools qemu-system-x86 qemu-system-gui ovmf xvfb imagemagick tesseract-ocr socat", workflow)
        self.assertIn("Validate ISO boot structure, checksum, and source digest", workflow)
        self.assertIn("generate-iso --variant server --web-ui", workflow)
        self.assertIn('bash tools/validate-installer-iso.sh "$ISO_NAME" "$VERIFIED_DIGEST"', workflow)
        self.assertIn("Boot installer ISO with UEFI firmware in QEMU", workflow)
        self.assertIn('workflows: ["Build LEOS"]', workflow)
        self.assertIn("workflow_run:", workflow)
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

    def test_iso_waits_for_successful_main_image_build_and_avoids_stale_push_runs(self):
        workflow = (ROOT / ".github/workflows/iso.yml").read_text(encoding="utf-8")
        self.assertIn('workflows: ["Build LEOS"]', workflow)
        self.assertIn("branches: [main]", workflow)
        self.assertIn("workflow_run:", workflow)
        self.assertNotIn("  push:", workflow)
        self.assertNotIn('      - ".github/workflows/iso.yml"', workflow)
        self.assertIn(
            "if: github.event_name != 'workflow_run' || github.event.workflow_run.conclusion == 'success'",
            workflow,
        )
        self.assertIn("(github.event_name == 'workflow_run')", workflow)
        smoke = workflow.index("Smoke-test the packaged LEOS first-session selector")
        generate = workflow.index("Generate bootable installer ISO")
        self.assertLess(smoke, generate)
        self.assertNotIn("  pull_request:", workflow)

    def test_image_smoke_checks_the_complete_leos_desktop_profile(self):
        smoke = (ROOT / "tools/smoke-test-leos-session-selector.sh").read_text(encoding="utf-8")
        for asset in (
            "/usr/share/plasma/desktoptheme/leos/metadata.json",
            "/usr/share/plasma/look-and-feel/org.leos.desktop/manifest.json",
            "/usr/share/plasma/look-and-feel/org.leos.desktop/contents/splash/Splash.qml",
            "/usr/share/icons/leos/index.theme",
            "/usr/share/aurorae/themes/leos/metadata.desktop",
            "/usr/share/aurorae/themes/leos/leosrc",
            "/usr/share/sddm/themes/leos/Main.qml",
            "/usr/share/plymouth/themes/leos/leos.plymouth",
        ):
            self.assertIn(asset, smoke)
        for executable in ("plasma-apply-colorscheme", "plasma-apply-desktoptheme", "kreadconfig6", "kwriteconfig6"):
            self.assertIn(executable, smoke)
        self.assertIn("plasma-changeicons", smoke)
        self.assertIn("style = PlasmaStyleManager()", smoke)
        self.assertIn("PlasmaIconThemeManager", smoke)
        self.assertIn("KdeColorSchemeManager", smoke)
        self.assertIn("PlasmaVisualChromeManager", smoke)
        self.assertIn("LEOS Aurorae window decoration", smoke)
        self.assertIn("LEOS first-run identity dialog shown successfully", smoke)
        self.assertIn("/usr/bin/python3 - <<PY\nfrom desktop.icon_theme", smoke)
        self.assertIn("\nPY\n\n        expected_exec=", smoke)

    def test_iso_uses_the_exact_image_tag_from_its_triggering_main_commit(self):
        workflow = (ROOT / ".github/workflows/iso.yml").read_text(encoding="utf-8")
        self.assertIn("SOURCE_SHA: ${{ github.event.workflow_run.head_sha || github.sha }}", workflow)
        self.assertIn('source_prefix="${SOURCE_SHA:0:7}-"', workflow)
        self.assertIn('skopeo list-tags --authfile /root/.docker/config.json', workflow)
        self.assertIn("Expected exactly one published image tag", workflow)
        self.assertIn('echo "tag=$IMAGE_TAG" >> "$GITHUB_OUTPUT"', workflow)
        self.assertIn("steps.image.outputs.tag", workflow)
        self.assertLess(
            workflow.index("Authenticate to GitHub Container Registry"),
            workflow.index("Select published image"),
        )
        self.assertLess(
            workflow.index("Select published image"),
            workflow.index("Resolve and verify LEOS image tag"),
        )

    def test_successful_main_image_build_triggers_all_three_installer_isos(self):
        workflow = (ROOT / ".github/workflows/iso.yml").read_text(encoding="utf-8")
        self.assertIn('workflows: ["Build LEOS"]', workflow)
        self.assertIn("types: [completed]", workflow)
        self.assertIn("branches: [main]", workflow)
        self.assertIn(
            "if: github.event_name != 'workflow_run' || github.event.workflow_run.conclusion == 'success'",
            workflow,
        )
        self.assertIn("(github.event_name == 'workflow_run')", workflow)
        self.assertIn("'[\"standard\",\"nvidia-legacy\",\"nvidia-modern\"]'", workflow)
        self.assertIn("max-parallel: 1", workflow)
        self.assertIn("VARIANT: ${{ matrix.variant }}", workflow)
        self.assertIn("name: LEOS-installer-${{ matrix.variant }}-${{ steps.image.outputs.tag }}", workflow)
        self.assertIn("inputs.variant || 'standard'", workflow)
        self.assertIn("inputs.image_tag || 'latest'", workflow)

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
