"""Runtime tests for creating and verifying LEOS Sigstore artifact bundles."""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".github/scripts/sign-iso-artifacts.sh"
FAKE_BUNDLE = '{"fake":"sigstore-bundle"}\\n'


class SignIsoArtifactsTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.workdir = Path(self.temporary_directory.name)
        self.iso = self.workdir / "LEOS-standard-test.iso"
        self.manifest = self.workdir / "LEOS-standard-test.iso.json"
        self.public_key = self.workdir / "cosign.pub"
        self.iso.write_bytes(b"test ISO payload")
        self.manifest.write_text('{"product":"LEOS"}\\n', encoding="utf-8")
        self.public_key.write_text("test-public-key\\n", encoding="utf-8")

        self.bin_dir = self.workdir / "bin"
        self.bin_dir.mkdir()
        self.call_log = self.workdir / "cosign-calls.txt"
        self.fake_cosign = self.bin_dir / "cosign"
        self.fake_cosign.write_text(
            "#!/usr/bin/env bash\\n"
            "set -euo pipefail\\n"
            '[[ -z "${SIGNING_SECRET:-}" ]]\\n'
            'printf "%s\\\\n" "$*" >> "$COSIGN_CALL_LOG"\\n'
            'command="$1"; shift\\n'
            'if [[ "$command" == sign-blob ]]; then\\n'
            '  [[ "$1" == --yes ]]\\n'
            '  shift\\n'
            '  [[ "$1" == --key && "$3" == --bundle ]]\\n'
            '  key="$2"; bundle="$4"; file="$5"\\n'
            '  [[ "$(stat -c %a "$key")" == 600 ]]\\n'
            '  [[ "$(cat "$key")" == "test-private-key" ]]\\n'
            '  [[ -s "$file" ]]\\n'
            '  printf \'{"fake":"sigstore-bundle"}\\\\n\' > "$bundle"\\n'
            'elif [[ "$command" == verify-blob ]]; then\\n'
            '  [[ "$1" == --key && "$3" == --bundle ]]\\n'
            '  key="$2"; bundle="$4"; file="$5"\\n'
            '  [[ "$key" == "$EXPECTED_PUBLIC_KEY" ]]\\n'
            '  [[ "$(cat "$bundle")" == \'{"fake":"sigstore-bundle"}\' ]]\\n'
            '  [[ -s "$file" ]]\\n'
            'else\\n'
            '  exit 97\\n'
            'fi\\n',
            encoding="utf-8",
        )
        self.fake_cosign.chmod(0o755)

    def run_signer(self, *, secret="test-private-key"):
        environment = os.environ.copy()
        environment["PATH"] = f"{self.bin_dir}:{environment.get('PATH', '')}"
        environment["COSIGN_CALL_LOG"] = str(self.call_log)
        environment["EXPECTED_PUBLIC_KEY"] = str(self.public_key)
        environment.pop("SIGNING_SECRET", None)
        if secret is not None:
            environment["SIGNING_SECRET"] = secret
        return subprocess.run(
            [
                "bash",
                str(SCRIPT),
                str(self.iso),
                str(self.manifest),
                str(self.public_key),
            ],
            check=False,
            capture_output=True,
            text=True,
            env=environment,
        )

    def test_signs_and_verifies_iso_and_provenance_with_sigstore_bundles(self):
        result = self.run_signer()
        self.assertEqual(result.returncode, 0, result.stderr)
        iso_bundle = Path(f"{self.iso}.sigstore.json")
        manifest_bundle = Path(f"{self.manifest}.sigstore.json")
        self.assertEqual(iso_bundle.read_text(encoding="utf-8"), FAKE_BUNDLE)
        self.assertEqual(manifest_bundle.read_text(encoding="utf-8"), FAKE_BUNDLE)
        calls = self.call_log.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(calls), 4)
        self.assertTrue(calls[0].startswith("sign-blob --yes --key "))
        self.assertTrue(calls[1].startswith("verify-blob --key "))
        self.assertTrue(calls[2].startswith("sign-blob --yes --key "))
        self.assertTrue(calls[3].startswith("verify-blob --key "))
        self.assertNotIn("test-private-key", "\\n".join(calls))

    def test_refuses_to_sign_without_repository_secret(self):
        result = self.run_signer(secret=None)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SIGNING_SECRET", result.stderr)
        self.assertFalse(self.call_log.exists())
        self.assertFalse(Path(f"{self.iso}.sigstore.json").exists())
        self.assertFalse(Path(f"{self.manifest}.sigstore.json").exists())

    def test_refuses_to_overwrite_existing_bundle(self):
        existing_bundle = Path(f"{self.iso}.sigstore.json")
        existing_bundle.write_text("keep-me\\n", encoding="utf-8")
        result = self.run_signer()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(existing_bundle.read_text(encoding="utf-8"), "keep-me\\n")
        self.assertFalse(self.call_log.exists())

    def test_iso_workflow_uploads_both_sigstore_bundles_before_download(self):
        workflow = (ROOT / ".github/workflows/iso.yml").read_text(encoding="utf-8")
        sign = workflow.index("Sign and verify LEOS ISO and provenance artifacts")
        upload = workflow.index("Upload installer ISO and checksum")
        self.assertLess(sign, upload)
        self.assertIn("SIGNING_SECRET: ${{ secrets.SIGNING_SECRET }}", workflow[sign:upload])
        self.assertIn("bash .github/scripts/sign-iso-artifacts.sh", workflow[sign:upload])
        self.assertIn("${{ steps.image.outputs.filename }}.sigstore.json", workflow[upload:])
        self.assertIn("${{ steps.image.outputs.provenance }}.sigstore.json", workflow[upload:])


if __name__ == "__main__":
    unittest.main()
