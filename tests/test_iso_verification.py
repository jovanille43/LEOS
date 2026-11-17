from __future__ import annotations

import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".github/scripts/verify-installer-iso.sh"
WORKFLOW = ROOT / ".github/workflows/iso.yml"


class InstallerIsoVerificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bin_dir = self.root / "bin"
        self.bin_dir.mkdir()
        self.iso = self.root / "LEOS-test.iso"
        self.iso.write_bytes(b"synthetic ISO fixture")
        self.checksum = Path(f"{self.iso}.sha256")
        self.write_valid_checksum()

        self.xorriso = self.bin_dir / "xorriso"
        self.xorriso.write_text(
            "#!/usr/bin/env python3\n"
            "import os\n"
            "import sys\n"
            "print(os.environ.get('MOCK_XORRISO_REPORT', ''))\n"
            "sys.exit(int(os.environ.get('MOCK_XORRISO_EXIT', '0')))\n",
            encoding="utf-8",
        )
        self.xorriso.chmod(0o755)

    def write_valid_checksum(self) -> None:
        digest = hashlib.sha256(self.iso.read_bytes()).hexdigest()
        self.checksum.write_text(f"{digest}  {self.iso.name}\n", encoding="utf-8")

    def run_verifier(self, report: str, *, xorriso_exit: int = 0) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["PATH"] = f"{self.bin_dir}:{environment.get('PATH', '')}"
        environment["MOCK_XORRISO_REPORT"] = report
        environment["MOCK_XORRISO_EXIT"] = str(xorriso_exit)
        return subprocess.run(
            ["bash", str(SCRIPT), str(self.iso)],
            check=False,
            capture_output=True,
            text=True,
            env=environment,
        )

    def test_accepts_matching_checksum_and_uefi_catalog(self) -> None:
        report = "El Torito catalog : 1 1164\nEl Torito boot img : 1 UEFI y none\n"
        result = self.run_verifier(report)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("LEOS-test.iso: OK", result.stdout)
        self.assertIn("UEFI boot-catalog checks passed", result.stdout)

    def test_rejects_checksum_mismatch_before_inspecting_boot_catalog(self) -> None:
        self.iso.write_bytes(b"changed ISO fixture")
        report = "El Torito catalog : 1 1164\nEl Torito boot img : 1 UEFI y none\n"
        result = self.run_verifier(report)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("FAILED", result.stdout)
        self.assertNotIn("El Torito catalog", result.stdout)

    def test_rejects_iso_without_uefi_entry(self) -> None:
        report = "El Torito catalog : 1 1164\nEl Torito boot img : 1 BIOS y none\n"
        result = self.run_verifier(report)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("does not advertise an UEFI", result.stderr)

    def test_rejects_unreadable_boot_catalog(self) -> None:
        result = self.run_verifier("xorriso failure", xorriso_exit=32)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("could not read the ISO", result.stderr)

    def test_requires_iso_checksum_sidecar(self) -> None:
        self.checksum.unlink()
        report = "El Torito catalog : 1 1164\nEl Torito boot img : 1 UEFI y none\n"
        result = self.run_verifier(report)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("checksum file is missing", result.stderr)

    def test_workflow_runs_verifier_before_signing_the_iso(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        verify = workflow.index("Verify ISO checksum and UEFI boot catalog")
        sign = workflow.index("Sign and verify LEOS ISO and provenance artifacts")
        self.assertLess(verify, sign)
        self.assertIn("verify-installer-iso.sh", workflow[verify:sign])
        self.assertIn("xorriso", workflow)


if __name__ == "__main__":
    unittest.main()
