"""Offline tests for LEOS installer provenance manifests."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.installer_manifest import (
    VALIDATION_SCOPE,
    sha256_file,
    write_installer_manifest,
)


class InstallerManifestTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.iso = self.root / "LEOS-standard-test.iso"
        self.payload = b"LEOS installer test payload"
        self.iso.write_bytes(self.payload)
        self.checksum = hashlib.sha256(self.payload).hexdigest()
        Path(str(self.iso) + ".sha256").write_text(
            f"{self.checksum}  {self.iso.name}\n", encoding="utf-8"
        )
        self.digest = "sha256:" + "a" * 64
        Path(str(self.iso) + ".source-digest").write_text(
            self.digest + "\n", encoding="utf-8"
        )
        self.commit = "b" * 40

    def tearDown(self):
        self.temporary.cleanup()

    def test_writes_manifest_only_after_checksum_and_source_digest_match(self):
        output = write_installer_manifest(
            self.iso, "standard", "abc123-latest", self.commit, self.digest
        )
        manifest = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(output, Path(str(self.iso) + ".manifest.json"))
        self.assertEqual(manifest["product"], "LEOS")
        self.assertEqual(manifest["variant"], "standard")
        self.assertEqual(manifest["iso_file"], self.iso.name)
        self.assertEqual(manifest["iso_sha256"], self.checksum)
        self.assertEqual(manifest["source_commit"], self.commit)
        self.assertEqual(manifest["source_image_digest"], self.digest)
        self.assertEqual(manifest["installer_uefi_qemu_smoke"], "passed")
        self.assertEqual(manifest["validation_scope"], VALIDATION_SCOPE)

    def test_sha256_reads_in_bounded_chunks(self):
        self.assertEqual(sha256_file(self.iso, chunk_size=3), self.checksum)
        with self.assertRaisesRegex(ValueError, "positive"):
            sha256_file(self.iso, chunk_size=0)

    def test_rejects_a_mismatched_iso_checksum(self):
        Path(str(self.iso) + ".sha256").write_text("0" * 64 + "  wrong.iso\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "checksum"):
            write_installer_manifest(self.iso, "standard", "tag", self.commit, self.digest)

    def test_rejects_a_mismatched_source_image_digest(self):
        with self.assertRaisesRegex(ValueError, "source digest"):
            write_installer_manifest(
                self.iso, "standard", "tag", self.commit, "sha256:" + "c" * 64
            )

    def test_rejects_invalid_commit_digest_variant_and_image_tag(self):
        cases = [
            ("unknown", "tag", self.commit, self.digest),
            ("standard", "bad tag", self.commit, self.digest),
            ("standard", "tag", "not-a-commit", self.digest),
            ("standard", "tag", self.commit, "not-a-digest"),
        ]
        for variant, tag, commit, digest in cases:
            with self.subTest(variant=variant, tag=tag, commit=commit, digest=digest):
                with self.assertRaises(ValueError):
                    write_installer_manifest(self.iso, variant, tag, commit, digest)

    def test_rejects_empty_iso_and_missing_sidecars(self):
        empty_iso = self.root / "empty.iso"
        empty_iso.touch()
        with self.assertRaisesRegex(ValueError, "missing or empty"):
            write_installer_manifest(empty_iso, "standard", "tag", self.commit, self.digest)
        missing = self.root / "missing.iso"
        missing.write_bytes(b"iso")
        with self.assertRaisesRegex(ValueError, "checksum sidecar"):
            write_installer_manifest(missing, "standard", "tag", self.commit, self.digest)


if __name__ == "__main__":
    unittest.main()
