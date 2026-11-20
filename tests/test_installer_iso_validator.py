"""Regression tests for the fail-closed installer ISO validator."""

import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "tools" / "validate-installer-iso.sh"
SOURCE_DIGEST = "sha256:" + ("a" * 64)

VALID_EL_TORITO = """El Torito catalog  : 22 1
El Torito boot img :   1  BIOS  y   none  0x0000  0x00      4         299
El Torito boot img :   2  UEFI  y   none  0x0000  0x00  26544     3040898
"""

VALID_EL_TORITO_PLATFORM_ID = """El Torito catalog: 22 1
El Torito image: 1
  Platform Id : 0xef (EFI)
"""

VALID_ISO_CONTENTS = """EFI/BOOT/BOOTX64.EFI
EFI/BOOT/grub.cfg
images/pxeboot/vmlinuz
images/pxeboot/initrd.img
images/install.img
"""

VALID_RUNTIME_CONTENTS = """squashfs-root/usr/lib/systemd/system/webui-cockpit-ws.service
squashfs-root/usr/libexec/anaconda/webui-desktop
squashfs-root/usr/share/cockpit/anaconda-webui/index.html
"""


class InstallerIsoValidatorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.iso = self.work / "LEOS-standard-latest.iso"
        self.iso.write_bytes(b"test ISO fixture bytes")
        digest = hashlib.sha256(self.iso.read_bytes()).hexdigest()
        Path(str(self.iso) + ".sha256").write_text(
            f"{digest}  {self.iso.name}\n", encoding="utf-8"
        )
        Path(str(self.iso) + ".source-digest").write_text(
            SOURCE_DIGEST + "\n", encoding="utf-8"
        )

        fake_bin = self.work / "bin"
        fake_bin.mkdir()
        xorriso = fake_bin / "xorriso"
        xorriso.write_text(
            '#!/bin/sh\nprintf "%s\\n" "$LEOS_TEST_EL_TORITO_OUTPUT"\n',
            encoding="utf-8",
        )
        bsdtar = fake_bin / "bsdtar"
        bsdtar.write_text(
            '#!/bin/sh\ncase "$1" in\n'
            '  -tf) printf "%s\\n" "$LEOS_TEST_ISO_CONTENTS" ;;\n'
            '  -xOf) printf "fake SquashFS payload\\n" ;;\n'
            '  *) exit 2 ;;\nesac\n',
            encoding="utf-8",
        )
        unsquashfs = fake_bin / "unsquashfs"
        unsquashfs.write_text(
            '#!/bin/sh\\ncase "$1" in\\n'
            '  -ll) printf "%s\\n" "$LEOS_TEST_RUNTIME_CONTENTS" ;;\\n'
            '  -cat) printf "%s\\n" "$LEOS_TEST_ANACONDA_PROFILE" ;;\\n'
            '  *) exit 2 ;;\\nesac\\n',
            encoding="utf-8",
        )
        xorriso.chmod(0o755)
        bsdtar.chmod(0o755)
        unsquashfs.chmod(0o755)

        self.env = os.environ.copy()
        self.env["PATH"] = str(fake_bin) + os.pathsep + self.env.get("PATH", "")
        self.env["LEOS_TEST_EL_TORITO_OUTPUT"] = VALID_EL_TORITO
        self.env["LEOS_TEST_ISO_CONTENTS"] = VALID_ISO_CONTENTS
        self.env["LEOS_TEST_RUNTIME_CONTENTS"] = VALID_RUNTIME_CONTENTS
        self.env["LEOS_TEST_ANACONDA_PROFILE"] = (
            "[Profile]\\n"
            "profile_id = fedora-server\\n"
            "base_profile = fedora\\n"
            "[Profile Detection]\\n"
            "os_id = fedora\\n"
            "variant_id = server\\n"
        )

    def run_validator(self):
        return subprocess.run(
            ["bash", str(VALIDATOR), str(self.iso), SOURCE_DIGEST],
            check=False,
            capture_output=True,
            text=True,
            env=self.env,
        )

    def test_accepts_iso_with_valid_checksum_uefi_catalog_and_installer_files(self):
        result = self.run_validator()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("LEOS installer ISO structural validation passed", result.stdout)

    def test_accepts_numeric_uefi_platform_id_from_older_xorriso_output(self):
        self.env["LEOS_TEST_EL_TORITO_OUTPUT"] = VALID_EL_TORITO_PLATFORM_ID
        result = self.run_validator()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_rejects_iso_without_uefi_boot_catalog_entry(self):
        self.env["LEOS_TEST_EL_TORITO_OUTPUT"] = (
            "El Torito boot img :   1  BIOS  y   none  0x0000  0x00      4         299"
        )
        result = self.run_validator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("does not advertise a UEFI", result.stderr)

    def test_rejects_iso_missing_anaconda_installation_runtime(self):
        self.env["LEOS_TEST_ISO_CONTENTS"] = VALID_ISO_CONTENTS.replace(
            "images/install.img\n", ""
        )
        result = self.run_validator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("images/install.img", result.stderr)

    def test_rejects_iso_missing_anaconda_webui_runtime(self):
        self.env["LEOS_TEST_RUNTIME_CONTENTS"] = VALID_RUNTIME_CONTENTS.replace(
            "usr/share/cockpit/anaconda-webui/index.html\n", ""
        )
        result = self.run_validator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("anaconda-webui/index.html", result.stderr)

    def test_rejects_installer_without_fedora_server_account_profile(self):
        self.env["LEOS_TEST_ANACONDA_PROFILE"] = (
            "[Profile]\\n"
            "profile_id = fedora-kinoite\\n"
            "base_profile = fedora-kde\\n"
            "[Profile Detection]\\n"
            "os_id = fedora\\n"
            "variant_id = kinoite\\n"
        )
        result = self.run_validator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("fedora-server profile", result.stderr)

    def test_rejects_checksum_mismatch(self):
        self.iso.write_bytes(b"corrupted ISO fixture bytes")
        result = self.run_validator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SHA-256 verification failed", result.stderr)

    def test_rejects_source_digest_mismatch(self):
        Path(str(self.iso) + ".source-digest").write_text(
            "sha256:" + ("b" * 64) + "\n", encoding="utf-8"
        )
        result = self.run_validator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("does not match", result.stderr)


if __name__ == "__main__":
    unittest.main()
