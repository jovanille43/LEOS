"""Tests for immutable GHCR image references used by ISO generation."""

from pathlib import Path
import os
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".github/scripts/pin-image-digest.sh"
VALID_IMAGE = "ghcr.io/leos-owner/leos:latest"
VALID_DIGEST = "sha256:" + "a" * 64


class IsoImagePinningTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.authfile = self.root / "auth.json"
        self.authfile.write_text("{}", encoding="utf-8")
        self.output_file = self.root / "github-output"
        self.call_log = self.root / "podman-calls"
        self.podman = self.root / "podman"
        self.podman.write_text(
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            "printf '%s\\n' \"$*\" >> \"$PODMAN_CALL_LOG\"\n"
            "if [[ \"$1\" == pull ]]; then\n"
            "  exit \"$MOCK_PULL_EXIT\"\n"
            "fi\n"
            "if [[ \"$1\" == image && \"$2\" == inspect ]]; then\n"
            "  printf '%s\\n' \"$MOCK_DIGEST\"\n"
            "  exit 0\n"
            "fi\n"
            "exit 64\n",
            encoding="utf-8",
        )
        self.podman.chmod(0o755)

    def run_helper(self, image_ref=VALID_IMAGE, *, digest=VALID_DIGEST, pull_exit=0):
        environment = os.environ.copy()
        environment.update(
            {
                "PODMAN_BIN": str(self.podman),
                "PODMAN_CALL_LOG": str(self.call_log),
                "MOCK_DIGEST": digest,
                "MOCK_PULL_EXIT": str(pull_exit),
            }
        )
        return subprocess.run(
            ["bash", str(SCRIPT), image_ref, str(self.authfile), str(self.output_file)],
            check=False,
            capture_output=True,
            text=True,
            env=environment,
        )

    def test_pulls_tag_then_outputs_immutable_repository_digest(self):
        result = self.run_helper()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            self.output_file.read_text(encoding="utf-8"),
            f"ref=ghcr.io/leos-owner/leos@{VALID_DIGEST}\n"
            f"tag_ref={VALID_IMAGE}\n",
        )
        calls = self.call_log.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(calls), 2)
        self.assertIn("pull --authfile", calls[0])
        self.assertTrue(calls[0].endswith(VALID_IMAGE))
        self.assertIn("image inspect --format {{.Digest}}", calls[1])
        self.assertTrue(calls[1].endswith(VALID_IMAGE))

    def test_rejects_image_references_outside_the_expected_ghcr_names(self):
        for image_ref in (
            "docker.io/leos-owner/leos:latest",
            "ghcr.io/leos-owner/unrelated:latest",
            "ghcr.io/leos-owner/leos:latest;touch /tmp/unexpected",
            "ghcr.io/leos-owner/leos",
        ):
            with self.subTest(image_ref=image_ref):
                result = self.run_helper(image_ref)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(self.call_log.exists())
                self.assertFalse(self.output_file.exists())

    def test_rejects_malformed_digest_without_writing_output(self):
        result = self.run_helper(digest="not-a-digest")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("valid SHA-256 image digest", result.stdout)
        self.assertFalse(self.output_file.exists())
        self.assertEqual(len(self.call_log.read_text(encoding="utf-8").splitlines()), 2)

    def test_failed_pull_does_not_inspect_or_pin_image(self):
        result = self.run_helper(pull_exit=23)

        self.assertEqual(result.returncode, 23)
        self.assertFalse(self.output_file.exists())
        self.assertEqual(len(self.call_log.read_text(encoding="utf-8").splitlines()), 1)

    def test_missing_authfile_fails_before_podman(self):
        self.authfile.unlink()
        result = self.run_helper()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("auth file is missing", result.stdout)
        self.assertFalse(self.call_log.exists())
        self.assertFalse(self.output_file.exists())

    def test_empty_digest_is_rejected(self):
        result = self.run_helper(digest="")

        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.output_file.exists())


if __name__ == "__main__":
    unittest.main()
